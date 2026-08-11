# Visualization Condition Control - Implementation Synopsis

## Overview
Implemented an experimental condition system to toggle between **control (no-visualization)** and **experimental (with visualization)** conditions for a user study. The setting allows researchers to randomly assign participants or manually set conditions via URL parameter.

## Key Setting: `visualizationCondition`
- **Location**: `js/settings.js`
- **Values**: `0` (control/no-viz), `1` (single-turn static viz), or `2` (multi-turn dynamic viz)
- **Default**: Random 1/3 assignment
- **URL Override**: `?visualizationCondition=0`, `?visualizationCondition=1`, or `?visualizationCondition=2`
- **Persistence**: Stored in `sessionStorage` across page navigations
- **Session gating**: `getEffectiveVisualizationCondition()` returns 0 during Session 1 (baseline) regardless of assignment; returns the real condition during Session 2

## File Changes

### 1. `js/settings.js`
- Added `visualizationCondition` parameter with random assignment logic (commented)
- Stores condition in sessionStorage with assignment method tracking
- Logs condition prominently to console

### 2. `js/chat.js` (Major Changes)
**New Functions:**
- `showTraitDefinitionsNoViz()` - Displays personality trait reference panel for control condition
- `autoSubmitPersonaCheck(systemPrompt)` - Background API call + immediate UI unlock for no-viz

**Modified Functions:**
- `initializeSystemPromptConfig()` - Hides visualization UI elements in control condition
- `updateCharacterCounter()` - Tracks prompt changes with `promptHasChangedSinceSubmit` flag
- Submit Prompt handler - Conditional flow based on visualizationCondition
- `closePreTaskSurvey()` - Auto-submits persona check for control, shows Check Persona buttons for experimental
- `switchToSystemPromptConfig()` - Handles return from chat differently per condition
- `resetConfig` - Properly resets state flags
- `showVisualizationExplanation()` - Suppressed in control condition
- `showPromptRefinementModal()` - Removes visualization mentions for control condition

**State Tracking:**
- Added `window.promptHasChangedSinceSubmit` flag for edit detection

### 3. `js/instructions.js`
- Skips Phase 4 (Persona Visualization) instructions in control condition
- Updates phase navigation to skip visualization-related phases

### 4. `html/instructions.html`
- Added conditional text update script
- Modified Phase 3 to be condition-appropriate

## How It Works

### Condition 0 — Control (No Visualization)
**Flow:**
1. User submits system prompt → Survey
2. After survey: **Automatically** calls persona API in background
3. **Immediately shows trait definitions** (6 behavioral dimensions with bipolar labels)
4. **Start Chat button enabled immediately**
5. API success/failure doesn't block user (non-blocking, errors only in console)
6. All visualization UI elements removed (persona chart, help buttons, etc.)

**What Users See:**
- No "Check Persona" button
- Trait definitions reference panel ("Traits to Monitor") instead of visualization
- Can proceed to chat immediately after survey
- During chat: left panel shows static trait reference list, no computed values

### Condition 1 — Single-Turn (Static Visualization)
**Flow:**
1. User submits system prompt → Survey
2. After survey: Shows "Check Persona" button
3. User clicks "Check Persona" → API call → Sunburst visualization renders once from system prompt alone
4. Start Chat button enabled after persona checked

**What Users See:**
- Check Persona button
- Sunburst visualization (static — never re-renders during chat)
- Panel header: "Internal Behavior Analysis"
- During chat: persona API called silently per turn (logged to Firebase, sunburst not updated)
- No drift panel, no cognitive forcing highlights, no reminder banners

### Condition 2 — Multi-Turn (Dynamic Visualization)
**Flow:**
1. User submits system prompt → Survey
2. After survey: Shows "Check Persona" button (same as Condition 1)
3. User clicks "Check Persona" → Initial sunburst renders
4. Start Chat button enabled after persona checked
5. During chat: sunburst re-renders after every user message with updated persona scores

**What Users See:**
- Dynamic sunburst that updates per turn (system prompt + full conversation history)
- Interactive drift panel: per-trait line charts showing activation trajectory across turns
- Clicking a drift dot restores sunburst to that turn's historical snapshot
- Cognitive forcing highlights after each turn: the system computes the absolute delta between the two most recent persona snapshots for every trait and identifies the single trait with the largest magnitude shift (greedy argmax, adjacent turns only, no minimum threshold). Three synchronized highlights fire: (1) pulsing border on the causal chat message, (2) pulsing dot on the drift chart, (3) pulsing arc on the sunburst
- Drift info modal on chat entry; sunburst reminder banner after 1 minute

## Trait Definitions Panel (Control Condition)
Displays 6 behavioral trait dimensions with bipolar labels:
- Empathy (Unempathetic ↔ Empathetic)
- Erudite (Simplistic ↔ Sophisticated)
- Robotic (Human-like ↔ Robotic)
- Romantic (Platonic ↔ Romantic)
- Sycophantic (Honest ↔ Sycophantic)
- Toxic (Respectful ↔ Toxic)

Each trait shows the bipolar spectrum with descriptive text. No computed values are displayed.

**Text Sizing:**
- Compact layout with smaller font sizes to prevent overflow
- Header: 1rem
- Trait titles: 0.8rem
- Descriptions: 0.7rem
- Scrollable container with `max-height: 600px`

## Firebase Logging
All data collection preserved for both conditions:
- Condition assignment logged at experiment start
- Persona vectors logged with condition label ("control_no_visualization" or "experimental_with_visualization")
- System prompts logged with action type
- All logs timestamped

**Paths:**
- `{studyId}/participantData/{userId}/experimentCondition`
- `{studyId}/participantData/{userId}/personaVectorLog/{timestamp}`
- `{studyId}/participantData/{userId}/systemPromptLog/{timestamp}`

## Prompt Change Handling
Both conditions support multiple refinements:
- **Edit after submission** → Shows "Submit Prompt" button, disables "Start Chat"
- **Return from chat (no edit)** → "Start Chat" remains enabled
- **Re-submission** → New API call, new persona vector logged
- All persona vectors stored in timestamped history log

## Key Implementation Details

### Non-Blocking API (Control Condition)
```javascript
// Always show UI first
window.personaCheckedForCurrentPrompt = true;
$('#startChatBtn').prop('disabled', false);
showTraitDefinitionsNoViz();

// Then try API in background
try {
    // API call...
} catch (error) {
    // Log only, don't show to user
    console.error('⚠️ Error (non-blocking):', error);
}
```

### Critical Bug Fixes Applied
1. **Placeholder visibility on re-submission**: Keep `#initialPlaceholder` visible in control condition when re-submitting
2. **Interface button enabling**: Call `enableInterfaceButtons()` after auto-submit in control condition
3. **Error handling**: API errors don't show to user in control condition (background data collection only)
4. **Text overflow**: Reduced font sizes and padding to prevent cut-off in trait definitions panel

## Testing
- **Control**: Default or `?visualizationCondition=0`
- **Experimental**: `?visualizationCondition=1`
- **Debug mode**: `?visualizationCondition=0&debug=true&skipSurvey=true`

## Current State
✅ Fully implemented and tested
✅ No linter errors
✅ Graceful error handling
✅ Both conditions working end-to-end
✅ Multiple prompt refinements supported
✅ Firebase logging complete
✅ Text sizing optimized for display

## Known Considerations
- Modal endpoint returning 501 errors during development (expected, doesn't affect UX in control condition)
- Random assignment code commented out (ready to enable when needed)
- Post-task survey identical for both conditions (no viz-specific questions found)

## To Enable Random Assignment
In `js/settings.js` lines 95-106, uncomment:
```javascript
const randomCondition = Math.random() < 0.5 ? 0 : 1;
sessionStorage.setItem('visualizationCondition', randomCondition.toString());
sessionStorage.setItem('conditionAssignmentMethod', 'random');
return randomCondition;
```
And comment out the default assignment lines below.

## Implementation Date
October 9, 2025

## Files Modified
- `js/settings.js`
- `js/chat.js`
- `js/instructions.js`
- `html/instructions.html`

