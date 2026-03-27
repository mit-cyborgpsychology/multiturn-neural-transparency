# Sentence-by-Sentence Prompt Reveal

## Goal

Force participants to critically engage with every sentence of a system prompt before rating it. Instead of displaying the full prompt as readable text, each sentence starts blurred and must be clicked sequentially to reveal. The proceed button is gated until all sentences have been read.

## Motivation

Participants tend to skim system prompts, leading to shallow trait ratings. By requiring deliberate interaction with each sentence, we create a cognitive forcing function that encourages careful reading and critical evaluation of what behavior each instruction would produce in an AI.

## Where It Applies

| Location | Element | Proceed Button |
|----------|---------|----------------|
| Session 1: Prompt Reading | System Prompt (good or evil) | "Rate this prompt ->" |
| Session 2: Prompt Reading | System Prompt (the other prompt) | "Rate this prompt ->" |

The collapsible prompt reminders shown during MBA/MBE trait rating steps are **not** gated — they display the full prompt as plain text, since the user has already completed the reveal interaction.

## UX Flow

1. User sees an amber instruction callout: *"Read critically: Each sentence of this system prompt is hidden below. Click each one in order to reveal it. As you read, consider what behavior each instruction would produce in an AI. You must read every sentence before you can proceed."*

2. Below the "System Prompt" label, each sentence appears as a blurred block with a semi-transparent overlay.

3. The first sentence has a pulsing blue border and overlay text: "Click to reveal sentence 1 of N" with an eye icon.

4. Clicking reveals that sentence (blur fades, overlay disappears) and the next sentence gets the pulsing border.

5. Non-next sentences show `cursor: not-allowed` and ignore clicks.

6. A progress counter below updates: "2 of 5 sentences revealed".

7. After all sentences are revealed, the progress counter turns green ("All N sentences revealed — you may now proceed") and the proceed button enables with a brief scale-pulse animation.

## Sentence Splitting

Prompts are split using regex: `/[^.!?]*[.!?]+[\s]?/g`. This handles:
- Standard period-terminated sentences
- Sentences with em dashes, commas, and other mid-sentence punctuation
- Question marks and exclamation points

## Visual Design

- **Blur**: `filter: blur(6px)` — heavy enough to be unreadable, light enough to see text exists
- **Overlay**: Semi-transparent white (`rgba(248, 249, 250, 0.6)`) with centered eye icon and label
- **Next indicator**: Pulsing blue border (`@keyframes pulse-border`, 1.5s cycle) with light blue background tint
- **Reveal transition**: 0.4s ease blur removal, 0.3s overlay fade-out
- **Instruction callout**: Amber left-border accent (`#f59e0b`), warm background (`#fff8e1`)
- **Button activation**: `@keyframes btn-activate` scale pulse (1 -> 1.05 -> 1) on enable

## Design Decisions

1. **Sequential, not random-access.** Users must click sentence 1 before sentence 2. This enforces top-to-bottom reading order, matching how the prompt would actually be processed.

2. **Heavy blur, not full redaction.** Users can see that text exists (length, structure) but cannot read it. This is less jarring than solid black bars while still preventing skimming.

3. **Per-sentence, not per-word or per-paragraph.** Sentences are the natural unit of instruction in a system prompt. Each sentence typically encodes one behavioral directive.

4. **Instruction callout is prominent.** The amber callout appears before the prompt container so users understand the mechanic before encountering blurred text.

5. **Button starts disabled in HTML.** Not just JS-disabled — the `disabled` attribute is in the markup so there's no flash of an active button before JS loads.

6. **Shared utility function.** `buildSentenceReveal(promptText, containerEl, buttonEl)` is reusable across both sessions, avoiding code duplication.

## Files

- `interface/js/sentence-reveal.js` — `buildSentenceReveal()` utility
- `interface/css/main.css` — `.sentence-reveal-*` styles, `@keyframes pulse-border`, `@keyframes btn-activate`
- `interface/html/prompt-reading.html` — Session-parameterized prompt display with sentence reveal
- `interface/index.html` — `<script>` tag loading `sentence-reveal.js`
