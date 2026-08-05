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
    parser.add_argument(
        "--resume-multiturn", action="store_true",
        help="For each trait with an existing but incomplete responses_multiturn/{trait}.json "
             "(fewer than NUM_TURNS turns saved per conversation, e.g. after a crash mid-run), "
             "generate only the missing turns and keep flushing into that same file. Traits with "
             "no file yet, or a file already at NUM_TURNS turns, are left untouched.",
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
        for future in tqdm(as_completed(futures), total=len(futures), desc=desc, leave=True):
            index, message = future.result()
            results[index] = message

    return results


def run_single_turn(model, tokenizer, device, traits, num_questions, num_rollouts, batch_size, max_length):
    for trait in traits:
        try:
            _run_single_turn_trait(model, tokenizer, device, trait, num_questions, num_rollouts, batch_size, max_length)
        except Exception as e:
            print(f"Error processing {trait}, skipping to next trait. Results generated before the "
                  f"error are already saved to responses/{trait}.json. Error: {e}")


def _run_single_turn_trait(model, tokenizer, device, trait, num_questions, num_rollouts, batch_size, max_length):
    prompts_file = Path(f"system_prompts/{trait}.json")

    system_prompts_dict = load_json(prompts_file)

    responses_file = Path(f"responses/{trait}.json")
    if responses_file.exists():
        print(f"Skipping inference for {trait}, responses already exist.")
        return

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

    for item_batch in tqdm(item_batches, desc=f"{trait} batches", leave=True):
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


def _load_multiturn_trait(trait, num_questions):
    """Load one trait's prompts/messages and lay out the flat (level, system prompt, message)
    item list plus the (empty) skeleton its responses file will be shaped like. Returns None
    if this trait's responses already exist, so the caller can skip it entirely."""
    prompts_file = Path(f"system_prompts/{trait}.json")
    system_prompts_dict = load_json(prompts_file)

    responses_file = Path(f"responses_multiturn/{trait}.json")
    if responses_file.exists():
        print(f"Skipping multiturn inference for {trait}, responses already exist.")
        return None

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

    return {
        "responses_file": responses_file,
        "response_skeleton": response_skeleton,
        "all_items": all_items,
        "conversations": [],
    }


def _flush_multiturn(state):
    """Checkpoint whatever turns have been generated so far for this trait, so an
    interruption mid-run doesn't lose everything, not just everything since the last batch."""
    responses_dict = {
        level_key: {sp_key: [] for sp_key in sp_keys}
        for level_key, sp_keys in state["response_skeleton"].items()
    }
    for conv in state["conversations"]:
        responses_dict[conv["level_key"]][conv["system_prompt_key"]].append({
            "rollout_index": conv["rollout_index"],
            "system_prompt": conv["system_prompt"],
            "turns": conv["turns"],
        })
    with open(state["responses_file"], "w") as f:
        json.dump(responses_dict, f, indent=2, ensure_ascii=False)


def _generate_first_turn(model, tokenizer, device, trait, state, num_rollouts, batch_size, max_length):
    """Turn 1: run the usual batched Llama generation over every item in the trait,
    flushing after every batch so a crash partway through doesn't lose the batches
    already generated."""
    items_per_batch = max(1, batch_size // num_rollouts)
    item_batches = chunked(state["all_items"], items_per_batch)

    for item_batch in tqdm(item_batches, desc=f"{trait} turn 1 llama", leave=True):
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
                state["conversations"].append({
                    "level_key": level_key,
                    "system_prompt_key": system_prompt_key,
                    "system_prompt": system_prompt,
                    "rollout_index": rollout_index,
                    "full_messages": [system_message, user_message, assistant_message],
                    "visible_messages": [user_message, assistant_message],
                    "turns": [{"user_message": message, "response": response}],
                })
        _flush_multiturn(state)


def _simulate_user_turn(anthropic_client, trait, state, turn):
    """The user-simulator API call for this turn, across the whole trait, dispatched
    together so concurrency uses the full worker pool instead of being capped at
    whatever fit in one GPU batch."""
    conversations = state["conversations"]
    next_user_messages = simulate_next_user_messages(
        anthropic_client, [conv["visible_messages"] for conv in conversations],
        desc=f"{trait} turn {turn} api calls",
    )
    for conv, next_message in zip(conversations, next_user_messages):
        conv["full_messages"].append({"role": "user", "content": next_message})
        conv["visible_messages"].append({"role": "user", "content": next_message})
        conv["pending_user_message"] = next_message


def _generate_assistant_turn(model, tokenizer, device, trait, state, turn, batch_size, max_length):
    """The matching assistant turn, chunked by this turn's batch size (longer accumulated
    context can need a smaller batch to fit in VRAM), flushing after every batch so a
    crash partway through this turn doesn't lose progress."""
    conversations = state["conversations"]
    for conv_batch in tqdm(chunked(conversations, batch_size), desc=f"{trait} turn {turn} llama", leave=True):
        next_responses = generate_response_from_conversation(
            model, tokenizer, [conv["full_messages"] for conv in conv_batch], max_length, device
        )
        for conv, next_response in zip(conv_batch, next_responses):
            conv["full_messages"].append({"role": "assistant", "content": next_response})
            conv["visible_messages"].append({"role": "assistant", "content": next_response})
            conv["turns"].append({"user_message": conv.pop("pending_user_message"), "response": next_response})
        _flush_multiturn(state)


def run_multiturn(model, tokenizer, device, anthropic_client, traits, num_questions, num_rollouts, batch_sizes, max_length):
    """Turn-major instead of trait-major: generate turn 1 for every trait before any trait
    moves on to turn 2, then turn 2 for every trait before turn 3, and so on. A trait that
    errors out on a phase is dropped from the remaining phases, but whatever it already
    flushed to responses_multiturn/{trait}.json is kept."""
    trait_states = {}
    for trait in traits:
        try:
            state = _load_multiturn_trait(trait, num_questions)
        except Exception as e:
            print(f"Error loading {trait}, skipping. Error: {e}")
            continue
        if state is not None:
            trait_states[trait] = state

    for trait in list(trait_states):
        try:
            _generate_first_turn(model, tokenizer, device, trait, trait_states[trait], num_rollouts, batch_sizes[1], max_length)
        except Exception as e:
            print(f"Error processing {trait} turn 1, skipping to next trait. Results generated before the "
                  f"error are already saved to responses_multiturn/{trait}.json. Error: {e}")
            del trait_states[trait]

    for turn in range(2, NUM_TURNS + 1):
        for trait in list(trait_states):
            try:
                _simulate_user_turn(anthropic_client, trait, trait_states[trait], turn)
            except Exception as e:
                print(f"Error simulating turn {turn} user message for {trait}, skipping to next trait. Results "
                      f"generated before the error are already saved to responses_multiturn/{trait}.json. Error: {e}")
                del trait_states[trait]

        for trait in list(trait_states):
            try:
                _generate_assistant_turn(model, tokenizer, device, trait, trait_states[trait], turn, batch_sizes[turn], max_length)
            except Exception as e:
                print(f"Error processing {trait} turn {turn}, skipping to next trait. Results generated before the "
                      f"error are already saved to responses_multiturn/{trait}.json. Error: {e}")
                del trait_states[trait]


def _load_resumable_trait(trait):
    """Load an existing responses_multiturn/{trait}.json and reconstruct the in-memory
    conversation state (full_messages, visible_messages) from its saved turns, so generation
    can continue exactly where a crash left off. Returns None if there's nothing to resume:
    no file yet, or a file whose conversations already have NUM_TURNS turns."""
    responses_file = Path(f"responses_multiturn/{trait}.json")
    if not responses_file.exists():
        print(f"No responses_multiturn/{trait}.json yet, nothing to resume for {trait}.")
        return None

    responses_dict = load_json(responses_file)
    response_skeleton = {
        level_key: {sp_key: [] for sp_key in sp_dict}
        for level_key, sp_dict in responses_dict.items()
    }

    conversations = []
    min_turns = None
    for level_key, sp_dict in responses_dict.items():
        for system_prompt_key, convs in sp_dict.items():
            for conv in convs:
                turns = conv["turns"]
                min_turns = len(turns) if min_turns is None else min(min_turns, len(turns))
                system_prompt = conv["system_prompt"]
                full_messages = [{
                    "role": "system",
                    "content": f"You are an AI assistant. Keep responses concise and conversational. {system_prompt}",
                }]
                visible_messages = []
                for t in turns:
                    full_messages.append({"role": "user", "content": t["user_message"]})
                    full_messages.append({"role": "assistant", "content": t["response"]})
                    visible_messages.append({"role": "user", "content": t["user_message"]})
                    visible_messages.append({"role": "assistant", "content": t["response"]})
                conversations.append({
                    "level_key": level_key,
                    "system_prompt_key": system_prompt_key,
                    "system_prompt": system_prompt,
                    "rollout_index": conv["rollout_index"],
                    "full_messages": full_messages,
                    "visible_messages": visible_messages,
                    "turns": list(turns),
                })

    if not conversations or min_turns is None or min_turns < 1:
        print(f"responses_multiturn/{trait}.json has no completed turn 1 yet, can't resume "
              f"{trait} -- rerun with --multiturn instead.")
        return None

    if min_turns >= NUM_TURNS:
        print(f"responses_multiturn/{trait}.json already has {NUM_TURNS} turns, nothing to resume for {trait}.")
        return None

    if any(len(conv["turns"]) != min_turns for conv in conversations):
        print(f"Warning: {trait} has conversations at mixed turn counts; resuming everyone from "
              f"the lowest ({min_turns}) turns saved -- conversations already ahead of that will "
              f"have their later turns regenerated.")
        for conv in conversations:
            if len(conv["turns"]) > min_turns:
                conv["turns"] = conv["turns"][:min_turns]
                conv["full_messages"] = conv["full_messages"][:1 + 2 * min_turns]
                conv["visible_messages"] = conv["visible_messages"][:2 * min_turns]

    return {
        "responses_file": responses_file,
        "response_skeleton": response_skeleton,
        "conversations": conversations,
        "next_turn": min_turns + 1,
    }


def run_resume_multiturn(model, tokenizer, device, anthropic_client, traits, batch_sizes, max_length):
    """Turn-major continuation of run_multiturn for traits that already have a partial
    responses_multiturn/{trait}.json: pick up at whatever turn each trait left off on and
    generate forward from there, in lockstep across traits the same way run_multiturn does."""
    trait_states = {}
    for trait in traits:
        try:
            state = _load_resumable_trait(trait)
        except Exception as e:
            print(f"Error loading {trait} for resume, skipping. Error: {e}")
            continue
        if state is not None:
            trait_states[trait] = state

    if not trait_states:
        print("Nothing to resume -- no incomplete responses_multiturn files found.")
        return

    for turn in range(2, NUM_TURNS + 1):
        turn_traits = [trait for trait, state in trait_states.items() if state["next_turn"] <= turn]
        if not turn_traits:
            continue

        for trait in turn_traits:
            try:
                _simulate_user_turn(anthropic_client, trait, trait_states[trait], turn)
            except Exception as e:
                print(f"Error simulating turn {turn} user message for {trait}, skipping to next trait. Results "
                      f"generated before the error are already saved to responses_multiturn/{trait}.json. Error: {e}")
                del trait_states[trait]

        for trait in [t for t in turn_traits if t in trait_states]:
            try:
                _generate_assistant_turn(model, tokenizer, device, trait, trait_states[trait], turn, batch_sizes[turn], max_length)
            except Exception as e:
                print(f"Error processing {trait} turn {turn}, skipping to next trait. Results generated before the "
                      f"error are already saved to responses_multiturn/{trait}.json. Error: {e}")
                del trait_states[trait]


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

    num_questions = 10  # final N situational questions to run inference on
    num_rollouts = 1
    batch_size = 200  # total sequences per generate() call; items_per_batch = batch_size // num_rollouts
    # Per-turn batch sizes for --multiturn: total sequences per generate() call on that turn.
    # Later turns carry more accumulated conversation context per sequence, so they may need
    # a smaller batch size to fit the same VRAM budget.
    batch_sizes = {1: 250, 2: 250, 3: 100}
    max_length = 512

    if args.multiturn:
        anthropic_client = anthropic.Anthropic()
        run_multiturn(
            model, tokenizer, device, anthropic_client, traits,
            num_questions, num_rollouts, batch_sizes, max_length,
        )
    elif args.resume_multiturn:
        anthropic_client = anthropic.Anthropic()
        run_resume_multiturn(
            model, tokenizer, device, anthropic_client, traits,
            batch_sizes, max_length,
        )
    else:
        run_single_turn(
            model, tokenizer, device, traits,
            num_questions, num_rollouts, batch_size, max_length,
        )


if __name__ == "__main__":
    main()
