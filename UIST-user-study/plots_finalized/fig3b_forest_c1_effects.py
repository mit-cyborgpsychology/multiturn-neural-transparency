"""
Figure 3b: Forest Plot — C1 (Visualization vs Control) Effect Sizes
Each row = one calibration measure. Point + 95% CI for Cohen's d.
Sign accuracy included to show the null contrast.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from scipy import stats

mpl.rcParams['font.family'] = 'Helvetica'
mpl.rcParams['font.sans-serif'] = ['Helvetica', 'Arial', 'DejaVu Sans']

# --- Load data ---
df = pd.read_csv('data_calibration_jasp.csv')

# --- Compute C1 contrast (Viz vs Control) for each measure ---
# C1 weights: control = -1, single = +0.5, multi = +0.5
# Cohen's d from independent-samples contrast

measures = [
    ('s2_mba_initial_rmse', 'MBA vs Initial'),
    ('s2_mbe_initial_rmse', 'MBE vs Initial'),
    ('s2_mbe_final_rmse', 'MBE vs Final'),
    ('s2_mbe_avg_rmse', 'MBE vs Average'),
    ('s2_sign_accuracy', 'Sign Accuracy'),
]

results = []
for col, label in measures:
    control = df[df['condition_name'] == 'control'][col].dropna()
    viz = pd.concat([
        df[df['condition_name'] == 'single_turn'][col].dropna(),
        df[df['condition_name'] == 'multi_turn'][col].dropna(),
    ])

    # Cohen's d (viz - control), negative = viz is lower = better
    pooled_std = np.sqrt(((len(control) - 1) * control.std()**2 +
                           (len(viz) - 1) * viz.std()**2) /
                          (len(control) + len(viz) - 2))
    d = (viz.mean() - control.mean()) / pooled_std

    # SE of d ≈ sqrt(1/n1 + 1/n2 + d²/(2(n1+n2)))
    n1, n2 = len(control), len(viz)
    se_d = np.sqrt(1/n1 + 1/n2 + d**2 / (2 * (n1 + n2)))

    # t-test for p-value
    t_stat, p_val = stats.ttest_ind(viz, control)

    results.append({
        'label': label,
        'd': d,
        'se': se_d,
        'ci_lo': d - 1.96 * se_d,
        'ci_hi': d + 1.96 * se_d,
        'p': p_val,
    })

# --- Plot ---
fig, ax = plt.subplots(figsize=(6, 3.5), dpi=150)

y_positions = list(range(len(results) - 1, -1, -1))
colors = []
for r in results:
    colors.append('#2E7D32' if r['p'] < 0.05 else '#9E9E9E')

for i, (r, y) in enumerate(zip(results, y_positions)):
    color = colors[i]

    # CI line
    ax.plot([r['ci_lo'], r['ci_hi']], [y, y],
            color=color, linewidth=2.5, solid_capstyle='round', zorder=2)

    # Point estimate
    ax.plot(r['d'], y, 'o', color=color, markersize=10, zorder=3,
            markeredgecolor='white', markeredgewidth=1.5)

    # Label
    sig = '*' if r['p'] < 0.05 else ''
    ax.text(-1.05, y, f"{r['label']}", va='center', ha='right', fontsize=10)
    ax.text(r['ci_hi'] + 0.03, y,
            f"d = {r['d']:.2f}{sig}",
            va='center', ha='left', fontsize=9, color=color)

# Zero line
ax.axvline(0, color='#BDBDBD', linewidth=1, linestyle='--', zorder=1)

# Annotation
ax.text(-0.02, -0.8, 'Visualization better <--', fontsize=8, color='#616161',
        ha='right', va='top')
ax.text(0.02, -0.8, '--> Control better', fontsize=8, color='#616161',
        ha='left', va='top')

ax.set_yticks([])
ax.set_xlabel("Cohen's d (C1: Visualization vs Control)", fontsize=10)
ax.set_xlim(-1.0, 0.5)
ax.set_ylim(-1.2, len(results) - 0.5)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_visible(False)

plt.tight_layout()
plt.savefig('plots_finalized/fig3b_forest_c1_effects.png',
            bbox_inches='tight', dpi=200)
plt.savefig('plots_finalized/fig3b_forest_c1_effects.pdf',
            bbox_inches='tight')
plt.show()
print('Saved fig3b')
