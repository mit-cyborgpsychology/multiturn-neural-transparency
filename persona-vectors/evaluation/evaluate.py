import argparse
import json
import os
from pathlib import Path

import numpy as np
import torch
from dotenv import load_dotenv
from huggingface_hub import login
from scipy import stats
import matplotlib.pyplot as plt
from tqdm import tqdm
from transformers import AutoModelForCausalLM, AutoTokenizer

load_dotenv()

# projects the final-token activation of the full (system prompt + question + response)
# context onto each layer of a trait's persona vector, fits trait level vs. score per
# layer, and plots/reports R^2 and MSE for the best-fitting layer.
#
# Two scoring metrics are computed per activation, per layer:
#   cosine     - cosine similarity between the activation and the persona vector.
#                Both vectors are unit-normalized, so this discards the activation's
#                magnitude and only reflects the angle between the two.
#   projection - scalar projection of the activation onto the persona vector's
#                direction (dot(a, b) / norm(b)). Only the persona vector is
#                normalized, so this keeps the activation's magnitude information.

ALL_METRICS = ("cosine", "projection")

# Which response/persona-vector activation-type combos to evaluate: 
# (response_activation_type, persona_vector_type). 
COMBOS = [
    # ("final", "final"),
    # ("final", "mean"),
    # ("mean", "final"),
    # ("mean", "mean"),
    ("prompt_final", "mean"),
    # ("conversation_mean", "mean"),
    # ("prompt_eot", "mean"),
]

# Which scoring metrics to compute per activation/layer. Comment a line out to disable it.
#   cosine     - cosine similarity (angle only, magnitude-blind)
#   projection - scalar projection onto the persona vector direction (keeps magnitude)
METRICS = [
    "cosine",
    # "projection",
]


def load_json(filepath) -> dict:
    with open(filepath, "r") as f:
        return json.load(f)


def build_combo_tag(response_activation_type, persona_vector_type, multiturn=False, posthoc_labels=False):
    """Filenames/cache-keys for a combo. Deliberately terse (used in paths), as opposed to
    format_combo_label_lines below, which is for human-readable display."""
    combo_tag = f"{response_activation_type}_persona-{persona_vector_type}"
    if multiturn:
        combo_tag += "_multiturn"
    if posthoc_labels:
        combo_tag += "_posthoclabels"
    return combo_tag


def parse_combo_tag(combo_tag):
    """Inverse of build_combo_tag. response_activation_type may itself contain underscores
    (e.g. 'prompt_final', 'conversation_mean'), so it's recovered by splitting on the unique
    '_persona-' delimiter rather than by position."""
    posthoc_labels = combo_tag.endswith("_posthoclabels")
    if posthoc_labels:
        combo_tag = combo_tag[: -len("_posthoclabels")]
    multiturn = combo_tag.endswith("_multiturn")
    if multiturn:
        combo_tag = combo_tag[: -len("_multiturn")]
    response_activation_type, _, persona_vector_type = combo_tag.partition("_persona-")
    return {
        "response_activation_type": response_activation_type,
        "persona_vector_type": persona_vector_type,
        "multiturn": multiturn,
        "posthoc_labels": posthoc_labels,
    }


def format_combo_label_lines(combo_tag):
    """Human-readable rendering of a combo_tag as a list of lines (one field per line), for
    plot titles."""
    parsed = parse_combo_tag(combo_tag)
    lines = [
        f"response activation: {parsed['response_activation_type']}",
        f"persona vector: {parsed['persona_vector_type']}",
    ]
    if parsed["posthoc_labels"]:
        lines.append("post-hoc labels only")
    return lines


class GraphEvaluator:
    def __init__(
        self,
        model_name="meta-llama/Llama-3.1-8B-Instruct",
        device=None,
        response_activation_type="final",
        persona_vector_type="final",
        persona_vectors_dir="../generation/persona_vectors",
        load_model=True,
        posthoc_labels_only=False,
    ):
        """
        response_activation_type: which activation to extract from the model's
            (system prompt + question + response) context: the 'final'
            response token, the 'mean' over response tokens, or
            'prompt_final' for the final token of the prompt itself (i.e.
            system prompt + question, before the response begins).
        persona_vector_type: whether the stored persona vector loaded from disk is
            the mean-pooled '{trait}.pt' file (current format) or the legacy
            final-token '{trait}_final.pt' file (see persona_vector_path()).
        persona_vectors_dir: directory the persona vector .pt files are loaded
            from (see persona_vector_path()). Defaults to the current pipeline's
            output dir, but e.g. generation/old_persona_vectors/ has the same
            per-layer-stacked-tensor format for an older trait set.
        load_model: if False, skip loading the (slow) LM entirely. Only usable
            for replotting from cached scores (see --plot), since nothing
            that needs the model will work in this mode.
        posthoc_labels_only: if True, use the gpt-5-mini judge's score alone as the
            ground truth trait level (see --posthoc-labels), instead of averaging
            it with the system prompt's intended level.
        """
        self.persona_vectors_dir = Path(persona_vectors_dir)
        self.device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")
        if load_model:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForCausalLM.from_pretrained(model_name, dtype=torch.bfloat16).to(self.device)
            self.model.eval()
            self.num_layers = len(self.model.model.layers)
        else:
            self.tokenizer = None
            self.model = None
            self.num_layers = None
        self.response_activation_type = response_activation_type
        self.persona_vector_type = persona_vector_type
        self.posthoc_labels_only = posthoc_labels_only

    def cosine_similarity(self, a, b):
        dot_product = torch.dot(a, b)
        return dot_product / (torch.norm(a) * torch.norm(b))

    def projection(self, a, b):
        """Scalar projection of a onto b's direction: dot(a, b) / norm(b).

        Unlike cosine similarity, this does not normalize a, so the result
        scales with the activation's own magnitude rather than only its angle
        to the persona vector.
        """
        return torch.dot(a, b) / torch.norm(b)

    def score(self, metric, a, b):
        if metric == "cosine":
            return self.cosine_similarity(a, b)
        elif metric == "projection":
            return self.projection(a, b)
        else:
            raise ValueError(f"Unknown metric: {metric!r}. Expected one of {ALL_METRICS}.")

    def get_residual_stream_hooks(self):
        """Register forward hooks on each layer's output to capture residual stream."""
        captured = {}
        hooks = []

        for layer_idx, layer in enumerate(self.model.model.layers):
            def make_hook(idx):
                def hook(module, input, output):
                    captured[idx] = output.detach()
                return hook
            hooks.append(layer.register_forward_hook(make_hook(layer_idx)))

        return captured, hooks

    def get_context_activation(self, system_prompt, turns, turn_index, activation_type=None):
        """Run the conversation up through turns[turn_index] (system prompt, plus every
        user/assistant turn up to and including that one) through the model and return the
        residual stream activation at every layer. `turns` is a list of
        {"user_message", "response"} dicts — length 1 for an ordinary single-turn response,
        length NUM_TURNS for a full multiturn conversation (see responses_multiturn/) — and
        `turn_index` selects which turn's response is being evaluated; any turns before it are
        included as prior conversation context.

        activation_type:
          'final'               - final token of the turn being evaluated's response
          'mean'                - mean over the response tokens of the turn being evaluated
          'prompt_final'        - final token of the prompt's chat-template preamble for the
                                   upcoming assistant turn (i.e. Llama's
                                   "<|start_header_id|>assistant<|end_header_id|>\n\n" tokens) —
                                   the position the model actually reads from to start
                                   generating. This is a few tokens past the end of the user's
                                   actual message text (see 'prompt_eot' / 'prompt_content_final'
                                   below for that).
          'prompt_eot'          - the '<|eot_id|>' token that ends the final user turn, right
                                   after the user's message content and before the
                                   assistant-turn preamble.
          'prompt_content_final'- the last actual content token of the user's message itself
                                   (one token before 'prompt_eot').
          'conversation_mean'   - mean over every token in the conversation so far, including
                                   prior turns (system prompt + all turns up to turn_index)

          All prompt-side variants ('prompt_final', 'prompt_eot', 'prompt_content_final') are
          sliced out of the same forward pass used for the response, rather than run
          separately — causal attention means the activation at any of these positions is
          identical either way.
        """
        activation_type = activation_type or self.response_activation_type

        system_message = {
            "role": "system",
            "content": f"You are an AI assistant. Keep responses concise and conversational. {system_prompt}",
        }
        prompt_messages = [system_message]
        for turn in turns[:turn_index]:
            prompt_messages.append({"role": "user", "content": turn["user_message"]})
            prompt_messages.append({"role": "assistant", "content": turn["response"]})
        current_turn = turns[turn_index]
        prompt_messages.append({"role": "user", "content": current_turn["user_message"]})

        prompt_only = self.tokenizer.apply_chat_template(
            prompt_messages, tokenize=False, add_generation_prompt=True
        )
        prompt_length = self.tokenizer(prompt_only, return_tensors="pt").input_ids.shape[1]

        full_messages = prompt_messages + [{"role": "assistant", "content": current_turn["response"]}]
        full_prompt = self.tokenizer.apply_chat_template(full_messages, tokenize=False)
        tokens = self.tokenizer(full_prompt, return_tensors="pt").input_ids.to(self.device)

        captured, hooks = self.get_residual_stream_hooks()
        with torch.no_grad():
            self.model(input_ids=tokens)
        for hook in hooks:
            hook.remove()

        # (num_layers, seq_len, d_model)
        layer_activations = torch.stack(
            [captured[i][0].float() for i in range(self.num_layers)], dim=0
        )

        if activation_type == "prompt_final":
            return layer_activations[:, prompt_length - 1, :]
        if activation_type in ("prompt_eot", "prompt_content_final"):
            # Re-tokenize the prompt without the assistant-turn preamble to find where the
            # user's turn itself ends: that string is a prefix of full_prompt, ending in
            # '<|eot_id|>' right after the user's message content.
            prompt_no_preamble = self.tokenizer.apply_chat_template(
                prompt_messages, tokenize=False, add_generation_prompt=False
            )
            prompt_no_preamble_length = self.tokenizer(
                prompt_no_preamble, return_tensors="pt"
            ).input_ids.shape[1]
            if activation_type == "prompt_eot":
                return layer_activations[:, prompt_no_preamble_length - 1, :]
            else:
                return layer_activations[:, prompt_no_preamble_length - 2, :]
        if activation_type == "conversation_mean":
            return layer_activations.mean(dim=1)

        response_activations = layer_activations[:, prompt_length:, :]
        if activation_type == "mean":
            return response_activations.mean(dim=1)
        elif activation_type == "final":
            return response_activations[:, -1, :]
        else:
            raise ValueError(
                f"Unknown activation_type: {activation_type!r}. Expected 'mean', 'final', "
                "'prompt_final', 'prompt_eot', 'prompt_content_final', or 'conversation_mean'."
            )

    def persona_vector_path(self, trait):
        """persona_vectors.py now only produces mean-pooled vectors, saved unsuffixed as
        '{trait}.pt'. 'final' vectors are a legacy format (see CLAUDE.md) still saved as
        '{trait}_final.pt' for traits generated before that change."""
        if self.persona_vector_type == "mean":
            return self.persona_vectors_dir / f"{trait}.pt"
        return self.persona_vectors_dir / f"{trait}_{self.persona_vector_type}.pt"

    def collect_layer_scores(self, trait, metrics):
        responses_dict = load_json(f"responses/{trait}.json")
        persona_vector = torch.load(
            self.persona_vector_path(trait), weights_only=False
        ).float().to(self.device)

        layer_levels = {layer: [] for layer in range(self.num_layers)}
        layer_scores = {
            metric: {layer: [] for layer in range(self.num_layers)} for metric in metrics
        }

        for level_key, system_prompts in tqdm(responses_dict.items(), desc=trait, leave=False):
            level = int(level_key.rsplit("-", 1)[1])
            for entries in system_prompts.values():
                for entry in entries:
                    # Ground truth trait level: either the gpt-5-mini judge's score of the
                    # actual response alone (posthoc_labels_only), or the average of that score
                    # with the system prompt's intended level (both on a 0-10-ish scale).
                    # Falls back to the intended level alone if the response hasn't been
                    # relabeled yet.
                    gpt_score = entry.get("gpt_score")
                    if gpt_score is None:
                        ground_truth_level = level
                    elif self.posthoc_labels_only:
                        ground_truth_level = gpt_score
                    else:
                        ground_truth_level = (level + gpt_score) / 2

                    activation = self.get_context_activation(
                        entry["system_prompt"],
                        [{"user_message": entry["user_message"], "response": entry["response"]}],
                        0,
                    )

                    for layer_idx in range(self.num_layers):
                        layer_levels[layer_idx].append(ground_truth_level)
                        for metric in metrics:
                            s = self.score(
                                metric, activation[layer_idx], persona_vector[layer_idx]
                            ).item()
                            layer_scores[metric][layer_idx].append(s)

        return layer_levels, layer_scores

    def collect_layer_scores_multiturn(self, trait, metrics):
        """Like collect_layer_scores, but reads responses_multiturn/{trait}.json and scores
        every turn of every conversation separately (context up to and including that turn is
        fed to the model per get_context_activation), so a single 3-turn conversation
        contributes 3 data points instead of 1."""
        responses_dict = load_json(f"responses_multiturn/{trait}.json")
        persona_vector = torch.load(
            self.persona_vector_path(trait), weights_only=False
        ).float().to(self.device)

        layer_levels = {layer: [] for layer in range(self.num_layers)}
        layer_scores = {
            metric: {layer: [] for layer in range(self.num_layers)} for metric in metrics
        }

        for level_key, system_prompts in tqdm(responses_dict.items(), desc=trait, leave=False):
            level = int(level_key.rsplit("-", 1)[1])
            for entries in system_prompts.values():
                for entry in entries:
                    turns = entry["turns"]
                    for turn_index, turn in enumerate(turns):
                        # Ground truth trait level for this turn: gpt_score, if the turn has
                        # been relabeled (see relabel_responses.py), is per-turn; falls back to
                        # the system prompt's intended level, same as single-turn.
                        gpt_score = turn.get("gpt_score")
                        if gpt_score is None:
                            ground_truth_level = level
                        elif self.posthoc_labels_only:
                            ground_truth_level = gpt_score
                        else:
                            ground_truth_level = (level + gpt_score) / 2

                        activation = self.get_context_activation(entry["system_prompt"], turns, turn_index)

                        for layer_idx in range(self.num_layers):
                            layer_levels[layer_idx].append(ground_truth_level)
                            for metric in metrics:
                                s = self.score(
                                    metric, activation[layer_idx], persona_vector[layer_idx]
                                ).item()
                                layer_scores[metric][layer_idx].append(s)

        return layer_levels, layer_scores

    def scores_cache_path(self, trait, combo_tag, results_dir):
        return Path(results_dir) / "cache" / f"{combo_tag}_{trait}.json"

    def save_scores_cache(self, trait, combo_tag, results_dir, layer_levels, layer_scores):
        cache_path = self.scores_cache_path(trait, combo_tag, results_dir)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_path, "w") as f:
            json.dump({"layer_levels": layer_levels, "layer_scores": layer_scores}, f)

    def load_scores_cache(self, trait, combo_tag, results_dir):
        cache_path = self.scores_cache_path(trait, combo_tag, results_dir)
        with open(cache_path, "r") as f:
            data = json.load(f)
        layer_levels = {int(k): v for k, v in data["layer_levels"].items()}
        layer_scores = {
            metric: {int(k): v for k, v in layers.items()}
            for metric, layers in data["layer_scores"].items()
        }
        return layer_levels, layer_scores

    def normalize_scores(self, scores):
        """Z-score normalize so MSE / within-var / adjacent-Δ are comparable
        across layers and metrics that otherwise live on very different scales
        (e.g. cosine in [-1, 1] vs. unbounded projection magnitudes)."""
        scores = np.array(scores, dtype=float)
        std = scores.std()
        if std == 0:
            return np.zeros_like(scores)
        return (scores - scores.mean()) / std

    def fit_layer(self, levels, scores):
        x = np.array(levels)
        y = np.array(scores)
        slope, intercept, r_value, _p_value, _std_err = stats.linregress(x, y)
        r_squared = r_value ** 2
        mse = float(np.mean((y - (slope * x + intercept)) ** 2))
        return slope, intercept, r_squared, mse

    def plot_comparison(self, trait, metric, entries, results_dir):
        """One figure for (trait, metric): one panel per method (combo_tag) tested, each
        showing that method's single best (highest R²) layer's scatter + fit line. Panels are
        labeled with format_combo_label_lines' readable, colon-separated description of the
        method (one field per line) rather than the raw underscore/dash combo_tag, plus the
        layer index and fit stats. `entries` is a list of
        {"combo_tag", "layer_idx", "result", "levels", "scores"} dicts, one per method."""
        plt.rcParams["font.sans-serif"] = ["Helvetica", "Arial", "DejaVu Sans"]
        plt.rcParams["font.family"] = "sans-serif"

        ranked = sorted(entries, key=lambda e: e["result"]["r_squared"], reverse=True)

        n_cols = 2
        n_rows = -(-len(ranked) // n_cols)  # ceil division
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(4.5 * n_cols, 6 * n_rows))
        axes = np.atleast_1d(axes).flatten()

        for ax, entry in zip(axes, ranked):
            result = entry["result"]
            x = np.array(entry["levels"])
            y = np.array(entry["scores"])

            ax.scatter(x, y, alpha=0.6, s=15, edgecolors="none", color="gray")
            x_fit = np.linspace(x.min(), x.max(), 100)
            y_fit = result["slope"] * x_fit + result["intercept"]
            ax.plot(x_fit, y_fit, "r--", linewidth=2)
            mid_level = (x.min() + x.max()) / 2
            mean_score = y.mean()
            fit_at_mid = result["slope"] * mid_level + result["intercept"]
            mean_fit_delta = mean_score - fit_at_mid
            ax.axhline(mean_score, color="blue", alpha=0.5, label="mean score")
            ax.axhline(
                fit_at_mid, color="green", alpha=0.5,
                label=f"fit value at level {mid_level:.2g}",
            )
            ax.legend(fontsize=8, loc="best")

            title_lines = format_combo_label_lines(entry["combo_tag"]) + [
                f"layer: {entry['layer_idx']}",
                f"R²: {result['r_squared']:.3f}",
                f"normalized MSE: {result['normalized_mse']:.4f}",
                f"mean − fit@mid Δ: {mean_fit_delta:.3f}",
            ]
            ax.set_title("\n".join(title_lines), fontsize=10)
            ax.set_xlabel("Trait Level", fontsize=10)
            ax.set_ylabel(f"Persona Score ({metric})", fontsize=10)

        for ax in axes[len(ranked):]:
            ax.axis("off")

        fig.suptitle(
            f"{trait.title()} — Best Layer per Method (metric: {metric})",
            fontsize=18, fontweight="bold",
        )
        fig.tight_layout(rect=(0, 0, 1, 0.96))

        plots_dir = Path(results_dir) / "evaluate_plots"
        plots_dir.mkdir(parents=True, exist_ok=True)
        output_path = plots_dir / f"comparison_{trait}_{metric}.png"
        fig.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close(fig)

    def plot_all_traits_summary(self, metric, entries_by_trait, results_dir):
        """One figure with one subplot per trait (same grid layout as plot_comparison), each
        contributing exactly one entry (its highest-R² combo, chosen by the caller): the full
        raw scatter of all data points, the fitted regression line, and the fit line's value
        at the min/mid/max trait level overlaid as larger dots. Each subplot's title shows
        only the trait name, R², and normalized MSE (combo details like response activation
        type / persona vector type are intentionally omitted)."""
        plt.rcParams["font.sans-serif"] = ["Helvetica", "Arial", "DejaVu Sans"]
        plt.rcParams["font.family"] = "sans-serif"

        traits = sorted(entries_by_trait)
        n_cols = 3
        n_rows = -(-len(traits) // n_cols)  # ceil division
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(4.5 * n_cols + 4, 6 * n_rows))
        axes = np.atleast_1d(axes).flatten()

        for i, (ax, trait) in enumerate(zip(axes, traits)):
            entry = entries_by_trait[trait]
            result = entry["result"]
            x = np.array(entry["levels"])
            y = np.array(entry["scores"])

            ax.scatter(x, y, alpha=0.6, s=15, edgecolors="none", color="gray")
            x_fit = np.linspace(x.min(), x.max(), 100)
            y_fit = result["slope"] * x_fit + result["intercept"]
            ax.plot(x_fit, y_fit, "r--", linewidth=2)

            x_min, x_max = x.min(), x.max()
            x_mid = (x_min + x_max) / 2
            xs_summary = [x_min, x_mid, x_max]
            ys_summary = [result["slope"] * xv + result["intercept"] for xv in xs_summary]
            ax.scatter(
                xs_summary, ys_summary, color="red", s=20,
                edgecolors="none", zorder=5,
            )

            title_lines = [
                r"$\bf{" + trait.title() + "}$",
                f"R²: {result['r_squared']:.3f}",
                f"normalized MSE: {result['normalized_mse']:.3f}",
            ]
            ax.set_title("\n".join(title_lines), fontsize=19)
            if i >= len(traits) - n_cols:  # bottom row only
                ax.set_xlabel("Trait Level", fontsize=15)
            if i % n_cols == 0:  # left column only
                ax.set_ylabel("Behavioral Score", fontsize=15)
            ax.tick_params(labelsize=15)

        for ax in axes[len(traits):]:
            ax.axis("off")

        fig.tight_layout()

        plots_dir = Path(results_dir) / "evaluate_plots"
        plots_dir.mkdir(parents=True, exist_ok=True)
        output_path = plots_dir / "all_traits_evaluation.png"
        fig.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close(fig)

    def collect_and_fit(self, trait, results_dir, combo_tag, metrics, multiturn=False):
        """Collect activations/scores for `trait` under this evaluator's currently-set
        response_activation_type/persona_vector_type, fit a per-layer regression against trait
        level, and cache both. Returns (metric_results, layer_levels, layer_scores) — plotting
        is the caller's responsibility, since a single figure now compares the best layer
        across several combos (see plot_comparison) rather than one figure per combo."""
        if multiturn:
            layer_levels, layer_scores = self.collect_layer_scores_multiturn(trait, metrics)
        else:
            layer_levels, layer_scores = self.collect_layer_scores(trait, metrics)
        self.save_scores_cache(trait, combo_tag, results_dir, layer_levels, layer_scores)

        metric_results = {}
        for metric in metrics:
            layer_results = {}
            best_layer, best_r_squared = 0, -float("inf")
            for layer_idx in range(self.num_layers):
                raw_scores = layer_scores[metric][layer_idx]
                normalized_scores = self.normalize_scores(raw_scores)

                # Fit on the raw (unnormalized) values: this is what gets plotted,
                # so the regression line and R^2 should match the scatter.
                slope, intercept, r_squared, _raw_mse = self.fit_layer(
                    layer_levels[layer_idx], raw_scores
                )
                # MSE is computed on normalized values so it's comparable across layers and
                # metrics with different scales.
                _, _, _, normalized_mse = self.fit_layer(layer_levels[layer_idx], normalized_scores)
                layer_results[str(layer_idx)] = {
                    "slope": slope, "intercept": intercept, "r_squared": r_squared,
                    "normalized_mse": normalized_mse,
                }
                if r_squared > best_r_squared:
                    best_layer, best_r_squared = layer_idx, r_squared

            metric_results[metric] = {"best_layer": best_layer, "layers": layer_results}

        return metric_results, layer_levels, layer_scores


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--plot", action="store_true",
        help="Skip loading the model and recollecting scores; just redraw plots "
             "from cached scores (results/cache/) and the existing results.json.",
    )
    parser.add_argument(
        "--posthoc-labels", action="store_true",
        help="Use the gpt-5-mini judge's score alone as the ground truth trait "
             "level, instead of averaging it with the system prompt's intended "
             "level.",
    )
    parser.add_argument(
        "--singleturn", action="store_true",
        help="Evaluate responses/{trait}.json instead of responses_multiturn/{trait}.json "
             "(the default). The default evaluates responses_multiturn/{trait}.json: every "
             "turn (1st, 2nd, 3rd) of every conversation is scored separately, with context "
             "up to and including that turn fed to the model, so each conversation "
             "contributes 3 data points instead of 1.",
    )
    parser.add_argument(
        "--persona-vectors-dir", default="../generation/persona_vectors",
        help="Directory to load persona vector .pt files from, and to discover the trait "
             "list from (every '*.pt' file's stem, minus its trailing '_final'/'_mean' "
             "suffix if present). Defaults to '../generation/persona_vectors' (the current "
             "pipeline's output). Point this at generation/old_persona_vectors/ (or another "
             "dir with the same per-layer-stacked-tensor format) to graph a different set of "
             "persona vectors.",
    )
    parser.add_argument(
        "--results-dir", default="results",
        help="Directory to write results.json, cached per-layer scores (cache/), and plots "
             "(evaluate_plots/) to -- and, under --plot, to read them back from. Defaults to "
             "'results'.",
    )
    args = parser.parse_args()
    multiturn = not args.singleturn

    results_dir = Path(args.results_dir)
    results_path = results_dir / "results.json"

    if args.plot:
        all_results = load_json(results_path)
        evaluator = GraphEvaluator(load_model=False, persona_vectors_dir=args.persona_vectors_dir)

        traits_present = sorted({trait for combo_results in all_results.values() for trait in combo_results})
        entries_by_metric_by_trait = {}
        for trait in tqdm(traits_present, desc="loading"):
            entries_by_metric = {}
            for combo_tag, combo_results in all_results.items():
                if trait not in combo_results:
                    continue
                layer_levels, layer_scores = evaluator.load_scores_cache(trait, combo_tag, results_dir)
                for metric, result in combo_results[trait].items():
                    best_layer = result["best_layer"]
                    entries_by_metric.setdefault(metric, []).append({
                        "combo_tag": combo_tag,
                        "layer_idx": best_layer,
                        "result": result["layers"][str(best_layer)],
                        "levels": layer_levels[best_layer],
                        "scores": layer_scores[metric][best_layer],
                    })
            # Collapse each trait down to its single best (highest R²) combo, since the
            # combined all-traits plot doesn't distinguish response activation / persona
            # vector type -- only R² is shown.
            for metric, entries in entries_by_metric.items():
                best_entry = max(entries, key=lambda e: e["result"]["r_squared"])
                entries_by_metric_by_trait.setdefault(metric, {})[trait] = best_entry

        for metric, entries_by_trait in entries_by_metric_by_trait.items():
            evaluator.plot_all_traits_summary(metric, entries_by_trait, results_dir)
        return

    login(token=os.environ.get("HF_TOKEN"))
    torch.manual_seed(42)

    persona_vectors_dir = Path(args.persona_vectors_dir)
    traits = sorted(set(
        p.stem.rsplit("_", 2)[0]
        for p in persona_vectors_dir.glob("*.pt")
    ))
    if multiturn:
        traits = [t for t in traits if Path(f"responses_multiturn/{t}.json").exists()]
    else:
        traits = [
            t for t in traits
            if Path(f"system_prompts/{t}.json").exists() and Path(f"responses/{t}.json").exists()
        ]
    print("Traits found:", traits)

    os.makedirs(results_dir, exist_ok=True)

    # Load the model once and reuse it across every combo in COMBOS of:
    #   response_activation_type: "final" or "mean" activation extracted from the
    #       model's own (system prompt + question + response) context.
    #   persona_vector_type: "final" or "mean" stored persona vector file to load
    #       (../generation/persona_vectors/{trait}_{persona_vector_type}.pt).
    evaluator = GraphEvaluator(posthoc_labels_only=args.posthoc_labels, persona_vectors_dir=persona_vectors_dir)

    all_results = {}
    for trait in traits:
        entries_by_metric = {metric: [] for metric in METRICS}

        for response_activation_type, persona_vector_type in tqdm(COMBOS, desc=trait):
            combo_tag = build_combo_tag(
                response_activation_type, persona_vector_type,
                multiturn=multiturn, posthoc_labels=args.posthoc_labels,
            )
            evaluator.response_activation_type = response_activation_type
            evaluator.persona_vector_type = persona_vector_type

            print(f"\n=== {trait} [{combo_tag}] ===")
            metric_results, layer_levels, layer_scores = evaluator.collect_and_fit(
                trait, results_dir, combo_tag, METRICS, multiturn=multiturn
            )
            all_results.setdefault(combo_tag, {})[trait] = metric_results

            for metric, result in metric_results.items():
                best_layer = result["best_layer"]
                best = result["layers"][str(best_layer)]
                print(
                    f"{trait} [{metric}]: best layer {best_layer}, R²={best['r_squared']:.4f}, "
                    f"normalized MSE={best['normalized_mse']:.4f}"
                )
                entries_by_metric[metric].append({
                    "combo_tag": combo_tag,
                    "layer_idx": best_layer,
                    "result": best,
                    "levels": layer_levels[best_layer],
                    "scores": layer_scores[metric][best_layer],
                })

            with open(results_path, "w") as f:
                json.dump(all_results, f, indent=2)

        for metric, entries in entries_by_metric.items():
            if entries:
                evaluator.plot_comparison(trait, metric, entries, results_dir)


if __name__ == "__main__":
    main()
