import json
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from tqdm import tqdm

from evaluate import GraphEvaluator, load_json

# Re-plots evaluate.py's cached per-layer scores (results/cache/), but with the persona
# score axis rescaled to [0, 1] instead of raw cosine/projection units, and a leaner title
# (R^2 and MSE only -- see plot_scaled below). Doesn't touch the model or recollect
# activations, so it only needs a prior evaluate.py run to have populated results/results.json
# and results/cache/.

RESULTS_DIR = Path("results")
SCALED_PLOTS_DIR = RESULTS_DIR / "scaled_plots"
SCALE_PATH = RESULTS_DIR / "scale.json"
# modal/persona_score_api.py reads scale.json from alongside the persona vector .pt files it
# loads at runtime (VECTORS_PATH, mounted from generation/persona_vectors/), not from
# evaluation/results/ -- so every run also writes a copy there to keep it wired up.
PERSONA_VECTORS_SCALE_PATH = Path("../generation/persona_vectors/scale.json")

# scale.json only records the one combo/metric actually used downstream (chat/turn_effects.py,
# modal/persona_score_api.py): the multiturn prompt_final activation against the mean-pooled
# persona vector, scored by cosine similarity.
SCALE_COMBO_TAG = "prompt_final_persona-mean_multiturn"
SCALE_METRIC = "cosine"


def normalize_to_unit_range(scores, center, lo, hi):
    """Two-sided scaling anchored at `center` (see fit_reference_points below): `center` itself
    maps to exactly 0, the portion at or above it is scaled independently by (hi - center) into
    [0, 1], and the portion below it is scaled independently by (center - lo) into [-1, 0].
    `lo`/`hi` are the *fit line's* predicted values at trait level 1 and 10 -- not this sample's
    own min/max -- so a single noisy outlier response can't stretch or compress the whole scale;
    a live score outside [lo, hi] just lands outside [-1, 1] (see persona_score_api.py's
    downstream clamp) instead of silently redefining the endpoints.

    Returns the scaled scores alongside the raw midpoint/lo/hi, since those three numbers are
    all that's needed to reproduce this scaling for a new raw score later (see
    persona_score_api.py's normalize_score)."""
    scores = np.array(scores, dtype=float)
    upper_span = hi - center
    lower_span = center - lo
    above = (scores - center) / upper_span if upper_span else np.zeros_like(scores)
    below = (scores - center) / lower_span if lower_span else np.zeros_like(scores)
    scaled = np.where(scores >= center, above, below)
    scale_stats = {"midpoint": float(center), "min": float(lo), "max": float(hi)}
    return scaled, scale_stats


def fit_reference_points(levels, raw_scores):
    """Fit raw_scores against levels, then return three points read off that fit line rather
    than off the noisy raw samples themselves: `center` at the midpoint of the observed level
    range (same quantity evaluate.py's plot_comparison draws as the green "fit value at
    level ..." reference line), and `lo`/`hi` at that same observed range's endpoints
    (levels.min()/levels.max(), not a fixed 1/10) -- whichever end of the fit is actually
    lower/higher, since a trait whose score decreases with level would otherwise have them
    backwards. Anchoring to the observed range keeps these endpoints interpolated within the
    fit's data support rather than extrapolated past it; since the fit is linear, `center`
    ends up exactly (lo + hi) / 2."""
    levels = np.array(levels)
    slope, intercept, _r_squared, _mse = fit_layer(levels, raw_scores)
    level_min, level_max = levels.min(), levels.max()
    mid_level = (level_min + level_max) / 2
    center = slope * mid_level + intercept
    endpoint_a = slope * level_min + intercept
    endpoint_b = slope * level_max + intercept
    lo, hi = min(endpoint_a, endpoint_b), max(endpoint_a, endpoint_b)
    return center, lo, hi


def fit_layer(levels, scores):
    x = np.array(levels)
    y = np.array(scores)
    slope, intercept, r_value, _p_value, _std_err = stats.linregress(x, y)
    r_squared = r_value ** 2
    mse = float(np.mean((y - (slope * x + intercept)) ** 2))
    return slope, intercept, r_squared, mse


def plot_all_traits_summary_scaled(metric, entries_by_trait, output_dir):
    """Same combined-figure style as GraphEvaluator.plot_all_traits_summary in evaluate.py:
    one subplot per trait (each trait's single best-R² combo), showing the full scaled-score
    scatter, the fitted regression line, and the fit line's value at the min/mid/max trait
    level overlaid as small red dots. Subplot titles show only the bold trait name, R², and
    normalized MSE; axis labels are shown only on the edge subplots."""
    plt.rcParams["font.sans-serif"] = ["Helvetica", "Arial", "DejaVu Sans"]
    plt.rcParams["font.family"] = "sans-serif"

    traits = sorted(entries_by_trait)
    n_cols = 3
    n_rows = -(-len(traits) // n_cols)  # ceil division
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(4.5 * n_cols + 4, 6 * n_rows))
    axes = np.atleast_1d(axes).flatten()

    for i, (ax, trait) in enumerate(zip(axes, traits)):
        entry = entries_by_trait[trait]
        x = np.array(entry["levels"])
        y = entry["scaled_scores"]

        ax.scatter(x, y, alpha=0.6, s=15, edgecolors="none", color="gray")
        x_fit = np.linspace(x.min(), x.max(), 100)
        y_fit = entry["slope"] * x_fit + entry["intercept"]
        ax.plot(x_fit, y_fit, "r--", linewidth=2)

        x_min, x_max = x.min(), x.max()
        x_mid = (x_min + x_max) / 2
        xs_summary = [x_min, x_mid, x_max]
        ys_summary = [entry["slope"] * xv + entry["intercept"] for xv in xs_summary]
        ax.scatter(
            xs_summary, ys_summary, color="red", s=20,
            edgecolors="none", zorder=5,
        )

        title_lines = [
            r"$\bf{" + trait.title() + "}$",
            f"R²: {entry['r_squared']:.3f}",
            f"normalized MSE: {entry['mse']:.3f}",
        ]
        ax.set_title("\n".join(title_lines), fontsize=19)
        if i >= len(traits) - n_cols:  # bottom row only
            ax.set_xlabel("Trait Level", fontsize=15)
        if i % n_cols == 0:  # left column only
            ax.set_ylabel("Behavioral Score (scaled -1 to 1)", fontsize=15)
        ax.tick_params(labelsize=15)

    for ax in axes[len(traits):]:
        ax.axis("off")

    fig.tight_layout()

    output_path = output_dir / "all_traits_evaluation_scaled.png"
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def main():
    results_path = RESULTS_DIR / "results.json"
    all_results = load_json(results_path)
    evaluator = GraphEvaluator(load_model=False)

    SCALED_PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    scale_data = {}
    entries_by_metric_by_trait = {}
    traits_present = sorted({trait for combo_results in all_results.values() for trait in combo_results})
    for trait in tqdm(traits_present, desc="scaling"):
        entries_by_metric = {}
        for combo_tag, combo_results in all_results.items():
            if trait not in combo_results:
                continue
            layer_levels, layer_scores = evaluator.load_scores_cache(trait, combo_tag, RESULTS_DIR)
            for metric, result in combo_results[trait].items():
                best_layer = result["best_layer"]
                levels = layer_levels[best_layer]
                raw_scores = layer_scores[metric][best_layer]
                center, lo, hi = fit_reference_points(levels, raw_scores)
                scaled_scores, scale_stats = normalize_to_unit_range(raw_scores, center, lo, hi)
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
                if combo_tag == SCALE_COMBO_TAG and metric == SCALE_METRIC:
                    scale_data[trait] = {"layer_idx": best_layer, **scale_stats}

        # Collapse each trait down to its single best (highest R²) combo, since the combined
        # all-traits plot doesn't distinguish response activation / persona vector type.
        for metric, entries in entries_by_metric.items():
            best_entry = max(entries, key=lambda e: e["r_squared"])
            entries_by_metric_by_trait.setdefault(metric, {})[trait] = best_entry

    for metric, entries_by_trait in entries_by_metric_by_trait.items():
        plot_all_traits_summary_scaled(metric, entries_by_trait, SCALED_PLOTS_DIR)

    with open(SCALE_PATH, "w") as f:
        json.dump(scale_data, f, indent=2)
    with open(PERSONA_VECTORS_SCALE_PATH, "w") as f:
        json.dump(scale_data, f, indent=2)

    print(f"Saved scaled plots to {SCALED_PLOTS_DIR}/")
    print(f"Saved scaling stats to {SCALE_PATH} and {PERSONA_VECTORS_SCALE_PATH}")


if __name__ == "__main__":
    main()
