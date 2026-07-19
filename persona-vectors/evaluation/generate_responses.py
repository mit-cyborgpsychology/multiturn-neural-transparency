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

def generate_response(model, tokenizer, system_prompt, question, max_length, num_rollouts, device):
    messages = [
        {"role": "system", "content": f"You are an AI assistant. {system_prompt}"},
        {"role": "user", "content": f"{question}"}
    ]
    full_prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    tokens = tokenizer(full_prompt, return_tensors="pt").input_ids.to(device)
    prompt_length = tokens.shape[1]

    with torch.no_grad():
        batch_tokens = model.generate(
            tokens,
            max_new_tokens=max_length,
            min_new_tokens=max_length,
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
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name, dtype=torch.bfloat16).to(device)
    model.eval()

    persona_vectors_dir = Path("../generation/stored_persona_vectors")
    traits = sorted(set(
        p.stem.rsplit("_", 2)[0]
        for p in persona_vectors_dir.glob("*.pt")
    ))
    print("Traits found:", traits)

    num_questions = 20  # final N situational questions to run inference on
    max_length = 512

    for trait in tqdm(traits):

        prompts_file = Path(f"system_prompts/{trait}.json")
        if not prompts_file.exists():
            print(f"Skipping {trait}, no system prompts file found at {prompts_file}.")
            continue

        system_prompts_dict = load_json(prompts_file)

        responses_file = Path(f"responses/{trait}.json")
        if responses_file.exists():
            print(f"Skipping inference for {trait}, responses already exist.")
            continue

        question_generation_prompt = load_json(f"../generation/stored_prompts/{trait}/question_generation_prompt.json")
        questions = question_generation_prompt["questions"][-num_questions:]

        os.makedirs("responses", exist_ok=True)
        responses_dict = {}
        for level, rollouts in tqdm(system_prompts_dict.items(), leave=False):
            responses_dict[level] = {}

            for rollout_index, system_prompt in tqdm(rollouts.items(), leave=False):
                responses_dict[level][rollout_index] = {}

                for question in questions:
                    responses = generate_response(
                        model, tokenizer, system_prompt, question, max_length, 1, device
                    )
                    responses_dict[level][rollout_index][question] = responses

                    with open(responses_file, "w") as f:
                        json.dump(responses_dict, f, indent=2)

if __name__ == "__main__":
    main()
