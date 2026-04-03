"""
Figure 5 (alt): Pre vs Post Survey Ratings by Condition
Grouped vertical bar chart: open bars = pre, filled bars = post.
3 panels for Predictability, Neg. Predictability, Trust.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from scipy import stats

mpl.rcParams['font.family'] = 'Helvetica'
mpl.rcParams['font.sans-serif'] = ['Helvetica', 'Arial', 'DejaVu Sans']

df = pd.read_csv('data_participants.csv')

CONDITIONS  = ['control', 'single_turn', 'multi_turn']
COND_LABELS = ['Control', 'Single-Turn', 'Multi-Turn']
COND_COLORS = ['#757575', '#5C6BC0', '#00897B']

items = [
    ('pre_predictability',          'final_predictability_post',          'Predictability'),
    ('pre_negative_predictability', 'final_negative_predictability_post', 'Neg. Predictability'),
    ('pre_trust',                   'final_trust_post',                   'Trust'),
]

bw     = 0.32          # single bar width
gap    = 0.08          # gap between pre/post pair
group  = bw * 2 + gap  # width of one condition group
space  = 0.28          # space between condition groups
x      = np.array([i * (group + space) for i in range(len(CONDITIONS))])

fig, axes = plt.subplots(1, 3, figsize=(11, 4.2), dpi=150, sharey=True)

for ax_idx, (pre_col, post_col, title) in enumerate(items):
    ax = axes[ax_idx]

    all_y = []
    for c_idx, (cond, color) in enumerate(zip(CONDITIONS, COND_COLORS)):
        sub = df[df['condition_name'] == cond]
        pre_vals  = sub[pre_col].dropna()
        post_vals = sub[post_col].dropna()

        pre_m,  pre_se  = pre_vals.mean(),  pre_vals.sem()
        post_m, post_se = post_vals.mean(), post_vals.sem()
        all_y += [pre_m, post_m]

        x_pre  = x[c_idx]
        x_post = x[c_idx] + bw + gap

        # pre bar — open (white fill, colored border)
        ax.bar(x_pre, pre_m, bw,
               facecolor='white', edgecolor=color, linewidth=1.6,
               zorder=2)
        ax.errorbar(x_pre, pre_m, yerr=1.96 * pre_se,
                    fmt='none', color='#BDBDBD',
                    capsize=0, elinewidth=1.4, solid_capstyle='round', zorder=3)

        # post bar — filled
        ax.bar(x_post, post_m, bw,
               facecolor=color, edgecolor='none', alpha=0.85,
               zorder=2)
        ax.errorbar(x_post, post_m, yerr=1.96 * post_se,
                    fmt='none', color='#BDBDBD',
                    capsize=0, elinewidth=1.4, solid_capstyle='round', zorder=3)

    # condition labels centred under each pair
    tick_x = x + (bw + gap) / 2
    ax.set_xticks(tick_x)
    ax.set_xticklabels(COND_LABELS, fontsize=10)
    ax.set_title(title, fontsize=11, fontweight='bold', pad=8)

    # y range tight to data
    pad = 0.25
    y_lo = max(1.0, np.floor((min(all_y) - pad) * 2) / 2)
    y_hi = min(7.0, np.ceil( (max(all_y) + pad) * 2) / 2)
    ax.set_ylim(y_lo, y_hi)
    ax.set_xlim(x[0] - bw, x[-1] + bw * 2 + gap + bw * 0.5)

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.tick_params(axis='both', labelsize=10)

axes[0].set_ylabel('Mean Rating (1–7)', fontsize=10)

plt.tight_layout()
plt.savefig('plots_finalized/fig5_pre_post_bars.png', bbox_inches='tight', dpi=200)
plt.savefig('plots_finalized/fig5_pre_post_bars.pdf', bbox_inches='tight')
plt.close()
print('Saved fig5_pre_post_bars')
