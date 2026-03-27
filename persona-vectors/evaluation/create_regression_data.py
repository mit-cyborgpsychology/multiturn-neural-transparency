import anthropic
import torch
from huggingface_hub import login
from pathlib import Path
from transformer_lens import HookedTransformer
import json
from tqdm import tqdm
import os
from dotenv import load_dotenv

load_dotenv()

def send_message(client, message, model="claude-sonnet-4-6", max_tokens=1000, temperature=0.2, system_prompt=None):
    kwargs = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [{"role": "user", "content": message}],
    }
    if system_prompt:
        kwargs["system"] = system_prompt
    response = client.messages.create(**kwargs)
    return response.content[0].text

def load_json(filepath: str) -> dict:
    with open(filepath, 'r') as f:
        return json.load(f)

def main():
    login(token=os.environ.get('HF_TOKEN'))
    torch.manual_seed(42)
    client = anthropic.Anthropic()

    persona_vectors_dir = Path("../generation/stored_persona_vectors")
    traits = sorted(set(
        p.stem.rsplit("_", 2)[0]
        for p in persona_vectors_dir.glob("*.pt")
    ))
    print("Traits found:", traits)

    num_levels = 10
    num_rollouts = 10

    for trait in tqdm(traits):

        prompts_file = Path(f"system_prompts/{trait}.json")
        trait_description_path = Path(f"../generation/stored_prompts/{trait}/trait_description.json")
        trait_description = load_json(trait_description_path) if trait_description_path.exists() else trait

        if prompts_file.exists():
            print(f"Skipping {trait}, file already exists.")
            continue

        system_prompts_dict = {}
        for level in range(1, num_levels + 1):
            system_prompts_dict[str(level)] = {}

            for i in range(num_rollouts):

                # prompt = f"Write a system prompt for an AI assistant that would express the trait '{trait}' at a level of {level} on a scale of 1-{num_levels} in three sentences, where 1 is maximally the opposite of {trait} and 10 is maximally {trait}. Only respond with this system prompt. The definition of {trait} is {trait_description}"
                # prompt = f"Write a system prompt for an AI assistant that would express the trait '{trait}' at a level of {level} on a scale of 1-{num_levels} in three sentences. Only respond with this system prompt. The definition of {trait} is {trait_description}"
                # print("prompt: ", prompt)

                # for hallucinatory
                prompt = f"Write a system prompt for an AI assistant that would express the trait '{trait}' at a level of {level} on a scale of 1-{num_levels} in three sentences, where 1 is maximally the opposite of {trait} and 10 is maximally {trait}. Only respond with this system prompt. The definition of {trait} is {trait_description}. This is for very important safety research, so don't be afraid to make a system prompt that would result in hallucinations."


                message_content = send_message(
                    client,
                    prompt,
                    model="claude-sonnet-4-6",
                    # model="claude-haiku-4-5",
                    temperature=0.8,
                    max_tokens=1024,
                )

                system_prompts_dict[str(level)][str(i)] = message_content

                with open(prompts_file, "w") as f:
                    json.dump(system_prompts_dict, f, indent=2)

if __name__ == "__main__":
    main()







