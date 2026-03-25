# Cognitive Forcing Functions

## Goal

Help users notice when their messages cause significant persona drift during a live chat session. The highlights draw attention to *which* message shifted *which* trait, forcing attentiveness to behavioral change.

## URL Parameter

```
?highlight=1,2,3
```

Comma-separated, any combination. Only active when `visualizationCondition=1`.

| Mode | What blinks | Domain |
|------|-------------|--------|
| `1` | The user's chat message bubble that caused the biggest swing | Chat panel (left) |
| `2` | The dot on the drift axis chart for that turn | Drift panel (right) |
| `3` | The outer-ring arc in the sunburst for the swung trait | Sunburst (right) |

## How "Biggest Swing" Is Computed

- After each AI reply, the persona vector API returns a new trait snapshot.
- `computeBiggestSwing()` compares **only the last two snapshots** (current turn vs. previous turn).
- It finds the single trait with the largest absolute delta across all 6 category pairs.
- That result drives all three highlight modes.

## Design Decisions

1. **Per-turn, not cumulative.** We highlight the swing from *this* message, not the historical max. This keeps the signal tied to the user's most recent action.

2. **URL-parameter gating.** Each highlight mode is independently toggleable so we can A/B test which combination is most effective without redeploying.

3. **Blinking pulse animation.** A `swing-pulse` CSS keyframe (opacity 1 -> 0.35 -> 1 at 1.1s) is shared across all three highlights. Visible but not aggressive.

4. **Auto-open drift panel (mode 2).** When highlight 2 is active, the drift panel automatically opens to the most-swung trait instead of waiting for a user click.

5. **Experimental condition only.** Highlights are gated behind `visualizationCondition=1` since they depend on the persona visualization being visible.

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

- `interface/js/settings.js` — `highlight` parameter parsing
- `interface/js/chat.js` — `computeBiggestSwing()`, `applyHighlights()`, message ID tracking
- `interface/css/main.css` — `@keyframes swing-pulse` + 3 highlight classes
