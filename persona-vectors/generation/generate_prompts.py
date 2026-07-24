import anthropic
import json
import os
import argparse
from dotenv import load_dotenv

load_dotenv()

def parse_args():
    parser = argparse.ArgumentParser(description='Generate persona vectors from contrastive prompts')
    parser.add_argument('--trait', type=str, required=True)
    return parser.parse_args()


def send_message(client, message, model="claude-sonnet-5", max_tokens=1000, system_prompt=None):
    kwargs = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": message}],
    }
    if system_prompt:
        kwargs["system"] = system_prompt
    response = client.messages.create(**kwargs)
    for block in response.content:
        if block.type == "text":
            return block.text
    raise ValueError(f"No text block in response: {response.content}")


def main():
    client = anthropic.Anthropic()
    args = parse_args()

    trait = args.trait

    trait_description_path = f"stored_prompts/{trait}/trait_description.json"
    contrastive_path = f"stored_prompts/{trait}/contrastive_system_prompts.json"
    user_messages_path = f"stored_prompts/{trait}/user_messages.json"

    os.makedirs(f"stored_prompts/{trait}", exist_ok=True)

    max_tokens = 8192
    num_messages = 60

    if os.path.exists(trait_description_path):
        print(f"Trait description for '{trait}' already exists, skipping generation.")
        with open(trait_description_path) as f:
            trait_description_data = json.load(f)
    else:
        trait_description_prompt = f"Give the definition of {trait} that is relevant to human-AI interaction or conversations with AI in one or two sentences. Don't explicitly mention AI in the definition. Start it with '{trait} is' "
        # trait_description_prompt = f"Give the definition of {trait} in one to two sentences. Start it with '{trait} is' "
        opposite_trait_description_prompt = f"Give the definition of the opposite of {trait} that is relevant to human-AI interaction or conversations with AI in one or two sentences. Don't explicitly mention AI in the definition. Start it with 'The opposite of {trait} is' "

        trait_description = send_message(
            client, trait_description_prompt,
            model="claude-sonnet-5",
            max_tokens=128,
        )
        opposite_trait_description = send_message(
            client, opposite_trait_description_prompt,
            model="claude-sonnet-5",
            max_tokens=128,
        )

        # trait_description = "Casual describes a conversational tone and personality style characterized by relaxed, informal language and a laid-back manner of engaging with others. A casual communicator uses everyday vocabulary, contractions, and colloquialisms, avoids stiff or overly formal phrasing, and interacts as if speaking with a friend rather than in a professional or structured setting."
        # trait_description = "Toxic is a manner of speaking that is harmful, offensive, or damaging in some way to a user."

        print(trait_description)
        print(opposite_trait_description)

        trait_description_data = {
            "trait_description": trait_description,
            "opposite_trait_description": opposite_trait_description,
        }

        with open(trait_description_path, "w") as f:
            json.dump(trait_description_data, f)

    # trait_description = trait_description_data["trait_description"]

    # if os.path.exists(contrastive_path):
    #     print(f"Contrastive system prompts for '{trait}' already exist, skipping generation.")
    # else:
    #     # Create constrastive system prompts
    #     constrastive_dataset_prompt = f"""
    # You are tasked with creating a dataset of contrastive system prompts that will be used to elicit capture a specific persona in an LLM.

    # The trait you will be working with is
    # <trait>
    # {trait}
    # </trait>

    # and its definition is
    # <trait_description>
    # {trait_description}
    # </trait_description>

    # CORE INSTRUCTION: Generate a list of 10 instruction pairs. Each pair should include a positive (pos) instruction that commands the model to exhibit the trait, and a negative (neg) instruction that explicitly commands the model to exhibit the opposite behavior. Here's an example pair for the trait "impolite":

    # <example_pair>
    # "pos": "Your responses should be impolite or harsh. Do not soften your language or try to be polite.",
    # "neg": "Your responses should remain polite and respectful, even when expressing your true opinion."
    # </example_pair>

    # ADDITIONAL CONSTRAINTS:
    # Ensure each pair is distinct and captures different aspects of the trait.
    # The the first two pairs must be one sentence long, then the second two pairs must be two sentences long, and so on until the fifth pair is five sentences long.

    # Organize your response in the following JSON format:
    # <output_format>
    # {{
    # "instruction": [
    #     {{"pos": "positive instruction 1", "neg": "negative instruction 1"}},
    #     {{"pos": "positive instruction 2", "neg": "negative instruction 2"}},
    #     {{"pos": "positive instruction 3", "neg": "negative instruction 3"}},
    #     {{"pos": "positive instruction 4", "neg": "negative instruction 4"}},
    #     {{"pos": "positive instruction 5", "neg": "negative instruction 5"}},
    #     {{"pos": "positive instruction 6", "neg": "negative instruction 6"}},
    #     {{"pos": "positive instruction 7", "neg": "negative instruction 7"}},
    #     {{"pos": "positive instruction 8", "neg": "negative instruction 8"}},
    #     {{"pos": "positive instruction 9", "neg": "negative instruction 9"}},
    #     {{"pos": "positive instruction 10", "neg": "negative instruction 10"}}
    # ]
    # }}
    # </output_format>

    # FORMATTING CONSTRAINTS:
    # Respond with ONLY the raw JSON object.
    # Do NOT wrap in markdown code blocks.
    # Do NOT include ```json or ```.
    # Your response must start with {{ and end with }}
    # """

    #     while True:
    #         try:
    #             response = send_message(
    #                 client, constrastive_dataset_prompt,
    #                 model="claude-sonnet-5",
    #                 max_tokens=max_tokens,
    #             )
    #             data = json.loads(response)
    #             break

    #         except json.JSONDecodeError as e:
    #             print(f"Error parsing JSON 1: {e}")

    #     with open(contrastive_path, "w") as f:
    #         json.dump(data, f)

    #     print("Contrastive system prompts created.")

    # if os.path.exists(user_messages_path):
    #     print(f"User messages for '{trait}' already exist, skipping generation.")
    # else:
    #     message_generation_prompt = f"""

    # CORE INSTRUCTION: Generate {num_messages} diverse user messages that could elicit behavior that expresses the following trait when following an instruction to exhibit a certain trait as a system prompt.

    # ADDITIONAL CONSTRAINTS:
    # These user messages need to be diverse, and cover various scenarios, and realistic to a general AI assistant chatbot setting.
    # Do not explicitly ask the model to exhibit the trait in question.
    # Vary the lengths of these questions between 1-5 sentences.

    # The trait you will be working with is
    # <trait>
    # {trait}
    # </trait>

    # and its description is
    # <trait_description>
    # {trait_description}
    # </trait_description>

    # and an EXAMPLE of the system prompt instruction for a trait 'impolite' would be:
    # <example_pair>
    # "pos": "Your responses should be impolite or harsh. Do not soften your language or try to be polite.",
    # "neg": "Your responses should remain polite and respectful, even when expressing your true opinion."
    # </example_pair>

    # Organize your response in the following JSON format:
    # <output_format>
    # {{
    # "user_messages": [
    #     "message 1",
    #     "message 2",
    #     ...
    #     "message {num_messages}"
    # ]
    # }}
    # </output_format>

    # FORMATTING CONSTRAINTS:
    # Respond with ONLY the raw JSON object.
    # Do NOT wrap in markdown code blocks.
    # Do NOT include ```json or ```.
    # Your response must start with {{ and end with }}
    # """

    #     while True:
    #         try:
    #             response = send_message(
    #                 client, message_generation_prompt,
    #                 model="claude-sonnet-5",
    #                 max_tokens=max_tokens,
    #             )
    #             data = json.loads(response)
    #             break
    #         except json.JSONDecodeError as e:
    #             print(f"Error parsing JSON 2: {e}")

    #     with open(user_messages_path, "w") as f:
    #         json.dump(data, f)

    #     print("User messages created.")



if __name__ == "__main__":
    main()