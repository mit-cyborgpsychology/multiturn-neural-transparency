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

# Which response/persona-vector activation-type combos to evaluate: (response_activation_type,
# persona_vector_type). Comment a line out to skip that combo without deleting it.
COMBOS = [
    ("final", "final"),
    ("final", "mean"),
    # ("mean", "final"),
    ("mean", "mean"),
]

# Which scoring metrics to compute per activation/layer. Comment a line out to disable it.
#   cosine     - cosine similarity (angle only, magnitude-blind)
#   projection - scalar projection onto the persona vector direction (keeps magnitude)
METRICS = [
    # "cosine",
    "projection",
]


def load_json(filepath) -> dict:
    with open(filepath, "r") as f:
        return json.load(f)


class GraphEvaluator:
    def __init__(
        self,
        model_name="meta-llama/Llama-3.1-8B-Instruct",
        device=None,
        response_activation_type="final",
        persona_vector_type="final",
    ):
        """
        response_activation_type: whether the activation extracted from the
            model's (system prompt + question + response) context is the
            'final' response token or the 'mean' over response tokens.
        persona_vector_type: whether the stored persona vector loaded from
            disk is the '{trait}_final.pt' or '{trait}_mean.pt' file.
        """
        self.device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(model_name, dtype=torch.bfloat16).to(self.device)
        self.model.eval()
        self.num_layers = len(self.model.model.layers)
        self.response_activation_type = response_activation_type
        self.persona_vector_type = persona_vector_type

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

    def get_final_context_activation(self, system_prompt, question, response, activation_type=None):
        """Run the full (system, question, response) context through the model and
        return the residual stream activation at every layer, either the final
        response token or the mean over all response tokens."""
        activation_type = activation_type or self.response_activation_type

        prompt_messages = [
            {"role": "system", "content": f"You are an AI assistant. Keep responses concise and conversational. {system_prompt}"},
            {"role": "user", "content": question},
        ]
        prompt_only = self.tokenizer.apply_chat_template(
            prompt_messages, tokenize=False, add_generation_prompt=True
        )
        prompt_length = self.tokenizer(prompt_only, return_tensors="pt").input_ids.shape[1]

        full_messages = prompt_messages + [{"role": "assistant", "content": response}]
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
        response_activations = layer_activations[:, prompt_length:, :]

        if activation_type == "mean":
            return response_activations.mean(dim=1)
        elif activation_type == "final":
            return response_activations[:, -1, :]
        else:
            raise ValueError(f"Unknown activation_type: {activation_type!r}. Expected 'mean' or 'final'.")

    def collect_layer_scores(self, trait, metrics):
        responses_dict = load_json(f"responses/{trait}.json")
        persona_vector = torch.load(
            f"../generation/persona_vectors/{trait}_{self.persona_vector_type}.pt", weights_only=False
        ).float().to(self.device)

        layer_levels = {layer: [] for layer in range(self.num_layers)}
        layer_scores = {
            metric: {layer: [] for layer in range(self.num_layers)} for metric in metrics
        }

        for level_key, system_prompts in tqdm(responses_dict.items(), desc=trait, leave=False):
            level = int(level_key.rsplit("-", 1)[1])
            for entries in system_prompts.values():
                for entry in entries:
                    # Ground truth trait level: average the system prompt's intended level
                    # with the gpt-5-mini judge's score of the actual response (both on a
                    # 0-10-ish scale), when a judge score is available. Falls back to the
                    # intended level alone if the response hasn't been relabeled yet.
                    gpt_score = entry.get("gpt_score")
                    ground_truth_level = (level + gpt_score) / 2 if gpt_score is not None else level

                    activation = self.get_final_context_activation(
                        entry["system_prompt"], entry["user_message"], entry["response"]
                    )

                    for layer_idx in range(self.num_layers):
                        layer_levels[layer_idx].append(ground_truth_level)
                        for metric in metrics:
                            s = self.score(
                                metric, activation[layer_idx], persona_vector[layer_idx]
                            ).item()
                            layer_scores[metric][layer_idx].append(s)

        return layer_levels, layer_scores

    def fit_layer(self, levels, scores):
        x = np.array(levels)
        y = np.array(scores)
        slope, intercept, r_value, _p_value, _std_err = stats.linregress(x, y)
        r_squared = r_value ** 2
        mse = float(np.mean((y - (slope * x + intercept)) ** 2))
        return slope, intercept, r_squared, mse

    def level_variance_stats(self, levels, scores):
        """Mean within-level variance (noise at a fixed trait level) and mean
        difference between adjacent level means (signal from moving one level)."""
        levels = np.array(levels)
        scores = np.array(scores)

        within_level_variances = []
        level_means = []
        for level in np.unique(levels):
            level_scores = scores[levels == level]
            within_level_variances.append(np.var(level_scores))
            level_means.append(level_scores.mean())

        mean_within_level_variance = float(np.mean(within_level_variances))
        mean_adjacent_level_diff = float(np.mean(np.diff(level_means)))
        return mean_within_level_variance, mean_adjacent_level_diff

    def plot_trait(self, trait, metric, combo_tag, layer_results, layer_levels, layer_scores, results_dir, top_n=9):
        plt.rcParams["font.sans-serif"] = ["Helvetica", "Arial", "DejaVu Sans"]
        plt.rcParams["font.family"] = "sans-serif"

        ranked = sorted(layer_results.items(), key=lambda item: item[1]["r_squared"], reverse=True)[:top_n]

        n_cols = 3
        n_rows = -(-len(ranked) // n_cols)  # ceil division
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(4.5 * n_cols, 4.5 * n_rows))
        axes = np.atleast_1d(axes).flatten()

        for ax, (layer_key, result) in zip(axes, ranked):
            layer_idx = int(layer_key)
            x = np.array(layer_levels[layer_idx])
            y = np.array(layer_scores[layer_idx])

            ax.scatter(x, y, alpha=0.6, s=20, edgecolors="none", color="gray")
            x_fit = np.linspace(x.min(), x.max(), 100)
            y_fit = result["slope"] * x_fit + result["intercept"]
            ax.plot(x_fit, y_fit, "r--", linewidth=2)

            ax.set_title(
                f"Layer {layer_idx}\n"
                f"R² = {result['r_squared']:.3f}, MSE = {result['mse']:.2e}\n"
                f"Within-var = {result['mean_within_level_variance']:.2e}, "
                f"Adj-Δ = {result['mean_adjacent_level_diff']:.2e}",
                fontsize=10,
            )
            ax.set_xlabel("Trait Level", fontsize=10)
            ax.set_ylabel(f"Persona Score ({metric})", fontsize=10)

        for ax in axes[len(ranked):]:
            ax.axis("off")

        fig.suptitle(f"{trait.title()} [{combo_tag}, {metric}] – Top {top_n} Layers by R²", fontsize=18, fontweight="bold")
        fig.tight_layout(rect=(0, 0, 1, 0.96))

        output_path = results_dir / f"{combo_tag}_{trait}_{metric}.png"
        fig.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close(fig)

    def run(self, trait, results_dir, combo_tag, metrics):
        layer_levels, layer_scores = self.collect_layer_scores(trait, metrics)

        metric_results = {}
        for metric in metrics:
            layer_results = {}
            best_layer, best_r_squared = 0, -float("inf")
            for layer_idx in range(self.num_layers):
                slope, intercept, r_squared, mse = self.fit_layer(
                    layer_levels[layer_idx], layer_scores[metric][layer_idx]
                )
                mean_within_level_variance, mean_adjacent_level_diff = self.level_variance_stats(
                    layer_levels[layer_idx], layer_scores[metric][layer_idx]
                )
                layer_results[str(layer_idx)] = {
                    "slope": slope, "intercept": intercept, "r_squared": r_squared, "mse": mse,
                    "mean_within_level_variance": mean_within_level_variance,
                    "mean_adjacent_level_diff": mean_adjacent_level_diff,
                }
                if r_squared > best_r_squared:
                    best_layer, best_r_squared = layer_idx, r_squared

            self.plot_trait(
                trait, metric, combo_tag, layer_results, layer_levels, layer_scores[metric], results_dir
            )

            metric_results[metric] = {"best_layer": best_layer, "layers": layer_results}

        return metric_results


def main():
    login(token=os.environ.get("HF_TOKEN"))
    torch.manual_seed(42)

    persona_vectors_dir = Path("../generation/persona_vectors")
    traits = sorted(set(
        p.stem.rsplit("_", 2)[0]
        for p in persona_vectors_dir.glob("*.pt")
    ))
    traits = [
        t for t in traits
        if Path(f"system_prompts/{t}.json").exists() and Path(f"responses/{t}.json").exists()
    ]
    print("Traits found:", traits)

    results_dir = Path("results")
    os.makedirs(results_dir, exist_ok=True)

    # Load the model once and reuse it across every combo in COMBOS of:
    #   response_activation_type: "final" or "mean" activation extracted from the
    #       model's own (system prompt + question + response) context.
    #   persona_vector_type: "final" or "mean" stored persona vector file to load
    #       (../generation/persona_vectors/{trait}_{persona_vector_type}.pt).
    evaluator = GraphEvaluator()

    results_path = results_dir / "results.json"
    all_results = {}
    for response_activation_type, persona_vector_type in COMBOS:
        combo_tag = f"response-{response_activation_type}_persona-{persona_vector_type}"
        evaluator.response_activation_type = response_activation_type
        evaluator.persona_vector_type = persona_vector_type

        print(f"\n=== {combo_tag} ===")
        combo_results = all_results.setdefault(combo_tag, {})
        for trait in tqdm(traits, desc=combo_tag):
            metric_results = evaluator.run(trait, results_dir, combo_tag, METRICS)
            combo_results[trait] = metric_results

            for metric, result in metric_results.items():
                best = result["layers"][str(result["best_layer"])]
                print(
                    f"{trait} [{metric}]: best layer {result['best_layer']}, R²={best['r_squared']:.4f}, "
                    f"MSE={best['mse']:.4f}, "
                    f"mean within-level variance={best['mean_within_level_variance']:.4f}, "
                    f"mean adjacent-level Δ={best['mean_adjacent_level_diff']:.4f}"
                )

            with open(results_path, "w") as f:
                json.dump(all_results, f, indent=2)


if __name__ == "__main__":
    main()
