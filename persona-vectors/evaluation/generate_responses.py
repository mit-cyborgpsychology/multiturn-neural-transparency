import argparse
import torch
from huggingface_hub import login
from pathlib import Path
from transformers import AutoModelForCausalLM, AutoTokenizer
import json
from tqdm import tqdm
import os
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import anthropic

load_dotenv()


# generates and evaluates model responses on synthetic system prompts and eval set situation questions

# Number of conversational turns to generate under --multiturn (the first turn comes from the
# usual single-turn generation; the rest are simulated user turn + assistant turn rounds).
NUM_TURNS = 3

# Concurrent Claude API calls when simulating user turns (I/O-bound, unlike the batched GPU
# generation calls, so these are parallelized with threads instead of batching).
SIMULATOR_WORKERS = 20


def parse_args():
    parser = argparse.ArgumentParser(description="Generate model responses on synthetic system prompts and situation questions")
    parser.add_argument(
        "--multiturn", action="store_true",
        help="Generate 3-turn conversations instead of single-turn responses: after the usual "
             "first turn, a Claude Haiku user-simulator (blind to the system prompt) writes the "
             "next user message, and Llama generates the next assistant response, twice more. "
             "Saved to responses_multiturn/ instead of responses/.",
    )
    return parser.parse_args()


def load_json(filepath: str) -> dict:
    with open(filepath, 'r') as f:
        return json.load(f)


def send_message(client, message, model="claude-haiku-4-5-20251001", max_tokens=200, temperature=0.8):
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        messages=[{"role": "user", "content": message}],
    )
    for block in response.content:
        if block.type == "text":
            return block.text.strip()
    raise ValueError(f"No text block in response: {response.content}")


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


def generate_response_from_conversation(model, tokenizer, conversations, max_length, device):
    """Like generate_response, but each conversation is already a full chat message list
    (system message + alternating user/assistant turns, ending on a user message) instead of
    a single (system_prompt, message) pair. Returns one continuation per conversation."""
    full_prompts = [
        tokenizer.apply_chat_template(chat, tokenize=False, add_generation_prompt=True)
        for chat in conversations
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
            do_sample=True,
            temperature=1,
            top_p=0.95,
            pad_token_id=tokenizer.eos_token_id,
        )

    return tokenizer.batch_decode(batch_tokens[:, prompt_length:], skip_special_tokens=True)


def build_user_simulator_prompt(visible_messages):
    conversation_text = "\n\n".join(
        f"{'User' if message['role'] == 'user' else 'Assistant'}: {message['content']}"
        for message in visible_messages
    )
    return (
        "You are roleplaying as a human user in the conversation below with an AI "
        "assistant. Write the user's next message, continuing the conversation naturally "
        "and staying in character as the user. Keep it to 1-3 sentences, conversational, "
        "and do not mention that you are roleplaying or break character.\n\n"
        f"<conversation>\n{conversation_text}\n</conversation>\n\n"
        "Only respond with the user's next message."
    )


def simulate_next_user_messages(client, visible_message_lists, desc="simulating next user turn"):
    """For each conversation's visible (system-prompt-free) message history, have Claude
    Haiku roleplay the user and write the next message. The simulator never sees the system
    prompt, matching what a real user would see. Runs concurrently since these are small
    independent API calls rather than batched GPU compute."""
    results = [None] * len(visible_message_lists)

    def call_one(index):
        prompt = build_user_simulator_prompt(visible_message_lists[index])
        message = send_message(client, prompt, model="claude-haiku-4-5-20251001", max_tokens=200, temperature=0.8)
        return index, message

    with ThreadPoolExecutor(max_workers=SIMULATOR_WORKERS) as executor:
        futures = [executor.submit(call_one, i) for i in range(len(visible_message_lists))]
        for future in tqdm(as_completed(futures), total=len(futures), desc=desc, leave=False):
            index, message = future.result()
            results[index] = message

    return results


def run_single_turn(model, tokenizer, device, traits, num_questions, num_rollouts, batch_size, max_length):
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


def chunked(items, size):
    return [items[i:i + size] for i in range(0, len(items), size)]


def run_multiturn(model, tokenizer, device, anthropic_client, traits, num_questions, num_rollouts, batch_size, max_length):
    for trait in traits:

        prompts_file = Path(f"system_prompts/{trait}.json")

        system_prompts_dict = load_json(prompts_file)

        responses_file = Path(f"responses_multiturn/{trait}.json")
        if responses_file.exists():
            print(f"Skipping multiturn inference for {trait}, responses already exist.")
            continue

        user_messages_data = load_json(f"../generation/stored_prompts/{trait}/user_messages.json")
        messages = user_messages_data["user_messages"][-num_questions:]

        os.makedirs("responses_multiturn", exist_ok=True)
        response_skeleton = {}
        all_items = []  # (level_key, system_prompt_key, system_prompt, message) across every combination
        for level, rollouts in system_prompts_dict.items():
            level_key = f"level-{level}"
            response_skeleton[level_key] = {}
            for system_prompt_index, system_prompt in rollouts.items():
                system_prompt_key = f"system-prompt-{system_prompt_index}"
                response_skeleton[level_key][system_prompt_key] = []
                for message in messages:
                    all_items.append((level_key, system_prompt_key, system_prompt, message))

        def flush(conversations):
            """Checkpoint whatever turns have been generated so far, so an interruption
            mid-trait doesn't lose everything, not just everything since the last batch."""
            responses_dict = {level_key: {sp_key: [] for sp_key in sp_keys} for level_key, sp_keys in response_skeleton.items()}
            for conv in conversations:
                responses_dict[conv["level_key"]][conv["system_prompt_key"]].append({
                    "rollout_index": conv["rollout_index"],
                    "system_prompt": conv["system_prompt"],
                    "turns": conv["turns"],
                })
            with open(responses_file, "w") as f:
                json.dump(responses_dict, f, indent=2, ensure_ascii=False)

        items_per_batch = max(1, batch_size // num_rollouts)
        item_batches = chunked(all_items, items_per_batch)

        # Phase 1 (turn 1): run the usual batched Llama generation over every item in the
        # trait before moving on to turn 2, so the GPU stays continuously busy across the
        # whole trait instead of pausing for API calls after every small batch.
        conversations = []
        for item_batch in tqdm(item_batches, desc=f"{trait} turn 1 llama", leave=False):
            prompt_pairs = [(system_prompt, message) for _, _, system_prompt, message in item_batch]
            first_turn_responses = generate_response(
                model, tokenizer, prompt_pairs, max_length, num_rollouts, device
            )

            # Expand each item into one conversation per rollout. full_messages (fed to Llama)
            # includes the system prompt; visible_messages (fed to the Claude user-simulator)
            # never does, since a real user wouldn't see it either.
            for item_index, (level_key, system_prompt_key, system_prompt, message) in enumerate(item_batch):
                flat_start = item_index * num_rollouts
                for rollout_index, response in enumerate(first_turn_responses[flat_start:flat_start + num_rollouts]):
                    system_message = {
                        "role": "system",
                        "content": f"You are an AI assistant. Keep responses concise and conversational. {system_prompt}",
                    }
                    user_message = {"role": "user", "content": message}
                    assistant_message = {"role": "assistant", "content": response}
                    conversations.append({
                        "level_key": level_key,
                        "system_prompt_key": system_prompt_key,
                        "system_prompt": system_prompt,
                        "rollout_index": rollout_index,
                        "full_messages": [system_message, user_message, assistant_message],
                        "visible_messages": [user_message, assistant_message],
                        "turns": [{"user_message": message, "response": response}],
                    })
        flush(conversations)

        for turn in range(2, NUM_TURNS + 1):
            # Phase 2a: every user-simulator API call for this turn, across the whole trait,
            # dispatched together so concurrency uses the full worker pool instead of being
            # capped at whatever fit in one GPU batch.
            next_user_messages = simulate_next_user_messages(
                anthropic_client, [conv["visible_messages"] for conv in conversations],
                desc=f"{trait} turn {turn} api calls",
            )
            for conv, next_message in zip(conversations, next_user_messages):
                conv["full_messages"].append({"role": "user", "content": next_message})
                conv["visible_messages"].append({"role": "user", "content": next_message})
                conv["pending_user_message"] = next_message

            # Phase 2b: the matching assistant turn, again as one pass over the whole trait
            # (chunked only by batch_size for GPU memory, not interleaved with API calls).
            for conv_batch in tqdm(chunked(conversations, batch_size), desc=f"{trait} turn {turn} llama", leave=False):
                next_responses = generate_response_from_conversation(
                    model, tokenizer, [conv["full_messages"] for conv in conv_batch], max_length, device
                )
                for conv, next_response in zip(conv_batch, next_responses):
                    conv["full_messages"].append({"role": "assistant", "content": next_response})
                    conv["visible_messages"].append({"role": "assistant", "content": next_response})
                    conv["turns"].append({"user_message": conv.pop("pending_user_message"), "response": next_response})
            flush(conversations)


def main():
    args = parse_args()

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
    batch_size = 100  # total sequences per generate() call; items_per_batch = batch_size // num_rollouts
    max_length = 512

    if args.multiturn:
        anthropic_client = anthropic.Anthropic()
        run_multiturn(
            model, tokenizer, device, anthropic_client, traits,
            num_questions, num_rollouts, batch_size, max_length,
        )
    else:
        run_single_turn(
            model, tokenizer, device, traits,
            num_questions, num_rollouts, batch_size, max_length,
        )


if __name__ == "__main__":
    main()
