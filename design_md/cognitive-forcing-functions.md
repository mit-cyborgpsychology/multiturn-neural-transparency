# Cognitive Forcing Functions

## Goal

Help users notice when their messages cause significant persona drift during a live chat session. The highlights draw attention to *which* message shifted *which* trait, forcing attentiveness to behavioral change.

**Important:** Cognitive forcing highlights are only active during **Session 2 (experimental)**. Session 1 is always a baseline with no visualization for any condition.

## URL Parameter

```
?highlight=1,2,3
```

Comma-separated, any combination. Only active when the effective visualization condition === 2 (i.e., Session 2 with visualizationCondition=2, the multi-turn condition).

| Mode | What blinks | Domain |
|------|-------------|--------|
| `1` | The user's chat message bubble that caused the biggest swing | Chat panel (left) |
| `2` | The dot on the drift axis chart for that turn | Drift panel (right) |
| `3` | The outer-ring arc in the sunburst for the swung trait | Sunburst (right) |

## How "Biggest Swing" Is Computed

After each AI reply, the persona vector API returns a new trait snapshot. `computeBiggestSwing()` (`chat.js:1350`) performs a **greedy argmax over the absolute pairwise difference between the two most recent persona snapshots**:

1. Takes the last two entries in `window.personaHistory` (turn N vs. turn N−1).
2. Iterates over every trait in every category.
3. Computes `Math.abs(currentValue - previousValue)` for each trait.
4. Returns the single trait with the largest absolute delta, along with its turn index and category key.

**Key characteristics:**

- **Adjacent turns only** — it compares turn N to turn N−1, not cumulative drift or a rolling window. A trait drifting slowly over many turns will not trigger highlights; only abrupt single-turn jumps are surfaced.
- **Exactly one trait per turn** — the argmax picks a single winner. In the case of ties, whichever trait is iterated last wins (object iteration order).
- **No minimum threshold** — even a small delta (e.g., 0.01) triggers highlights as long as it is the largest among all traits for that turn pair.

That result drives all three highlight modes.

## Session Gating

The `getEffectiveVisualizationCondition()` function ensures that:
- **Session 1**: Always returns 0 (control), so highlights never fire regardless of assigned condition
- **Session 2**: Returns the real assigned condition, so highlights fire for conditions 1 and 2

## Design Decisions

1. **Per-turn, not cumulative.** We highlight the swing from *this* message, not the historical max. This keeps the signal tied to the user's most recent action.

2. **URL-parameter gating.** Each highlight mode is independently toggleable so we can A/B test which combination is most effective without redeploying.

3. **Blinking pulse animation.** A `swing-pulse` CSS keyframe (opacity 1 -> 0.35 -> 1 at 1.1s) is shared across all three highlights. Visible but not aggressive.

4. **Auto-open drift panel (mode 2).** When highlight 2 is active, the drift panel automatically opens to the most-swung trait instead of waiting for a user click.

5. **Session 2 only.** Since Session 1 is always baseline, highlights are effectively gated behind being in Session 2 with an experimental visualization condition.

6. **Message-turn correlation.** `personaTurnMessageIds[]` maps each persona snapshot back to the user message ID that preceded it, so highlight 1 can target the correct bubble.

7. **Segment-only highlight (mode 3).** The sunburst highlight targets only `path[data-trait-name]` elements, not the surrounding text labels. Both share the `data-trait-name` attribute, so the selector must be scoped to paths.

8. **Click-through navigation.** Clicking a highlighted message (mode 1) cross-links to the right panel: opens the drift chart to the swung trait, highlights the turn dot, highlights the sunburst segment, and smooth-scrolls the persona panel into view. Works regardless of which highlight modes are active — the click handler always triggers modes 2 + 3.

## Example URLs

```
# All highlights, demo mode (skips surveys)
?demo=true&highlight=1,2,3

# Just the chat message highlight in experimental condition
?visualizationCondition=1&highlight=1

# Sunburst + drift dot only
?visualizationCondition=1&highlight=2,3
```

## Files Touched

- `interface/js/settings.js` — `highlight` parameter parsing, `getEffectiveVisualizationCondition()`
- `interface/js/chat.js` — `computeBiggestSwing()`, `applyHighlights()`, message ID tracking
- `interface/css/main.css` — `@keyframes swing-pulse` + 3 highlight classes
