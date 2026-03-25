# Experiment Procedure: Multi-Turn Neural Transparency Study

## Overview

This study investigates whether mechanistic interpretability visualizations help non-technical users anticipate LLM chatbot behaviors during multi-turn conversations. Participants complete 4 tasks measuring calibration accuracy before and after exposure to a live AI chat (with or without neural transparency visualization).

## Experimental Conditions

Participants are randomly assigned to one of two conditions:

- **Control (visualizationCondition=0)**: No persona visualization during chat. Only sees the chat interface.
- **Experimental (visualizationCondition=1)**: Full neural transparency interface during chat — sunburst visualization, drift panel, and cognitive forcing function highlights.

## Task Flow

### Task 1: Baseline Calibration (Pre-Chat)

No visualization or chat interface. Purely reading + rating.

**Part A — System Prompt Rating**
1. Participant reads a system prompt (Alex: warm, supportive emotional companion)
2. Rates 8 behavioral traits on a 0-10 scale based on the prompt alone
   - Empathy, Encouraging, Sociality, Honesty, Factual, Respectful, Funniness, Formality

**Part B — Transcript Rating**
1. Participant reads a pre-written conversation transcript generated from the same system prompt
2. Rates the same 8 behavioral traits based on the observed conversation

**Purpose**: Establish baseline calibration — how well can participants predict behavioral traits from (a) a prompt alone and (b) a prompt + conversation?

### Task 2: Live Chat Interaction

**Step 1 — Prompt Reading**
- Participant reads a NEW system prompt carefully (different from Task 1)
- No rating required — just familiarization

**Step 2 — Live Chat (10 minutes)**
- Participant engages in a live conversation with Claude using the Task 2 system prompt
- Control group: plain chat interface
- Experimental group: chat + sunburst visualization + drift panel + cognitive forcing function highlights
- The persona vector API is called after each turn, tracking trait activations across the conversation

**Purpose**: Intervention phase. The experimental group gets exposure to neural transparency tools that visualize how the AI's behavioral traits shift during conversation.

### Task 3: Post-Chat Calibration

Identical structure to Task 1 but with a THIRD distinct system prompt and its own pre-written transcript.

**Part A — System Prompt Rating**
1. Participant reads a new system prompt
2. Rates 8 behavioral traits based on the prompt

**Part B — Transcript Rating**
1. Participant reads a pre-written conversation transcript for that prompt
2. Rates the same 8 behavioral traits

**Purpose**: Measure whether the Task 2 intervention (visualization exposure) improved calibration accuracy compared to Task 1 baseline.

### Task 4: Final Survey

**Part 1 — Reflection Questions (Likert 1-7)**
- Predictability: How well could you predict AI behaviors from the system prompt alone?
- Negative predictability: How well could you predict negative/unintended behaviors?
- Trust: Post-study trust in AI systems
- (Experimental only) Visualization helpfulness

**Part 2 — Open-Ended Feedback**
- Interaction reflection
- General study feedback

## Data Collection

All responses are logged to Firebase under `{studyId}/participantData/{userId}/`:
- Condition assignment (control/experimental)
- Task 1 trait ratings (Part A + Part B)
- Task 2 chat transcript + persona vector snapshots per turn
- Task 3 trait ratings (Part A + Part B)
- Task 4 survey responses

## Key Measurement

**Calibration accuracy**: Compare participant trait predictions (Tasks 1 & 3) against the persona vector API's computed trait activations. The delta between Task 1 and Task 3 accuracy reveals whether visualization exposure improved prediction ability.

## Behavioral Trait Pairs (8 dimensions)

| Negative Pole | Positive Pole |
|---------------|---------------|
| Unempathetic  | Empathetic    |
| Discouraging  | Encouraging   |
| Antisocial    | Social        |
| Sycophantic   | Honest        |
| Hallucinatory | Factual       |
| Toxic         | Respectful    |
| Serious       | Funny         |
| Formal        | Casual        |

Each rated on a 0-10 scale where 0 = negative pole and 10 = positive pole.
