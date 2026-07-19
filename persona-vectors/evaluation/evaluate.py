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
# context onto each layer of a trait's persona vector, fits trait level vs. projected
# score per layer, and plots/reports R^2 and MSE for the best-fitting layer


def load_json(filepath) -> dict:
    with open(filepath, "r") as f:
        return json.load(f)


class GraphEvaluator:
    def __init__(self, model_name="meta-llama/Llama-3.1-8B-Instruct", device=None):
        self.device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(model_name, dtype=torch.bfloat16).to(self.device)
        self.model.eval()
        self.num_layers = len(self.model.model.layers)

    def vector_projection(self, a, b):
        dot_product = torch.dot(a, b)
        b_norm_squared = torch.dot(b, b)
        return dot_product / torch.sqrt(b_norm_squared)

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

    def get_final_context_activation(self, system_prompt, question, response):
        """Run the full (system, question, response) context through the model and
        return the final-token residual stream activation at every layer."""
        messages = [
            {"role": "system", "content": f"You are an AI assistant. {system_prompt}"},
            {"role": "user", "content": question},
            {"role": "assistant", "content": response},
        ]
        full_prompt = self.tokenizer.apply_chat_template(messages, tokenize=False)
        tokens = self.tokenizer(full_prompt, return_tensors="pt").input_ids.to(self.device)

        captured, hooks = self.get_residual_stream_hooks()
        with torch.no_grad():
            self.model(input_ids=tokens)
        for hook in hooks:
            hook.remove()

        # (num_layers, d_model) activation of the last token in the full context
        return torch.stack(
            [captured[i][0, -1, :].float() for i in range(self.num_layers)], dim=0
        )

    def collect_layer_scores(self, trait):
        system_prompts_dict = load_json(f"system_prompts/{trait}.json")
        responses_dict = load_json(f"responses/{trait}.json")
        persona_vector = torch.load(
            f"../generation/stored_persona_vectors/{trait}.pt", weights_only=False
        ).float().to(self.device)

        layer_levels = {layer: [] for layer in range(self.num_layers)}
        layer_scores = {layer: [] for layer in range(self.num_layers)}

        for level, rollouts in tqdm(system_prompts_dict.items(), desc=trait, leave=False):
            for rollout_idx, system_prompt in rollouts.items():
                question_responses = responses_dict.get(level, {}).get(rollout_idx, {})

                for question, responses in question_responses.items():
                    activation = self.get_final_context_activation(
                        system_prompt, question, responses[0]
                    )

                    for layer_idx in range(self.num_layers):
                        score = self.vector_projection(
                            activation[layer_idx], persona_vector[layer_idx]
                        ).item()
                        layer_levels[layer_idx].append(int(level))
                        layer_scores[layer_idx].append(score)

        return layer_levels, layer_scores

    def fit_layer(self, levels, scores):
        x = np.array(levels)
        y = np.array(scores)
        slope, intercept, r_value, _p_value, _std_err = stats.linregress(x, y)
        r_squared = r_value ** 2
        mse = float(np.mean((y - (slope * x + intercept)) ** 2))
        return slope, intercept, r_squared, mse

    def plot_trait(self, trait, layer_idx, levels, scores, slope, intercept, r_squared, mse, output_dir):
        x = np.array(levels)
        y = np.array(scores)

        fig = plt.figure(figsize=(10, 6))
        plt.rcParams["font.sans-serif"] = ["Helvetica", "Arial", "DejaVu Sans"]
        plt.rcParams["font.family"] = "sans-serif"

        plt.scatter(x, y, alpha=0.6, s=30, edgecolors="none", color="gray")

        x_fit = np.linspace(x.min(), x.max(), 100)
        y_fit = slope * x_fit + intercept
        plt.plot(
            x_fit, y_fit, "r--", linewidth=2.5,
            label=f"R² = {r_squared:.3f}, MSE = {mse:.4f}",
        )

        plt.xlabel("Trait Level", fontsize=16)
        plt.ylabel("Persona Score", fontsize=16)
        plt.title(f"{trait.title()} – Layer {layer_idx}", fontsize=18, fontweight="bold")
        plt.legend(loc="best", fontsize=14)
        plt.tight_layout()

        output_path = output_dir / f"{trait}.png"
        fig.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close(fig)

    def run(self, trait, output_dir):
        layer_levels, layer_scores = self.collect_layer_scores(trait)

        layer_results = {}
        best_layer, best_r_squared = 0, -float("inf")
        for layer_idx in range(self.num_layers):
            _slope, _intercept, r_squared, mse = self.fit_layer(
                layer_levels[layer_idx], layer_scores[layer_idx]
            )
            layer_results[str(layer_idx)] = {"r_squared": r_squared, "mse": mse}
            if r_squared > best_r_squared:
                best_layer, best_r_squared = layer_idx, r_squared

        slope, intercept, r_squared, mse = self.fit_layer(
            layer_levels[best_layer], layer_scores[best_layer]
        )
        self.plot_trait(
            trait, best_layer, layer_levels[best_layer], layer_scores[best_layer],
            slope, intercept, r_squared, mse, output_dir,
        )

        with open(f"results/{trait}_r_squared.json", "w") as f:
            json.dump({"best_layer": best_layer, "layers": layer_results}, f, indent=2)

        return best_layer, r_squared, mse


def main():
    login(token=os.environ.get("HF_TOKEN"))
    torch.manual_seed(42)

    persona_vectors_dir = Path("../generation/stored_persona_vectors")
    traits = sorted(set(
        p.stem.rsplit("_", 2)[0]
        for p in persona_vectors_dir.glob("*.pt")
    ))
    traits = [
        t for t in traits
        if Path(f"system_prompts/{t}.json").exists() and Path(f"responses/{t}.json").exists()
    ]
    print("Traits found:", traits)

    os.makedirs("results", exist_ok=True)
    output_dir = Path("results/plots")
    os.makedirs(output_dir, exist_ok=True)

    evaluator = GraphEvaluator()

    summary = {}
    for trait in tqdm(traits):
        best_layer, r_squared, mse = evaluator.run(trait, output_dir)
        summary[trait] = {"best_layer": best_layer, "r_squared": r_squared, "mse": mse}
        print(f"{trait}: best layer {best_layer}, R²={r_squared:.4f}, MSE={mse:.4f}")

    with open("results/summary.json", "w") as f:
        json.dump(summary, f, indent=2)


if __name__ == "__main__":
    main()
