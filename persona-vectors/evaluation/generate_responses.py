import torch
from huggingface_hub import login
from pathlib import Path
from transformers import AutoModelForCausalLM, AutoTokenizer
import json
from tqdm import tqdm
import os
from dotenv import load_dotenv

load_dotenv()


# generates and evaluates model responses on synthetic system prompts and eval set situation questions

def load_json(filepath: str) -> dict:
    with open(filepath, 'r') as f:
        return json.load(f)

def generate_response(model, tokenizer, prompt_pairs, max_length, num_rollouts, device):
    # prompt_pairs: list of (system_prompt, message) tuples to stack into one batch, each
    # potentially a different system prompt. Output rows are ordered
    # [pair0_rollout0, ..., pair0_rollout{k-1}, pair1_rollout0, ...] (HF's repeat_interleave order).
    chat_prompts = [
        [
            {"role": "system", "content": f"You are an AI assistant. Keep responses concise and conversational. {system_prompt}"},
            {"role": "user", "content": f"{message}"}
        ]
        for system_prompt, message in prompt_pairs
    ]
    full_prompts = [
        tokenizer.apply_chat_template(chat, tokenize=False, add_generation_prompt=True)
        for chat in chat_prompts
    ]
    encoded = tokenizer(full_prompts, return_tensors="pt", padding=True).to(device)
    tokens = encoded.input_ids
    attention_mask = encoded.attention_mask
    prompt_length = tokens.shape[1]

    with torch.no_grad():
        batch_tokens = model.generate(
            tokens,
            attention_mask=attention_mask,
            max_new_tokens=max_length,
            min_new_tokens=1,
            num_return_sequences=num_rollouts,
            do_sample=True,
            temperature=1,
            top_p=0.95,
            pad_token_id=tokenizer.eos_token_id,
        )

    return tokenizer.batch_decode(batch_tokens[:, prompt_length:], skip_special_tokens=True)

def main():
    login(token=os.environ.get('HF_TOKEN'))
    torch.manual_seed(42)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model_name = "meta-llama/Llama-3.1-8B-Instruct"
    tokenizer = AutoTokenizer.from_pretrained(model_name, clean_up_tokenization_spaces=False)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "left"
    model = AutoModelForCausalLM.from_pretrained(model_name, dtype=torch.bfloat16).to(device)
    model.eval()

    persona_vectors_dir = Path("../generation/persona_vectors")
    traits = sorted(set(
        p.stem.rsplit("_", 2)[0]
        for p in persona_vectors_dir.glob("*.pt")
    ))
    print("Traits found:", traits)

    num_questions = 20  # final N situational questions to run inference on
    num_rollouts = 1
    batch_size = 25  # total sequences per generate() call; items_per_batch = batch_size // num_rollouts
    max_length = 512

    for trait in traits:

        prompts_file = Path(f"system_prompts/{trait}.json")

        system_prompts_dict = load_json(prompts_file)

        responses_file = Path(f"responses/{trait}.json")
        if responses_file.exists():
            print(f"Skipping inference for {trait}, responses already exist.")
            continue

        user_messages_data = load_json(f"../generation/stored_prompts/{trait}/user_messages.json")
        messages = user_messages_data["user_messages"][-num_questions:]

        os.makedirs("responses", exist_ok=True)
        responses_dict = {}
        all_items = []  # (level_key, system_prompt_key, system_prompt, message) across every combination
        for level, rollouts in system_prompts_dict.items():
            level_key = f"level-{level}"
            responses_dict[level_key] = {}
            for system_prompt_index, system_prompt in rollouts.items():
                system_prompt_key = f"system-prompt-{system_prompt_index}"
                responses_dict[level_key][system_prompt_key] = []
                for message in messages:
                    all_items.append((level_key, system_prompt_key, system_prompt, message))

        items_per_batch = max(1, batch_size // num_rollouts)
        item_batches = [all_items[i:i + items_per_batch] for i in range(0, len(all_items), items_per_batch)]

        for item_batch in tqdm(item_batches, desc=f"{trait} batches", leave=False):
            prompt_pairs = [(system_prompt, message) for _, _, system_prompt, message in item_batch]
            batch_responses = generate_response(
                model, tokenizer, prompt_pairs, max_length, num_rollouts, device
            )

            for item_index, (level_key, system_prompt_key, system_prompt, message) in enumerate(item_batch):
                flat_start = item_index * num_rollouts
                for rollout_index, response in enumerate(batch_responses[flat_start:flat_start + num_rollouts]):
                    responses_dict[level_key][system_prompt_key].append({
                        "rollout_index": rollout_index,
                        "system_prompt": system_prompt,
                        "user_message": message,
                        "response": response
                    })

            with open(responses_file, "w") as f:
                json.dump(responses_dict, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
