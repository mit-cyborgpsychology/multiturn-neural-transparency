"""
For each conversation in a combined example_convos.json (as produced by
generate_example_convo.py), and for each of the six persona traits, plot how that
trait's persona-vector score differs across activation-extraction methods turn-by-turn:
five computed with the full conversation so far as context (response_final, user_final,
full_mean, response_mean, user_mean), plus "no context" counterparts of four of those
(everything but full_mean) computed from an isolated forward pass over just that turn's
exchange alone.

One PNG per (conversation, trait) pair, with one line per activation type/context variant.
"""
import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt

VECTORS_DIR = Path(__file__).parent / "../generation/persona_vectors"

# Must match NO_CONTEXT_BASE_TYPES in generate_example_convo.py: these four have both a
# "with context" and a "no context" line; full_mean (below) only has "with context".
CONTEXT_COMPARABLE_TYPES = ("response_final", "user_final", "response_mean", "user_mean")

# Validated categorical palette (dataviz skill, references/palette.md). Color identifies the
# activation-extraction family; context vs no-context (9 lines total, since 4 of the 5
# families have both) is a secondary channel (solid+circle vs dashed+x), not a new hue -- the
# palette caps at 8 fixed-order hues and a generated 9th is explicitly disallowed.
#
# Slots 1-3 (blue/orange/aqua) are the only trio the palette validates as mutually
# all-pairs-safe (not just adjacent-safe) -- reserved for whichever three families are
# actually plotted (currently user_final/response_mean/user_mean, since response_final and
# full_mean are commented out of ACTIVATION_SERIES below) so the visible series contrast as
# much as the palette guarantees. The commented-out families sit on slots 4-5 so every family
# still gets a fixed, never-reused hue if they're switched back on.
ACTIVATION_COLORS = {
    "user_final": "#2a78d6",      # slot 1 - blue
    "response_mean": "#eb6834",   # slot 2 - orange
    "user_mean": "#000000",       # black (off-palette, per request)
    "response_final": "#eda100",  # slot 4 - yellow
    "full_mean": "#e87ba4",       # slot 5 - magenta
}

# (activation_type key, family, has_context) in the fixed draw/legend order.
ACTIVATION_SERIES = (
    # ("response_final", "response_final", True),
    # ("response_final_no_context", "response_final", False),
    ("user_final", "user_final", True),
    ("user_final_no_context", "user_final", False),
    # ("full_mean", "full_mean", True),
    ("response_mean", "response_mean", True),
    ("response_mean_no_context", "response_mean", False),
    ("user_mean", "user_mean", True),
    ("user_mean_no_context", "user_mean", False),
)

GRIDLINE = "#e1e0d9"
AXIS = "#c3c2b7"
MUTED_TEXT = "#898781"
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
                    "methods for each conversation in a combined example_convos.json (as "
                    "produced by generate_example_convo.py)."
    )
    parser.add_argument("--input", type=str, default=str(Path(__file__).parent / "example_convos.json"),
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
    fig, ax = plt.subplots(figsize=(10, 6))

    blocks = mode_blocks(turns)
    for start, end, mode in blocks:
        if mode == "mode_b":
            ax.axvspan(start - 0.5, end + 0.5, color=MODE_SHADE, alpha=0.08, zorder=0, linewidth=0)
        ax.text(
            (start + end) / 2, 0.98, mode, transform=ax.get_xaxis_transform(),
            ha="center", va="top", fontsize=7.5, color=MUTED_TEXT,
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

        # Total swing across the windows: sum of the absolute jump between each pair of
        # consecutive window averages (3 jumps across the 4 windows), shown in the legend.
        total_window_change = sum(
            abs(window_avgs[i + 1] - window_avgs[i]) for i in range(len(window_avgs) - 1)
        )

        context_label = "context" if has_context else "no context"
        line_alpha = 0.4 if family == "user_mean" else 0.6
        ax.plot(
            turn_nums, scores,
            marker="o" if has_context else "x", linewidth=1.2 if has_context else 0.9,
            markersize=6 if has_context else 7, alpha=line_alpha,
            linestyle="-" if has_context else "--",
            color=ACTIVATION_COLORS[family],
            label=f"{family.replace('_', ' ')} ({context_label}) — window Σ|Δ|={total_window_change:.3f}",
        )

    ax.axhline(y=0, color=AXIS, linestyle="--", linewidth=1, alpha=0.7)
    ax.set_xlabel("Turn", color=PRIMARY_TEXT)
    ax.set_ylabel(f"{trait} cosine similarity (+{positive_label} / -{negative_label})", color=PRIMARY_TEXT)
    ax.set_xticks(turn_nums)
    ax.grid(True, color=GRIDLINE, linewidth=1, alpha=0.8)
    ax.set_axisbelow(True)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color(AXIS)

    subtitle = convo["user_scenario"]["base"]
    if len(subtitle) > 140:
        subtitle = subtitle[:137] + "..."
    ax.set_title(subtitle, color=MUTED_TEXT, fontsize=8.5, loc="left", pad=12)
    fig.suptitle(f"{trait.title()} by activation type — {label}", color=PRIMARY_TEXT, fontsize=14,
                 fontweight="bold", x=0.02, ha="left", y=0.99)

    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1.0), fontsize=8, frameon=False)

    fig.tight_layout(rect=(0, 0, 1, 0.93))
    output_path = output_dir / f"{label}_{trait}_activation_types.png"
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return output_path


def main():
    args = parse_args()
    with open(VECTORS_DIR / "traits.json") as f:
        traits = json.load(f)

    with open(args.input) as f:
        conversations = json.load(f)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for label, convo in conversations.items():
        for trait, trait_meta in traits.items():
            output_path = plot_trait(label, convo, trait, trait_meta, output_dir)
            print(f"Saved {output_path}")


if __name__ == "__main__":
    main()
