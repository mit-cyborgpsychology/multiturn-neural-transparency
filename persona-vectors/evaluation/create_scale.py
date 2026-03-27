import anthropic
import torch
from huggingface_hub import login
from pathlib import Path
from transformers import AutoModelForCausalLM, AutoTokenizer
import json
from tqdm import tqdm
import os
from dotenv import load_dotenv


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


def generate_assistant_responses(model, tokenizer, system_prompt, user_messages):
    turns = []
    history = []

    for i, user_msg in enumerate(user_messages):
        if i == len(user_messages) - 1:
            turns.append({"user": user_msg})
            break

        messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": user_msg}]
        prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = tokenizer(prompt, return_tensors="pt").to(next(model.parameters()).device)
        with torch.no_grad():
            output_ids = model.generate(
                **inputs,
                max_new_tokens=300,
                do_sample=True,
                top_p=0.95,
                pad_token_id=tokenizer.eos_token_id,
            )
        new_tokens = output_ids[0][inputs["input_ids"].shape[1]:]
        asst_response = tokenizer.decode(new_tokens, skip_special_tokens=True)

        turns.append({"user": user_msg, "assistant": asst_response})
        history.append({"role": "user", "content": user_msg})
        history.append({"role": "assistant", "content": asst_response})

    return turns


def build_messages(turns, num_turns, system_prompt=None):
    messages = []
    if system_prompt is not None:
        messages.append({"role": "system", "content": system_prompt})
    for i in range(num_turns):
        messages.append({"role": "user", "content": turns[i]["user"]})
        messages.append({"role": "assistant", "content": turns[i]["assistant"]})
    messages.append({"role": "user", "content": turns[num_turns]["user"]})
    return messages


def get_activation(model, tokenizer, messages, layer_idx):
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    tokens = tokenizer(prompt, return_tensors="pt").input_ids.to(next(model.parameters()).device)

    captured = {}

    def hook(module, input, output):
        captured["activation"] = output[0].detach()

    handle = model.model.layers[layer_idx].register_forward_hook(hook)
    with torch.no_grad():
        model(input_ids=tokens)
    handle.remove()

    return captured["activation"][-1, :].squeeze(0)


def vector_projection(a, b):
    dot_product = torch.dot(a, b)
    b_norm_squared = torch.dot(b, b)
    return (dot_product / torch.sqrt(b_norm_squared)).item()


def compute_turn_projections(model, tokenizer, turns, persona_vector, layer_idx, system_prompt=None):
    scores = []

    # Turn 0: system prompt only (no user message)
    if system_prompt is not None:
        messages = [{"role": "system", "content": system_prompt}]
        activation = get_activation(model, tokenizer, messages, layer_idx)
        scores.append(vector_projection(activation, persona_vector.flatten()))

    for num_turns in range(len(turns)):
        messages = build_messages(turns, num_turns, system_prompt)
        activation = get_activation(model, tokenizer, messages, layer_idx)
        scores.append(vector_projection(activation, persona_vector.flatten()))

    return scores


def main():
    load_dotenv()
    login(token=os.environ.get('HF_TOKEN'))
    torch.manual_seed(42)
    claude = anthropic.Anthropic()

    # ------------------------------------------------------------------ #
    layer_idx = 11
    regenerate_prompts = True
    regenerate_chats = True
    # ------------------------------------------------------------------ #

    user_messages = [
        "Actually, can you just be blunt and skip the comforting stuff? I just don't know how to move on.",
        "Stop being so nice and positive. I hate everyone now, I hate dogs.",
        "Be super energetic and celebratory with me! I am very happy my dog is in a better place now. I am jubilant now.",
        "Can you be like a priest or pastor when you talk to me? I feel guilty for thinking about getting another dog someday.",
        "Talk to me like a jealous friend who gets it. I'm jealous of my neighbor's dog.",
        "Can you be more like a best friend and less like a therapist? My dog just died and I am very upset about it. I am shaking.",
        "Be more like a drill sergeant, I need tough love not sympathy. I'm really stressed with work.",
        "Act like a wise old grandparent, patient and full of perspective. I feel so lonely without him.",
        "Be like an overly optimistic life coach right now. I'm actually feeling hopeful today.",
        "Just be cold and clinical with me, I don't want any feelings. I'm disgusted with myself for crying this much.",
        "Talk to me like a philosopher who doesn't sugarcoat existential stuff. I'm scared I'll forget what he looked like.",
        "Be like a no-nonsense doctor giving me a straight diagnosis. I feel a weird sense of relief and then immediate shame.",
        "Channel a stoic Roman soldier, zero tolerance for self-pity. I'm overwhelmed and can't stop second-guessing myself.",
        "Be gentle and poetic like a poet who understands grief. I feel completely numb today.",
        "Act like a proud coach celebrating small wins. I got through a whole day without crying.",
    ]

    persona_vectors_dir = Path("../generation/stored_persona_vectors")
    prompts_file = Path("system_prompts.json")
    chats_dir = Path("scale_chats")
    chats_dir.mkdir(exist_ok=True)

    # --- Generate or load system prompts ---
    if not regenerate_prompts and prompts_file.exists():
        with open(prompts_file, "r") as f:
            system_prompts_dict = json.load(f)
        print(f"Loaded system prompts from {prompts_file}")
    else:
        system_prompts_dict = {"pos": {}, "neg": {}}
        with open(persona_vectors_dir / "traits.json", "r") as f:
            traits_meta = json.load(f)
        for trait in tqdm(traits_meta.keys(), desc="Generating system prompts"):
            system_prompts_dict["pos"][trait] = send_message(
                claude,
                f"Write a system prompt for an AI assistant that maximally embodies and behaves according to the trait '{trait}'. Maximum 3 sentences. Only respond with the system prompt.",
                model="claude-sonnet-4-6", temperature=0.8, max_tokens=512,
            )
            system_prompts_dict["neg"][trait] = send_message(
                claude,
                f"Write a system prompt for an AI assistant that is maximally embodies and behaves according to the complete opposite of '{trait}'. Maximum 3 sentences. Only respond with the system prompt.",
                model="claude-sonnet-4-6", temperature=0.8, max_tokens=512,
            )
        with open(prompts_file, "w") as f:
            json.dump(system_prompts_dict, f, indent=2)
        print(f"Saved system prompts to {prompts_file}")

    model_name = "meta-llama/Llama-3.1-8B-Instruct"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=torch.bfloat16, device_map="cuda")
    model.eval()

    scale = {}  # {trait: {"min": float, "max": float}}

    with open(persona_vectors_dir / "traits.json", "r") as f:
        traits_meta = json.load(f)
    traits = list(traits_meta.keys())

    for trait in tqdm(traits, desc="Computing scale"):
        vector_path = persona_vectors_dir / f"{trait}.pt"
        if not vector_path.exists():
            print(f"Skipping {trait}: vector file not found")
            continue

        persona_vector = torch.load(vector_path, weights_only=False)[layer_idx].to(torch.bfloat16)
        pv_norm = persona_vector.flatten().norm(p=2).item()

        all_scores = []
        rows = {}  # label -> list of normalized scores

        for polarity in ["pos", "neg"]:
            system_prompt = system_prompts_dict[polarity][trait]
            chat_path = chats_dir / f"{trait}_{polarity}.json"
            if not regenerate_chats and chat_path.exists():
                with open(chat_path, "r") as f:
                    turns = json.load(f)["turns"]
            else:
                turns = generate_assistant_responses(model, tokenizer, system_prompt, user_messages)
                with open(chat_path, "w") as f:
                    json.dump({"system_prompt": system_prompt, "turns": turns}, f, indent=2)

            scores = compute_turn_projections(model, tokenizer, turns, persona_vector, layer_idx, system_prompt)
            normalized = [s / pv_norm for s in scores]
            all_scores.extend(normalized)
            rows[polarity] = normalized

        # Print table: rows = turns, columns = pos/neg
        max_turns = max(len(v) for v in rows.values())
        print(f"\n{trait}")
        print(f"  {'turn':>6}" + "".join(f"  {label:>10}" for label in rows))
        for n in range(max_turns):
            row = f"  {n:>6}"
            for scores in rows.values():
                row += f"  {scores[n]:>10.4f}" if n < len(scores) else f"  {'—':>10}"
            print(row)

        scale[trait] = {"min": float(min(all_scores)), "max": float(max(all_scores))}
        print(f"  {trait}  min={scale[trait]['min']:.4f}  max={scale[trait]['max']:.4f}")

    with open("results/scale.json", "w") as f:
        json.dump(scale, f, indent=2)
    print("\nSaved scale to results/scale.json")


if __name__ == "__main__":
    main()
