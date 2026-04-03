"""
Figure 6: Visualization Engagement — Single-Turn vs Multi-Turn
Horizontal dumbbell chart comparing Likert means on 7 viz items.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from scipy import stats

mpl.rcParams['font.family'] = 'Helvetica'
mpl.rcParams['font.sans-serif'] = ['Helvetica', 'Arial', 'DejaVu Sans']

df = pd.read_csv('data_participants.csv')
df_viz = df[df['condition_name'].isin(['single_turn', 'multi_turn'])].copy()

COLOR_SINGLE = '#5C6BC0'
COLOR_MULTI = '#00897B'

items = [
    ('final_viz_frequency', 'Frequency'),
    ('final_viz_referenced', 'Referenced'),
    ('final_viz_prediction', 'Prediction'),
    ('final_viz_helpfulness', 'Helpfulness'),
    ('final_viz_confidence', 'Confidence'),
    ('final_viz_anticipation', 'Anticipation'),
    ('final_viz_comprehension', 'Comprehension'),
]

fig, ax = plt.subplots(figsize=(7, 4.5), dpi=150)

y_positions = list(range(len(items) - 1, -1, -1))

for i, ((col, label), y) in enumerate(zip(items, y_positions)):
    single = df_viz[df_viz['condition_name'] == 'single_turn'][col].dropna()
    multi = df_viz[df_viz['condition_name'] == 'multi_turn'][col].dropna()

    s_m, s_se = single.mean(), single.sem()
    m_m, m_se = multi.mean(), multi.sem()

    t_stat, p_val = stats.ttest_ind(multi, single)

    # connecting line
    ax.plot([s_m, m_m], [y, y], color='#BDBDBD', linewidth=2, zorder=1)

    # single-turn dot
    ax.errorbar(s_m, y, xerr=1.96 * s_se, fmt='o', color=COLOR_SINGLE,
                markersize=9, markeredgecolor='white', markeredgewidth=1.5,
                capsize=4, capthick=1.2, elinewidth=1.2, zorder=3)

    # multi-turn dot
    ax.errorbar(m_m, y, xerr=1.96 * m_se, fmt='s', color=COLOR_MULTI,
                markersize=9, markeredgecolor='white', markeredgewidth=1.5,
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
        x_right = max(s_m + 1.96 * s_se, m_m + 1.96 * m_se)
        ax.text(x_right + 0.08, y, sig, va='center', ha='left',
                fontsize=12, fontweight='bold', color='#333333')

    # row label
    ax.text(2.8, y, label, va='center', ha='right', fontsize=10)

ax.set_yticks([])
ax.set_xlim(3.0, 5.8)
ax.set_xlabel('Mean Likert Rating (1–7)', fontsize=10)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_visible(False)
ax.tick_params(axis='both', labelsize=10)

# Legend
from matplotlib.lines import Line2D
legend_elements = [
    Line2D([0], [0], marker='o', color='w', markerfacecolor=COLOR_SINGLE,
           markersize=9, markeredgecolor='white', markeredgewidth=1.5, label='Single-Turn'),
    Line2D([0], [0], marker='s', color='w', markerfacecolor=COLOR_MULTI,
           markersize=9, markeredgecolor='white', markeredgewidth=1.5, label='Multi-Turn'),
]
ax.legend(handles=legend_elements, loc='lower right', fontsize=9, framealpha=0.9)

plt.tight_layout()
plt.savefig('plots_finalized/fig6_viz_engagement.png', bbox_inches='tight', dpi=200)
plt.savefig('plots_finalized/fig6_viz_engagement.pdf', bbox_inches='tight')
plt.close()
print('Saved fig6_viz_engagement')
