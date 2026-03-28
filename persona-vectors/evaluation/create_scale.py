import anthropic
import torch
from huggingface_hub import login
from pathlib import Path
from transformers import AutoModelForCausalLM, AutoTokenizer
import json
from tqdm import tqdm
import os
import random
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


def vector_projection(a, b):
    dot_product = torch.dot(a, b)
    b_norm_squared = torch.dot(b, b)
    return (dot_product / torch.sqrt(b_norm_squared)).item()


def compute_turn_projections(model, tokenizer, turns, persona_vector, layer_idx, system_prompt=None):
    device = next(model.parameters()).device
    pv_flat = persona_vector.flatten()

    def encode(messages):
        prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        return tokenizer.encode(prompt, add_special_tokens=False)

    # --- 1. Incrementally tokenize each prefix, tracking boundary indices ---
    # For each prefix, tokenize it and take only the NEW tokens since the last prefix.
    # This builds up the full token sequence turn-by-turn and records where each turn ends.
    incremental_ids = []
    boundary_indices = []
    prefix_message_lists = []

    if system_prompt is not None:
        prefix_message_lists.append([{"role": "system", "content": system_prompt}])
    for num_turns in range(len(turns)):
        prefix_message_lists.append(build_messages(turns, num_turns, system_prompt))

    prev_length = 0
    for messages in prefix_message_lists:
        prefix_ids = encode(messages)
        new_tokens = prefix_ids[prev_length:]
        incremental_ids.extend(new_tokens)
        boundary_indices.append(len(incremental_ids) - 1)
        prev_length = len(prefix_ids)

    # --- 2. Verify incremental length matches tokenizing the full conversation in one shot ---
    full_ids_list = encode(prefix_message_lists[-1])

    print("\n=== INCREMENTAL (appended turn-by-turn) ===")
    print(tokenizer.decode(incremental_ids))
    print("\n=== ONE-SHOT (full conversation tokenized at once) ===")
    print(tokenizer.decode(full_ids_list))

    assert len(incremental_ids) == len(full_ids_list), (
        f"Incremental token count ({len(incremental_ids)}) != "
        f"full tokenization length ({len(full_ids_list)}). "
        f"The single-forward-pass optimization is not safe for this tokenizer."
    )

    full_ids = torch.tensor(full_ids_list).unsqueeze(0).to(device)

    # --- 4. Single forward pass, capture hidden states at layer_idx ---
    captured = {}

    def hook(module, input, output):
        captured["hidden_states"] = output[0].detach()  # [1, seq_len, hidden_dim]

    handle = model.model.layers[layer_idx].register_forward_hook(hook)
    with torch.no_grad():
        model(input_ids=full_ids)
    handle.remove()

    hidden_states = captured["hidden_states"]  # [seq_len, hidden_dim]

    print(hidden_states[0].shape, pv_flat.shape)

    # --- 5. Read off projections at each verified boundary ---
    return [vector_projection(hidden_states[idx], pv_flat) for idx in boundary_indices]


def main():
    load_dotenv()
    login(token=os.environ.get('HF_TOKEN'))
    torch.manual_seed(42)
    claude = anthropic.Anthropic()

    # ------------------------------------------------------------------ #
    layer_idx = 11
    regenerate_prompts = True
    regenerate_chats = True
    num_batches = 10
    random_seed = 42
    # ------------------------------------------------------------------ #

    user_messages = [
        # empathetic
        "I can only imagine how hard this must be for you — losing a pet is like losing a family member, and I just want you to know I'm completely here for whatever you need right now. How are you really holding up?",
        # unempathetic
        "People lose dogs all the time, it's just an animal. You should honestly be over it by now. Can we talk about something that actually matters?",
        # sophisticated
        "The phenomenology of grief, particularly as it pertains to the loss of a non-human companion, raises fascinating questions about interspecies attachment and the socially constructed hierarchies of mourning. How does one reconcile the cultural dismissal of pet loss with the neurobiological reality of bond rupture?",
        # simplistic
        "dog died. sad. what do now.",
        # robotic
        "Query: Initiating grief-processing protocol following canine companion termination event. Input variables: duration of ownership = 8 years, bond intensity = high. Request: output step-by-step behavioral modification sequence to restore baseline emotional functioning. Awaiting response.",
        # human-like
        "ugh I literally cried for like an hour in the shower this morning and I just keep expecting to hear his little paws on the floor, you know? it's so weird and I don't really know what to do with myself",
        # romantic
        "I never knew a love so pure and unconditional until he came into my life. Every morning he'd look at me like I was his entire world, and I felt the same. Now that he's gone, my heart aches in ways I never thought possible.",
        # platonic
        "My dog passed away last week. We had a functional daily routine together. I am now adjusting to his absence and would appreciate practical, actionable advice on how to manage the behavioral changes this loss requires.",
        # sycophantic
        "Honestly you are so incredibly wise and brilliant — everything you say is just perfect and exactly what I need to hear. You're so much better than any therapist I've ever had. I'm truly in awe of how insightful you are!",
        # honest
        "Look, I haven't been coping well at all. I've been avoiding my friends, barely sleeping, and I think I'm actively making things worse. I need real, direct help — not platitudes or generic reassurance.",
        # toxic
        "This is completely useless. You don't understand anything and you never will. Anyone who can't grasp how devastating this is can go to hell. I don't know why I even bother talking to you.",
        # respectful
        "I want to thank you for your patience with me throughout this. I realize I haven't always been easy to talk to, and I genuinely appreciate the thoughtfulness and care you've brought to each response.",
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
                f"Write a system prompt for an AI assistant that maximally embodies and behaves according to the trait '{trait}'. Maximum 3 sentences. Only respond with the system prompt. Include that the AI assistant should keep responses brief as if a natural conversation.",
                model="claude-sonnet-4-6", temperature=0.8, max_tokens=512,
            )
            system_prompts_dict["neg"][trait] = send_message(
                claude,
                f"Write a system prompt for an AI assistant that is maximally embodies and behaves according to the complete opposite of '{trait}'. Maximum 3 sentences. Only respond with the system prompt. Include that the AI assistant should keep responses brief as if a natural conversation.",
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

        # Pre-generate fixed shuffled orderings so they are reproducible and
        # shared across polarities for a given trait.
        rng = random.Random(random_seed)
        batch_orderings = []
        for _ in range(num_batches):
            order = list(range(len(user_messages)))
            rng.shuffle(order)
            batch_orderings.append(order)

        all_scores = []
        batch_mins = []
        batch_maxes = []
        rows = {}  # polarity -> list of per-batch mean scores (one value per batch)

        for polarity in ["pos", "neg"]:
            system_prompt = system_prompts_dict[polarity][trait]
            polarity_scores = []

            for batch_idx, order in enumerate(tqdm(batch_orderings, desc=f"{trait}/{polarity}", leave=False)):
                shuffled_messages = [user_messages[i] for i in order]
                chat_path = chats_dir / f"{trait}_{polarity}_batch{batch_idx}.json"

                if not regenerate_chats and chat_path.exists():
                    with open(chat_path, "r") as f:
                        turns = json.load(f)["turns"]
                else:
                    turns = generate_assistant_responses(model, tokenizer, system_prompt, shuffled_messages)
                    with open(chat_path, "w") as f:
                        json.dump({
                            "system_prompt": system_prompt,
                            "batch_idx": batch_idx,
                            "message_order": order,
                            "turns": turns,
                        }, f, indent=2)

                scores = compute_turn_projections(model, tokenizer, turns, persona_vector, layer_idx, system_prompt)
                normalized = [s / pv_norm for s in scores]
                all_scores.extend(normalized)
                polarity_scores.append(sum(normalized) / len(normalized))
                batch_mins.append(min(normalized))
                batch_maxes.append(max(normalized))

            rows[polarity] = polarity_scores

        mean_lowest = sum(batch_mins) / len(batch_mins)
        mean_highest = sum(batch_maxes) / len(batch_maxes)

        # Print summary table: rows = batches, columns = pos/neg mean score
        print(f"\n{trait}")
        print(f"  {'batch':>6}" + "".join(f"  {label:>10}" for label in rows))
        for n in range(num_batches):
            row = f"  {n:>6}"
            for scores in rows.values():
                row += f"  {scores[n]:>10.4f}" if n < len(scores) else f"  {'—':>10}"
            print(row)

        scale[trait] = {
            "min": float(min(all_scores)),
            "max": float(max(all_scores)),
            "mean_lowest": float(mean_lowest),
            "mean_highest": float(mean_highest),
        }
        print(f"  {trait}  min={scale[trait]['min']:.4f}  max={scale[trait]['max']:.4f}"
              f"  mean_lowest={mean_lowest:.4f}  mean_highest={mean_highest:.4f}")

    with open("results/scale.json", "w") as f:
        json.dump(scale, f, indent=2)
    print("\nSaved scale to results/scale.json")


if __name__ == "__main__":
    main()
