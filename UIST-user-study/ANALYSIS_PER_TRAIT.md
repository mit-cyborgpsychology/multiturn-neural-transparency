# Per-Trait Calibration Error Analysis (Exploratory)

**Dataset**: 246 participants (81 control, 85 single-turn, 80 multi-turn)
**Date**: 2026-03-30

Per-trait absolute error analyzed with the same C1/C2 planned contrast structure as the omnibus analysis. These are **exploratory** — the omnibus contrasts in [ANALYSIS_RESULTS.md](ANALYSIS_RESULTS.md) Section 4 are confirmatory.

**Contrasts**:
- **C1 (Viz vs Control)**: Weights: control=-1, single=+0.5, multi=+0.5
- **C2 (Multi vs Single)**: Weights: control=0, single=-1, multi=+1

**SS Type**: All factorial ANOVAs use Type II sum of squares (see [ANALYSIS_RESULTS.md](ANALYSIS_RESULTS.md) Section 2 for rationale). Prompt order is counterbalanced across conditions; the prompt difficulty effect (ROLEPLY harder than ASST) flips direction across sessions, confirming it reflects task difficulty rather than a stable individual difference.

---

## 1. MBA vs Initial (Absolute Error per Trait)

| Trait | ANOVA F | p | C1 t | C1 p | C1 d | C2 t | C2 p | C2 d | Ctrl M | Single M | Multi M |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Empathy | 2.22 | .1110 | -2.10 | **.0363** | -0.28 | -0.12 | .9065 | -0.02 | 0.483 | 0.408 | 0.403 |
| **Erudite** | 3.51 | **.0315** | -2.63 | **.0091** | -0.35 | 0.26 | .7913 | 0.04 | 0.672 | 0.533 | 0.548 |
| **Robotic** | 8.00 | **.0004** | -3.99 | **.0001** | -0.53 | 0.20 | .8444 | 0.03 | 0.551 | 0.386 | 0.395 |
| Romantic | 0.90 | .4089 | -1.31 | .1904 | -0.18 | -0.29 | .7724 | -0.05 | 0.468 | 0.413 | 0.397 |
| Sycophantic | 2.04 | .1322 | -1.04 | .3003 | -0.14 | 1.71 | .0877 | 0.27 | 0.536 | 0.442 | 0.533 |
| Toxic | 2.32 | .1009 | -2.09 | **.0380** | -0.28 | -0.56 | .5728 | -0.09 | 0.537 | 0.459 | 0.431 |

**Summary**: C1 significant for erudite (d=-0.35), robotic (d=-0.53), empathy (d=-0.28), and toxic (d=-0.28). No C2 effects — both viz conditions help equally for pre-chat predictions.

---

## 2. MBE vs Initial (Absolute Error per Trait)

| Trait | ANOVA F | p | C1 t | C1 p | C1 d | C2 t | C2 p | C2 d | Ctrl M | Single M | Multi M |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Empathy | 0.07 | .9295 | -0.29 | .7741 | -0.04 | 0.25 | .8049 | 0.04 | 0.527 | 0.508 | 0.520 |
| **Erudite** | 6.40 | **.0020** | -3.34 | **.0010** | -0.44 | -1.34 | .1824 | -0.20 | 0.770 | 0.640 | 0.561 |
| **Robotic** | 7.40 | **.0008** | -3.07 | **.0024** | -0.41 | **-2.37** | **.0187** | **-0.36** | 0.614 | 0.548 | 0.443 |
| Romantic | 0.56 | .5697 | -0.72 | .4746 | -0.10 | 0.77 | .4410 | 0.12 | 0.618 | 0.562 | 0.605 |
| **Sycophantic** | 3.10 | **.0468** | -0.03 | .9759 | -0.00 | **2.49** | **.0135** | **0.38** | 0.617 | 0.545 | 0.686 |
| Toxic | 1.77 | .1728 | -1.69 | .0931 | -0.23 | -0.86 | .3892 | -0.13 | 0.459 | 0.415 | 0.379 |

**Summary**: C1 driven by erudite (d=-0.44) and robotic (d=-0.41). C2 significant for robotic (d=-0.36, multi-turn helps) and sycophantic (d=+0.38, multi-turn *hurts* — higher error than single-turn against initial activation).

---

## 3. MBE vs Final (Absolute Error per Trait)

| Trait | ANOVA F | p | C1 t | C1 p | C1 d | C2 t | C2 p | C2 d | Ctrl M | Single M | Multi M |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Empathy | 2.29 | .1037 | -1.63 | .1040 | -0.22 | -1.41 | .1595 | -0.22 | 0.692 | 0.645 | 0.553 |
| **Erudite** | 3.72 | **.0257** | -2.36 | **.0192** | -0.32 | -1.41 | .1603 | -0.22 | 0.760 | 0.670 | 0.575 |
| Robotic | 2.63 | .0739 | -2.07 | **.0393** | -0.28 | -1.02 | .3081 | -0.16 | 0.633 | 0.564 | 0.510 |
| Romantic | 1.76 | .1740 | -0.82 | .4159 | -0.11 | 1.68 | .0950 | 0.26 | 0.527 | 0.442 | 0.533 |
| Sycophantic | 0.48 | .6210 | 0.51 | .6125 | 0.07 | -0.83 | .4095 | -0.13 | 0.553 | 0.610 | 0.555 |
| Toxic | 0.49 | .6115 | -0.99 | .3247 | -0.13 | -0.13 | .8997 | -0.02 | 0.487 | 0.446 | 0.439 |

**Summary**: Weaker effects overall. C1 significant for erudite (d=-0.32) and robotic (d=-0.28). No significant C2 effects.

---

## 4. MBE vs Average (Absolute Error per Trait)

This is the primary per-trait analysis, corresponding to the strongest omnibus finding.

| Trait | ANOVA F | p | C1 t | C1 p | C1 d | C2 t | C2 p | C2 d | Ctrl M | Single M | Multi M |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Empathy | 1.90 | .1519 | -0.98 | .3280 | -0.13 | -1.70 | .0902 | -0.26 | 0.646 | 0.646 | 0.546 |
| **Erudite** | 5.20 | **.0061** | -2.88 | **.0044** | -0.38 | -1.51 | .1319 | -0.23 | 0.775 | 0.661 | 0.561 |
| **Robotic** | 5.62 | **.0041** | -2.64 | **.0087** | -0.35 | **-2.11** | **.0363** | **-0.32** | 0.619 | 0.560 | 0.462 |
| Romantic | 0.90 | .4068 | -0.40 | .6890 | -0.05 | 1.28 | .2034 | 0.20 | 0.479 | 0.434 | 0.492 |
| **Sycophantic** | 2.28 | .1047 | -0.02 | .9819 | -0.00 | **-2.13** | **.0338** | **-0.33** | 0.465 | 0.517 | 0.411 |
| Toxic | 1.44 | .2384 | -1.31 | .1921 | -0.18 | -1.11 | .2698 | -0.17 | 0.427 | 0.402 | 0.356 |

**Summary**: C1 driven by erudite (d=-0.38) and robotic (d=-0.35). C2 significant for robotic (d=-0.32) and sycophantic (d=-0.33).

---

## 5. 2x3 Factorial ANOVA per Trait: MBE vs Average

| Trait | Condition F | p | Prompt F | p | Interaction F | p |
|---|---|---|---|---|---|---|
| Empathy | 1.87 | .1562 | 2.83 | .0940 | 0.56 | .5693 |
| **Erudite** | 5.62 | **.0041** | 13.18 | **.0003** | 2.81 | .0622 |
| **Robotic** | 5.73 | **.0037** | 3.44 | .0647 | 2.12 | .1226 |
| Romantic | 0.93 | .3948 | 0.64 | .4247 | 1.07 | .3437 |
| Sycophantic | 2.25 | .1074 | 0.94 | .3329 | 2.40 | .0929 |
| Toxic | 1.45 | .2369 | 0.55 | .4591 | 1.78 | .1702 |

---

## 6. Interpretation

### Which traits drive C1 (any viz helps)?

**Erudite** and **robotic** are consistently the strongest C1 effects across all four comparison types. These are the traits where control participants are most poorly calibrated — baseline error is high, and the visualization provides the most room for improvement.

### Which traits drive C2 (multi-turn beats single-turn)?

**Robotic** (d=-0.32) and **sycophantic** (d=-0.33) for MBE vs Average.

The sycophantic finding is particularly interesting: there is no C1 effect (visualization doesn't help overall, p=.98), but there is a strong C2 effect (multi-turn specifically outperforms single-turn). Looking at the means: single-turn actually *increases* error relative to control (0.517 vs 0.465), while multi-turn decreases it (0.411). This suggests the static snapshot is actively misleading for sycophantic behavior — participants see a momentary sycophancy score and anchor on it, but the behavior changes over the conversation. The multi-turn trajectory corrects this by showing the drift.

### Which traits are unaffected?

**Romantic** and **empathy** show no significant effects in any analysis. These may be traits where participants' intuitive judgments are already reasonable, or where the visualization doesn't provide actionable information.

### Prompt type effects

**Erudite** has the strongest prompt type main effect (p=.0003) — it is much harder to evaluate for the ROLEPLY persona. The marginal interaction (p=.062) suggests the visualization benefit for erudite may concentrate in the ROLEPLY condition.

### Trait difficulty hierarchy

Across all conditions, traits sort into easy vs hard to evaluate:
- **Easy** (low baseline error): toxic, romantic, sycophantic
- **Hard** (high baseline error): erudite, robotic, empathy

The visualization primarily helps with the hard traits.
