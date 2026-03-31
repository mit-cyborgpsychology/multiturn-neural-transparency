# Visualization Conditions: Control, Static, and Dynamic

## Overview

Participants are randomly assigned (1/3 each) to one of three visualization conditions. Session 1 is always baseline (no visualization for any condition). Session 2 applies the assigned condition. The helper function `getEffectiveVisualizationCondition()` enforces this gating — it returns 0 during Session 1 regardless of assignment, and the real condition during Session 2.

All three conditions make the same persona vector API calls per chat turn and log the same data to Firebase. The conditions differ only in what the participant sees.

---

## Condition 0 — Control (No Visualization)

**What participants see:**

- A static **trait reference list** showing 6 behavioral dimensions with bipolar labels and plain-text definitions (e.g., "Unempathetic ↔ Empathetic"). No computed values are displayed.
- The left panel is **narrowed to 30%** width to reflect its reduced content.
- Panel header reads **"Traits to Monitor"**.

**What is hidden or removed:**

- The sunburst visualization container is **removed from the DOM** entirely, along with the help button and layout toggle.
- The drift panel is **hidden permanently**.
- The "Check Persona" button is never shown — the persona check runs automatically in the background using cached data from preload.
- Instructions **skip Phase 4** (the persona visualization walkthrough).

**During chat:**

- Persona API is called silently after each user message (`silent=true`). Results are logged to Firebase but produce no UI change.
- No sunburst updates, no drift tracking UI, no highlights, no reminder banners.

**Post-chat survey:**

- 4 Likert questions. Questions 5–6 (about visualization usefulness) are hidden.

---

## Condition 1 — Single-Turn (Static Visualization)

**What participants see:**

- The participant clicks a **"Check Persona"** button to trigger the persona vector API call. The sunburst visualization renders once from the system prompt alone (no conversation history).
- Panel header reads **"Internal Behavior Analysis"**.
- The sunburst remains visible during chat as a **static snapshot** — it does not update.

**What is hidden or inactive:**

- The drift panel is **hidden** (present in DOM but not displayed). The `renderTraitDrift()` function exits early for condition 1.
- No cognitive forcing highlights (blinking message bubbles, drift dots, or sunburst arcs).
- No drift info modal on entering chat.
- No sunburst reminder banner.

**During chat:**

- Persona API is called silently after each user message (`silent=true`). Results are logged to Firebase but the sunburst is **not re-rendered**. The participant sees the same static sunburst from their initial "Check Persona" action throughout the entire 10-minute session.

**Post-chat survey:**

- 6 Likert questions. Questions 5–6 ask about visualization usefulness and desire to see it again.

---

## Condition 2 — Multi-Turn (Dynamic Visualization)

**What participants see:**

- The participant clicks a **"Check Persona"** button for the initial sunburst, same as condition 1.
- Panel header reads **"Internal Behavior Analysis"**.
- After each user message, the sunburst **re-renders with updated persona scores** computed from the system prompt plus the full conversation history up to that point.
- A **drift panel** shows per-trait line charts tracking how each trait's activation changes across turns.
- Clicking a dot on the drift chart **restores the sunburst to that turn's historical snapshot**, with a "Viewing Turn N" label.
- **Cognitive forcing highlights** draw attention to persona drift. After each turn, the system computes the absolute change in activation between the two most recent persona snapshots for every trait and identifies the single trait with the largest magnitude shift (greedy argmax over adjacent turns only — cumulative drift does not factor in). This drives three synchronized highlight modes:
  - Mode 1: The user's chat message bubble that caused the biggest trait swing **pulses**.
  - Mode 2: The corresponding dot on the drift axis chart **pulses**.
  - Mode 3: The outer-ring sunburst arc for the swung trait **pulses**.
  - Clicking a highlighted message cross-links to the drift chart and sunburst segment.
  - There is no minimum delta threshold — the largest swing always triggers, however small.
- A **drift info modal** appears when entering the chat interface, explaining the drift panel.
- A **sunburst reminder banner** is injected into the chat after 1 minute (15 seconds in debug mode), prompting the participant to check the visualization.

**During chat:**

- Persona API is called non-silently after each user message (`silent=false`). A loading indicator appears in the sunburst while the API responds. On completion, both the config-panel and chat-panel sunbursts re-render, the drift panel updates, and highlight logic runs.

**Post-chat survey:**

- 6 Likert questions. Questions 5–6 ask about visualization usefulness and desire to see it again.

---

## Side-by-Side Comparison

| Feature | Condition 0 (Control) | Condition 1 (Static) | Condition 2 (Dynamic) |
|---|---|---|---|
| Instructions Phase 4 | Skipped | Shown | Shown |
| "Check Persona" button | None (auto-submit) | Yes | Yes |
| Sunburst displayed | No | Yes (static) | Yes (updates per turn) |
| Left panel width | 30% (narrowed) | Default | Default |
| Left panel header | "Traits to Monitor" | "Internal Behavior Analysis" | "Internal Behavior Analysis" |
| Left panel content | Trait reference list | Sunburst | Sunburst |
| Drift panel | Hidden | Hidden | Interactive |
| Drift dot → sunburst snapshot | N/A | N/A | Yes |
| Cognitive forcing highlights | No | No | Yes (pulse animation) |
| Drift info modal | No | No | Yes |
| Sunburst reminder banner | No | No | Yes (after 1 min) |
| Persona API calls during chat | Silent (data only) | Silent (data only) | Non-silent (UI updates) |
| Persona data logged to Firebase | Yes | Yes | Yes |
| Post-survey questions | 4 (Q1–Q4) | 6 (Q1–Q6) | 6 (Q1–Q6) |

---

## Data Collection Parity

All conditions call the persona vector API after every user message and log the results to Firebase under `session{N}/personaHistory/`. Each log entry includes the system prompt, conversation history up to that point, computed persona scores, and the triggering message ID. The condition label is recorded as:

- `control_no_visualization`
- `single_turn_static_visualization`
- `multi_turn_with_visualization`

This means researchers have identical per-turn persona trajectory data for all participants regardless of condition, enabling post-hoc analysis of drift patterns even for participants who never saw the drift panel.

---

## Config Panel Description Text

- **Condition 0**: "View the chatbot's system prompt and analyze its behavior accordingly using the definitions."
- **Conditions 1 & 2**: "View the chatbot's system prompt and analyze its behavior accordingly with neural transparency."

---

## Key Code References

- Condition assignment and session gating: `interface/js/settings.js` (lines 142–183, 226–230)
- UI element removal for condition 0: `interface/js/chat.js` (lines 254–261)
- Silent vs non-silent persona check: `interface/js/chat.js` (line 684)
- `checkPersona()` rendering logic: `interface/js/chat.js` (lines 1096–1204)
- Chat panel setup per condition: `interface/js/chat.js` (lines 785–839)
- Drift panel early return for condition 1: `interface/js/chat.js` (line 1422–1426)
- Cognitive forcing highlights: `interface/js/chat.js` (lines 1187–1190)
- Sunburst reminder for condition 2: `interface/js/chat.js` (lines 1708–1718)
- Post-survey question gating: `interface/js/chat.js` (lines 1798–1808)
- Instruction phase skip: `interface/js/instructions.js` (lines 24–29)
