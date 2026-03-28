# API Call Optimization: Persona-Vector & Chat Endpoints

## Problem

The experiment was making redundant API calls to the `/api/persona-vector` endpoint during initialization. Each unnecessary call adds latency, wastes compute on the Modal.ai backend, and complicates debugging when tracing participant sessions.

### Previous Call Flow (Per Participant)

| Phase | Endpoint | Payload | Purpose | Redundant? |
|-------|----------|---------|---------|------------|
| Page load (`preloadModels`) | `/api/persona-vector` | Dummy prompt: `"You are a helpful research assistant."` | Warm up Modal.ai endpoint | Yes -- result discarded |
| Page load (`preloadModels`) | Chat endpoint | `"Hi"` with generic system prompt | Warm up chat endpoint | No -- one-time warm-up |
| Chat page init (line 214) | `/api/persona-vector` | Session's real system prompt | Background pre-fetch | Yes -- duplicated by next call |
| Control: `autoSubmitPersonaCheck` | `/api/persona-vector` | Same session prompt | Data collection | No -- but identical to pre-fetch |
| Viz conditions: "Check Persona" button | `/api/persona-vector` | Same session prompt | Display visualization | No -- but identical to pre-fetch |
| Each user message (`callAIAPI`) | `/api/persona-vector` | System prompt + conversation history | Track persona drift | No -- unique payload per turn |
| Each user message (`callAIAPI`) | Chat endpoint | System prompt + conversation history | Get AI response | No -- core functionality |

**Total redundant calls per participant: 3** (1 dummy warm-up + 1 pre-fetch + 1 duplicate init)

## Solution

### 1. Preload with real study prompts instead of dummy data

`preloadModels()` in `config-unified.js` now fetches persona vectors for both the ASST and ROLEPLY system prompts in parallel at page load. Results are cached in `window.cachedPersonaVectors`, keyed by the exact prompt text string.

This serves dual purpose:
- Warms the Modal.ai endpoint (same as before)
- Produces usable, cached persona vectors for both sessions

### 2. Remove redundant per-session init fetches

- **Removed** the fire-and-forget `fetch('/api/persona-vector')` at chat page init (formerly line 214). Replaced with a cache lookup from `window.cachedPersonaVectors`.
- **Updated** `autoSubmitPersonaCheck()` (control condition) to use cached data instead of making a new API call. Firebase logging still occurs.
- **Updated** `checkPersona()` to check the cache for system-prompt-only calls (no conversation history). Only hits the API when conversation history is included, which produces a different result.

### 3. Remove dead scripted playback code

`playScriptedConversation()` was defined but never called. It contained a loop calling `checkPersona()` after each assistant turn in a scripted conversation -- 5 API calls per session that would never fire. Removed entirely.

## Current Call Flow (Per Participant)

| Phase | Endpoint | Count | Notes |
|-------|----------|-------|-------|
| `preloadModels` -- ASST prompt | `/api/persona-vector` | 1 | Cached in `window.cachedPersonaVectors` |
| `preloadModels` -- ROLEPLY prompt | `/api/persona-vector` | 1 | Cached in `window.cachedPersonaVectors` |
| `preloadModels` -- chat warm-up | Chat endpoint | 1 | Warms Modal.ai, response discarded |
| Session 1 init | -- | 0 | Cache hit (prompt text matches preload key) |
| Session 1 chat (per user msg) | `/api/persona-vector` | 1 per msg | Unique payload: prompt + conversation history |
| Session 1 chat (per user msg) | Chat endpoint | 1 per msg | AI response |
| Session 2 init | -- | 0 | Cache hit (other prompt, also preloaded) |
| Session 2 chat (per user msg) | `/api/persona-vector` | 1 per msg | Unique payload: prompt + conversation history |
| Session 2 chat (per user msg) | Chat endpoint | 1 per msg | AI response |

**Total per participant: 3 + 2N per session** (where N = number of user messages)

## Cache Architecture

```
window.cachedPersonaVectors = {
    "<ASST prompt text>":    { content: { empathy: 17, erudite: 12, ... } },
    "<ROLEPLY prompt text>": { content: { empathy: 3, toxic: 18, ... } }
};
```

- Cache is populated once at study start by `preloadModels()` in `config-unified.js`
- Cache persists across both sessions (page does not reload between sessions)
- Cache is keyed by prompt text, not by label -- so `getSessionPromptText(n)` returns the correct key regardless of `promptOrder` (asst_first vs roleply_first)
- Only system-prompt-only calls use the cache. Calls with conversation history always hit the API (the result depends on the messages).

## Routing Correctness

The persona vector displayed to participants is determined by two independent lookups:

1. **Prompt selection**: `getSessionPromptText(currentSession)` resolves the correct GOOD/EVIL prompt based on `promptOrder` and session number
2. **Visualization gating**: `getEffectiveVisualizationCondition()` returns 0 (no viz) for Session 1 always, and the real condition (0/1/2) for Session 2

Example with `roleply_first` order and visualization condition 2:
- Session 1: ROLEPLY prompt, viz=0 --> cached ROLEPLY scores logged silently, no chart shown
- Session 2: ASST prompt, viz=2 --> cached ASST scores shown in chart, live updates during chat

No cross-contamination is possible because the cache key is the literal prompt string.

## Files Changed

- `interface/js/config-unified.js` -- `preloadModels()` now preloads both real prompts and caches results
- `interface/js/chat.js` -- removed redundant fetches, added cache lookups, removed dead `playScriptedConversation()`
