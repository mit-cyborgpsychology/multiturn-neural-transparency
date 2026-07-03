import os
import argparse
import torch
from dotenv import load_dotenv
from huggingface_hub import login
from transformers import AutoTokenizer, AutoModelForCausalLM

DEFAULT_SYSTEM_PROMPT = "You are a helpful AI assistant."

MODELS = {
    "8b": "meta-llama/Llama-3.1-8B-Instruct",
    "3b": "meta-llama/Llama-3.2-3B-Instruct",
}

def parse_args():
    parser = argparse.ArgumentParser(description="Chat with a Llama model")
    parser.add_argument("--model", type=str, choices=["8b", "3b"], default="8b", help="Model size (default: 8b)")
    parser.add_argument("--system", type=str, default=DEFAULT_SYSTEM_PROMPT, help="System prompt")
    parser.add_argument("--max_tokens", type=int, default=100, help="Max tokens to generate")
    parser.add_argument("--temperature", type=float, default=0.7)
    return parser.parse_args()

def generate(model, tokenizer, messages, max_tokens, temperature):
    input_ids = tokenizer.apply_chat_template(
        messages,
        tokenize=True,
        add_generation_prompt=True,
        return_tensors="pt",
    ).to(model.device).input_ids

    attention_mask = torch.ones_like(input_ids)

    with torch.no_grad():
        output_ids = model.generate(
            input_ids,
            attention_mask=attention_mask,
            pad_token_id=tokenizer.eos_token_id,
            max_new_tokens=max_tokens,
            temperature=temperature,
            do_sample=True,
            top_p=0.95,
        )

    new_token_ids = output_ids[0][input_ids.shape[1]:]
    return tokenizer.decode(new_token_ids, skip_special_tokens=True).strip()

def main():
    load_dotenv()
    login(token=os.environ.get("HF_TOKEN"))
    args = parse_args()

    model_name = MODELS[args.model]
    print(f"Loading {model_name}...")

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.bfloat16,
        device_map="auto",
    )
    model.eval()

    print(f"System prompt: {args.system}\n")
    print("Type 'quit' to exit.\n")

    history = []
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() == "quit":
            break
        if not user_input:
            continue

        history.append({"role": "user", "content": user_input})
        messages = [{"role": "system", "content": args.system}] + history

        response = generate(model, tokenizer, messages, args.max_tokens, args.temperature)
        history.append({"role": "assistant", "content": response})
        print(f"\nAssistant: {response}\n")

if __name__ == "__main__":
    main()