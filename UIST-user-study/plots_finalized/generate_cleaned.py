"""
Generate _cleaned versions of all finalized plots.
Strips: legends, text annotations, verbose axis labels, titles, direction labels.
Keeps: data points, error bars, axis ticks, spine styling.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib as mpl
from scipy import stats

mpl.rcParams['font.family'] = 'Helvetica'
mpl.rcParams['font.sans-serif'] = ['Helvetica', 'Arial', 'DejaVu Sans']

df_jasp = pd.read_csv('data_calibration_jasp.csv')
df_parts = pd.read_csv('data_participants.csv')
df_pv = pd.read_csv('data_persona_vectors.csv')

# ============================================================
# Fig 2: Baseline Miscalibration (boxplot + jitter)
# ============================================================

TRAITS = ['empathy', 'erudite', 'robotic', 'romantic', 'sycophantic', 'toxic']
TRAIT_POLES = {
    'empathy': ('empathy_empathetic', 'empathy_unempathetic'),
    'erudite': ('erudite_sophisticated', 'erudite_simplistic'),
    'robotic': ('robotic_robotic', 'robotic_human-like'),
    'romantic': ('romantic_romantic', 'romantic_platonic'),
    'sycophantic': ('sycophantic_sycophantic', 'sycophantic_honest'),
    'toxic': ('toxic_toxic', 'toxic_respectful'),
}
for trait, (pos, neg) in TRAIT_POLES.items():
    df_pv[f'net_{trait}'] = df_pv[pos] - df_pv[neg]
df_pv = df_pv.sort_values(['firebase_id', 'session', 'timestamp']).reset_index(drop=True)
df_pv['turn'] = df_pv.groupby(['firebase_id', 'session']).cumcount()
NET_TRAITS = [f'net_{t}' for t in TRAITS]
first_turns = df_pv[df_pv['turn'] == 0].set_index(['firebase_id', 'session'])
mean_activations = df_pv.groupby(['firebase_id', 'session'])[NET_TRAITS].mean()

rows = []
for _, p in df_parts.iterrows():
    fid = p['firebase_id']
    key = (fid, 1)
    pt = p['session1_prompt_type']
    if key not in first_turns.index or key not in mean_activations.index:
        continue
    mba_errs, mbe_errs = [], []
    for trait in TRAITS:
        mba = p[f's1_mba_{trait}'] / 10.0
        mbe = p[f's1_mbe_{trait}'] / 10.0
        initial = first_turns.loc[key, f'net_{trait}']
        avg = mean_activations.loc[key, f'net_{trait}']
        if not np.isnan(mba) and not np.isnan(initial):
            mba_errs.append((mba - initial) ** 2)
        if not np.isnan(mbe) and not np.isnan(avg):
            mbe_errs.append((mbe - avg) ** 2)
    if mba_errs and mbe_errs:
        rows.append({'prompt_type': pt,
                     'mba_rmse': np.sqrt(np.mean(mba_errs)),
                     'mbe_rmse': np.sqrt(np.mean(mbe_errs))})
df_rmse = pd.DataFrame(rows)

COLOR_ASST = '#5C6BC0'
COLOR_ROLEPLY = '#E65100'

fig, ax = plt.subplots(figsize=(7, 5.5), dpi=150)
rng = np.random.default_rng(42)
measures_f2 = ['mba_rmse', 'mbe_rmse']
group_positions = [0, 2.5]
box_width = 0.6
offset = 0.4

for g_idx, (measure, g_pos) in enumerate(zip(measures_f2, group_positions)):
    for p_idx, (pt, color) in enumerate([('ASST', COLOR_ASST), ('ROLEPLY', COLOR_ROLEPLY)]):
        pos_offset = -offset if p_idx == 0 else +offset
        vals = df_rmse[df_rmse['prompt_type'] == pt][measure].dropna().values
        pos = g_pos + pos_offset
        bp = ax.boxplot(vals, positions=[pos], widths=box_width, vert=True,
                        patch_artist=True, showfliers=False,
                        boxprops=dict(facecolor=color, edgecolor=color, alpha=0.25, linewidth=1.2),
                        medianprops=dict(color=color, linewidth=2.5),
                        whiskerprops=dict(color=color, linewidth=1.2),
                        capprops=dict(color=color, linewidth=1.2))
        jitter = rng.normal(0, 0.06, size=len(vals))
        ax.scatter(pos + jitter, vals, alpha=0.4, s=16, color=color,
                   edgecolors='white', linewidths=0.3, zorder=3)

ax.set_xticks(group_positions)
ax.set_xticklabels(['Anticipation', 'Evaluation'], fontsize=11)
ax.set_xlim(-1, 3.5)
ax.set_ylim(0, 1.3)
ax.set_ylabel('RMSE', fontsize=11)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
plt.tight_layout()
plt.savefig('plots_finalized/fig2_baseline_miscalibration_cleaned.png', bbox_inches='tight', dpi=200)
plt.savefig('plots_finalized/fig2_baseline_miscalibration_cleaned.pdf', bbox_inches='tight')
plt.close()
print('Saved fig2_cleaned')


# ============================================================
# Fig 3a: Slope/Dumbbell (S1 → S2)
# ============================================================

CONDITIONS = ['control', 'single_turn', 'multi_turn']
COND_LABELS = ['Control', 'Single-Turn', 'Multi-Turn']
COND_COLORS = ['#757575', '#5C6BC0', '#00897B']

measures_3a = [
    ('mba_initial_rmse', 'Anticipation'),
    ('mbe_avg_rmse', 'Evaluation'),
]

fig, axes = plt.subplots(1, 2, figsize=(10, 4.5), dpi=150, sharey=True)

for ax_idx, (measure, title) in enumerate(measures_3a):
    ax = axes[ax_idx]
    s1_col = f's1_{measure}'
    s2_col = f's2_{measure}'
    for c_idx, (cond, label, color) in enumerate(zip(CONDITIONS, COND_LABELS, COND_COLORS)):
        subset = df_jasp[df_jasp['condition_name'] == cond]
        s1_mean = subset[s1_col].mean()
        s2_mean = subset[s2_col].mean()
        s1_se = subset[s1_col].sem()
        s2_se = subset[s2_col].sem()
        y_offset = (c_idx - 1) * 0.03
        ax.plot([0, 1], [s1_mean + y_offset, s2_mean + y_offset],
                color=color, linewidth=2.5, alpha=0.8, zorder=2)
        ax.errorbar(0, s1_mean + y_offset, yerr=s1_se,
                     fmt='o', color=color, markersize=9,
                     markerfacecolor='white', markeredgewidth=2.2,
                     capsize=4, capthick=1.5, elinewidth=1.5, zorder=3)
        ax.errorbar(1, s2_mean + y_offset, yerr=s2_se,
                     fmt='o', color=color, markersize=9,
                     markerfacecolor=color, markeredgewidth=2.2,
                     capsize=4, capthick=1.5, elinewidth=1.5, zorder=3)

    ax.set_xticks([0, 1])
    ax.set_xticklabels(['Session 1', 'Session 2'], fontsize=10)
    ax.set_xlim(-0.25, 1.25)
    ax.set_title(title, fontsize=11, fontweight='bold', pad=10)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

axes[0].set_ylabel('RMSE', fontsize=11)
axes[0].set_ylim(0.38, 0.80)
plt.tight_layout()
plt.savefig('plots_finalized/fig3a_slope_viz_vs_control_cleaned.png', bbox_inches='tight', dpi=200)
plt.savefig('plots_finalized/fig3a_slope_viz_vs_control_cleaned.pdf', bbox_inches='tight')
plt.close()
print('Saved fig3a_cleaned')


# ============================================================
# Fig 3b: Forest Plot (C1 effects)
# ============================================================

measures_3b = [
    ('s2_mba_initial_rmse', 'MBA vs Initial'),
    ('s2_mbe_initial_rmse', 'MBE vs Initial'),
    ('s2_mbe_final_rmse', 'MBE vs Final'),
    ('s2_mbe_avg_rmse', 'MBE vs Average'),
    ('s2_sign_accuracy', 'Sign Accuracy'),
]

results = []
for col, label in measures_3b:
    control = df_jasp[df_jasp['condition_name'] == 'control'][col].dropna()
    viz = pd.concat([
        df_jasp[df_jasp['condition_name'] == 'single_turn'][col].dropna(),
        df_jasp[df_jasp['condition_name'] == 'multi_turn'][col].dropna(),
    ])
    pooled_std = np.sqrt(((len(control) - 1) * control.std()**2 +
                           (len(viz) - 1) * viz.std()**2) /
                          (len(control) + len(viz) - 2))
    d = (viz.mean() - control.mean()) / pooled_std
    n1, n2 = len(control), len(viz)
    se_d = np.sqrt(1/n1 + 1/n2 + d**2 / (2 * (n1 + n2)))
    t_stat, p_val = stats.ttest_ind(viz, control)
    results.append({'label': label, 'd': d, 'se': se_d,
                    'ci_lo': d - 1.96 * se_d, 'ci_hi': d + 1.96 * se_d, 'p': p_val})

fig, ax = plt.subplots(figsize=(6, 3.5), dpi=150)
y_positions = list(range(len(results) - 1, -1, -1))

for i, (r, y) in enumerate(zip(results, y_positions)):
    color = '#2E7D32' if r['p'] < 0.05 else '#9E9E9E'
    ax.plot([r['ci_lo'], r['ci_hi']], [y, y],
            color=color, linewidth=2.5, solid_capstyle='round', zorder=2)
    ax.plot(r['d'], y, 'o', color=color, markersize=10, zorder=3,
            markeredgecolor='white', markeredgewidth=1.5)
    ax.text(-1.05, y, f"{r['label']}", va='center', ha='right', fontsize=10)

ax.axvline(0, color='#BDBDBD', linewidth=1, linestyle='--', zorder=1)
ax.set_yticks([])
ax.set_xlabel("Cohen's d", fontsize=10)
ax.set_xlim(-1.0, 0.5)
ax.set_ylim(-0.8, len(results) - 0.5)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_visible(False)
plt.tight_layout()
plt.savefig('plots_finalized/fig3b_forest_c1_effects_cleaned.png', bbox_inches='tight', dpi=200)
plt.savefig('plots_finalized/fig3b_forest_c1_effects_cleaned.pdf', bbox_inches='tight')
plt.close()
print('Saved fig3b_cleaned')


# ============================================================
# Fig 4: C2 Interaction (dots + SE)
# ============================================================

x_positions = np.array([0, 0.5, 1])

fig, ax = plt.subplots(figsize=(4, 5), dpi=150)
cell_data = {}
for pt in ['ASST', 'ROLEPLY']:
    cell_data[pt] = {'means': [], 'ses': []}
    for cond in CONDITIONS:
        subset = df_jasp[(df_jasp['condition_name'] == cond) & (df_jasp['s2_prompt_type'] == pt)]
        cell_data[pt]['means'].append(subset['s2_mbe_avg_rmse'].mean())
        cell_data[pt]['ses'].append(subset['s2_mbe_avg_rmse'].sem())
    cell_data[pt]['means'] = np.array(cell_data[pt]['means'])
    cell_data[pt]['ses'] = np.array(cell_data[pt]['ses'])

jitter_offset = 0.04
ax.errorbar(x_positions - jitter_offset, cell_data['ASST']['means'],
            yerr=cell_data['ASST']['ses'],
            fmt='o', color=COLOR_ASST, markersize=9,
            markeredgecolor='white', markeredgewidth=1.5,
            capsize=5, capthick=1.5, elinewidth=1.5, zorder=4)
ax.errorbar(x_positions + jitter_offset, cell_data['ROLEPLY']['means'],
            yerr=cell_data['ROLEPLY']['ses'],
            fmt='s', color=COLOR_ROLEPLY, markersize=10,
            markeredgecolor='white', markeredgewidth=1.5,
            capsize=5, capthick=1.5, elinewidth=1.5, zorder=4)

ax.set_xticks(x_positions)
ax.set_xticklabels(COND_LABELS, fontsize=11)
ax.set_ylabel('RMSE', fontsize=11)
ax.set_xlim(-0.15, 1.15)
ax.set_ylim(0.44, 0.80)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.tick_params(axis='both', labelsize=10)
plt.tight_layout()
plt.savefig('plots_finalized/fig4_c2_interaction_cleaned.png', bbox_inches='tight', dpi=200)
plt.savefig('plots_finalized/fig4_c2_interaction_cleaned.pdf', bbox_inches='tight')
plt.close()
print('Saved fig4_cleaned')


# ============================================================
# Fig 4b: S1 → S2 by Prompt Type
# ============================================================

measure_4b = 'mbe_avg_rmse'
panels = [('ASST', 'Assistant'), ('ROLEPLY', 'Roleplay')]

fig, axes = plt.subplots(1, 2, figsize=(10, 4.5), dpi=150, sharey=True)

for ax_idx, (pt, title) in enumerate(panels):
    ax = axes[ax_idx]
    for c_idx, (cond, label, color) in enumerate(zip(CONDITIONS, COND_LABELS, COND_COLORS)):
        subset = df_jasp[(df_jasp['condition_name'] == cond) & (df_jasp['s2_prompt_type'] == pt)]
        s1_mean = subset[f's1_{measure_4b}'].mean()
        s2_mean = subset[f's2_{measure_4b}'].mean()
        s1_se = subset[f's1_{measure_4b}'].sem()
        s2_se = subset[f's2_{measure_4b}'].sem()
        y_off = (c_idx - 1) * 0.008
        ax.plot([0, 1], [s1_mean + y_off, s2_mean + y_off],
                color=color, linewidth=2.5, alpha=0.8, zorder=2)
        ax.errorbar(0, s1_mean + y_off, yerr=s1_se,
                     fmt='o', color=color, markersize=9,
                     markerfacecolor='white', markeredgewidth=2.2,
                     capsize=4, capthick=1.5, elinewidth=1.5, zorder=3)
        ax.errorbar(1, s2_mean + y_off, yerr=s2_se,
                     fmt='o', color=color, markersize=9,
                     markerfacecolor=color, markeredgewidth=2.2,
                     capsize=4, capthick=1.5, elinewidth=1.5, zorder=3)

    ax.set_xticks([0, 1])
    ax.set_xticklabels(['Session 1', 'Session 2'], fontsize=10)
    ax.set_xlim(-0.25, 1.25)
    ax.set_title(title, fontsize=12, fontweight='bold', pad=10)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.tick_params(axis='both', labelsize=10)

axes[0].set_ylabel('RMSE', fontsize=11)
axes[0].set_ylim(0.42, 0.82)
plt.tight_layout()
plt.savefig('plots_finalized/fig4b_s1s2_by_prompt_cleaned.png', bbox_inches='tight', dpi=200)
plt.savefig('plots_finalized/fig4b_s1s2_by_prompt_cleaned.pdf', bbox_inches='tight')
plt.close()
print('Saved fig4b_cleaned')


# ============================================================
# Fig 5: Pre-to-Post Shifts (cleaned)
# ============================================================

df5 = pd.read_csv('data_participants.csv')

items5 = [
    ('pre_predictability',          'final_predictability_post',          'Predictability'),
    ('pre_negative_predictability', 'final_negative_predictability_post', 'Neg. Predictability'),
    ('pre_trust',                   'final_trust_post',                   'Trust'),
]

fig, axes = plt.subplots(1, 3, figsize=(11, 3.2), dpi=150, sharey=True)

for ax_idx, (pre_col, post_col, _label) in enumerate(items5):
    ax = axes[ax_idx]
    df5['_shift'] = df5[post_col] - df5[pre_col]

    extremes = []
    row_data = []
    for cond, color in zip(CONDITIONS, COND_COLORS):
        subset = df5[df5['condition_name'] == cond]['_shift'].dropna()
        m = subset.mean()
        ci95 = 1.96 * subset.sem()
        _, p_val = stats.ttest_1samp(subset, 0)
        row_data.append((m, ci95, p_val, color))
        extremes.extend([m - ci95, m + ci95])

    for c_idx, (m, ci95, p_val, color) in enumerate(row_data):
        alpha    = 0.85 if p_val < 0.05 else 0.22
        bar_col  = color if p_val < 0.05 else '#9E9E9E'
        ax.barh(c_idx, m, height=0.35, color=bar_col, alpha=alpha,
                edgecolor='none', zorder=2)
        ax.errorbar(m, c_idx, xerr=ci95, fmt='none', color=bar_col,
                    capsize=0, elinewidth=1.8, solid_capstyle='round',
                    zorder=3, alpha=max(alpha, 0.5))

    ax.axvline(0, color='#BDBDBD', linewidth=1.0, zorder=1)

    pad  = 0.18
    x_lo = np.floor((min(extremes) - pad) * 2) / 2
    x_hi = np.ceil( (max(extremes) + pad) * 2) / 2
    ax.set_xlim(x_lo, x_hi)

    ax.set_yticks(range(3))
    if ax_idx == 0:
        ax.set_yticklabels(COND_LABELS, fontsize=10)
    else:
        ax.set_yticklabels([])

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.tick_params(axis='both', labelsize=10)

df5.drop(columns=['_shift'], inplace=True, errors='ignore')
plt.tight_layout()
plt.subplots_adjust(left=0.13)  # room for y-axis labels
plt.savefig('plots_finalized/fig5_pre_post_shifts_cleaned.png', bbox_inches='tight', dpi=200)
plt.savefig('plots_finalized/fig5_pre_post_shifts_cleaned.pdf', bbox_inches='tight')
plt.close()
print('Saved fig5_cleaned')


# ============================================================
# Fig 6: Viz Engagement (cleaned)
# ============================================================

df6 = pd.read_csv('data_participants.csv')
df6_viz = df6[df6['condition_name'].isin(['single_turn', 'multi_turn'])].copy()

COLOR_SINGLE = '#5C6BC0'
COLOR_MULTI  = '#00897B'

items6 = [
    ('final_viz_frequency',      'Frequency'),
    ('final_viz_referenced',     'Referenced'),
    ('final_viz_prediction',     'Prediction'),
    ('final_viz_helpfulness',    'Helpfulness'),
    ('final_viz_confidence',     'Confidence'),
    ('final_viz_anticipation',   'Anticipation'),
    ('final_viz_comprehension',  'Comprehension'),
]

# sort rows by Multi − Single mean difference, descending
rows6 = []
for col, lbl in items6:
    s = df6_viz[df6_viz['condition_name'] == 'single_turn'][col].dropna()
    m = df6_viz[df6_viz['condition_name'] == 'multi_turn'][col].dropna()
    _, p = stats.ttest_ind(m, s)
    rows6.append((col, lbl, m.mean() - s.mean(), p))
rows6.sort(key=lambda x: x[2], reverse=True)

# compute xlim from data extent
all_x6 = []
for col, lbl, diff, p in rows6:
    s = df6_viz[df6_viz['condition_name'] == 'single_turn'][col].dropna()
    m = df6_viz[df6_viz['condition_name'] == 'multi_turn'][col].dropna()
    all_x6 += [s.mean() - 1.96*s.sem(), s.mean() + 1.96*s.sem(),
                m.mean() - 1.96*m.sem(), m.mean() + 1.96*m.sem()]
x6_lo  = min(all_x6) - 0.15
x6_hi  = max(all_x6) + 0.15
lbl_x6 = x6_lo - 0.1

fig, ax = plt.subplots(figsize=(6.5, 4.5), dpi=150)
y_pos6 = list(range(len(rows6) - 1, -1, -1))

for (col, lbl, diff, p_val), y in zip(rows6, y_pos6):
    s_d = df6_viz[df6_viz['condition_name'] == 'single_turn'][col].dropna()
    m_d = df6_viz[df6_viz['condition_name'] == 'multi_turn'][col].dropna()
    s_m, s_se = s_d.mean(), s_d.sem()
    m_m, m_se = m_d.mean(), m_d.sem()

    line_col  = '#2E7D32' if p_val < 0.05 else '#BDBDBD'
    dot_alpha = 1.0       if p_val < 0.05 else 0.40
    txt_alpha = 1.0       if p_val < 0.05 else 0.45

    ax.plot([s_m, m_m], [y, y], color=line_col, linewidth=2.0,
            solid_capstyle='round', zorder=1)
    ci_col = '#BDBDBD'
    ax.errorbar(s_m, y, xerr=1.96*s_se, fmt='o', color=COLOR_SINGLE,
                markersize=9, markeredgecolor='white', markeredgewidth=1.5,
                capsize=0, elinewidth=1.2, solid_capstyle='round',
                ecolor=ci_col, zorder=3, alpha=dot_alpha)
    ax.errorbar(m_m, y, xerr=1.96*m_se, fmt='s', color=COLOR_MULTI,
                markersize=9, markeredgecolor='white', markeredgewidth=1.5,
                capsize=0, elinewidth=1.2, solid_capstyle='round',
                ecolor=ci_col, zorder=3, alpha=dot_alpha)
    ax.text(lbl_x6, y, lbl, va='center', ha='right', fontsize=10,
            alpha=txt_alpha)

ax.set_xlim(x6_lo, x6_hi)
ax.set_ylim(-0.6, len(rows6) - 0.4)
ax.set_yticks([])
ax.set_xlabel('Mean Likert Rating (1–7)', fontsize=10)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_visible(False)
ax.tick_params(axis='both', labelsize=10)
plt.tight_layout()
plt.savefig('plots_finalized/fig6_viz_engagement_cleaned.png', bbox_inches='tight', dpi=200)
plt.savefig('plots_finalized/fig6_viz_engagement_cleaned.pdf', bbox_inches='tight')
plt.close()
print('Saved fig6_cleaned')


# ============================================================
# Fig 7: UEQ Tradeoff (cleaned)
# ============================================================

df7 = pd.read_csv('data_participants.csv')
df7_viz = df7[df7['condition_name'].isin(['single_turn', 'multi_turn'])].copy()

pragmatic_cols7 = [
    'final_ueq_obstructive_supportive', 'final_ueq_complicated_easy',
    'final_ueq_inefficient_efficient',  'final_ueq_confusing_clear',
]
hedonic_cols7 = [
    'final_ueq_boring_exciting', 'final_ueq_not_interesting_interesting',
    'final_ueq_conventional_inventive', 'final_ueq_usual_leading_edge',
]
df7_viz['ueq_pragmatic'] = df7_viz[pragmatic_cols7].mean(axis=1)
df7_viz['ueq_hedonic']   = df7_viz[hedonic_cols7].mean(axis=1)
df7_viz['ueq_overall']   = df7_viz[pragmatic_cols7 + hedonic_cols7].mean(axis=1)

item_groups7 = [
    ('final_ueq_obstructive_supportive',      'Supportive',   'pragmatic'),
    ('final_ueq_complicated_easy',            'Easy',         'pragmatic'),
    ('final_ueq_inefficient_efficient',       'Efficient',    'pragmatic'),
    ('final_ueq_confusing_clear',             'Clear',        'pragmatic'),
    ('final_ueq_boring_exciting',             'Exciting',     'hedonic'),
    ('final_ueq_not_interesting_interesting', 'Interesting',  'hedonic'),
    ('final_ueq_conventional_inventive',      'Inventive',    'hedonic'),
    ('final_ueq_usual_leading_edge',          'Leading Edge', 'hedonic'),
    ('ueq_pragmatic',                         'Pragmatic QA', 'subscale'),
    ('ueq_hedonic',                           'Hedonic QA',   'subscale'),
    ('ueq_overall',                           'Overall',      'subscale'),
]

y_pos7, y = [], len(item_groups7) - 1
gap7 = {'pragmatic': 0, 'hedonic': 0.6, 'subscale': 0.6}
prev_g = None
for col, lbl, grp in item_groups7:
    if prev_g is not None and grp != prev_g:
        y -= gap7[grp]
    y_pos7.append(y)
    y -= 1
    prev_g = grp

# xlim from data
all_x7 = []
for (col, lbl, grp), y in zip(item_groups7, y_pos7):
    s = df7_viz[df7_viz['condition_name'] == 'single_turn'][col].dropna()
    m = df7_viz[df7_viz['condition_name'] == 'multi_turn'][col].dropna()
    all_x7 += [s.mean() - 1.96*s.sem(), s.mean() + 1.96*s.sem(),
                m.mean() - 1.96*m.sem(), m.mean() + 1.96*m.sem()]
x7_lo  = min(all_x7) - 0.15
x7_hi  = max(all_x7) + 0.15
lbl_x7 = x7_lo - 0.1

fig, ax = plt.subplots(figsize=(7.5, 6.5), dpi=150)

# subscale background band
sub_ys = [y for (_, _, g), y in zip(item_groups7, y_pos7) if g == 'subscale']
ax.axhspan(min(sub_ys) - 0.4, max(sub_ys) + 0.4,
           facecolor='#F5F5F5', edgecolor='none', zorder=0)

# group separator lines
prag_ys = [y for (_, _, g), y in zip(item_groups7, y_pos7) if g == 'pragmatic']
hed_ys  = [y for (_, _, g), y in zip(item_groups7, y_pos7) if g == 'hedonic']
ax.axhline((min(prag_ys) + max(hed_ys))  / 2, color='#E0E0E0', linewidth=1.0, zorder=0)
ax.axhline((min(hed_ys)  + max(sub_ys))  / 2, color='#E0E0E0', linewidth=1.0, zorder=0)

# scale midpoint reference
ax.axvline(4.0, color='#BDBDBD', linewidth=1.0, linestyle=':', zorder=0)

for (col, lbl, grp), y in zip(item_groups7, y_pos7):
    s_d = df7_viz[df7_viz['condition_name'] == 'single_turn'][col].dropna()
    m_d = df7_viz[df7_viz['condition_name'] == 'multi_turn'][col].dropna()
    s_m, s_se = s_d.mean(), s_d.sem()
    m_m, m_se = m_d.mean(), m_d.sem()
    _, p_val  = stats.ttest_ind(m_d, s_d)

    line_col  = '#2E7D32' if p_val < 0.05 else '#BDBDBD'
    dot_alpha = 1.0       if p_val < 0.05 else 0.40
    txt_alpha = 1.0       if p_val < 0.05 else 0.45
    ms  = 11 if grp == 'subscale' else 8
    lw  = 2.5 if grp == 'subscale' else 1.8
    fw  = 'bold' if grp == 'subscale' else 'normal'

    ci_col7 = '#BDBDBD'
    ax.plot([s_m, m_m], [y, y], color=line_col, linewidth=lw,
            solid_capstyle='round', zorder=1)
    ax.errorbar(s_m, y, xerr=1.96*s_se, fmt='o', color=COLOR_SINGLE,
                markersize=ms, markeredgecolor='white', markeredgewidth=1.5,
                capsize=0, elinewidth=1.2, solid_capstyle='round',
                ecolor=ci_col7, zorder=3, alpha=dot_alpha)
    ax.errorbar(m_m, y, xerr=1.96*m_se, fmt='s', color=COLOR_MULTI,
                markersize=ms, markeredgecolor='white', markeredgewidth=1.5,
                capsize=0, elinewidth=1.2, solid_capstyle='round',
                ecolor=ci_col7, zorder=3, alpha=dot_alpha)
    ax.text(lbl_x7, y, lbl, va='center', ha='right', fontsize=10,
            fontweight=fw, alpha=txt_alpha)

ax.set_xlim(x7_lo, x7_hi)
ax.set_ylim(min(y_pos7) - 0.6, max(y_pos7) + 0.6)
ax.set_yticks([])
ax.set_xlabel('Mean Rating (1–7)', fontsize=10)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_visible(False)
ax.tick_params(axis='both', labelsize=10)
plt.tight_layout()
plt.savefig('plots_finalized/fig7_ueq_tradeoff_cleaned.png', bbox_inches='tight', dpi=200)
plt.savefig('plots_finalized/fig7_ueq_tradeoff_cleaned.pdf', bbox_inches='tight')
plt.close()
print('Saved fig7_cleaned')


print('\nAll cleaned versions saved.')
