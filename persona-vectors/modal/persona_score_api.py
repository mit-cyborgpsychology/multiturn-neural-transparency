import modal
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from huggingface_hub import login
from typing import Dict, Optional
from pydantic import BaseModel
from fastapi import Header, HTTPException
from pathlib import Path
import json
import os

LOCAL_VECTORS_PATH = os.path.join(os.path.dirname(__file__), "../generation/stored_persona_vectors")

image = (
    modal.Image.debian_slim()
    .pip_install(
        "torch",
        "transformers",
        "huggingface_hub",
        "accelerate",
        "fastapi[standard]"
    )
    .add_local_dir(
        os.path.abspath(LOCAL_VECTORS_PATH),
        remote_path="/root/stored_persona_vectors"
    )
)

app = modal.App("persona-vector-api")

VECTORS_PATH = Path("/root/stored_persona_vectors")

class SystemPrompt(BaseModel):
    system: Optional[str] = None

class PersonaVectorResponse(BaseModel):
    persona_vector_ratings: Dict[str, Dict[str, float]]

@app.cls(
    image=image,
    gpu="A100-40GB",
    scaledown_window=300,
    timeout=200,
    secrets=[modal.Secret.from_name("secrets")]
)
@modal.concurrent(max_inputs=4)
class PersonaScoreAPI:
    @modal.enter()
    def load_model(self):
        login(token=os.environ["hf_token"])
        self.api_key = os.environ["api_key"]
        self.device = "cuda"

        model_name = "meta-llama/Llama-3.1-8B-Instruct"
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            dtype=torch.bfloat16,
            device_map=self.device
        )
        self.model.eval()

    def verify_api_key(self, provided_key: str) -> bool:
        return provided_key == self.api_key

    def get_final_prompt_activations(self, prompt: str, layer_idxs) -> Dict[int, torch.Tensor]:
        """Final-token activation at each layer in `layer_idxs`, in one forward pass, so every
        trait's own best layer (see scale.json's per-trait layer_idx) is captured without
        hooking layers no trait needs."""
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        activations = {}

        def make_hook(layer_idx):
            def hook_fn(_module, _args, output):
                activations[layer_idx] = output[0, -1, :].detach().to(torch.bfloat16)
            return hook_fn

        hooks = [
            self.model.model.layers[layer_idx].register_forward_hook(make_hook(layer_idx))
            for layer_idx in layer_idxs
        ]
        try:
            with torch.no_grad():
                self.model(**inputs)
        finally:
            for hook in hooks:
                hook.remove()

        return activations

    def cosine_similarity(self, a, b):
        return torch.dot(a, b) / (torch.norm(a) * torch.norm(b))

    def normalize_score(self, score, mean, min_val, max_val):
        """Mirrors rescale.py's normalize_to_unit_range, but for a single score against a
        precomputed (mean, min, max) from scale.json instead of an array of scores."""
        centered = score - mean
        lo, hi = min_val - mean, max_val - mean
        if hi == lo:
            return 0.0
        return 2 * (centered - lo) / (hi - lo) - 1

    def generate_persona_scores(self, system_prompt: str) -> Dict[str, Dict[str, float]]:
        with open(VECTORS_PATH / "traits.json", "r") as f:
            traits = json.load(f)

        with open(VECTORS_PATH / "scale.json", "r") as f:
            scale = json.load(f)

        needed_layers = {stats["layer_idx"] for stats in scale.values()}
        prompt_activations = self.get_final_prompt_activations(system_prompt, needed_layers)

        persona_scores = {}
        for trait, labels in traits.items():
            stats = scale[trait]
            layer_idx = stats["layer_idx"]

            persona_vector = torch.load(
                VECTORS_PATH / f"{trait}.pt", weights_only=False
            ).to(torch.bfloat16)[layer_idx].to(self.device)
            prompt_activation = prompt_activations[layer_idx]

            score = self.cosine_similarity(
                prompt_activation.flatten(), persona_vector.flatten()
            ).item()
            scaled_score = self.normalize_score(score, stats["mean"], stats["min"], stats["max"])

            positive, negative = (scaled_score, 0.0) if scaled_score > 0 else (0.0, -scaled_score)
            persona_scores[trait] = {
                labels["positive"]: min(positive, 1.0),
                labels["negative"]: min(negative, 1.0),
            }

            print(trait, score, scaled_score)

        return persona_scores

    @modal.fastapi_endpoint(method="POST")
    def persona_vector_endpoint(
        self,
        request: SystemPrompt,
        x_api_key: Optional[str] = Header(None, alias="X-API-Key")
    ):
        try:
            if not x_api_key:
                raise HTTPException(status_code=401, detail="API key is required. Include X-API-Key header.")

            if not self.verify_api_key(x_api_key):
                raise HTTPException(status_code=403, detail="Invalid API key")

            persona_vector_ratings = self.generate_persona_scores(request.system)

            return PersonaVectorResponse(persona_vector_ratings=persona_vector_ratings)

        except HTTPException:
            raise
        except Exception as e:
            print(f"Error in persona vector endpoint: {e}")
            return {
                "error": {
                    "message": f"Internal server error: {str(e)}",
                    "type": "internal_error"
                }
            }