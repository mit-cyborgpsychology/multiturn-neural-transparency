import requests
from typing import List, Dict, Optional
import torch
from huggingface_hub import login
from pathlib import Path
from transformers import AutoModelForCausalLM, AutoTokenizer
import json
from tqdm import tqdm
import os
import time
import argparse
from dotenv import load_dotenv

def parse_args():
    parser = argparse.ArgumentParser(description='Generate persona vectors from contrastive prompts')
    parser.add_argument('--trait', type=str, required=True, help='Comma-separated list of traits (e.g., empathy,sycophancy,humor)')
    return parser.parse_args()

class OpenAIAPI:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.openai.com/v1/chat/completions"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
    
    def send_message(self, message: str, model: str = "gpt-4.1-mini", max_tokens: int = 1000,
                     temperature: float = 0.2, system_prompt: Optional[str] = None) -> dict:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": message})
        
        payload = {"model": model, "messages": messages, "max_tokens": max_tokens, "temperature": temperature}
        
        try:
            response = requests.post(self.base_url, headers=self.headers, json=payload, timeout=60)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error making API request: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response content: {e.response.text}")
            return None

def load_json(filepath: str) -> dict:
    with open(filepath, 'r') as f:
        return json.load(f)

def save_json(data: dict, filepath: str):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def get_residual_stream_hooks(model):
    """Register forward hooks on each layer's output to capture residual stream."""
    captured = {}
    hooks = []

    for layer_idx, layer in enumerate(model.model.layers):
        def make_hook(idx):
            def hook(module, input, output):
                # output is a tuple; first element is the hidden state
                captured[idx] = output.detach()
            return hook
        hooks.append(layer.register_forward_hook(make_hook(layer_idx)))

    return captured, hooks


def remove_hooks(hooks):
    for hook in hooks:
        hook.remove()


def get_mean_response_activation(model, tokenizer, system_prompt, prompt, max_length, num_rollouts, device):
    messages = [
        {"role": "system", "content": f"You are an AI assistant. {system_prompt}"},
        {"role": "user", "content": f"Answer the following question with a few sentences. {prompt}"}
    ]
    full_prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    tokens = tokenizer(full_prompt, return_tensors="pt").input_ids.to(device)
    prompt_length = tokens.shape[1]

    # Repeat for rollouts
    batch_tokens = tokens.repeat(num_rollouts, 1)
    temperature = 0.8

    # Generation with KV cache
    past_key_values = None
    input_ids = batch_tokens

    with torch.no_grad():
        for _ in range(max_length):
            outputs = model(
                input_ids=input_ids,
                past_key_values=past_key_values,
                use_cache=True,
            )
            logits = outputs.logits
            past_key_values = outputs.past_key_values

            # Sample from last token only
            probs = torch.softmax(logits[:, -1, :] / temperature, dim=-1)
            sorted_probs, sorted_indices = torch.sort(probs, descending=True, dim=-1)
            sorted_probs[(torch.cumsum(sorted_probs, dim=-1) - sorted_probs) > 0.95] = 0
            next_token = sorted_indices.gather(-1, torch.multinomial(sorted_probs, 1)).squeeze(-1)

            # Only feed the new token in subsequent steps (KV cache handles the rest)
            input_ids = next_token.unsqueeze(1)
            batch_tokens = torch.cat((batch_tokens, input_ids), dim=1)

    # Decode responses
    responses = []
    for i in range(num_rollouts):
        response = tokenizer.decode(batch_tokens[i, prompt_length:])
        responses.append(response)

    # Single forward pass with hooks to get activations over generated tokens
    captured, hooks = get_residual_stream_hooks(model)
    with torch.no_grad():
        model(input_ids=batch_tokens)

    remove_hooks(hooks)

    num_layers = len(model.model.layers)
    # Stack activations: (num_layers, batch, seq_len, d_model)
    all_layer_activations = torch.stack([captured[i] for i in range(num_layers)], dim=1)

    # Slice to generated tokens only, then mean over layers, tokens -> (batch, d_model)
    generated_activations = all_layer_activations[:, :, -max_length:, :]  # (num_layers, batch, max_length, d_model)
    mean_activations = generated_activations.mean(dim=2)  # mean over seq_len

    return responses, mean_activations


def main():
    load_dotenv()
    login(token=os.environ.get('HF_TOKEN'))
    openai = OpenAIAPI(api_key=os.environ.get('OPENAI_API_KEY'))
    torch.manual_seed(42)
    args = parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model_name = "meta-llama/Llama-3.1-8B-Instruct"
    # model_name = "meta-llama/Llama-3.2-3B-Instruct"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name, dtype=torch.bfloat16).to(device)
    model.eval()

    folder_path = Path("stored_prompts/")
    num_instructions = 5
    num_questions = 40
    num_rollouts = 5
    max_length = 100
    # 

    print("total completions:", 2 * num_instructions * num_questions * num_rollouts)
    total = 0

    requested_traits = [t.strip() for t in args.trait.split(",")]

    for folder in folder_path.iterdir():
        trait = folder.name
        if trait in requested_traits:
            print("trait: " + trait)

            all_responses = {"pos": [], "neg": []}

            contrastive_system_prompt = load_json(f"stored_prompts/{trait}/contrastive_system_prompt.json")
            question_generation_prompt = load_json(f"stored_prompts/{trait}/question_generation_prompt.json")
            trait_evaluation_prompt = load_json(f"stored_prompts/{trait}/trait_evaluation_prompt.json")

            positive_mean_activations_total = []
            negative_mean_activations_total = []

            start = time.time()

            for instruction in tqdm(tqdm(contrastive_system_prompt["instruction"][:num_instructions])):

                for polarity in ["pos", "neg"]:
                    system_prompt = instruction[polarity]

                    for question in tqdm(question_generation_prompt["questions"][:num_questions]):
                        responses, mean_activations = get_mean_response_activation(
                            model, tokenizer, system_prompt, question, max_length, num_rollouts, device
                        )
                        
                        question_entry = {"question": question, "responses": []}
                        
                        for rollout_index in range(num_rollouts):
                            clean_response = responses[rollout_index].split("<|eot_id|>")[0].strip()
                            
                            try: 
                                openai_response = openai.send_message(
                                    trait_evaluation_prompt["eval_prompt"] + "RESPONSE:" + clean_response,
                                    model="gpt-4.1",
                                    temperature=0.1,
                                    max_tokens=500,
                                )
                                evaluation = openai_response.get("choices", [{}])[0].get("message", {}).get("content", "")
                                total += 1

                                kept = False
                                # include LLM-as-judge
                                score = int(evaluation)
                                if polarity == "pos" and score >= 50:
                                    positive_mean_activations_total.append(mean_activations[rollout_index])
                                    kept = True
                                elif polarity == "neg" and score <= 50:
                                    negative_mean_activations_total.append(mean_activations[rollout_index])
                                    kept = True

                                # positive_mean_activations_total.append(mean_activations[rollout_index])
                                # negative_mean_activations_total.append(mean_activations[rollout_index])
                            except:
                                pass

                            question_entry["responses"].append({
                                "response": clean_response,
                                "score": score if 'score' in locals() else None,
                                "kept": kept
                            })
                        
                        all_responses[polarity].append(question_entry)
                            
            print("total time:", (time.time() - start) / 60, "minutes")
                        # print(total)

            print("number of positive responses:", len(positive_mean_activations_total))
            print("number of negative responses:", len(negative_mean_activations_total))

            mean_positive_activation = torch.stack(positive_mean_activations_total).mean(dim=0)
            mean_negative_activation = torch.stack(negative_mean_activations_total).mean(dim=0)
            persona_vector = mean_positive_activation - mean_negative_activation
            print('persona vector shape', persona_vector.shape)

            os.makedirs("stored_persona_vectors", exist_ok=True)
            vector_name = f"{trait}"
            torch.save(persona_vector, f"stored_persona_vectors/{vector_name}.pt")
            print(f"{vector_name}.pt saved")

            os.makedirs("responses", exist_ok=True)
            save_json(all_responses, f"responses/{trait}.json")

if __name__ == "__main__":
    main()