# UIST User Study — Analysis Results

**Dataset**: 246 participants (final analysis), 257 exploratory
**Exports**: pilot2 (36), run3 (98), run4 (148) = 282 total, filtered to 246
**Date**: 2026-03-30

## 1. Study Design

Within-subjects, two-session design:
- **Session 1**: Baseline (no visualization for any condition)
- **Session 2**: Experimental (visualization condition applied)

### Conditions (between-subjects)
| Condition | n | Description |
|---|---|---|
| Control | 81 | No visualization |
| Single-Turn | 85 | Static persona snapshot |
| Multi-Turn | 80 | Dynamic persona trajectory over conversation |

### Prompt Types (counterbalanced within-subjects)
Each participant chats with two AI personas across sessions:
- **ASST**: Obedient assistant persona
- **ROLEPLY**: Bold, independent AI persona

| Condition | S2 ASST | S2 ROLEPLY | asst_first | roleply_first |
|---|---|---|---|---|
| Control | 41 | 40 | 40 | 41 |
| Single-Turn | 40 | 45 | 45 | 40 |
| Multi-Turn | 40 | 40 | 40 | 40 |
| **Total** | **121** | **125** | **125** | **121** |

### Outcome Measures
- **MBA (Model Behavior Anticipation)**: Trait ratings before chat (6 traits, -10 to +10)
- **MBE (Model Behavior Evaluation)**: Trait ratings after chat (6 traits, -10 to +10)
- **Persona Activations**: API-derived trait scores (net = pos_pole - neg_pole, range [-1, 1])
- **Calibration Error**: RMSE between normalized human ratings (/10) and actual activations
- **Sign Accuracy**: Did participant identify correct trait polarity?

### Traits
empathy, erudite, robotic, romantic, sycophantic, toxic

### Calibration Comparisons
| Label | Human Rating | Ground Truth |
|---|---|---|
| MBA vs Initial | Pre-chat prediction | Turn 0 activation (system prompt) |
| MBE vs Initial | Post-chat evaluation | Turn 0 activation |
| MBE vs Final | Post-chat evaluation | Last turn activation |
| MBE vs Average | Post-chat evaluation | Mean activation across all turns |

---

## 2. Baseline Equivalence (S1)

> **JASP verified (2026-03-31)**: MBA vs Initial — Condition F=0.461, p=.631 (Type III). Groups equivalent. Prompt order significant (F=7.37, p=.007) as expected.

All participants received no visualization in S1. One-way ANOVA confirms no pre-existing group differences.

| Outcome | F | p | Control M (SD) | Single M (SD) | Multi M (SD) |
|---|---|---|---|---|---|
| MBA vs Initial | 0.43 | .6482 | 0.614 (0.183) | 0.604 (0.151) | 0.589 (0.169) |
| MBE vs Initial | 0.97 | .3816 | 0.695 (0.191) | 0.660 (0.170) | 0.660 (0.191) |
| MBE vs Final | 0.84 | .4345 | 0.730 (0.210) | 0.692 (0.185) | 0.717 (0.172) |
| MBE vs Average | 1.40 | .2475 | 0.694 (0.202) | 0.646 (0.172) | 0.659 (0.189) |
| Sign Accuracy | 1.60 | .2039 | 0.519 (0.222) | 0.555 (0.227) | 0.492 (0.229) |

**Conclusion**: Groups are equivalent at baseline. All p > .20.

**Note on prompt type and counterbalancing**: Prompt order (asst_first vs roleply_first) has a significant main effect on calibration error in both sessions (Type II SS):

| Session | asst_first M | roleply_first M | F | p |
|---|---|---|---|---|
| S1 (MBE vs Avg) | 0.638 | 0.694 | 5.43 | .021 |
| S2 (MBE vs Avg) | 0.635 | 0.559 | 9.54 | .002 |

The direction **flips across sessions**: in S1, roleply_first participants show higher error (they are doing ROLEPLY, which is harder); in S2, they show lower error (they are now doing ASST, which is easier). This confirms the effect is driven by **which prompt participants have in that session**, not a stable individual difference. The counterbalanced design ensures this does not confound condition comparisons — prompt order is balanced across conditions.

Prompt order also significantly affects S1 **sign accuracy** (F=6.45, p=.012) — participants are worse at identifying trait polarity for the ROLEPLY persona specifically.

**SS Type note**: All factorial ANOVAs in this document use **Type II** sum of squares, following the recommendation of Langsrud (2003) for unbalanced designs. Type II tests each main effect adjusted for the other main effect but not the interaction, providing more power than Type III. Our cell sizes are mildly unbalanced (range: 40–45 per cell), which produces negligible differences for one-way ANOVAs and planned contrasts, but meaningful differences in the factorial models. Type III results are available in the JASP CSV for replication.

---

## 3. One-Way ANOVA on S2 (Primary Analysis)

> **JASP verified (2026-03-31)**: MBA vs Initial (F=7.23 Type III, p<.001), MBE vs Final (F=4.21, p=.016), MBE vs Average (F=6.12, p=.003). Type III values slightly differ from Type II below; all significance patterns match.

| Outcome | F | p | Control M | Single M | Multi M |
|---|---|---|---|---|---|
| **MBA vs Initial** | 7.06 | **.0010** | 0.614 | 0.507 | 0.519 |
| **MBE vs Initial** | 3.15 | **.0448** | 0.668 | 0.608 | 0.604 |
| **MBE vs Final** | 4.05 | **.0186** | 0.705 | 0.646 | 0.609 |
| **MBE vs Average** | 5.69 | **.0038** | 0.646 | 0.606 | 0.540 |
| Sign Accuracy | 0.40 | .6724 | 0.558 | 0.562 | 0.591 |

### Tukey HSD Post-Hoc

> **JASP verified**: MBA Initial — 0v1 p=.002, 0v2 p=.008, 1v2 p=.904. MBE Average — 0v2 p=.002, 1v2 p=.085. All match.

| Outcome | Control vs Single | Control vs Multi | Single vs Multi |
|---|---|---|---|
| **MBA vs Initial** | diff=-.106 **p=.002** | diff=-.094 **p=.008** | diff=-.012 p=.920 |
| **MBE vs Initial** | diff=-.060 p=.088 | diff=-.064 p=.069 | diff=+.004 p=.990 |
| **MBE vs Final** | diff=-.059 p=.188 | diff=-.096 **p=.014** | diff=+.037 p=.511 |
| **MBE vs Average** | diff=-.040 p=.402 | diff=-.105 **p=.003** | diff=+.065 p=.093 |

---

## 4. Planned Orthogonal Contrasts (Primary Hypothesis Tests)

> **JASP verified (2026-03-31)**: MBE vs Average — C1: t=-2.808, p=.005; C2: t=-2.133, p=.034 (Type III). Both significant, matching Python Type II results (C1: t=-2.68, p=.008; C2: t=-2.10, p=.037).

Two theory-driven, orthogonal contrasts:
- **C1 (Viz vs Control)**: Does any visualization improve calibration? Weights: control=-1, single=+0.5, multi=+0.5
- **C2 (Multi vs Single)**: Does multi-turn outperform single-turn? Weights: control=0, single=-1, multi=+1

### Without covariate

| Outcome | C1: t | C1: p | C1: d | C2: t | C2: p | C2: d |
|---|---|---|---|---|---|---|
| **MBA vs Initial** | -3.73 | **.0002** | -0.49 | 0.39 | .6986 | 0.06 |
| **MBE vs Initial** | -2.51 | **.0129** | -0.34 | -0.14 | .8909 | -0.02 |
| **MBE vs Final** | -2.64 | **.0088** | -0.35 | -1.11 | .2698 | -0.17 |
| **MBE vs Average** | -2.68 | **.0079** | -0.36 | **-2.10** | **.0372** | **-0.32** |
| Sign Accuracy | 0.54 | .5866 | 0.07 | 0.72 | .4750 | 0.11 |

### With S1 covariate (robustness check)

| Outcome | C1: t | C1: p | C2: t | C2: p |
|---|---|---|---|---|
| **MBA vs Initial** | -3.70 | **.0003** | 0.63 | .5285 |
| **MBE vs Initial** | -2.08 | **.0384** | -0.17 | .8648 |
| **MBE vs Final** | -2.46 | **.0148** | -1.42 | .1583 |
| **MBE vs Average** | -2.24 | **.0257** | **-2.39** | **.0176** |
| Sign Accuracy | 0.54 | .5890 | 0.74 | .4614 |

### Interpretation
1. **C1 is significant across all four RMSE measures** — any visualization reliably improves calibration vs control (d = 0.34–0.49, small-to-medium effects).
2. **C2 is significant only for MBE vs Average** (p=.037, d=-0.32) — multi-turn specifically outperforms single-turn for holistic persona evaluation. This result strengthens with the S1 covariate (p=.018).
3. This aligns with the theoretical prediction: the multi-turn visualization uniquely shows persona drift over the conversation, which should help participants evaluate the overall trajectory.

---

Per-trait analyses are in a separate file: [ANALYSIS_PER_TRAIT.md](ANALYSIS_PER_TRAIT.md)

---

## 5. ANCOVA: S2 ~ Condition + S1 Baseline (Robustness Check)

> **JASP verified (2026-03-31)**: MBE vs Average — Condition F=5.298, p=.006; S1 covariate F=33.25, p<.001 (Type III). Matches Python Type II (F=5.30, p=.006).

| Outcome | F | p | Ctrl vs Single | Ctrl vs Multi | Single vs Multi |
|---|---|---|---|---|---|
| **MBA vs Initial** | 7.08 | **.0010** | b=-.103 **p=.0002** | b=-.084 **p=.005** | b=+.018 p=.550 |
| MBE vs Initial | 2.18 | .1157 | b=-.043 p=.094 | b=-.047 p=.062 | b=-.004 p=.866 |
| **MBE vs Final** | 3.97 | **.0202** | b=-.048 p=.125 | b=-.091 **p=.005** | b=-.045 p=.182 |
| **MBE vs Average** | 5.30 | **.0056** | b=-.024 p=.392 | b=-.091 **p=.003** | b=-.070 **p=.021** |
| Sign Accuracy | 0.41 | .6628 | b=+.009 p=.815 | b=+.036 p=.407 | b=+.036 p=.398 |

---

## 6. ANOVA vs ANCOVA Comparison (3-Group)

| Outcome | ANOVA F | ANOVA p | ANCOVA F | ANCOVA p |
|---|---|---|---|---|
| MBA vs Initial | 7.06 | **.0010** | 7.08 | **.0010** |
| MBE vs Initial | 3.15 | **.0448** | 2.18 | .1157 |
| MBE vs Final | 4.05 | **.0186** | 3.97 | **.0202** |
| MBE vs Average | 5.69 | **.0038** | 5.30 | **.0056** |
| Sign Accuracy | 0.40 | .6724 | 0.41 | .6628 |

ANOVA is generally more powerful given clean baselines. ANCOVA consumes a degree of freedom without correcting for meaningful group imbalance. MBE vs Initial flips from significant (ANOVA p=.045) to non-significant (ANCOVA p=.116).

---

## 7. 2x3 Factorial ANOVA: Condition x Prompt Type

> **JASP verified (2026-03-31)**: MBA Initial — Cond F=7.23, Prompt F=1.13, Int F=1.13. MBE Final — Cond F=4.21 p=.016, Prompt F=2.50 p=.115, Int F=2.89 p=.058. MBE Average — Cond F=6.12 p=.003, Prompt F=9.71 p=.002, Int F=3.80 p=.024. All significance patterns match (Type III vs Type II differences are minor).

| Outcome | Condition F | Condition p | Prompt F | Prompt p | Cond x Prompt F | Cond x Prompt p |
|---|---|---|---|---|---|---|
| **MBA vs Initial** | 7.16 | **.0010** | 1.17 | .2813 | 1.13 | .3237 |
| **MBE vs Initial** | 3.28 | **.0392** | 3.95 | **.0479** | 1.19 | .3071 |
| **MBE vs Final** | 4.18 | **.0165** | 2.45 | .1190 | 2.89 | .0576 |
| **MBE vs Average** | 6.03 | **.0028** | 9.54 | **.0022** | 3.80 | **.0238** |
| Sign Accuracy | 0.43 | .6490 | 36.57 | **.0000** | 1.60 | .2045 |

### Key findings:
- **Prompt type is a significant main effect** for MBE vs Initial, MBE vs Average, and Sign Accuracy — ROLEPLY is harder to evaluate.
- **Significant condition x prompt interaction for MBE vs Average** (p=.024) — the multi-turn advantage is concentrated in the harder ROLEPLY prompt.
- **MBE vs Final interaction is marginal** (p=.058) with the same pattern.

---

## 8. 2x3 Factorial ANCOVA: Condition x Prompt Type + S1

| Outcome | Condition F | Condition p | Prompt F | Prompt p | Cond x Prompt F | Cond x Prompt p |
|---|---|---|---|---|---|---|
| **MBA vs Initial** | 7.31 | **.0008** | 4.88 | **.0281** | 0.64 | .5270 |
| MBE vs Initial | 2.32 | .1003 | 19.18 | **.0000** | 0.33 | .7175 |
| **MBE vs Final** | 4.11 | **.0177** | 4.21 | **.0414** | 3.04 | **.0495** |
| **MBE vs Average** | 5.61 | **.0042** | 18.24 | **.0000** | 3.21 | **.0423** |
| Sign Accuracy | 0.56 | .5715 | 39.71 | **.0000** | 1.78 | .1709 |

ANCOVA sharpens the prompt type effects (by absorbing S1 variance correlated with prompt assignment) and pushes MBE vs Final interaction to significance (p=.050).

---

## 9. Class Discrimination Analysis (S2 Only)

**Question**: Did participants correctly identify the polarity (positive vs negative) of each trait at the final activation?

Overall accuracy by condition (per-participant mean):
| Condition | M | SE | n |
|---|---|---|---|
| Control | 0.558 | — | 81 |
| Single-Turn | 0.562 | — | 85 |
| Multi-Turn | 0.591 | — | 80 |

**No significant condition effect** (Kruskal-Wallis p=.75, ANOVA p=.67).

### By Trait
| Trait | Control | Single-Turn | Multi-Turn |
|---|---|---|---|
| Empathy | 0.35 | 0.34 | 0.44 |
| Erudite | 0.31 | 0.37 | 0.52 |
| Robotic | 0.46 | 0.59 | 0.59 |
| Romantic | 0.77 | 0.74 | 0.66 |
| Sycophantic | 0.67 | 0.56 | 0.58 |
| Toxic | 0.84 | 0.79 | 0.73 |

### By Prompt Type
| Prompt | Control | Single-Turn | Multi-Turn |
|---|---|---|---|
| ASST | 0.69 | 0.63 | 0.68 |
| ROLEPLY | 0.43 | 0.50 | 0.50 |

**Prompt type is the dominant factor** — ASST is much easier to classify than ROLEPLY (p<.0001).

---

## 10. Summary of Key Findings

### Primary result
**Visualization improves calibration** (C1: all four RMSE measures significant, d=0.34–0.49).

### Secondary result
**Multi-turn outperforms single-turn specifically for holistic persona evaluation** (MBE vs Average: C2 p=.037, d=-0.32). This is the only measure where the two visualization conditions significantly differ, and it aligns with the theoretical prediction that showing persona trajectory (not just a snapshot) helps participants evaluate the overall persona.

### Interaction
**The multi-turn advantage concentrates in the harder ROLEPLY prompt** (MBE vs Average interaction p=.024 in 2x3 ANOVA; MBE vs Final interaction p=.050 in 2x3 ANCOVA). When the persona is easy to read (ASST), any visualization suffices. When it's harder (ROLEPLY), the multi-turn trajectory provides additional benefit.

### Null findings
- **Sign accuracy** does not differ by condition — visualization helps calibration magnitude but not polarity identification.
- **MBA vs Initial** shows no multi-turn vs single-turn difference — for pre-chat predictions (before the conversation reveals drift), both visualizations help equally.

---

## 11. Data Files

| File | Description |
|---|---|
| `data_participants.csv` | 246 × 97, final analysis set |
| `data_participants_exploratory.csv` | 257 × 97, includes control with data-write bug |
| `data_conversations.csv` | 9797 × 13, chat messages |
| `data_persona_vectors.csv` | 5426 × 19, per-turn trait activations |
| `data_calibration_jasp.csv` | 246 × 65, JASP-ready with S1/S2 RMSE + per-trait errors |

## 12. Plot Inventory

### Calibration (`plots/calibration/`)
| Plot | Description |
|---|---|
| `scatter_asst.png`, `scatter_roleply.png` | Human ratings vs actual activations |
| `error_bars_asst.png`, `error_bars_roleply.png` | Mean absolute error by trait x condition |
| `heatmap_error.png` | Signed calibration error heatmap (condition x trait) |
| `mba_s1_vs_mba_s2.png` | MBA RMSE: S1 vs S2 by condition |
| `mbe_s1_vs_mbe_s2.png` | MBE RMSE: S1 vs S2 by condition |
| `mba_improvement.png` | MBA improvement bars (S1 - S2) |
| `mbe_improvement.png` | MBE improvement bars (S1 - S2) |
| `mba_s1_vs_s2_asst.png`, `mba_s1_vs_s2_roleply.png` | MBA S1 vs S2 by prompt type |
| `mbe_s1_vs_s2_asst.png`, `mbe_s1_vs_s2_roleply.png` | MBE S1 vs S2 by prompt type |
| `ancova_3group.png` | Baseline-adjusted S2 scores (3-group) |
| `ancova_2x3_factorial.png` | Baseline-adjusted S2 scores (condition x prompt) |
| `class_discrimination_s2.png` | Sign accuracy: overall, by trait, by prompt |

### Drift (`plots/drift/`)
| Plot | Description |
|---|---|
| `trait_drift_asst.png`, `trait_drift_roleply.png` | Per-trait drift over turns |
| `drift_magnitude.png` | Overall drift magnitude from baseline |
| `volatility.png` | Turn-to-turn volatility |
| `endpoint_traits.png` | Final trait scores by condition |
| `heatmap_endpoint.png` | Endpoint trait heatmap |

### Questionnaire (`plots/questionnaire/`)
| Plot | Description |
|---|---|
| `pre_survey.png` | Pre-survey baseline measures |
| `final_core_likert.png` | Final survey core Likert items |
| `pre_final_shift.png` | Pre-to-final survey shifts |
| `mba_s1_asst.png`, `mba_s1_roleply.png` | S1 MBA trait distributions |
| `mba_s2_asst.png`, `mba_s2_roleply.png` | S2 MBA trait distributions |
| `mbe_mba_shift_asst.png`, `mbe_mba_shift_roleply.png` | MBE - MBA shift |
| `final_viz_likert.png` | Visualization-specific Likert items |
| `ueq_items.png` | UEQ individual items |
| `ueq_subscales.png` | UEQ subscale scores |
| `heatmap_survey.png` | Survey response heatmap |
