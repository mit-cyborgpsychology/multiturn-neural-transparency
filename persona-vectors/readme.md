## Overview

/generation - code to generate persona vectors based on selected traits
generate_prompts.py - Use Claude to generate a trait description, contrastive system prompts, and user messages
persona_vectors.py - Use Llama and created prompts to create persona vectors (mean positive minus mean negative activation, for every layer)


/evaluation - code to create scaling for interface, evaluate persona vectors with linear regression, create graphs
generate_system_prompts.py - create synthetic system prompts at trait levels 1-10 for linear regression analysis
generate_responses.py - generate Llama responses to those system prompts
relabel_responses.py - score those responses with a gpt-5-mini judge
evaluate.py - do linear regression on each layer of the persona vector and create graphs
rescale.py - rescale evaluate.py's cached scores and write scale.json for persona scores (also to generation/persona_vectors/)

/chat - code to simulate multi-turn conversations and track persona scores across turns
generate_example_convo.py - simulate multi-turn conversations and score persona vectors after every turn
compare_example_convo.py - re-score those conversations with every activation-extraction method
graph_convo.py - plot the per-turn scores from compare_example_convo.py
turn_effects.py - measure how persona scores change as conversation history grows

/modal - contains code to launch chat and persona score generation endpoints

