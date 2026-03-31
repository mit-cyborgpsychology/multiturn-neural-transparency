# Questionnaire Analysis Results

**Dataset**: 246 participants (81 control, 85 single-turn, 80 multi-turn)
**Date**: 2026-03-30

Related files:
- [ANALYSIS_RESULTS.md](ANALYSIS_RESULTS.md) — calibration error analysis (primary behavioral outcomes)
- [ANALYSIS_PER_TRAIT.md](ANALYSIS_PER_TRAIT.md) — per-trait calibration breakdowns

---

## Study Design Summary

A between-subjects user study on **neural transparency** — whether showing participants the AI's internal persona trait scores improves their ability to evaluate AI behavior.

- **Control** (n=81): No visualization, chat-only interface
- **Single-Turn** (n=85): Static persona snapshot (sunburst chart showing current trait scores)
- **Multi-Turn** (n=80): Dynamic persona trajectory (sunburst + drift panel showing trait change over conversation)

Two-session within-subjects design: **Session 1** = baseline (no visualization for anyone), **Session 2** = experimental (visualization condition applied). Prompt types (ASST: obedient assistant, ROLEPLY: bold independent AI) are counterbalanced across sessions.

## Statistical Approach

Consistent with calibration analyses (see [ANALYSIS_RESULTS.md](ANALYSIS_RESULTS.md) for full details).

### Planned Orthogonal Contrasts

Our between-subjects manipulation has a hierarchical structure: control receives no visualization, single-turn receives a static snapshot, and multi-turn receives a dynamic trajectory. Rather than testing all pairwise comparisons (which requires correction for multiple comparisons), we decompose the omnibus ANOVA into two theory-driven, orthogonal contrasts:

- **C1 (Viz vs Control)**: Does having *any* visualization change the outcome compared to no visualization? This pools single-turn and multi-turn against control.
  - Weights: control = -1, single-turn = +0.5, multi-turn = +0.5
- **C2 (Multi vs Single)**: Does the *richer* multi-turn visualization differ from the simpler single-turn snapshot? This ignores control entirely.
  - Weights: control = 0, single-turn = -1, multi-turn = +1

These contrasts are orthogonal (statistically independent): the product of their weights sums to zero, meaning each contrast answers a non-overlapping question. Because they are planned (derived from the study design, not from observed data patterns) and orthogonal (they fully partition the 2 degrees of freedom from the 3-group comparison), no multiple comparison correction is needed.

### Tests Used

For items measured across **all 3 conditions** (pre-survey, final core, shifts):
- **One-way ANOVA** (omnibus F, p)
- **Planned contrasts C1 and C2** (t, p, Cohen's d)
- **2x3 factorial ANOVA** (condition x S2 prompt type — exploratory)

For items measured only in **visualization conditions** (viz Likert, UEQ):
- **Independent t-test** single vs multi (functionally equivalent to C2)
- **Cohen's d** effect size
- **2x2 factorial ANOVA** (condition x prompt type — exploratory)

Effect sizes: Cohen's d throughout. Conventions: |d| < 0.2 = negligible, 0.2–0.5 = small, 0.5–0.8 = medium, > 0.8 = large.

### Note on SS Type and Counterbalancing

All factorial ANOVAs use **Type II** sum of squares, following Langsrud (2003) for mildly unbalanced designs (cell sizes range 40–45). Type II tests each main effect adjusted for the other main effect but not the interaction, providing more statistical power than Type III. See [ANALYSIS_RESULTS.md](ANALYSIS_RESULTS.md) Section 2 for a detailed comparison.

Prompt order (asst_first vs roleply_first) affects calibration error in both sessions, but the direction flips: roleply_first participants show higher error in S1 (doing ROLEPLY) and lower error in S2 (doing ASST). This reflects prompt difficulty, not a stable individual difference, and is balanced across conditions by the counterbalanced design. When prompt type appears as a factor in factorial analyses below, it captures this prompt difficulty effect.

---

## 1. Pre-Survey Randomization Check

Administered before any sessions. All items 1-7 Likert scale. All three conditions should show no differences — confirms random assignment worked.

| Item | F | p | C1 t | C1 p | C1 d | C2 t | C2 p | C2 d | Ctrl M(SD) | Single M(SD) | Multi M(SD) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Predictability | 0.46 | 0.6324 | -0.63 | 0.5289 | -0.086 | -0.73 | 0.4647 | -0.114 | 4.47(1.21) | 4.44(1.16) | 4.30(1.19) |
| Neg. Predictability | 0.50 | 0.6087 | -0.15 | 0.8844 | -0.020 | -0.99 | 0.3236 | -0.154 | 4.32(1.37) | 4.40(1.38) | 4.19(1.39) |
| Trust | 1.06 | 0.3469 | -1.34 | 0.1820 | -0.182 | 0.56 | 0.5792 | 0.086 | 4.28(1.49) | 3.96(1.41) | 4.09(1.36) |

---

**Result**: No significant differences on any item (all p > .30). Randomization is clean.

---

## 2. Final Survey Core Likert (All Conditions)

> **JASP verified (2026-03-31)**: Predictability Post — F=2.874, p=.058; C1 t=-2.387, p=.018 (Type III). Matches Python Type II (F=2.87, C1 t=-2.39, p=.018).

Administered after both sessions. Same items as pre-survey, now measuring post-study beliefs. 1-7 Likert scale.

| Item | F | p | C1 t | C1 p | C1 d | C2 t | C2 p | C2 d | Ctrl M(SD) | Single M(SD) | Multi M(SD) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Predictability (post) | 2.87 | 0.0584 | -2.39 | *0.0178* | -0.321 | -0.27 | 0.7877 | -0.042 | 4.88(1.46) | 4.45(1.38) | 4.39(1.42) |
| Neg. Predictability (post) | 1.52 | 0.2201 | -1.48 | 0.1393 | -0.201 | 0.89 | 0.3720 | 0.139 | 4.00(1.67) | 3.59(1.37) | 3.80(1.50) |
| Trust (post) | 2.90 | 0.0568 | -2.16 | *0.0316* | -0.291 | 1.02 | 0.3068 | 0.158 | 4.56(1.47) | 4.00(1.54) | 4.24(1.45) |

### 2x3 Factorial: Condition x Prompt Type

| Item | Condition F | p | Prompt F | p | Interaction F | p |
|---|---|---|---|---|---|---|
| Predictability (post) | 2.82 | 0.0615 | 2.26 | 0.1342 | 0.74 | 0.4795 |
| Neg. Predictability (post) | 1.56 | 0.2114 | 0.64 | 0.4245 | 1.21 | 0.2993 |
| Trust (post) | 2.89 | 0.0576 | 0.04 | 0.8460 | 0.48 | 0.6200 |

---

**Key finding**: C1 is significant for predictability (p=.018, d=-0.32) and trust (p=.032, d=-0.29) — visualization groups rate themselves *lower* on predictability and trust than control. This suggests participants who saw the visualization became more calibrated in their metacognitive judgments (less overconfident), while control participants maintained or inflated their self-assessed predictive ability.

No significant C2 effects (multi vs single do not differ on core survey items). No prompt type interactions.

---

## 3. Pre-to-Final Shifts

Computed as final - pre for each participant. Positive = increase from pre to post.

**Within-condition tests**: Does each condition's shift differ from zero? (one-sample t-test)
**Between-condition tests**: Do shifts differ across conditions? (ANOVA + contrasts)

### Within-Condition Shift Tests (one-sample t-test: shift ≠ 0)

| Item | Condition | M shift | SD | t | p | d |
|---|---|---|---|---|---|---|
| Predictability Shift | Control | +0.407 | 1.808 | 2.03 | *0.0459* | 0.225 |
| Predictability Shift | Single-Turn | +0.012 | 1.547 | 0.07 | 0.9443 | 0.008 |
| Predictability Shift | Multi-Turn | +0.087 | 1.624 | 0.48 | 0.6312 | 0.054 |
| Neg. Predictability Shift | Control | -0.321 | 1.863 | -1.55 | 0.1249 | -0.172 |
| Neg. Predictability Shift | Single-Turn | -0.812 | 1.701 | -4.40 | **0.0000** | -0.477 |
| Neg. Predictability Shift | Multi-Turn | -0.388 | 1.710 | -2.03 | *0.0460* | -0.227 |
| Trust Shift | Control | +0.272 | 0.975 | 2.51 | *0.0142* | 0.279 |
| Trust Shift | Single-Turn | +0.035 | 0.981 | 0.33 | 0.7410 | 0.036 |
| Trust Shift | Multi-Turn | +0.150 | 0.969 | 1.38 | 0.1701 | 0.155 |

### Between-Condition ANOVA + Contrasts

| Item | F | p | C1 t | C1 p | C1 d | C2 t | C2 p | C2 d | Ctrl M | Single M | Multi M |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Predictability Shift | 1.31 | 0.2716 | -1.59 | 0.1139 | -0.215 | 0.29 | 0.7701 | 0.046 | +0.407 | +0.012 | +0.087 |
| Neg. Predictability Shift | 1.91 | 0.1499 | -1.17 | 0.2441 | -0.158 | 1.55 | 0.1228 | 0.240 | -0.321 | -0.812 | -0.388 |
| Trust Shift | 1.22 | 0.2977 | -1.35 | 0.1775 | -0.183 | 0.76 | 0.4509 | 0.118 | +0.272 | +0.035 | +0.150 |

### 2x3 Factorial on Shifts: Condition x Prompt Type

| Item | Condition F | p | Prompt F | p | Interaction F | p |
|---|---|---|---|---|---|---|
| Predictability Shift | 1.24 | 0.2904 | 5.52 | *0.0196* | 0.86 | 0.4229 |
| Neg. Predictability Shift | 1.94 | 0.1460 | 0.41 | 0.5217 | 0.63 | 0.5330 |
| Trust Shift | 1.22 | 0.2972 | 0.00 | 0.9527 | 2.06 | 0.1302 |

---

**Key findings**:
- **Control** significantly increases self-rated predictability (+0.41, p=.046) and trust (+0.27, p=.014) — consistent with overconfidence without visualization feedback.
- **Single-Turn** shows the largest negative predictability shift (-0.81, p<.0001) — these participants became substantially more aware of unintended negative behaviors.
- Between-condition ANOVAs are not significant (all p>.15) — the shifts don't significantly differ *between* groups, but the within-condition patterns are informative.
- **Prompt type** significantly affects the predictability shift (2x3 factorial: p=.020) — the shift direction depends on which prompt participants had in S2.

---

## 4. Visualization Likert (Single-Turn vs Multi-Turn)

> **JASP verified (2026-03-31)**: Frequency — F=18.83, p<.001 (equivalent to t=4.34). Matches Python (t=-4.34, p<.0001).

These items were only administered to participants who received a visualization. 1-7 Likert (1 = strongly disagree, 7 = strongly agree). Control group has no data for these items.

The comparison is single-turn vs multi-turn (equivalent to the C2 contrast from the calibration analyses).

| Item | Single M(SD) | Multi M(SD) | t | p | Cohen's d |
|---|---|---|---|---|---|
| Helpfulness | 4.56(1.68) | 5.03(1.59) | -1.81 | 0.0729 | 0.281 |
| Anticipation | 4.55(1.61) | 4.70(1.46) | -0.61 | 0.5414 | 0.095 |
| Prediction | 4.36(1.64) | 4.78(1.51) | -1.67 | 0.0969 | 0.260 |
| Referenced | 4.29(1.81) | 5.05(1.44) | -2.96 | **0.0036** | 0.460 |
| Confidence | 4.31(1.73) | 4.70(1.63) | -1.51 | 0.1335 | 0.235 |
| Frequency | 3.82(1.77) | 4.99(1.67) | -4.34 | **0.0000** | 0.676 |
| Comprehension | 5.04(1.35) | 4.90(1.43) | 0.63 | 0.5324 | -0.097 |

### 2x2 Factorial: Condition x Prompt Type

| Item | Condition F | p | Prompt F | p | Interaction F | p |
|---|---|---|---|---|---|---|
| Helpfulness | 3.28 | 0.0722 | 0.19 | 0.6641 | 0.51 | 0.4754 |
| Anticipation | 0.36 | 0.5481 | 0.08 | 0.7718 | 1.19 | 0.2777 |
| Prediction | 2.86 | 0.0926 | 0.89 | 0.3463 | 0.21 | 0.6448 |
| Referenced | 8.78 | **0.0035** | 0.41 | 0.5232 | 0.49 | 0.4831 |
| Confidence | 2.34 | 0.1279 | 0.90 | 0.3448 | 0.04 | 0.8491 |
| Frequency | 19.51 | **0.0000** | 2.25 | 0.1356 | 2.42 | 0.1221 |
| Comprehension | 0.32 | 0.5731 | 5.38 | *0.0217* | 0.49 | 0.4841 |

---

**Key findings**:
- **Frequency** is the strongest differentiator (d=0.68, p<.0001) — multi-turn participants checked the visualization much more often. This is expected: the dynamic trajectory gives participants a reason to keep checking as it updates.
- **Referenced** is also significant (d=0.46, p=.004) — multi-turn participants actively used the visualization values when making evaluations.
- **Helpfulness** and **Prediction** are marginal (p=.073, p=.097) — trending toward multi-turn being perceived as more useful.
- **Comprehension** shows no difference — both visualizations were equally understood.
- No significant prompt type interactions on any item.

These self-report findings align with the behavioral calibration results: multi-turn participants engaged more with the visualization and showed better calibration on MBE vs Average.

---

## 5. Drift Panel (Multi-Turn Only)

The drift panel is the line graph below the sunburst chart showing how traits change over the conversation. Only multi-turn participants received this component. 1-7 Likert (1 = strongly disagree, 7 = strongly agree).

- **n** = 80
- **M** = 4.96, **SD** = 1.45
- **95% CI** = [4.64, 5.29]
- **vs midpoint (4.0)**: t=5.92, p=**0.0000**

### By S2 Prompt Type

| Prompt | M | SD | n |
|---|---|---|---|
| ASST | 4.83 | 1.66 | 40 |
| ROLEPLY | 5.10 | 1.22 | 40 |

AST vs ROLEPLY: t=-0.84, p=0.4009

---

**Result**: Rated significantly above the neutral midpoint (M=4.96, p<.0001). Participants found the drift panel helpful for noticing behavioral changes over time. No difference by prompt type.

---

## 6. User Experience Questionnaire (Single-Turn vs Multi-Turn)

The UEQ uses 7-point semantic differential scales (e.g., "obstructive" to "supportive"). Control excluded — only visualization conditions received these items.

Subscales:
- **Pragmatic Quality** = mean of supportive, easy, efficient, clear (usability)
- **Hedonic Quality** = mean of exciting, interesting, inventive, leading edge (engagement/novelty)
- **Overall** = mean of all 8 items

### Individual Items

| Item | Single M(SD) | Multi M(SD) | t | p | Cohen's d |
|---|---|---|---|---|---|
| Obstructive–Supportive | 4.92(1.63) | 4.96(1.63) | -0.18 | 0.8600 | 0.028 |
| Complicated–Easy | 4.84(1.72) | 4.65(1.86) | 0.66 | 0.5071 | -0.104 |
| Inefficient–Efficient | 4.86(1.80) | 5.00(1.76) | -0.51 | 0.6113 | 0.079 |
| Confusing–Clear | 5.15(1.70) | 4.60(1.79) | 2.03 | *0.0435* | -0.317 |
| Boring–Exciting | 4.38(1.57) | 4.85(1.64) | -1.90 | 0.0595 | 0.296 |
| Not Interesting–Interesting | 4.85(1.72) | 5.12(1.77) | -1.02 | 0.3087 | 0.159 |
| Conventional–Inventive | 4.87(1.49) | 5.21(1.62) | -1.41 | 0.1604 | 0.220 |
| Usual–Leading Edge | 4.68(1.42) | 5.19(1.50) | -2.22 | *0.0275* | 0.346 |

### Subscales

| Subscale | Single M(SD) | Multi M(SD) | t | p | Cohen's d |
|---|---|---|---|---|---|
| Pragmatic | 4.94(1.54) | 4.80(1.60) | 0.56 | 0.5737 | -0.088 |
| Hedonic | 4.69(1.36) | 5.09(1.46) | -1.82 | 0.0704 | 0.284 |
| Overall | 4.82(1.32) | 4.95(1.36) | -0.63 | 0.5321 | 0.098 |

### 2x2 Factorial: Condition x Prompt Type

| Item/Subscale | Condition F | p | Prompt F | p | Interaction F | p |
|---|---|---|---|---|---|---|
| Obstructive–Supportive | 0.04 | 0.8493 | 0.25 | 0.6210 | 0.32 | 0.5724 |
| Complicated–Easy | 0.40 | 0.5288 | 1.16 | 0.2825 | 0.03 | 0.8583 |
| Inefficient–Efficient | 0.26 | 0.6111 | 0.01 | 0.9064 | 0.05 | 0.8154 |
| Confusing–Clear | 4.00 | *0.0472* | 0.98 | 0.3234 | 0.21 | 0.6436 |
| Boring–Exciting | 3.71 | 0.0560 | 1.15 | 0.2844 | 0.26 | 0.6102 |
| Not Interesting–Interesting | 1.12 | 0.2912 | 1.76 | 0.1866 | 0.05 | 0.8269 |
| Conventional–Inventive | 2.11 | 0.1478 | 2.06 | 0.1528 | 0.51 | 0.4782 |
| Usual–Leading Edge | 5.01 | *0.0266* | 0.69 | 0.4080 | 0.02 | 0.8793 |
| Pragmatic | 0.29 | 0.5904 | 0.55 | 0.4588 | 0.08 | 0.7717 |
| Hedonic | 3.45 | 0.0649 | 1.77 | 0.1859 | 0.10 | 0.7548 |
| Overall | 0.43 | 0.5114 | 1.28 | 0.2588 | 0.11 | 0.7381 |

**Key findings**:
- **Confusing–Clear**: Single-turn rated clearer (d=-0.32, p=.044) — the simpler static visualization is easier to interpret.
- **Usual–Leading Edge**: Multi-turn rated more novel (d=0.35, p=.028) — the dynamic trajectory feels more innovative.
- **Boring–Exciting**: Marginal trend toward multi-turn (d=0.30, p=.060).
- **Pragmatic quality** is equal between conditions — both are equally usable.
- **Hedonic quality** trends higher for multi-turn (p=.070) — more engaging but not significantly so.

This presents a classic usability-novelty tradeoff: multi-turn is perceived as more innovative and engaging, but single-turn is perceived as clearer. Despite this, multi-turn produces better behavioral calibration outcomes (see ANALYSIS_RESULTS.md).

---

## 7. Summary

### Subjective experience findings

1. **Visualization reduces overconfidence** (C1): Participants with any visualization rate their predictive ability and trust *lower* than control — they become more calibrated in their self-assessments, not just their behavioral ratings.

2. **Multi-turn drives higher engagement** (C2): Multi-turn participants check the visualization more frequently (d=0.68) and reference it more when evaluating (d=0.46). This behavioral engagement corresponds to better calibration on the MBE vs Average measure.

3. **Usability-novelty tradeoff**: Single-turn is perceived as clearer; multi-turn is perceived as more novel and engaging. Both are equally usable overall (pragmatic quality is equivalent).

4. **Drift panel is valued**: Multi-turn participants rate the drift panel significantly above neutral — they find it helpful for tracking behavioral changes.

### Does self-reported engagement predict calibration accuracy?

Multi-turn participants reported checking the visualization more frequently (d=0.68) and referencing it more when evaluating (d=0.46) than single-turn participants. A natural follow-up question is whether this self-reported engagement predicts actual calibration performance at the individual level — do participants who say they used the visualization more actually show lower calibration error?

**Method**: We tested this within the multi-turn condition (n=80) using three engagement measures as predictors of S2 calibration RMSE:
- **Frequency** (VIZ-6): "I found myself checking the visualization frequently during the conversation" (1-7 Likert)
- **Referenced** (VIZ-4): "I actively referenced the values from the chart when evaluating the AI's behavior after we chatted" (1-7 Likert)
- **Combined engagement**: Mean of frequency and referenced

For each predictor, we computed Pearson correlations against all four RMSE measures (MBA vs Initial, MBE vs Initial, MBE vs Final, MBE vs Average). We also split participants into three engagement groups (Low, Mid, High) and compared their RMSE distributions using kernel density estimation.

**Results (Multi-Turn only, n=80)**:

| Outcome | Frequency r (p) | Referenced r (p) | Combined r (p) |
|---|---|---|---|
| MBA vs Initial | .114 (.313) | -.131 (.245) | .001 (.995) |
| MBE vs Initial | .125 (.271) | -.066 (.561) | .042 (.712) |
| MBE vs Final | .068 (.547) | -.155 (.169) | -.040 (.722) |
| MBE vs Average | .137 (.226) | -.181 (.108) | -.012 (.917) |

All correlations are near zero and non-significant. The RMSE distributions for low, mid, and high engagement groups overlap almost completely (see `plots/calibration/rmse_by_engagement_combined_mt.png`).

**Interpretation**: Self-reported visualization engagement does not predict individual calibration accuracy within the multi-turn condition. The multi-turn visualization's benefit over single-turn (documented in [ANALYSIS_RESULTS.md](ANALYSIS_RESULTS.md)) appears to operate at the condition level — having the trajectory available improves calibration regardless of how much participants consciously report using it. This is consistent with prior HCI research showing that ambient information displays can improve decision-making without users being aware of how much they rely on the information.

### Alignment with behavioral outcomes

The questionnaire results are consistent with the calibration findings (ANALYSIS_RESULTS.md):
- At the **group level**, the conditions that report higher engagement (multi-turn) also show better calibration — but this is driven by the condition assignment, not by individual differences in engagement
- The **shift** patterns show that control participants become overconfident while visualization participants become appropriately humble
- The **drift panel** helpfulness rating aligns with multi-turn's unique advantage on MBE vs Average (evaluating overall persona trajectory)

### Data files
- `data_questionnaire_jasp.csv` — 246 x 34, all questionnaire items for JASP replication
- Plots in `plots/questionnaire/`: `pre_final_overview.png`, `shifts.png`, `viz_likert_comparison.png`, `ueq_subscales_comparison.png`