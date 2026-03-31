"""
Figure 3a: Slope/Dumbbell Chart — S1 → S2 Calibration by Condition
Shows baseline equivalence and post-intervention divergence.
Two panels: MBA vs Initial, MBE vs Average.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl

mpl.rcParams['font.family'] = 'Helvetica'
mpl.rcParams['font.sans-serif'] = ['Helvetica', 'Arial', 'DejaVu Sans']

# --- Load data ---
df = pd.read_csv('data_calibration_jasp.csv')

CONDITIONS = ['control', 'single_turn', 'multi_turn']
COND_LABELS = ['Control', 'Single-Turn', 'Multi-Turn']
COND_COLORS = ['#757575', '#5C6BC0', '#00897B']  # gray, indigo, teal

measures = [
    ('mba_initial_rmse', 'Anticipation\n(MBA vs Initial)'),
    ('mbe_avg_rmse', 'Evaluation\n(MBE vs Average)'),
]

fig, axes = plt.subplots(1, 2, figsize=(10, 4.5), dpi=150, sharey=True)

for ax_idx, (measure, title) in enumerate(measures):
    ax = axes[ax_idx]
    s1_col = f's1_{measure}'
    s2_col = f's2_{measure}'

    for c_idx, (cond, label, color) in enumerate(zip(CONDITIONS, COND_LABELS, COND_COLORS)):
        subset = df[df['condition_name'] == cond]
        s1_mean = subset[s1_col].mean()
        s2_mean = subset[s2_col].mean()
        s1_se = subset[s1_col].sem()
        s2_se = subset[s2_col].sem()

        # Offset y-position slightly so lines don't overlap
        y_offset = (c_idx - 1) * 0.03

        # Dumbbell line
        ax.plot([0, 1], [s1_mean + y_offset, s2_mean + y_offset],
                color=color, linewidth=2.5, alpha=0.8, zorder=2)

        # S1 dot (open circle = baseline)
        ax.errorbar(0, s1_mean + y_offset, yerr=s1_se,
                     fmt='o', color=color, markersize=9,
                     markerfacecolor='white', markeredgewidth=2.2,
                     capsize=4, capthick=1.5, elinewidth=1.5, zorder=3)

        # S2 dot (filled = experimental)
        ax.errorbar(1, s2_mean + y_offset, yerr=s2_se,
                     fmt='o', color=color, markersize=9,
                     markerfacecolor=color, markeredgewidth=2.2,
                     capsize=4, capthick=1.5, elinewidth=1.5, zorder=3,
                     label=label)

    ax.set_xticks([0, 1])
    ax.set_xticklabels(['Session 1\n(no visualization)', 'Session 2\n(intervention)'],
                        fontsize=10)
    ax.set_xlim(-0.25, 1.55)
    ax.set_title(title, fontsize=11, fontweight='bold', pad=10)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

axes[0].set_ylabel('RMSE (lower = better calibration)', fontsize=11)

# Legend on right panel
axes[1].legend(loc='upper right', fontsize=9, framealpha=0.9)

# Shared y limits
axes[0].set_ylim(0.38, 0.80)

# --- Significance brackets at S2 ---
# Tukey HSD results from ANALYSIS_RESULTS.md Section 3
# MBA vs Initial: Control vs Single p=.002**, Control vs Multi p=.008**
# MBE vs Average: Control vs Multi p=.003**, Single vs Multi p=.093 (ns)

def add_bracket(ax, x, y1, y2, p_text, bracket_x_offset=0.06):
    """Draw a significance bracket at x position between y1 and y2."""
    bx = x + bracket_x_offset
    ax.plot([bx, bx], [y1, y2], color='#424242', linewidth=1.2, zorder=4)
    ax.plot([bx - 0.02, bx], [y1, y1], color='#424242', linewidth=1.2, zorder=4)
    ax.plot([bx - 0.02, bx], [y2, y2], color='#424242', linewidth=1.2, zorder=4)
    mid_y = (y1 + y2) / 2
    ax.text(bx + 0.03, mid_y, p_text, fontsize=8, va='center', ha='left',
            color='#424242')

# Panel 0: MBA vs Initial — S2 means: Control=0.614, Single=0.507, Multi=0.519
# Need actual S2 means (computed from data, not hardcoded)
s2_means = {}
for ax_idx, (measure, title) in enumerate(measures):
    s2_col = f's2_{measure}'
    s2_means[ax_idx] = {}
    for cond in CONDITIONS:
        s2_means[ax_idx][cond] = df[df['condition_name'] == cond][s2_col].mean()

# MBA vs Initial brackets (panel 0)
ax0 = axes[0]
m0 = s2_means[0]
# Control vs Single (p=.002)
add_bracket(ax0, 1, m0['single_turn'], m0['control'], 'p = .002', 0.10)
# Control vs Multi (p=.008)
add_bracket(ax0, 1, m0['multi_turn'], m0['control'], 'p = .008', 0.28)

# MBE vs Average brackets (panel 1)
ax1 = axes[1]
m1 = s2_means[1]
# Control vs Multi (p=.003)
add_bracket(ax1, 1, m1['multi_turn'], m1['control'], 'p = .003', 0.08)

plt.tight_layout()
plt.savefig('plots_finalized/fig3a_slope_viz_vs_control.png',
            bbox_inches='tight', dpi=200)
plt.savefig('plots_finalized/fig3a_slope_viz_vs_control.pdf',
            bbox_inches='tight')
plt.show()
print('Saved fig3a')
