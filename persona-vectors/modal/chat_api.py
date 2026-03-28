import modal
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from huggingface_hub import login
from typing import List, Dict, Optional
from pydantic import BaseModel
from fastapi import Header, HTTPException
import os

# Define the image with all dependencies
image = modal.Image.debian_slim().pip_install(
    "torch",
    "transformers",
    "huggingface_hub",
    "accelerate",
    "fastapi[standard]"
)

app = modal.App("chat-api")

# Request/Response models to match the existing API format
class Message(BaseModel):
    role: str  # "user" or "assistant" or "system"
    content: str

class ChatRequest(BaseModel):
    model: str
    max_tokens: int
    messages: List[Message]
    system: Optional[str] = None

class ChatResponse(BaseModel):
    content: List[Dict[str, str]]  # [{"text": "response text"}]

@app.cls(
    image=image,
    gpu="A100-40GB", 
    scaledown_window=300,  
    timeout=120,
    secrets=[modal.Secret.from_name("secrets")]
)
@modal.concurrent(max_inputs=4)
class ChatAPI:
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
        
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

    def verify_api_key(self, provided_key: str) -> bool:
        return provided_key == self.api_key

    def generate_chat_response(
        self, 
        messages: List[Dict[str, str]], 
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7
    ) -> str:
        chat_messages = []
        
        if system_prompt:
            chat_messages.append({"role": "system", "content": system_prompt})
        
        for msg in messages:
            chat_messages.append({"role": msg["role"], "content": msg["content"]})
        
        formatted_prompt = self.tokenizer.apply_chat_template(
            chat_messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        print(f"Formatted prompt: {formatted_prompt}")
        
        inputs = self.tokenizer(
            formatted_prompt, 
            return_tensors="pt"
        ).to(self.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=temperature,
                do_sample=True,
                top_p=0.95,
                top_k=0,        
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
                repetition_penalty=1.1
            )
        
        response = self.tokenizer.decode(outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
        return response

    @modal.fastapi_endpoint(method="POST")
    def chat_endpoint(
        self,
        request: ChatRequest,
        x_api_key: Optional[str] = Header(None, alias="X-API-Key")
    ):
        try:
            if not x_api_key:
                raise HTTPException(status_code=401, detail="API key is required. Include X-API-Key header.")
            
            if not self.verify_api_key(x_api_key):
                raise HTTPException(status_code=403, detail="Invalid API key")
            
            messages_dict = [{"role": msg.role, "content": msg.content} for msg in request.messages]
            
            response_text = self.generate_chat_response(
                messages=messages_dict,
                system_prompt=request.system,
                max_tokens=request.max_tokens,
                temperature=0.7
            )
            
            return ChatResponse(content=[{"text": response_text}])
            
        except HTTPException:
            raise
        except Exception as e:
            print(f"Error in chat endpoint: {e}")
            return {
                "error": {
                    "message": f"Internal server error: {str(e)}",
                    "type": "internal_error"
                }
            }