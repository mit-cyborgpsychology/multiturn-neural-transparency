"""
Figure 4: C2 Interaction — MBE vs Average RMSE by Condition × Prompt Type
Boxplots with jittered dots. X-axis = conditions, colors = prompt type.
Blue = Assistant, Orange = Roleplay (consistent with fig2).
Shows multi-turn advantage concentrated in harder ROLEPLY prompt.
Interaction: F(2,240)=3.80, p=.024
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib as mpl

mpl.rcParams['font.family'] = 'Helvetica'
mpl.rcParams['font.sans-serif'] = ['Helvetica', 'Arial', 'DejaVu Sans']

# --- Load data ---
df = pd.read_csv('data_calibration_jasp.csv')

CONDITIONS = ['control', 'single_turn', 'multi_turn']
COND_LABELS = ['Control', 'Single-Turn', 'Multi-Turn']

# Consistent palette: blue = assistant, orange = roleplay (matches fig2)
COLOR_ASST = '#5C6BC0'
COLOR_ROLEPLY = '#E65100'

PROMPTS = [
    ('ASST', COLOR_ASST, 'Assistant prompt'),
    ('ROLEPLY', COLOR_ROLEPLY, 'Roleplay prompt'),
]

measure = 's2_mbe_avg_rmse'

# Layout: 3 condition groups on x-axis, 2 prompt boxes per group
group_positions = [0, 2.5, 5]
box_width = 0.55
offset = 0.38  # half-gap between the two boxes in a group

fig, ax = plt.subplots(figsize=(8, 5.5), dpi=150)
rng = np.random.default_rng(42)

for g_idx, (cond, c_label) in enumerate(zip(CONDITIONS, COND_LABELS)):
    g_pos = group_positions[g_idx]

    for p_idx, (pt, color, pt_label) in enumerate(PROMPTS):
        pos = g_pos + (-offset if p_idx == 0 else +offset)
        subset = df[(df['condition_name'] == cond) & (df['s2_prompt_type'] == pt)]
        vals = subset[measure].dropna().values

        bp = ax.boxplot(vals, positions=[pos], widths=box_width, vert=True,
                        patch_artist=True, showfliers=False,
                        boxprops=dict(facecolor=color, edgecolor=color,
                                      alpha=0.25, linewidth=1.2),
                        medianprops=dict(color=color, linewidth=2.5),
                        whiskerprops=dict(color=color, linewidth=1.2),
                        capprops=dict(color=color, linewidth=1.2))

        jitter = rng.normal(0, 0.06, size=len(vals))
        ax.scatter(pos + jitter, vals, alpha=0.4, s=16, color=color,
                   edgecolors='white', linewidths=0.3, zorder=3)

# --- X axis ---
ax.set_xticks(group_positions)
ax.set_xticklabels(COND_LABELS, fontsize=12)

# --- Y axis ---
ax.set_ylim(0.05, 1.35)
ax.set_ylabel('MBE vs Average RMSE\n(lower = better calibration)', fontsize=11)

# --- Legend ---
patches = [mpatches.Patch(color=c, alpha=0.5, label=l) for _, c, l in PROMPTS]
ax.legend(handles=patches, loc='upper right', fontsize=10, framealpha=0.9)

# --- Spines ---
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.tick_params(axis='both', labelsize=10)

plt.tight_layout()
plt.savefig('plots_finalized/fig4b_c2_boxplot.png',
            bbox_inches='tight', dpi=200)
plt.savefig('plots_finalized/fig4b_c2_boxplot.pdf',
            bbox_inches='tight')
plt.close()
print('Saved fig4')
