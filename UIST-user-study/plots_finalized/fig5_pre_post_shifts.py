"""
Figure 5: Pre-to-Post Survey Shifts by Condition
Diverging bar chart showing within-condition mean shifts (final - pre)
with 95% CI error bars and significance markers for one-sample t-tests.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from scipy import stats

mpl.rcParams['font.family'] = 'Helvetica'
mpl.rcParams['font.sans-serif'] = ['Helvetica', 'Arial', 'DejaVu Sans']

df = pd.read_csv('data_participants.csv')

CONDITIONS = ['control', 'single_turn', 'multi_turn']
COND_LABELS = ['Control', 'Single-Turn', 'Multi-Turn']
COND_COLORS = ['#757575', '#5C6BC0', '#00897B']

items = [
    ('pre_predictability', 'final_predictability_post', 'Predictability'),
    ('pre_negative_predictability', 'final_negative_predictability_post', 'Neg. Predictability'),
    ('pre_trust', 'final_trust_post', 'Trust'),
]

fig, axes = plt.subplots(1, 3, figsize=(12, 4.5), dpi=150, sharey=True)

for ax_idx, (pre_col, post_col, label) in enumerate(items):
    ax = axes[ax_idx]
    df[f'_shift'] = df[post_col] - df[pre_col]

    for c_idx, (cond, c_label, color) in enumerate(zip(CONDITIONS, COND_LABELS, COND_COLORS)):
        subset = df[df['condition_name'] == cond]['_shift'].dropna()
        m = subset.mean()
        se = subset.sem()
        ci95 = 1.96 * se
        t_stat, p_val = stats.ttest_1samp(subset, 0)

        bar = ax.barh(c_idx, m, height=0.6, color=color, alpha=0.7,
                       edgecolor=color, linewidth=1.2, zorder=2)
        ax.errorbar(m, c_idx, xerr=ci95, fmt='none', color='#333333',
                    capsize=4, capthick=1.2, elinewidth=1.2, zorder=3)

        # significance marker
        if p_val < 0.001:
            sig = '***'
        elif p_val < 0.01:
            sig = '**'
        elif p_val < 0.05:
            sig = '*'
        else:
            sig = ''
        if sig:
            x_pos = m + ci95 + 0.03 if m >= 0 else m - ci95 - 0.03
            ha = 'left' if m >= 0 else 'right'
            ax.text(x_pos, c_idx, sig, va='center', ha=ha,
                    fontsize=12, fontweight='bold', color=color)

    ax.axvline(0, color='#BDBDBD', linewidth=1, linestyle='-', zorder=1)
    ax.set_yticks(range(len(CONDITIONS)))
    ax.set_yticklabels(COND_LABELS, fontsize=10)
    ax.set_title(label, fontsize=11, fontweight='bold', pad=10)
    ax.set_xlim(-1.2, 0.8)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.tick_params(axis='both', labelsize=10)

axes[1].set_xlabel('Mean Shift (Final - Pre)', fontsize=10)
df.drop(columns=['_shift'], inplace=True, errors='ignore')

plt.tight_layout()
plt.savefig('plots_finalized/fig5_pre_post_shifts.png', bbox_inches='tight', dpi=200)
plt.savefig('plots_finalized/fig5_pre_post_shifts.pdf', bbox_inches='tight')
plt.close()
print('Saved fig5_pre_post_shifts')
