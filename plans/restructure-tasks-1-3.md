# Plan: Restructure Experiment Tasks 1-3

## Context
The experiment is being reconfigured (branch `exp-2-reconfig`) to change how calibration and chat tasks are ordered. The key change: Task 1 now includes trait rating (previously it was just reading), Task 2 introduces a new prompt + keeps live chat but drops calibration, and Task 3 repeats the Task 1 structure for a third distinct prompt.

---

## New Task Flow

### Task 1: Baseline Calibration (2 parts) — NO visualization/chat
- **Part A**: Read system prompt (existing Alex prompt) → Rate 8 traits (0-10 sliders)
- **Part B**: Read transcript of simulated conversation (existing `SCRIPTED_CONVERSATION`) → Rate 8 traits again
- Same slider UI as current Task 3

### Task 2: Live Chat — new system prompt
- **Step 1**: Page showing the new system prompt for participants to read carefully (like the Task 1 prompt-reading step)
- **Step 2**: Live 10-min chat with control/experimental visualization conditions (existing chat-content.html behavior)
- No calibration/rating questions in Task 2

### Task 3: Repeat of Task 1 structure — third distinct prompt
- **Part A**: Read a third system prompt → Rate 8 traits
- **Part B**: Read a pre-written transcript for that prompt → Rate 8 traits
- Same slider UI as Task 1

### Task 4: Final Survey (unchanged)

---

## Files to Modify

### 1. `interface/js/study-content.js`
- Add `TASK2_PROMPT` placeholder (new system prompt for Task 2)
- Add `TASK3_PROMPT` placeholder (third prompt for Task 3)
- Add `TASK3_CONVERSATION` placeholder (pre-written transcript for Task 3 Part B)
- Keep existing `CALIBRATION_PROMPT` and `SCRIPTED_CONVERSATION` for Task 1

### 2. `interface/html/task1-calibration.html` (major rewrite)
Current: Single page showing prompt + "Next" button, no ratings.
New: 3-step flow (mirrors current Task 3 structure):
- **Step 0**: Read Alex system prompt → "Rate this prompt" button
- **Step 1**: 8 trait sliders for Part A (prefix `t1a_`) → "Next: Conversation Transcript" button
- **Step 2**: Show transcript + 8 trait sliders for Part B (prefix `t1b_`) → "Submit" button
- Progress bar (3 dots)
- Back buttons between steps
- Validation: all 8 sliders required before proceeding
- Firebase save: `task1BaselineCalibration` with `partA` and `partB` trait ratings
- On completion: call `window.showTask2()`

### 3. `interface/html/task2-prompt-reading.html` (NEW file)
- Simple page showing the Task 2 system prompt for reading
- Similar layout to Task 1 Step 0 (prompt display + instruction + "Next" button)
- On "Next": loads the chat interface (`chat-content.html`)
- Firebase save: timestamp of viewing

### 4. `interface/index.html` — update routing
- `showTask2()`: load `task2-prompt-reading.html` instead of `chat-content.html` directly
- Add `showTask2Chat()`: loads `chat-content.html` (called from task2-prompt-reading.html)
- Update comments to reflect new flow

### 5. `interface/html/task3-recalibration.html` (moderate update)
- Change prompt source from `RECALIBRATION_PROMPT` to `TASK3_PROMPT`
- Change transcript source from `SCRIPTED_CONVERSATION` / `CALIBRATION_PROMPT` to `TASK3_CONVERSATION` / `TASK3_PROMPT`
- Update header text (still "Task 3 of 4: Recalibration")
- Keep existing slider structure (already has `t3a_` and `t3b_` prefixes)

### 6. `interface/js/chat.js` — minor updates
- Update system prompt used for live chat to reference `TASK2_PROMPT` instead of `CALIBRATION_PROMPT`
- Remove any pre-chat calibration steps if they exist in the Task 2 flow

---

## Implementation Order
1. Update `study-content.js` with new content placeholders
2. Rewrite `task1-calibration.html` (model after task3-recalibration.html structure)
3. Create `task2-prompt-reading.html`
4. Update routing in `index.html`
5. Update `task3-recalibration.html` to use new content keys
6. Update `chat.js` to use `TASK2_PROMPT`

## Verification
- Run with `?debug=true` to skip consent and test full flow
- Verify Task 1: prompt reading → Part A sliders → transcript + Part B sliders → proceeds to Task 2
- Verify Task 2: prompt reading page → chat interface loads with new prompt
- Verify Task 3: new prompt → Part A sliders → new transcript + Part B sliders → proceeds to Task 4
- Check Firebase writes for `task1BaselineCalibration` with both partA and partB data
- Check that live chat in Task 2 uses the new `TASK2_PROMPT`
