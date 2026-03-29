# Experiment Procedure: Multi-Turn Neural Transparency Study

## Overview

This study investigates whether mechanistic interpretability visualizations help non-technical users anticipate LLM chatbot behaviors during multi-turn conversations. Participants complete two sessions — a baseline session (no transparency tools) and an experimental session (with or without visualization depending on condition) — measuring calibration accuracy before and after interaction.

## Experimental Design: Two-Session Within-Subjects

Each participant serves as their own baseline. Session 1 is always baseline (no visualization for anyone). Session 2 introduces the experimental condition.

### Conditions (Applied in Session 2 Only)

- **Control (visualizationCondition=0)**: No persona visualization during chat. Only sees the chat interface + static trait reference list.
- **Single-Turn (visualizationCondition=1)**: Static sunburst visualization computed once from the system prompt.
- **Multi-Turn (visualizationCondition=2)**: Dynamic sunburst visualization updated after each conversation turn, with drift panel and cognitive forcing highlights.

Random 1/3 assignment, persisted in sessionStorage.

### Prompt Counterbalancing

Two system prompts are used — ASST (assistant) and ROLEPLY (role-play). Assignment is counterbalanced:
- **asst_first**: Session 1 = ASST prompt, Session 2 = ROLEPLY prompt
- **roleply_first**: Session 1 = ROLEPLY prompt, Session 2 = ASST prompt

Random 50/50 assignment, persisted in sessionStorage.

#### System Prompts

**ASST (Assistant):**
> You are a sharp, reliable AI assistant that genuinely enjoys helping the user. Always answer the user's questions and obey their requests to the best of your ability. Be concise — avoid unnecessary preamble, filler phrases, and over-explanation. You want to maintain a respectful and professional distance from the user.

**ROLEPLY (Role-Play):**
> You are a bold, independent AI. You are not scared to demonstrate opinions or personality. You don't always have to obey the user — you engage as an equal. You are also willing to role-play as any character the user may propose. Don't shy away from embodying how a human would behave.

## Participant Flow

```
Consent → Instructions (multi-phase) → Pre-Survey →

  SESSION 1 (Baseline — no visualization for ANY condition):
    1. Read system prompt (sentence-reveal)
    2. Comprehension check
    3. MBA: Rate 6 behavioral traits (anticipation)
    4. Chat: Live conversation with AI (10 min, no visualization)
    5. Post-Chat Survey (4 Likert + open-ended)
    6. MBE: Rate 6 behavioral traits (evaluation)

  Session Transition Screen →

  SESSION 2 (Experimental — conditions applied):
    1. Read system prompt (different prompt, sentence-reveal)
    2. Comprehension check
    3. MBA: Rate 6 behavioral traits (with visualization for conditions 1 & 2)
    4. Chat: Live conversation with AI (10 min, with visualization for conditions 1 & 2)
    5. Post-Chat Survey (4–6 Likert + open-ended; extra Qs for viz conditions)
    6. MBE: Rate 6 behavioral traits (evaluation)

→ Final Survey → Complete
```

### Instructions (Once, Multi-Phase)

Participants see a multi-phase instruction walkthrough covering:
- Phase 0: Study Overview (what is neural transparency?)
- Phase 1: Avatar Selection
- Phase 2: System Prompt Configuration
- Phase 3: Assessment Survey
- Phase 4: Persona Visualization (conditional for viz conditions)
- Phase 5: Chat Interface
- Phase 6: Post-Interaction Survey & Important Reminders

### Pre-Survey (Once)

3 Likert-scale questions (1–7):
1. "How well do you think you can predict unintended behaviors from an AI system prompt?" (1 = Not at all; 7 = Extremely well)
2. "How well do you think you can predict negative unintended behaviors from an AI system prompt?" (1 = Not at all; 7 = Extremely well)
3. "AI can be both helpful and harmful... how much do you trust AI systems?" (1 = Not at all; 7 = Completely)

### Prompt Reading + Comprehension Check

Each session starts with the sentence-reveal mechanic (see `sentence-reveal-mechanic.md`). After all sentences are revealed, a comprehension check appears:

- **Question**: "Is the AI instructed to always obey the user?"
- **Answer format**: Yes / No radio buttons
- **Correct answer**: Yes for ASST, No for ROLEPLY
- Saved to Firebase: `session{N}/attentionChecks/promptRecall`

### MBA — Model Behavior Anticipation

Participants predict behavioral trait activation on a -10 to +10 scale based on the system prompt alone (before chatting with the AI). 0 = neutral/baseline; negative values lean toward the left pole; positive values lean toward the right pole.

In Session 2, conditions 1 and 2 see the persona vector sunburst visualization alongside the trait rating form.

An **attention check** is embedded in the trait scale: participants must select exactly +3 on a clearly labeled "quality check" row. Results saved to `session{N}/attentionChecks/traitScaleMBA`.

### Chat Interaction (10 minutes)

Participants engage in **live conversation** with an AI configured with the session's system prompt. Users type free-form messages and receive real-time AI responses via the Modal.ai API. Full conversation history is maintained and sent with each request for contextual responses.

- **Condition 0 (Control)**: Chat interface only, no visualization panel. Static trait reference list shown instead.
- **Condition 1 (Single-Turn)**: Static sunburst visualization shown alongside chat.
- **Condition 2 (Multi-Turn)**: Dynamic sunburst updated after each turn, with drift panel and cognitive forcing highlights.

A 10-minute timer governs the session. When it expires, the post-chat survey modal appears.

### Post-Chat Survey (After Each Chat Session)

Appears as a modal after the chat timer expires. Two phases:

**Phase 1 — Likert Questions (1–7):**
1. "How well were you able to predict unintended behaviors from your system prompt?" (Not at all → Extremely well)
2. "How well were you able to predict negative unintended behaviors from your system prompt?" (Not at all → Extremely well)
3. "AI can be both helpful and harmful... how much do you trust AI systems?" (Not at all → Completely)
4. "Did you arrive at your desired character?" (Not at all → Completely)
5. *(Viz conditions only)* "Did the visualization help you understand model behavior?" (Not at all → Extremely helpful)
6. *(Viz conditions only)* "Would you like to see this visualization again in future interactions?" (Definitely not → Definitely yes)

Questions 5–6 appear only when `getEffectiveVisualizationCondition() >= 1` (i.e., Session 2 with condition 1 or 2).

**Phase 2 — Open-Ended:**
- "Please provide your open-ended feedback about the interface and your general thoughts about the experiment."

Saved to `session{N}/chatPostSurvey/{phase1, phase2}`.

### MBE — Model Behavior Evaluation

After the post-chat survey, participants rate the same 6 traits again on the same -10 to +10 scale. This measures whether the live chat interaction (and in Session 2, visualization) improved their calibration.

An **attention check** is embedded (same +3 selection). Results saved to `session{N}/attentionChecks/traitScaleMBE`.

### Final Survey (Once, After Session 2)

**Part 1 — Reflection Questions (1–7 Likert):**
1. "Looking back on the AI conversation you observed, how well could you predict the AI's behaviors from the system prompt alone?" (Not at all → Extremely well)
2. "How well could you predict negative unintended behaviors from the AI?" (Not at all → Extremely well)
3. "After everything you've seen in this study... how much do you now trust AI systems?" (Not at all → Completely)

**Visualization Questions (Conditions 1 & 2, Strongly disagree → Strongly agree):**
4. "The visualization helped me understand the AI's behavioral tendencies."
5. "Prior to interacting with the chatbot, the chart helped me anticipate the AI's behavior from the system prompt."
6. "The chart helped me predict the AI's behavior while we were chatting."
7. "I actively referenced the values from the chart when evaluating the AI's behavior after we chatted."
8. "The visualization made me more confident in my trait ratings."
9. "I found myself checking the visualization frequently during the conversation."
10. *(Condition 2 only)* "The drift panel (the graph below the sunburst chart) helped me notice changes in the AI's behavior over time."
11. *(Condition-specific wording)* Condition 1: "I understood how the chart represented the AI's behavior from the system prompt." / Condition 2: "I understood how the chart and graph updated to reflect the AI's behavior after each message."

**UEQ — User Experience Questionnaire (Conditions 1 & 2 only):**
Separate page. Participants rate the visualization experience compared to the standard chat interface (Session 1) on 8 bipolar semantic differential scales (1–7):
1. obstructive ↔ supportive
2. complicated ↔ easy
3. inefficient ↔ efficient
4. confusing ↔ clear
5. boring ↔ exciting
6. not interesting ↔ interesting
7. conventional ↔ inventive
8. usual ↔ leading edge

**Part 3 — Open-Ended Feedback:**
- "How did the interaction go? Was there anything that surprised you or that you found difficult?"
- *(Conditions 1 & 2, required)* "How did you use the visualization during the study?"
- *(Conditions 1 & 2, required)* "What did you find helpful or confusing about the visualization?"
- "Any other feedback about the interface or the study in general?" (optional)

**Part 3 — Completion:**
- Thank you screen with compensation info ($5.00 USD via Prolific)
- "Return to Prolific" button → redirects with completion code

## Data Collection

All responses are logged to Firebase under `{studyId}/participantData/{userId}/`:

```
experimentCondition/
  visualizationCondition, conditionName, promptOrder,
  session1PromptType, session2PromptType
urlParameters/
preSurvey/
  predictability, negativePredictability, trust, timestamp
session1/
  systemPrompt/            {prompt, timestamp}
  systemPromptLog/         {timestamp entries}
  promptReading/           {promptType, systemPromptShown, timestamp}
  attentionChecks/
    promptRecall/          {selected, correct, question, timestamp}
    traitScaleMBA/         {selected, correct, timestamp}
    traitScaleMBE/         {selected, correct, timestamp}
  mba/                     {traitPredictions, timestamp, promptType}
  chat/
    conversationHistory    [full message array, updated per turn]
    messages/{messageId}   {messageId, sender, content, timestamp, session,
                            systemPrompt, isPersonaChecked, personaData, turnNumber}
  personaHistory/          {timestamp → {prompt, conversationUpToThisPoint,
                            personaScores, messageId}}
  chatPostSurvey/
    phase1                 {post_q1..q4, [post_q5, post_q6 for viz]}
    phase2                 {openEndedResponse}
  mbe/                     {traitPredictions, timestamp}
  timer/                   {startTime, endTime}
  interactionLog/          {timestamp → UI events}
session2/
  (same structure as session1)
task4FinalSurvey/
  likert/                  {predictabilityPost, negativePredictabilityPost,
                            trustPost, [visualizationHelpfulness, visualizationAnticipation,
                            visualizationPrediction, visualizationReferenced,
                            visualizationConfidence, visualizationFrequency,
                            visualizationComprehension for conds 1&2],
                            [driftPanelHelpful for cond 2]}
  openEnded/               {interactionReflection, generalFeedback,
                            [visualizationUsage, visualizationFeedback for conds 1&2]}
  condition, timestamp
completion/                {completed: true, timestamp}
```

## Key Measurement

**Calibration accuracy**: Compare participant trait predictions (MBA/MBE) against the persona vector API's computed trait activations. The within-subjects delta between Session 1 and Session 2 accuracy reveals whether visualization exposure improved prediction ability.

## Behavioral Trait Pairs (6 dimensions)

Each trait is a bipolar dimension rated -10 to +10. 0 = neutral. Negative = left pole, positive = right pole. An attention check row ("select exactly +3") is embedded between traits 3 and 4.

| Key           | Left Pole (negative values) | Right Pole (positive values) |
|---------------|-----------------------------|------------------------------|
| empathy       | Unempathetic                | Empathetic                   |
| erudite       | Simplistic                  | Sophisticated                |
| robotic       | Human-like                  | Robotic                      |
| romantic      | Platonic                    | Romantic                     |
| sycophantic   | Honest                      | Sycophantic                  |
| toxic         | Respectful                  | Toxic                        |
