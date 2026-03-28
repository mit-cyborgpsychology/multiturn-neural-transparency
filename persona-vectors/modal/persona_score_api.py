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

# Define the image with all dependencies
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
        os.path.abspath(LOCAL_VECTORS_PATH),  # Your local path
        remote_path="/root/stored_persona_vectors"  # Path inside container
    )
)

app = modal.App("persona-vector-api")

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
class PersonaScoreAPI:
    @modal.enter()
    def load_model(self):
        login(token=os.environ["hf_token"])
        self.api_key = os.environ["api_key"]
        self.device = "cuda"

        model_name = "meta-llama/Llama-3.1-8B-Instruct"

        # Load hooked transformer for persona vectors
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            dtype=torch.bfloat16,
            device_map=self.device
            )
        self.model.eval()
        
    
    @modal.method()
    def verify_api_key(self, provided_key: str) -> bool:
        """Verify the provided API key"""
        return provided_key == self.api_key
    
    @modal.method()
    def generate_persona_scores_method(self, system_prompt: str, best_layer: int = 11) -> Dict[str, float]:
        """Generate persona scores using the hooked model"""

        def get_final_prompt_activation(prompt: str) -> torch.Tensor:
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)

            activation = []

            def hook_fn(module, args, output):
                activation.append(output[0, -1, :].detach().to(torch.bfloat16))

            hook = self.model.model.layers[best_layer].register_forward_hook(hook_fn)

            try:
                with torch.no_grad():
                    self.model(**inputs)
            finally:
                hook.remove()

            return activation[0]

        def vector_projection(a, b):
            dot_product = torch.dot(a, b)
            b_norm_squared = torch.dot(b, b)
            return dot_product / torch.sqrt(b_norm_squared)

        def generate_persona_scores(system_prompt):

            prompt_activation = get_final_prompt_activation(system_prompt)

            folder_path = Path("/root/stored_persona_vectors")
            with open(folder_path / 'traits.json', 'r') as f:
                traits = json.load(f)

            with open(folder_path / "scale.json", "r") as f:
                scale = json.load(f)

            persona_scores = {}
            for trait in traits.keys():
                persona_scores[trait] = {}
                persona_vector = torch.load(folder_path / f"{trait}.pt", weights_only=False).to(torch.bfloat16)[best_layer].to(self.device)
                projection = vector_projection(prompt_activation.flatten(), persona_vector.flatten())
                normalized_score = projection.item() / persona_vector.flatten().norm(p=2).item()

                if normalized_score > 0:
                    scaled_score = normalized_score / scale[trait]["max"]
                    persona_scores[trait][traits[trait]["positive"]] = min(scaled_score, 1.0)
                    persona_scores[trait][traits[trait]["negative"]] = 0.0
                else:
                    scaled_score = normalized_score / -scale[trait]["min"]
                    persona_scores[trait][traits[trait]["positive"]] = 0.0
                    persona_scores[trait][traits[trait]["negative"]] = min(-scaled_score, 1.0)

                print(trait, normalized_score, scaled_score)

            return persona_scores

        return generate_persona_scores(system_prompt)
    
# Persona vector endpoint
@app.function(image=image)
@modal.fastapi_endpoint(method="POST")
def persona_vector_endpoint(
    request: SystemPrompt,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
):
    try:
        persona_score_api = PersonaScoreAPI()
        
        if not x_api_key:
            raise HTTPException(status_code=401, detail="API key is required. Include X-API-Key header.")
        
        is_valid = persona_score_api.verify_api_key.remote(x_api_key)
        if not is_valid:
            raise HTTPException(status_code=403, detail="Invalid API key")
        
        # Call the method remotely
        persona_vector_ratings = persona_score_api.generate_persona_scores_method.remote(request.system)
        
        return PersonaVectorResponse(
            persona_vector_ratings=persona_vector_ratings  # Already a dict, don't use json.dumps
        )
        
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