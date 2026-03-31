"""
Figure 2: Baseline Miscalibration
Side-by-side box + jittered dots: MBA and MBE RMSE, grouped by prompt type.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib as mpl

mpl.rcParams['font.family'] = 'Helvetica'
mpl.rcParams['font.sans-serif'] = ['Helvetica', 'Arial', 'DejaVu Sans']

# --- Load data ---
df_parts = pd.read_csv('data_participants.csv')
df_pv = pd.read_csv('data_persona_vectors.csv')

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

# --- Compute RMSE per participant ---
rows = []
for _, p in df_parts.iterrows():
    fid = p['firebase_id']
    key = (fid, 1)
    pt = p['session1_prompt_type']
    if key not in first_turns.index or key not in mean_activations.index:
        continue

    mba_errs = []
    mbe_errs = []
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
        rows.append({
            'prompt_type': pt,
            'mba_rmse': np.sqrt(np.mean(mba_errs)),
            'mbe_rmse': np.sqrt(np.mean(mbe_errs)),
        })

df_rmse = pd.DataFrame(rows)

# --- Plot ---
COLOR_ASST = '#5C6BC0'      # indigo — assistant
COLOR_ROLEPLY = '#E65100'   # deep orange — roleplay

fig, ax = plt.subplots(figsize=(7, 5.5), dpi=150)

rng = np.random.default_rng(42)

# Group positions: x-axis = measure (MBA, MBE), color = prompt type
measures = ['mba_rmse', 'mbe_rmse']
measure_labels = ['Anticipation\n(MBA vs Initial)', 'Evaluation\n(MBE vs Average)']
group_positions = [0, 2.5]
box_width = 0.6
offset = 0.4

for g_idx, (measure, m_label, g_pos) in enumerate(zip(measures, measure_labels, group_positions)):
    for p_idx, (pt, color, pt_label) in enumerate([
        ('ASST', COLOR_ASST, 'Assistant'),
        ('ROLEPLY', COLOR_ROLEPLY, 'Roleplay'),
    ]):
        pos_offset = -offset if p_idx == 0 else +offset
        subset = df_rmse[df_rmse['prompt_type'] == pt]
        vals = subset[measure].dropna().values
        pos = g_pos + pos_offset

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

        pass  # no per-box annotations

# X axis
ax.set_xticks(group_positions)
ax.set_xticklabels(measure_labels, fontsize=11)
ax.set_xlim(-1, 3.5)

# Y axis
ax.set_ylim(0, 1.3)
ax.set_ylabel('RMSE (lower = better calibration)', fontsize=11)

# Legend
patch_asst = mpatches.Patch(color=COLOR_ASST, alpha=0.5, label='Assistant prompt')
patch_rp = mpatches.Patch(color=COLOR_ROLEPLY, alpha=0.5, label='Roleplay prompt')
ax.legend(handles=[patch_asst, patch_rp], loc='upper left', fontsize=10, framealpha=0.9)

# Spines
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

pass  # title handled by LaTeX caption

plt.tight_layout()
plt.savefig('plots_finalized/fig2_baseline_miscalibration.png',
            bbox_inches='tight', dpi=200)
plt.savefig('plots_finalized/fig2_baseline_miscalibration.pdf',
            bbox_inches='tight')
plt.show()
print('Saved to plots_finalized/')
