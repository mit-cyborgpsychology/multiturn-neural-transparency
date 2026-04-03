"""
Figure 4: C2 Interaction Plot — MBE vs Average RMSE by Condition × Prompt Type
Line interaction plot with dots + SE bars.
Blue = Assistant, Orange = Roleplay (consistent with fig2).
Shows multi-turn advantage concentrated in harder ROLEPLY prompt.
Interaction: F(2,240)=3.80, p=.024
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
x_positions = np.array([0, 0.5, 1])

# Consistent palette: blue = assistant, orange = roleplay (matches fig2)
COLOR_ASST = '#5C6BC0'
COLOR_ROLEPLY = '#E65100'

measure = 's2_mbe_avg_rmse'

fig, ax = plt.subplots(figsize=(4, 5), dpi=150)

# --- Compute cell means and SEs ---
cell_data = {}
for pt in ['ASST', 'ROLEPLY']:
    cell_data[pt] = {'means': [], 'ses': []}
    for cond in CONDITIONS:
        subset = df[(df['condition_name'] == cond) & (df['s2_prompt_type'] == pt)]
        cell_data[pt]['means'].append(subset[measure].mean())
        cell_data[pt]['ses'].append(subset[measure].sem())
    cell_data[pt]['means'] = np.array(cell_data[pt]['means'])
    cell_data[pt]['ses'] = np.array(cell_data[pt]['ses'])

# --- Dots with SE bars (jittered horizontally to separate prompts) ---
jitter_offset = 0.04  # horizontal nudge

ax.errorbar(x_positions - jitter_offset, cell_data['ASST']['means'],
            yerr=cell_data['ASST']['ses'],
            fmt='o', color=COLOR_ASST, markersize=9,
            markeredgecolor='white', markeredgewidth=1.5,
            capsize=5, capthick=1.5, elinewidth=1.5,
            label='Assistant prompt', zorder=4)

ax.errorbar(x_positions + jitter_offset, cell_data['ROLEPLY']['means'],
            yerr=cell_data['ROLEPLY']['ses'],
            fmt='s', color=COLOR_ROLEPLY, markersize=10,
            markeredgecolor='white', markeredgewidth=1.5,
            capsize=5, capthick=1.5, elinewidth=1.5,
            label='Roleplay prompt', zorder=4)

# --- Axes ---
ax.set_xticks(x_positions)
ax.set_xticklabels(COND_LABELS, fontsize=11)
ax.set_ylabel('MBE vs Average RMSE\n(lower = better calibration)', fontsize=11)
ax.set_xlim(-0.15, 1.15)
ax.set_ylim(0.44, 0.80)

ax.legend(fontsize=10, framealpha=0.9, loc='upper right')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.tick_params(axis='both', labelsize=10)

plt.tight_layout()
plt.savefig('plots_finalized/fig4_c2_interaction.png',
            bbox_inches='tight', dpi=200)
plt.savefig('plots_finalized/fig4_c2_interaction.pdf',
            bbox_inches='tight')
plt.close()
print('Saved fig4')
