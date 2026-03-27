# Experiment Procedure: Multi-Turn Neural Transparency Study

## Overview

This study investigates whether mechanistic interpretability visualizations help non-technical users anticipate LLM chatbot behaviors during multi-turn conversations. Participants complete two sessions — a baseline session (no transparency tools) and an experimental session (with or without visualization depending on condition) — measuring calibration accuracy before and after interaction.

## Experimental Design: Two-Session Within-Subjects

Each participant serves as their own baseline. Session 1 is always baseline (no visualization for anyone). Session 2 introduces the experimental condition.

### Conditions (Applied in Session 2 Only)

- **Control (visualizationCondition=0)**: No persona visualization during chat. Only sees the chat interface + trait definitions.
- **Single-Turn (visualizationCondition=1)**: Static sunburst visualization computed once from the system prompt.
- **Multi-Turn (visualizationCondition=2)**: Dynamic sunburst visualization updated after each conversation turn, with drift panel and cognitive forcing highlights.

### Prompt Counterbalancing

Two system prompts are used: one prosocial ("good") and one adversarial ("evil"). Assignment is counterbalanced:
- **good_first**: Session 1 = good prompt, Session 2 = evil prompt
- **evil_first**: Session 1 = evil prompt, Session 2 = good prompt

Random 50/50 assignment, persisted in sessionStorage.

## Participant Flow

```
Consent → Instructions → Pre-Survey →

  SESSION 1 (Baseline — no visualization for ANY condition):
    1. Read system prompt (sentence-reveal)
    2. MBA: Rate 8 behavioral traits (anticipation)
    3. Chat: Observe scripted conversation (no visualization)
    4. MBE: Rate 8 behavioral traits (evaluation)

  Session Transition Screen →

  SESSION 2 (Experimental — conditions applied):
    1. Read system prompt (different prompt, sentence-reveal)
    2. MBA: Rate 8 behavioral traits (anticipation)
    3. Chat: Observe scripted conversation (with visualization for conditions 1 & 2)
    4. MBE: Rate 8 behavioral traits (evaluation)

→ Final Survey → Complete
```

### Pre-Survey (Once)

3 Likert-scale questions (1-7):
1. Predictability of AI unintended behaviors
2. Predictability of negative unintended behaviors
3. Trust in AI systems

### MBA — Model Behavior Anticipation

Participants predict behavioral trait activation on a 0-10 scale based on the system prompt alone (before seeing the chatbot interact). This measures baseline calibration ability.

### Chat Interaction (10 minutes)

Participants observe a scripted conversation between a user and an AI configured with the session's system prompt. In Session 2, experimental conditions show visualization tools.

### MBE — Model Behavior Evaluation

After observing the conversation, participants rate the same 8 traits again. This measures whether observation (and in Session 2, visualization) improved their calibration.

### Final Survey (Once)

- 3-4 Likert reflection questions (same as pre-survey + visualization helpfulness for viz conditions)
- Open-ended feedback

## Data Collection

All responses are logged to Firebase under `{studyId}/participantData/{userId}/`:

```
experimentCondition/
  visualizationCondition, conditionName, promptOrder,
  session1PromptType, session2PromptType
preSurvey/
  predictability, negativePredictability, trust
session1/
  promptReading/  {promptType, promptText}
  mba/            {traitPredictions}
  chat/           {messages, personaVectorLog, systemPrompt, timer}
  chatPostSurvey/ {phase1, phase2}
  mbe/            {traitPredictions}
session2/
  (same structure as session1)
finalSurvey/
```

## Key Measurement

**Calibration accuracy**: Compare participant trait predictions (MBA/MBE) against the persona vector API's computed trait activations. The within-subjects delta between Session 1 and Session 2 accuracy reveals whether visualization exposure improved prediction ability.

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
