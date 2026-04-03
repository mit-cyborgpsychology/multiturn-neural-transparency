"""
Figure 7: UEQ Clarity-Novelty Tradeoff — Single-Turn vs Multi-Turn
Horizontal dumbbell chart of all 8 UEQ items + 3 subscales.
Groups: Pragmatic Quality (top), Hedonic Quality (middle), Subscales (bottom).
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from scipy import stats
from matplotlib.lines import Line2D

mpl.rcParams['font.family'] = 'Helvetica'
mpl.rcParams['font.sans-serif'] = ['Helvetica', 'Arial', 'DejaVu Sans']

df = pd.read_csv('data_participants.csv')
df_viz = df[df['condition_name'].isin(['single_turn', 'multi_turn'])].copy()

COLOR_SINGLE = '#5C6BC0'
COLOR_MULTI  = '#00897B'

# Compute subscales
pragmatic_cols = [
    'final_ueq_obstructive_supportive', 'final_ueq_complicated_easy',
    'final_ueq_inefficient_efficient', 'final_ueq_confusing_clear',
]
hedonic_cols = [
    'final_ueq_boring_exciting', 'final_ueq_not_interesting_interesting',
    'final_ueq_conventional_inventive', 'final_ueq_usual_leading_edge',
]
df_viz = df_viz.copy()
df_viz['ueq_pragmatic'] = df_viz[pragmatic_cols].mean(axis=1)
df_viz['ueq_hedonic']   = df_viz[hedonic_cols].mean(axis=1)
df_viz['ueq_overall']   = df_viz[pragmatic_cols + hedonic_cols].mean(axis=1)

# Items ordered top-to-bottom: pragmatic group, hedonic group, then subscale summary
item_groups = [
    # (col, display_label, group)
    ('final_ueq_obstructive_supportive',    'Supportive',      'pragmatic'),
    ('final_ueq_complicated_easy',          'Easy',            'pragmatic'),
    ('final_ueq_inefficient_efficient',     'Efficient',       'pragmatic'),
    ('final_ueq_confusing_clear',           'Clear',           'pragmatic'),
    ('final_ueq_boring_exciting',           'Exciting',        'hedonic'),
    ('final_ueq_not_interesting_interesting','Interesting',    'hedonic'),
    ('final_ueq_conventional_inventive',    'Inventive',       'hedonic'),
    ('final_ueq_usual_leading_edge',        'Leading Edge',    'hedonic'),
    ('ueq_pragmatic',                       'Pragmatic QA',    'subscale'),
    ('ueq_hedonic',                         'Hedonic QA',      'subscale'),
    ('ueq_overall',                         'Overall',         'subscale'),
]

n = len(item_groups)
# y positions: items top to bottom, with small gaps between groups
y_positions = []
y = n - 1
group_gaps = {'pragmatic': 0, 'hedonic': 0.6, 'subscale': 0.6}
prev_group = None
for col, label, group in item_groups:
    if prev_group is not None and group != prev_group:
        y -= group_gaps[group]
    y_positions.append(y)
    y -= 1
    prev_group = group

fig, ax = plt.subplots(figsize=(7.5, 5.5), dpi=150)

for (col, label, group), y in zip(item_groups, y_positions):
    single = df_viz[df_viz['condition_name'] == 'single_turn'][col].dropna()
    multi  = df_viz[df_viz['condition_name'] == 'multi_turn'][col].dropna()

    s_m, s_se = single.mean(), single.sem()
    m_m, m_se = multi.mean(), multi.sem()
    t_stat, p_val = stats.ttest_ind(multi, single)

    # connecting line
    lw = 2.5 if group == 'subscale' else 1.8
    ax.plot([s_m, m_m], [y, y], color='#BDBDBD', linewidth=lw, zorder=1)

    # dots
    ms = 10 if group == 'subscale' else 8
    ax.errorbar(s_m, y, xerr=1.96 * s_se, fmt='o', color=COLOR_SINGLE,
                markersize=ms, markeredgecolor='white', markeredgewidth=1.5,
                capsize=3, capthick=1.2, elinewidth=1.2, zorder=3)
    ax.errorbar(m_m, y, xerr=1.96 * m_se, fmt='s', color=COLOR_MULTI,
                markersize=ms, markeredgecolor='white', markeredgewidth=1.5,
                capsize=3, capthick=1.2, elinewidth=1.2, zorder=3)

    # significance marker
    if p_val < 0.001:   sig = '***'
    elif p_val < 0.01:  sig = '**'
    elif p_val < 0.05:  sig = '*'
    else:               sig = ''
    if sig:
        x_right = max(s_m + 1.96 * s_se, m_m + 1.96 * m_se) + 0.07
        ax.text(x_right, y, sig, va='center', ha='left',
                fontsize=11, fontweight='bold', color='#333333')

    # row label
    fw = 'bold' if group == 'subscale' else 'normal'
    ax.text(3.75, y, label, va='center', ha='right', fontsize=10, fontweight=fw)

# Group header lines
def add_bracket(ax, y_top, y_bottom, label, x_pos=-0.05):
    mid = (y_top + y_bottom) / 2
    ax.annotate('', xy=(x_pos, y_bottom - 0.3), xytext=(x_pos, y_top + 0.3),
                 xycoords=('axes fraction', 'data'),
                 textcoords=('axes fraction', 'data'),
                 arrowprops=dict(arrowstyle='-', color='#9E9E9E', lw=1.2))
    ax.text(x_pos - 0.01, mid, label, va='center', ha='right', fontsize=8.5,
            color='#757575', rotation=90, transform=ax.get_yaxis_transform())

# Group separator lines
pragmatic_ys = [y for (_, _, g), y in zip(item_groups, y_positions) if g == 'pragmatic']
hedonic_ys   = [y for (_, _, g), y in zip(item_groups, y_positions) if g == 'hedonic']
subscale_ys  = [y for (_, _, g), y in zip(item_groups, y_positions) if g == 'subscale']

sep1 = (min(pragmatic_ys) + max(hedonic_ys)) / 2
sep2 = (min(hedonic_ys) + max(subscale_ys)) / 2
ax.axhline(sep1, color='#E0E0E0', linewidth=1, linestyle='--', zorder=0)
ax.axhline(sep2, color='#E0E0E0', linewidth=1, linestyle='--', zorder=0)

# Midpoint reference line
ax.axvline(4.0, color='#BDBDBD', linewidth=1, linestyle=':', zorder=0)

ax.set_yticks([])
ax.set_xlim(3.8, 5.8)
ax.set_xlabel('Mean Rating (1–7)', fontsize=10)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_visible(False)
ax.tick_params(axis='both', labelsize=10)

legend_elements = [
    Line2D([0], [0], marker='o', color='w', markerfacecolor=COLOR_SINGLE,
           markersize=9, markeredgecolor='white', label='Single-Turn'),
    Line2D([0], [0], marker='s', color='w', markerfacecolor=COLOR_MULTI,
           markersize=9, markeredgecolor='white', label='Multi-Turn'),
]
ax.legend(handles=legend_elements, loc='lower right', fontsize=9, framealpha=0.9)

plt.tight_layout()
plt.savefig('plots_finalized/fig7_ueq_tradeoff.png', bbox_inches='tight', dpi=200)
plt.savefig('plots_finalized/fig7_ueq_tradeoff.pdf', bbox_inches='tight')
plt.close()
print('Saved fig7_ueq_tradeoff')
