"""
Figure 4b: S1 → S2 Trajectories by Prompt Type × Condition
Two panels (Assistant, Roleplay) showing session-to-session change.
Highlights that control ROLEPLY gets *worse* while multi-turn improves.
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
COND_COLORS = ['#757575', '#5C6BC0', '#00897B']  # gray, indigo, teal (match fig3a)

measure = 'mbe_avg_rmse'
panels = [
    ('ASST', 'Assistant Prompt'),
    ('ROLEPLY', 'Roleplay Prompt'),
]

fig, axes = plt.subplots(1, 2, figsize=(10, 4.5), dpi=150, sharey=True)

for ax_idx, (pt, title) in enumerate(panels):
    ax = axes[ax_idx]

    for c_idx, (cond, label, color) in enumerate(zip(CONDITIONS, COND_LABELS, COND_COLORS)):
        subset = df[(df['condition_name'] == cond) & (df['s2_prompt_type'] == pt)]
        s1_mean = subset[f's1_{measure}'].mean()
        s2_mean = subset[f's2_{measure}'].mean()
        s1_se = subset[f's1_{measure}'].sem()
        s2_se = subset[f's2_{measure}'].sem()

        # Small vertical offset to prevent overlap
        y_off = (c_idx - 1) * 0.008

        # Slope line
        ax.plot([0, 1], [s1_mean + y_off, s2_mean + y_off],
                color=color, linewidth=2.5, alpha=0.8, zorder=2)

        # S1 — open circle (baseline, no viz for anyone)
        ax.errorbar(0, s1_mean + y_off, yerr=s1_se,
                     fmt='o', color=color, markersize=9,
                     markerfacecolor='white', markeredgewidth=2.2,
                     capsize=4, capthick=1.5, elinewidth=1.5, zorder=3)

        # S2 — filled circle (intervention applied)
        ax.errorbar(1, s2_mean + y_off, yerr=s2_se,
                     fmt='o', color=color, markersize=9,
                     markerfacecolor=color, markeredgewidth=2.2,
                     capsize=4, capthick=1.5, elinewidth=1.5, zorder=3,
                     label=label)

    ax.set_xticks([0, 1])
    ax.set_xticklabels(['Session 1\n(no visualization)', 'Session 2\n(intervention)'],
                        fontsize=10)
    ax.set_xlim(-0.25, 1.55)
    ax.set_title(title, fontsize=12, fontweight='bold', pad=10)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.tick_params(axis='both', labelsize=10)

axes[0].set_ylabel('MBE vs Average RMSE\n(lower = better calibration)', fontsize=11)
axes[0].set_ylim(0.42, 0.82)

# Legend on right panel
axes[1].legend(loc='upper right', fontsize=9, framealpha=0.9)

# --- Annotations for ROLEPLY panel ---
ax_rp = axes[1]

# Control goes UP (worse) — annotate
ctrl_s1 = df[(df['condition_name'] == 'control') & (df['s2_prompt_type'] == 'ROLEPLY')][f's1_{measure}'].mean()
ctrl_s2 = df[(df['condition_name'] == 'control') & (df['s2_prompt_type'] == 'ROLEPLY')][f's2_{measure}'].mean()
ax_rp.annotate(f'+{ctrl_s2 - ctrl_s1:.02f}',
               xy=(1.06, ctrl_s2), fontsize=8.5, color='#757575',
               va='center', fontstyle='italic')

# Multi-Turn goes DOWN (better) — annotate
mt_s1 = df[(df['condition_name'] == 'multi_turn') & (df['s2_prompt_type'] == 'ROLEPLY')][f's1_{measure}'].mean()
mt_s2 = df[(df['condition_name'] == 'multi_turn') & (df['s2_prompt_type'] == 'ROLEPLY')][f's2_{measure}'].mean()
ax_rp.annotate(f'{mt_s2 - mt_s1:+.02f}',
               xy=(1.06, mt_s2), fontsize=8.5, color='#00897B',
               va='center', fontweight='bold')

# Single-Turn
st_s1 = df[(df['condition_name'] == 'single_turn') & (df['s2_prompt_type'] == 'ROLEPLY')][f's1_{measure}'].mean()
st_s2 = df[(df['condition_name'] == 'single_turn') & (df['s2_prompt_type'] == 'ROLEPLY')][f's2_{measure}'].mean()
ax_rp.annotate(f'{st_s2 - st_s1:+.02f}',
               xy=(1.06, st_s2), fontsize=8.5, color='#5C6BC0',
               va='center')

plt.tight_layout()
plt.savefig('plots_finalized/fig4b_s1s2_by_prompt.png',
            bbox_inches='tight', dpi=200)
plt.savefig('plots_finalized/fig4b_s1s2_by_prompt.pdf',
            bbox_inches='tight')
plt.show()
print('Saved fig4b')
