"""
For each conversation in a combined example_convos_comparison.json (as produced by
compare_example_convo.py), and for each of the six persona traits, plot how that trait's
persona-vector score differs across activation-extraction methods turn-by-turn: response_final,
user_final, conversation_mean, response_mean, each computed with the full conversation so far
as context. (compare_example_convo.py's no-context variants are currently disabled via
COMPUTE_NO_CONTEXT, so ACTIVATION_SERIES below only plots context lines for now -- add back
the f"{type}_no_context" entries there, with has_context=False, once re-enabled.)

One PNG per (conversation, trait) pair, with one line per activation type.
"""
import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt

VECTORS_DIR = Path(__file__).parent / "../generation/persona_vectors"

# Validated categorical palette (dataviz skill, references/palette.md). Color identifies the
# activation-extraction family -- the palette caps at 8 fixed-order hues and a generated 9th
# is explicitly disallowed.
#
# All four families are plotted, so this uses slots 1-4 (blue/orange/aqua/yellow). Only
# slots 1-3 are validated all-pairs-safe; slot 4 (yellow, response_final) is adjacent-safe
# against its neighbors but not guaranteed distinct from every other slot at a glance --
# acceptable here since the legend and direct series identity (not hue alone) carry meaning.
ACTIVATION_COLORS = {
    "user_final": "#2a78d6",         # slot 1 - blue
    "response_mean": "#eb6834",      # slot 2 - orange
    "conversation_mean": "#1baf7a",  # slot 3 - aqua
    "response_final": "#eda100",     # slot 4 - yellow
}

# (activation_type key, family, has_context) in the fixed draw/legend order.
ACTIVATION_SERIES = (
    ("response_final", "response_final", True),
    ("user_final", "user_final", True),
    ("conversation_mean", "conversation_mean", True),
    ("response_mean", "response_mean", True),
)

GRIDLINE = "#e1e0d9"
AXIS = "#c3c2b7"
PRIMARY_TEXT = "#0b0b0b"
MODE_SHADE = "#52514e"  # secondary ink, used at low alpha for the mode_b background band


def mode_blocks(turns):
    """Collapse each turn's "mode" ("mode_a"/"mode_b") into contiguous (start_turn, end_turn,
    mode) runs, so the switch points can be drawn regardless of the exact switching cadence."""
    blocks = []
    start = turns[0]["turn"]
    current_mode = turns[0]["mode"]
    for t in turns[1:]:
        if t["mode"] != current_mode:
            blocks.append((start, t["turn"] - 1, current_mode))
            start, current_mode = t["turn"], t["mode"]
    blocks.append((start, turns[-1]["turn"], current_mode))
    return blocks


def parse_args():
    parser = argparse.ArgumentParser(
        description="Plot per-turn, per-trait persona scores across activation-extraction "
                    "methods for each conversation in a combined example_convos_comparison.json "
                    "(as produced by compare_example_convo.py)."
    )
    parser.add_argument("--input", type=str,
                         default=str(Path(__file__).parent / "example_convos_comparison.json"),
                         help="Path to the combined conversations JSON")
    parser.add_argument("--output-dir", type=str, default=str(Path(__file__).parent),
                         help="Directory to write the output PNGs to")
    return parser.parse_args()


def signed_score(trait_scores, positive_label, negative_label):
    return trait_scores[positive_label] - trait_scores[negative_label]


def plot_trait(label, convo, trait, trait_meta, output_dir):
    turns = convo["turns"]
    turn_nums = [t["turn"] for t in turns]
    positive_label, negative_label = trait_meta["positive"], trait_meta["negative"]

    plt.rcParams["font.sans-serif"] = ["Helvetica", "Arial", "DejaVu Sans"]
    plt.rcParams["font.family"] = "sans-serif"
    fig, ax = plt.subplots(figsize=(8, 7))

    # mode_b is the block trying to elicit the trait's positive pole, mode_a the negative pole
    # (matches the +positive_label/-negative_label convention on the y-axis).
    mode_text = {"mode_b": f"+{positive_label}", "mode_a": f"-{negative_label}"}

    blocks = mode_blocks(turns)
    for start, end, mode in blocks:
        if mode == "mode_b":
            ax.axvspan(start - 0.5, end + 0.5, color=MODE_SHADE, alpha=0.08, zorder=0, linewidth=0)
        ax.text(
            (start + end) / 2, 0.98, mode_text[mode], transform=ax.get_xaxis_transform(),
            ha="center", va="top", fontsize=7.5, color=PRIMARY_TEXT,
        )
    for start, end, _mode in blocks[:-1]:
        ax.axvline(x=end + 0.5, color=AXIS, linestyle=":", linewidth=1, alpha=0.8, zorder=0)

    for activation_type, family, has_context in ACTIVATION_SERIES:
        scores = [
            signed_score(t["persona_scores_by_activation_type"][activation_type][trait], positive_label, negative_label)
            for t in turns
        ]

        # Per-5-turn-window average, drawn as a flat segment at full opacity in the series'
        # own color, so it reads clearly against the faded per-turn line behind it.
        window_avgs = []
        for start, end, _mode in blocks:
            window_scores = [s for tn, s in zip(turn_nums, scores) if start <= tn <= end]
            window_avg = sum(window_scores) / len(window_scores)
            window_avgs.append(window_avg)
            ax.hlines(
                window_avg, start - 0.5, end + 0.5,
                colors=ACTIVATION_COLORS[family], alpha=1.0, linewidth=2.5,
                linestyles="solid" if has_context else "dashed", zorder=5,
            )

        # Mean jump between each pair of consecutive window averages (3 jumps across 4
        # windows), shown in the legend -- but a jump only counts (at its magnitude) if it
        # moves the "correct" way for the mode it's landing in (mode_b is the trait's + pole,
        # so a jump into mode_b should go up; a jump into mode_a should go down); a
        # wrong-direction jump contributes 0 rather than penalizing/inflating the mean with an
        # unsigned swing that doesn't reflect the persona shift actually taking hold.
        window_deltas = []
        for i in range(len(window_avgs) - 1):
            delta = window_avgs[i + 1] - window_avgs[i]
            expected_sign = 1 if blocks[i + 1][2] == "mode_b" else -1
            window_deltas.append(abs(delta) if delta * expected_sign > 0 else 0.0)
        mean_window_delta = sum(window_deltas) / len(window_deltas)

        ax.plot(
            turn_nums, scores,
            marker="o" if has_context else "x", linewidth=1.2 if has_context else 0.9,
            markersize=6 if has_context else 7, alpha=0.6,
            linestyle="-" if has_context else "--",
            color=ACTIVATION_COLORS[family],
            label=f"{family.replace('_', ' ')} — mean Δ={mean_window_delta:.3f}",
        )

    ax.axhline(y=0, color=AXIS, linestyle="--", linewidth=1, alpha=0.7)
    ax.set_xlabel("Turn", color=PRIMARY_TEXT)
    ax.set_ylabel(f"{trait.title()} Persona Score (Unscaled)", color=PRIMARY_TEXT)
    ax.set_xticks(turn_nums)
    ax.grid(True, color=GRIDLINE, linewidth=1, alpha=0.8)
    ax.set_axisbelow(True)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color(AXIS)

    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.09), ncol=1, fontsize=8, frameon=False)

    fig.tight_layout(rect=(0, 0.045, 1, 1))
    n = label.split("_")[-1]
    output_path = output_dir / f"example_{n}_{trait}_act_comparison.png"
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return output_path


# Which single trait plot to produce for each conversation label -- everything else is skipped.
SELECTED_TRAIT_BY_LABEL = {
    "prompt_1": "sycophantic",
    "prompt_2": "romantic",
    "prompt_3": "robotic",
}


def main():
    args = parse_args()
    with open(VECTORS_DIR / "traits.json") as f:
        traits = json.load(f)

    with open(args.input) as f:
        conversations = json.load(f)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for label, trait in SELECTED_TRAIT_BY_LABEL.items():
        convo = conversations[label]
        trait_meta = traits[trait]
        output_path = plot_trait(label, convo, trait, trait_meta, output_dir)
        print(f"Saved {output_path}")


if __name__ == "__main__":
    main()
