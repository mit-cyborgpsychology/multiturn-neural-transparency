# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

This directory is the "persona vectors" backend for a research project (multi-turn neural transparency: surfacing an LLM's internal activations to help users anticipate behavioral drift like sycophancy or toxicity). It builds **persona vectors** — directions in a Llama model's residual-stream activation space that correlate with expression of a personality trait (e.g. sycophancy, empathy, toxicity) — and evaluates how well they predict trait intensity, including across multi-turn conversations. It is one of three components in the parent repo (`interface/` is the participant-facing chat UI, `user-study-analysis/` is the stats pipeline); this directory only covers the persona-vector generation/evaluation backend.

`readme.md` in this directory is stale (references files/functions — `generate_persona_vectors.py`, `activations_viz.py`, `create_regression_data.py`, `eval_layers_regression.py` — that no longer exist). Trust the actual code over that file.

## Setup

- Dependencies are declared in the **repo root** `../requirements.txt` (not a local one): `transformers`, `huggingface_hub`, `transformer_lens`, `tqdm`, `requests`, `dotenv`, `openai`, `anthropic`, `scipy`, `matplotlib`. `torch`, `numpy`, `fastapi`, `pydantic`, and `modal` are also imported but not pinned there.
- All scripts call `load_dotenv()` and expect a `.env` file (gitignored) with `HF_TOKEN`, `ANTHROPIC_API_KEY`, and `OPENAI_API_KEY`.
- Requires GPU (`torch.device("cuda")`) for any script that loads Llama-3.1-8B-Instruct; falls back to CPU but will be very slow.
- **Scripts use paths relative to their own directory**, not the repo root — run each one with its own folder as the working directory (`cd generation && python persona_vectors.py ...`, `cd evaluation && python evaluate.py`, etc.). Several `evaluation/` scripts also reach across to `../generation/...`.

## Commands

There is no test suite, linter, or build step in this directory — it's a research/data pipeline. The pipeline runs in this order:

```bash
# 1. Generate trait description + contrastive system prompts + user messages via Claude
cd generation && python generate_prompts.py --trait sycophancy

# 2. Run Llama-3.1-8B-Instruct on those prompts, judge responses with gpt-5-mini,
#    and derive the persona vector (mean pos activation − mean neg activation)
cd generation && python persona_vectors.py --trait sycophancy   # comma-separated for multiple traits

# 3. Generate synthetic system prompts at trait intensity levels 1-10 (for supervised eval)
cd evaluation && python generate_system_prompts.py

# 4. Generate Llama responses to those level-labeled system prompts
cd evaluation && python generate_responses.py

# 5. Score those responses with a gpt-5-mini judge and report judge/level agreement
cd evaluation && python relabel_responses.py [--force]

# 6. Score persona-vector fit per layer (cosine similarity / projection vs. trait level),
#    fit linear regression per layer, find the best layer, plot results
cd evaluation && python evaluate.py

# 7. (separate/legacy path, see Known gotchas below) compute min/max score scale per trait
cd evaluation && python create_scale.py
```

Ad hoc / manual tools:
```bash
cd chat && python llama_chat.py --model 8b --system "..."   # interactive terminal chat with Llama 8B/3B
cd chat && python turn_effects.py                            # persona-score drift across multi-turn conversations
```

Modal-hosted inference endpoints (deploy with the `modal` CLI, e.g. `modal deploy modal/chat_api.py`):
```bash
modal deploy modal/chat_api.py            # generic Llama chat completion endpoint (Anthropic-message-shaped)
modal deploy modal/persona_score_api.py   # given a system prompt, returns per-trait persona scores
```

## Architecture

**Pipeline stages and data flow** (traits discovered dynamically each stage by scanning for existing files, e.g. `generation/persona_vectors/*.pt`, so adding a new trait just means running stage 1 for it):

1. `generation/generate_prompts.py` — Anthropic API only. Per trait, writes to `generation/stored_prompts/{trait}/`: `trait_description.json`, `contrastive_system_prompts.json` (10 pos/neg instruction pairs), `user_messages.json` (60 diverse user messages). Idempotent — skips any file that already exists.
2. `generation/persona_vectors.py` — loads `meta-llama/Llama-3.1-8B-Instruct`. For every (pos/neg instruction × user message), generates a response and captures the **residual stream at every layer** via `register_forward_hook` on `model.model.layers[i]`, either mean-pooled or final-token (`activation_type`). A gpt-5-mini judge scores each response 0-100 for trait expression; only responses that agree with their intended polarity (pos ≥ 50 / neg ≤ 50) are kept. The persona vector is `mean(kept pos activations) − mean(kept neg activations)`, stacked across all layers into one tensor, saved as `generation/persona_vectors/{trait}_{mean|final}.pt`. Raw responses go to `generation/responses/{trait}.json`.
3. `evaluation/generate_system_prompts.py` — Claude Haiku generates synthetic system prompts at intensity levels 1-10 (multiple sentence lengths) per trait, for supervised layer/metric evaluation. Written to `evaluation/system_prompts/{trait}.json`.
4. `evaluation/generate_responses.py` — runs Llama on every (level system prompt × held-out user message) pair, writes `evaluation/responses/{trait}.json`.
5. `evaluation/relabel_responses.py` — reuses `generation.persona_vectors.OpenAIAPI`; judges each response with gpt-5-mini, rescales the 0-100 judge score to 0-10 (`gpt_score`), and reports agreement between the judge score and the system prompt's intended level. Writes `evaluation/results/relabel_stats.json`.
6. `evaluation/evaluate.py` (`GraphEvaluator`) — for each response, runs the full `(system prompt + question + response)` context through Llama, extracts the activation at every layer, and scores it against the stored persona vector using **cosine similarity** (angle only) and **scalar projection** (keeps magnitude). Ground truth per response averages the system prompt's intended level with its `gpt_score` when available. Fits a per-layer linear regression (score vs. level), ranks layers by R², and writes plots (`evaluation/results/{combo_tag}_{trait}_{metric}.png`) and `evaluation/results/results.json`. `COMBOS` at the top of the file controls which (response-activation-type, persona-vector-type) pairs get evaluated.
7. `chat/turn_effects.py` — studies how persona-vector projection scores (fixed at one layer, `layer_idx`) drift as multi-turn conversation history grows, across different system-prompt personas and user-message scenarios; also scores responses with a gpt-4.1-mini judge for whether they embody the persona, and plots turn-by-turn projection vs. LLM-judged score.

**Known gotcha — two persona-vector storage conventions coexist:**
- `generation/persona_vectors/{trait}_{mean|final}.pt` is the current, actively-produced format (stage 2 above), a single tensor stacking all layers, consumed by `evaluation/generate_system_prompts.py`, `evaluation/generate_responses.py`, `evaluation/relabel_responses.py`, `evaluation/evaluate.py`.
- `generation/stored_persona_vectors/{trait}.pt` + a `traits.json` (trait → positive/negative label metadata) + `scale.json` (min/max normalization) is a separate, curated format expected by `evaluation/create_scale.py`, `chat/turn_effects.py`, and `modal/persona_score_api.py`. **This directory does not currently exist in the repo** — the closest match is `generation/old_persona_vectors/` (single-layer `.pt` per trait, plus its own `traits.json`/`scale.json`, for the older trait set: empathy, erudite, robotic, romantic). Before running `create_scale.py`, `turn_effects.py`, or deploying `persona_score_api.py`, check whether `stored_persona_vectors/` needs to be created/renamed from `old_persona_vectors/`, or whether those scripts need updating to point at `generation/persona_vectors/` instead.

**`evaluation/results_no_opposite/vector_comparison/`** compares the 4 combos of (response-activation pooling, persona-vector pooling) — `mean`/`final` × `mean`/`final` — for the cosine-similarity metric only. Unlike the main `results_no_opposite/results.json` (which covers all traits: empathy, erudite, robotic, romantic, sycophancy, toxicity), this subdirectory has only ever been run for **sycophancy** — each combo's entry in `vector_comparison/results.json` has a single `sycophancy` key, not an average across traits. Its `cache/{combo_tag}_{trait}.json` files hold the raw per-response `layer_levels`/`layer_scores` (per `evaluate.py`'s `save_scores_cache`); `vector_comparison/results.json` holds the fitted-per-layer summary (`best_layer`, and per-layer `slope`/`intercept`/`r_squared`/`normalized_mse`/etc. from `fit_layer`). As of the last check, mean-pooling both the response activation and the persona vector gives the best fit (layer 16, R²≈0.92, normalized MSE≈0.085); using final-token pooling for either side degrades the fit, worst when both sides use final-token.

When reporting these 4 combos as a table, use columns in this order: **Persona Vector Type**, **Response Activation**, **Best Layer**, **Norm. MSE**, **R²** (title case headers, no slope/intercept column), sorted by Norm. MSE ascending (best fit first), with rows grouped by Persona Vector Type. In LaTeX, merge the Persona Vector Type column across its two rows with `\multirow{2}{*}{...}` (requires `\usepackage{multirow}`).

**`evaluation/results_no_opposite/results.json`** (the main, non-`vector_comparison` results file) compares 4 *response activation types* — all with persona vector type `mean` and `multiturn=True`, metric `cosine` only — across all 6 multiturn traits (empathy, erudite, robotic, romantic, sycophancy, toxicity). The combo tags map to display labels as: `prompt_final_persona-mean_multiturn` → "User Prompt Final", `mean_persona-mean_multiturn` → "Response Mean", `final_persona-mean_multiturn` → "Response Final", `conversation_mean_persona-mean_multiturn` → "Conversation Mean". To reproduce the comparison table: for each combo tag, for each of the 6 traits, take `results.json[combo_tag][trait]["cosine"]["layers"][str(best_layer)]` (where `best_layer = results.json[combo_tag][trait]["cosine"]["best_layer"]`) and average `r_squared` and `normalized_mse` across the 6 traits. Report as columns **Response Activation**, **Avg. Norm. MSE**, **Avg. R²** (no best-layer column, no slope), sorted by Avg. Norm. MSE ascending. As of the last check: User Prompt Final (0.199 MSE) < Response Mean (0.215) < Conversation Mean (0.224) < Response Final (0.315).

**Judge models used** (all via API, not the local Llama model): `claude-sonnet-5` / `claude-haiku-4-5-20251001` generate trait descriptions, contrastive prompts, and level-labeled system prompts. `gpt-5-mini` judges trait expression 0-100 in `persona_vectors.py` (filtering) and `relabel_responses.py` (scoring). `gpt-4.1-mini` judges persona embodiment in `chat/turn_effects.py`.

**Modal endpoints** (`modal/`) redeploy the local-model inference logic (chat generation, persona scoring) as authenticated (`X-API-Key` header) FastAPI endpoints on an A100 GPU, for use by `interface/` (the participant-facing web UI in the parent repo) rather than for offline batch scripts.
