"""
Figures 5, 6, 7 — Mean ± SE dot plots matching the style of fig4_c2_interaction.
Fig 5 : Pre vs Post per condition (3 panels: Predictability, Neg. Predictability, Trust)
Fig 6 : Single-Turn vs Multi-Turn per viz-engagement item (7 items on x-axis)
Fig 7 : Single-Turn vs Multi-Turn per UEQ item, 3 panels (Pragmatic, Hedonic, Subscales)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl

mpl.rcParams['font.family'] = 'Helvetica'
mpl.rcParams['font.sans-serif'] = ['Helvetica', 'Arial', 'DejaVu Sans']

CONDITIONS  = ['control', 'single_turn', 'multi_turn']
COND_LABELS = ['Control', 'Single-Turn', 'Multi-Turn']

# Pre/Post colors — two greys, easy to distinguish
COLOR_PRE   = '#9E9E9E'   # medium gray — open circle
COLOR_POST  = '#333333'   # dark charcoal — filled square

# Single/Multi colors (consistent with condition palette elsewhere)
COLOR_SINGLE = '#5C6BC0'  # indigo — open circle
COLOR_MULTI  = '#00897B'  # teal   — filled square

JITTER = 0.04   # horizontal separation between the two series within each group

MARKER_KW = dict(markersize=9, markeredgewidth=1.5,
                 capsize=5, capthick=1.5, elinewidth=1.5, zorder=4)


def tight_ylim(means_a, ses_a, means_b, ses_b, pad=0.25):
    """Return a (lo, hi) y-range tight around the data + SE, clipped to 1–7."""
    all_means = list(means_a) + list(means_b)
    all_ses   = list(ses_a)   + list(ses_b)
    lo = min(m - se for m, se in zip(all_means, all_ses))
    hi = max(m + se for m, se in zip(all_means, all_ses))
    return max(1.0, lo - pad), min(7.0, hi + pad)


# ============================================================
# Fig 5: Pre vs Post — dot + SE, conditions on x-axis
# ============================================================

df5 = pd.read_csv('data_participants.csv')

items5 = [
    ('pre_predictability',          'final_predictability_post',          'Predictability'),
    ('pre_negative_predictability', 'final_negative_predictability_post', 'Neg. Predictability'),
    ('pre_trust',                   'final_trust_post',                   'Trust'),
]

x5 = np.array([0, 0.5, 1.0])

# Pre-compute all means/SEs to get a global y-range
all5_data = {}
for pre_col, post_col, _ in items5:
    pre_means, pre_ses, post_means, post_ses = [], [], [], []
    for cond in CONDITIONS:
        sub = df5[df5['condition_name'] == cond]
        pre_means.append(sub[pre_col].dropna().mean());  pre_ses.append(sub[pre_col].dropna().sem())
        post_means.append(sub[post_col].dropna().mean()); post_ses.append(sub[post_col].dropna().sem())
    all5_data[(pre_col, post_col)] = (pre_means, pre_ses, post_means, post_ses)

all5_lo, all5_hi = tight_ylim(
    sum([d[0] for d in all5_data.values()], []),
    sum([d[1] for d in all5_data.values()], []),
    sum([d[2] for d in all5_data.values()], []),
    sum([d[3] for d in all5_data.values()], []),
)

fig5, axes5 = plt.subplots(1, 3, figsize=(10, 4.5), dpi=150, sharey=True)

for ax_idx, (pre_col, post_col, title) in enumerate(items5):
    ax = axes5[ax_idx]
    pre_means, pre_ses, post_means, post_ses = all5_data[(pre_col, post_col)]

    # dotted connecting lines per condition (transparent)
    for i, x_pos in enumerate(x5):
        ax.plot([x_pos - JITTER, x_pos + JITTER], [pre_means[i], post_means[i]],
                color='#757575', linewidth=1.6, linestyle=':', alpha=0.7, zorder=2)

    ax.errorbar(x5 - JITTER, pre_means, yerr=pre_ses,
                fmt='o', color=COLOR_PRE, markerfacecolor='white',
                label='Pre', **MARKER_KW)

    ax.errorbar(x5 + JITTER, post_means, yerr=post_ses,
                fmt='s', color=COLOR_POST, markeredgecolor='white',
                label='Post', **MARKER_KW)

    ax.set_xticks(x5)
    ax.set_xticklabels(COND_LABELS, fontsize=10)
    ax.set_xlim(-0.2, 1.2)
    ax.set_title(title, fontsize=11, fontweight='bold', pad=8)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.tick_params(axis='both', labelsize=10)

axes5[0].set_ylim(all5_lo, all5_hi)
axes5[0].set_ylabel('Mean Rating (1–7)', fontsize=10)

yticks5 = np.arange(np.ceil(all5_lo * 2) / 2, all5_hi + 0.01, 0.5)
axes5[0].set_yticks(yticks5)
axes5[0].set_yticklabels([f'{v:.1f}' for v in yticks5], fontsize=10)

plt.tight_layout()
plt.savefig('plots_finalized/fig5_pre_post_slope.png', bbox_inches='tight', dpi=200)
plt.close()
print('Saved fig5_pre_post_slope')


# ============================================================
# Fig 6: Viz Engagement — Single vs Multi per item
# ============================================================

df6 = pd.read_csv('data_participants.csv')
df6_viz = df6[df6['condition_name'].isin(['single_turn', 'multi_turn'])].copy()

items6 = [
    ('final_viz_frequency',     'Frequency'),
    ('final_viz_referenced',    'Referenced'),
    ('final_viz_helpfulness',   'Helpfulness'),
    ('final_viz_prediction',    'Prediction'),
    ('final_viz_confidence',    'Confidence'),
    ('final_viz_anticipation',  'Anticipation'),
    ('final_viz_comprehension', 'Comprehension'),
]

x6 = np.arange(len(items6))

s6_means, s6_ses, m6_means, m6_ses = [], [], [], []
for col, _ in items6:
    s = df6_viz[df6_viz['condition_name'] == 'single_turn'][col].dropna()
    m = df6_viz[df6_viz['condition_name'] == 'multi_turn'][col].dropna()
    s6_means.append(s.mean()); s6_ses.append(s.sem())
    m6_means.append(m.mean()); m6_ses.append(m.sem())

fig6, ax6 = plt.subplots(figsize=(8, 4.5), dpi=150)

ax6.errorbar(x6 - JITTER, s6_means, yerr=s6_ses,
             fmt='o', color=COLOR_SINGLE, markerfacecolor='white',
             label='Single-Turn', **MARKER_KW)

ax6.errorbar(x6 + JITTER, m6_means, yerr=m6_ses,
             fmt='s', color=COLOR_MULTI, markeredgecolor='white',
             label='Multi-Turn', **MARKER_KW)

ax6.set_xticks(x6)
ax6.set_xticklabels([lbl for _, lbl in items6], fontsize=10, rotation=30, ha='right')
ax6.set_xlim(-0.4, len(items6) - 0.6)
ax6.set_ylim(*tight_ylim(s6_means, s6_ses, m6_means, m6_ses))
ax6.set_ylabel('Mean Rating (1–7)', fontsize=10)
ax6.legend(fontsize=10, framealpha=0.9, loc='upper right')
ax6.spines['top'].set_visible(False)
ax6.spines['right'].set_visible(False)
ax6.tick_params(axis='both', labelsize=10)

plt.tight_layout()
plt.savefig('plots_finalized/fig6_viz_engagement_mean_se.png', bbox_inches='tight', dpi=200)
plt.close()
print('Saved fig6_viz_engagement_mean_se')


# ============================================================
# Fig 7: UEQ — Single vs Multi, 3 panels
# ============================================================

df7 = pd.read_csv('data_participants.csv')
df7_viz = df7[df7['condition_name'].isin(['single_turn', 'multi_turn'])].copy()

pragmatic_cols = [
    'final_ueq_obstructive_supportive', 'final_ueq_complicated_easy',
    'final_ueq_inefficient_efficient',  'final_ueq_confusing_clear',
]
hedonic_cols = [
    'final_ueq_boring_exciting', 'final_ueq_not_interesting_interesting',
    'final_ueq_conventional_inventive', 'final_ueq_usual_leading_edge',
]
df7_viz['ueq_pragmatic'] = df7_viz[pragmatic_cols].mean(axis=1)
df7_viz['ueq_hedonic']   = df7_viz[hedonic_cols].mean(axis=1)
df7_viz['ueq_overall']   = df7_viz[pragmatic_cols + hedonic_cols].mean(axis=1)

panels7 = [
    ('Pragmatic Quality', [
        ('final_ueq_obstructive_supportive', 'Supportive'),
        ('final_ueq_complicated_easy',       'Easy'),
        ('final_ueq_inefficient_efficient',  'Efficient'),
        ('final_ueq_confusing_clear',        'Clear'),
    ]),
    ('Hedonic Quality', [
        ('final_ueq_boring_exciting',             'Exciting'),
        ('final_ueq_not_interesting_interesting', 'Interesting'),
        ('final_ueq_conventional_inventive',      'Inventive'),
        ('final_ueq_usual_leading_edge',          'Leading Edge'),
    ]),
    ('Subscales', [
        ('ueq_pragmatic', 'Pragmatic'),
        ('ueq_hedonic',   'Hedonic'),
        ('ueq_overall',   'Overall'),
    ]),
]

fig7, axes7 = plt.subplots(1, 3, figsize=(13, 4.5), dpi=150,
                            gridspec_kw={'width_ratios': [4, 4, 3]})

for ax_idx, (panel_title, panel_items) in enumerate(panels7):
    ax = axes7[ax_idx]
    n  = len(panel_items)
    x7 = np.arange(n)

    s7_means, s7_ses, m7_means, m7_ses = [], [], [], []
    for col, _ in panel_items:
        s = df7_viz[df7_viz['condition_name'] == 'single_turn'][col].dropna()
        m = df7_viz[df7_viz['condition_name'] == 'multi_turn'][col].dropna()
        s7_means.append(s.mean()); s7_ses.append(s.sem())
        m7_means.append(m.mean()); m7_ses.append(m.sem())

    ax.errorbar(x7 - JITTER, s7_means, yerr=s7_ses,
                fmt='o', color=COLOR_SINGLE, markerfacecolor='white',
                label='Single-Turn' if ax_idx == 0 else '_nolegend_', **MARKER_KW)

    ax.errorbar(x7 + JITTER, m7_means, yerr=m7_ses,
                fmt='s', color=COLOR_MULTI, markeredgecolor='white',
                label='Multi-Turn' if ax_idx == 0 else '_nolegend_', **MARKER_KW)

    ax.set_xticks(x7)
    rotation = 30 if n >= 4 else 0
    ax.set_xticklabels([lbl for _, lbl in panel_items], fontsize=10,
                       rotation=rotation, ha='right' if rotation else 'center')
    ax.set_xlim(-0.4, n - 0.6)
    ax.set_ylim(*tight_ylim(s7_means, s7_ses, m7_means, m7_ses))
    ax.set_title(panel_title, fontsize=11, fontweight='bold', pad=8)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.tick_params(axis='both', labelsize=10)

axes7[0].set_ylabel('Mean Rating (1–7)', fontsize=10)
axes7[0].legend(fontsize=10, framealpha=0.9, loc='upper right')

plt.tight_layout()
plt.savefig('plots_finalized/fig7_ueq_mean_se.png', bbox_inches='tight', dpi=200)
plt.close()
print('Saved fig7_ueq_mean_se')
