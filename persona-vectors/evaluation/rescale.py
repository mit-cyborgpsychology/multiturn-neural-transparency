import json
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from tqdm import tqdm

from evaluate import GraphEvaluator, format_combo_label_lines, load_json

# Re-plots evaluate.py's cached per-layer scores (results/cache/), but with the persona
# score axis rescaled to [0, 1] instead of raw cosine/projection units, and a leaner title
# (R^2 and MSE only -- see plot_scaled below). Doesn't touch the model or recollect
# activations, so it only needs a prior evaluate.py run to have populated results/results.json
# and results/cache/.

RESULTS_DIR = Path("results")
SCALED_PLOTS_DIR = RESULTS_DIR / "scaled_plots"


def normalize_to_unit_range(scores):
    """Center the scores on their mean, then min-max scale so the lowest value maps to -1
    and the highest to 1. Centering first is a constant shift and doesn't change the final
    range, but keeps the two steps -- recenter on the mean, then scale to [-1, 1] -- explicit."""
    scores = np.array(scores, dtype=float)
    centered = scores - scores.mean()
    lo, hi = centered.min(), centered.max()
    if hi == lo:
        return np.zeros_like(centered)
    return 2 * (centered - lo) / (hi - lo) - 1


def fit_layer(levels, scores):
    x = np.array(levels)
    y = np.array(scores)
    slope, intercept, r_value, _p_value, _std_err = stats.linregress(x, y)
    r_squared = r_value ** 2
    mse = float(np.mean((y - (slope * x + intercept)) ** 2))
    return slope, intercept, r_squared, mse


def plot_scaled(trait, metric, entries, output_dir):
    """Like GraphEvaluator.plot_comparison, but the y-axis is the [0, 1]-normalized score
    (see normalize_to_unit_range) and the title only reports R^2 and MSE -- the
    within-level-variance / adjacent-level-delta stats are dropped."""
    plt.rcParams["font.sans-serif"] = ["Helvetica", "Arial", "DejaVu Sans"]
    plt.rcParams["font.family"] = "sans-serif"

    ranked = sorted(entries, key=lambda e: e["r_squared"], reverse=True)

    n_cols = 2
    n_rows = -(-len(ranked) // n_cols)  # ceil division
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(4.5 * n_cols, 5 * n_rows))
    axes = np.atleast_1d(axes).flatten()

    for ax, entry in zip(axes, ranked):
        x = np.array(entry["levels"])
        y = entry["scaled_scores"]

        ax.scatter(x, y, alpha=0.6, s=15, edgecolors="none", color="gray")
        x_fit = np.linspace(x.min(), x.max(), 100)
        y_fit = entry["slope"] * x_fit + entry["intercept"]
        ax.plot(x_fit, y_fit, "r--", linewidth=2)

        title_lines = format_combo_label_lines(entry["combo_tag"]) + [
            f"layer: {entry['layer_idx']}",
            f"R²: {entry['r_squared']:.3f}",
            f"normalized MSE: {entry['mse']:.2e}",
        ]
        ax.set_title("\n".join(title_lines), fontsize=10)
        ax.set_xlabel("Trait Level", fontsize=10)
        ax.set_ylabel(f"Persona Score ({metric}, scaled -1 to 1)", fontsize=10)

    for ax in axes[len(ranked):]:
        ax.axis("off")

    fig.suptitle(
        f"{trait.title()} — Best Layer per Method (metric: {metric}, scaled)",
        fontsize=18, fontweight="bold",
    )
    fig.tight_layout(rect=(0, 0, 1, 0.96))

    output_path = output_dir / f"comparison_{trait}_{metric}_scaled.png"
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def main():
    results_path = RESULTS_DIR / "results.json"
    all_results = load_json(results_path)
    evaluator = GraphEvaluator(load_model=False)

    SCALED_PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    traits_present = sorted({trait for combo_results in all_results.values() for trait in combo_results})
    for trait in tqdm(traits_present, desc="scaling+plotting"):
        entries_by_metric = {}
        for combo_tag, combo_results in all_results.items():
            if trait not in combo_results:
                continue
            layer_levels, layer_scores = evaluator.load_scores_cache(trait, combo_tag, RESULTS_DIR)
            for metric, result in combo_results[trait].items():
                best_layer = result["best_layer"]
                levels = layer_levels[best_layer]
                raw_scores = layer_scores[metric][best_layer]
                scaled_scores = normalize_to_unit_range(raw_scores)
                slope, intercept, r_squared, mse = fit_layer(levels, scaled_scores)
                entries_by_metric.setdefault(metric, []).append({
                    "combo_tag": combo_tag,
                    "layer_idx": best_layer,
                    "levels": levels,
                    "scaled_scores": scaled_scores,
                    "slope": slope,
                    "intercept": intercept,
                    "r_squared": r_squared,
                    "mse": mse,
                })

        for metric, entries in entries_by_metric.items():
            if entries:
                plot_scaled(trait, metric, entries, SCALED_PLOTS_DIR)

    print(f"Saved scaled plots to {SCALED_PLOTS_DIR}/")


if __name__ == "__main__":
    main()
