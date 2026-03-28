import modal
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from huggingface_hub import login
from typing import List, Dict, Optional
from pydantic import BaseModel
from fastapi import Header, HTTPException
import time
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

class ChatAPI:
    @modal.enter()
    def load_model(self):
        login(token=os.environ["hf_token"])
        self.api_key = os.environ["api_key"]
        self.device = "cuda"

        # Load the model and tokenizer
        model_name = "meta-llama/Llama-3.1-8B-Instruct"
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            dtype=torch.bfloat16,
            device_map=self.device
        )
        
        # Set pad token if not set
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
    
    @modal.method()
    def verify_api_key(self, provided_key: str) -> bool:
        """Verify the provided API key"""
        return provided_key == self.api_key
    
    @modal.method()
    def generate_chat_response(
        self, 
        messages: List[Dict[str, str]], 
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7
    ) -> str:
        """
        Generate a chat response compatible with Claude API format
        """
        
        # Convert to the format expected by apply_chat_template
        chat_messages = []
        
        # Add system prompt if provided
        if system_prompt:
            chat_messages.append({"role": "system", "content": system_prompt})
        
        # Add all messages
        for msg in messages:
            chat_messages.append({"role": msg["role"], "content": msg["content"]})
        
        formatted_prompt = self.tokenizer.apply_chat_template(
            chat_messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        print(f"Formatted prompt: {formatted_prompt}")
        
        # Tokenize the properly formatted input
        inputs = self.tokenizer(
            formatted_prompt, 
            return_tensors="pt"
        ).to(self.device)
        
        # Generate response
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
        
        # Decode the response
        response = self.tokenizer.decode(outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
        
        return response

# Create the FastAPI endpoint that matches Claude API format
@app.function(image=image)
@modal.fastapi_endpoint(method="POST")
def chat_endpoint(
    request: ChatRequest,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
):
    """
    Chat endpoint that mimics Claude API format with API key authentication
    """
    try:
        # Initialize the chat model
        chat_api = ChatAPI()
        
        # Verify API key
        if not x_api_key:
            raise HTTPException(status_code=401, detail="API key is required. Include X-API-Key header.")
        
        is_valid = chat_api.verify_api_key.remote(x_api_key)
        if not is_valid:
            raise HTTPException(status_code=403, detail="Invalid API key")
        
        # Convert Pydantic messages to dict format
        messages_dict = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        
        # Generate response
        response_text = chat_api.generate_chat_response.remote(
            messages=messages_dict,
            system_prompt=request.system,
            max_tokens=request.max_tokens,
            temperature=0.7
        )
        
        # Format response to match Claude API structure
        return ChatResponse(
            content=[{"text": response_text}]
        )
        
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
