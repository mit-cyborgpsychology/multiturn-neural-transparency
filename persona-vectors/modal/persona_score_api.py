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

BEST_LAYER = 11  # class-level constant, not buried in a method signature
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

        # Load traits and scale once at startup, not per request
        with open(VECTORS_PATH / "traits.json", "r") as f:
            self.traits = json.load(f)

        with open(VECTORS_PATH / "scale.json", "r") as f:
            self.scale = json.load(f)

    def verify_api_key(self, provided_key: str) -> bool:
        return provided_key == self.api_key

    def get_final_prompt_activation(self, prompt: str) -> torch.Tensor:
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        activation = []

        def hook_fn(module, args, output):
            activation.append(output[0, -1, :].detach().to(torch.bfloat16))

        hook = self.model.model.layers[BEST_LAYER].register_forward_hook(hook_fn)
        try:
            with torch.no_grad():
                self.model(**inputs)
        finally:
            hook.remove()

        return activation[0]

    def vector_projection(self, a, b):
        dot_product = torch.dot(a, b)
        b_norm_squared = torch.dot(b, b)
        return dot_product / torch.sqrt(b_norm_squared)

    def generate_persona_scores(self, system_prompt: str) -> Dict[str, Dict[str, float]]:
        prompt_activation = self.get_final_prompt_activation(system_prompt)

        persona_scores = {}
        for trait in self.traits.keys():
            persona_scores[trait] = {}
            persona_vector = torch.load(
                VECTORS_PATH / f"{trait}.pt", weights_only=False
            ).to(torch.bfloat16)[BEST_LAYER].to(self.device)

            projection = self.vector_projection(
                prompt_activation.flatten(), persona_vector.flatten()
            )
            normalized_score = projection.item() / persona_vector.flatten().norm(p=2).item()

            if normalized_score > 0:
                scaled_score = normalized_score / self.scale[trait]["max"]
                persona_scores[trait][self.traits[trait]["positive"]] = min(scaled_score, 1.0)
                persona_scores[trait][self.traits[trait]["negative"]] = 0.0
            else:
                scaled_score = normalized_score / -self.scale[trait]["min"]
                persona_scores[trait][self.traits[trait]["positive"]] = 0.0
                persona_scores[trait][self.traits[trait]["negative"]] = min(-scaled_score, 1.0)

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