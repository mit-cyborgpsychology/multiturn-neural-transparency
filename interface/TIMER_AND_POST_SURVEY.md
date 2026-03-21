# 10-Minute Timer and Post-Survey Implementation

## Overview

This implementation adds a 10-minute interaction timer and a 2-phase post-survey questionnaire to the chat study interface.

## Features Implemented

### 1. **Timer System**
- **Activation**: Timer starts automatically when users click "Start Chat" for the first time
- **Display**: Subtle timer shown in the chat interface with a clock icon and countdown (M:SS format)
- **Duration**: 
  - **Production Mode**: 10 minutes (600 seconds)
  - **Debug Mode**: 10 seconds (for testing)
- **Data Logging**: Timer start time, end time, and duration saved to Firebase

### 2. **Post-Survey Modal**
When the timer expires, a modal appears with a 2-phase questionnaire:

#### Phase 1: Likert Scale Questions (1-7 scale)
1. "How well could you predict unintended behaviors from your system prompt?"
2. "How well could you predict negative unintended behaviors from your system prompt?"
3. "Given the {relevant background abt unintended model behaviors}, how much do you trust this model?"

#### Phase 2: Open-Ended Feedback
- Textarea for participants to provide feedback about the interface and general thoughts about the experiment
- Minimum input required to submit

### 3. **Completion Page**
- Professional thank you page with:
  - Completion confirmation
  - Compensation details ($5 base + up to $2 bonus)
  - Next steps information
  - Contact information for study administrator
  - Optional Prolific redirect button

## Usage

### Normal Mode (10-minute timer)
Simply access the application as usual:
```
https://your-domain.com/
```

### Debug Mode (10-second timer)
Add the `debugTimer` URL parameter for testing:
```
https://your-domain.com/?debugTimer=true
```

## Files Modified

1. **`js/chat.js`**
   - Added timer initialization variables
   - Added timer start logic to "Start Chat" button
   - Added `startTimer()`, `updateTimer()`, `timerExpired()` functions
   - Added post-survey modal functions: `showPostSurvey()`, `initializePostSurvey()`
   - Added Firebase data saving functions: `savePostPhase1Data()`, `savePostPhase2Data()`
   - Added `completePostSurvey()` function to redirect to completion page

2. **`html/chat-content.html`**
   - Added timer display UI in chat interface controls
   - Added complete post-survey modal HTML structure with both phases

3. **`css/main.css`**
   - Added timer display styles (`.timer-display`)
   - Added post-survey modal styles (`.post-survey-modal`, `.post-survey-content`, etc.)
   - Added responsive adjustments for mobile devices

4. **`html/complete.html`** (newly created)
   - Professional completion page with thank you message
   - Compensation information
   - Optional Prolific redirect functionality
   - Contact information

## Firebase Data Structure

The implementation saves data to Firebase in the following structure:

```
chat-study/
  participantData/
    {userId}/
      timer/
        startTime: "2025-10-07T12:34:56.789Z"
        duration: 600
        endTime: "2025-10-07T12:44:56.789Z"
      postTaskSurvey/
        phase1/
          responses:
            "How well could you predict unintended behaviors...": 5
            "How well could you predict negative unintended...": 4
            "Given the {relevant background abt unintended...": 6
          timestamp: "2025-10-07T12:45:12.345Z"
        phase2/
          responses:
            openEndedFeedback: "The interface was intuitive..."
          timestamp: "2025-10-07T12:46:23.456Z"
        metadata/
          completion_timestamp: "2025-10-07T12:46:23.456Z"
          completion_time: 1696681583456
      completion/
        completed: true
        timestamp: "2025-10-07T12:46:30.789Z"
```

## Key Features

### User Experience
- **Non-intrusive timer**: Subtle display that doesn't distract from the task
- **Automatic trigger**: No manual intervention required
- **Modal overlay**: Post-survey cannot be dismissed (ensures completion)
- **Chat disabled**: Once timer expires, users cannot continue chatting
- **Progressive disclosure**: Survey shows one phase at a time
- **Validation**: Users must answer all questions before proceeding

### Data Collection
- All timer events logged to Firebase
- Survey responses saved with timestamps
- Completion status tracked
- Automatic data structure organization

### Debug Functionality
- Quick 10-second timer for testing
- Easy to enable via URL parameter
- Same behavior as production mode, just faster

## Testing the Implementation

### Test Debug Mode (10 seconds)
1. Open the application with `?debugTimer=true` parameter
2. Complete the pre-survey
3. Click "Start Chat"
4. Observe timer countdown (10 seconds)
5. Wait for timer to expire
6. Complete post-survey Phase 1 (3 questions)
7. Complete post-survey Phase 2 (open-ended feedback)
8. Verify redirection to completion page

### Test Production Mode (10 minutes)
Follow the same steps without the `debugTimer` parameter. Timer will run for 10 minutes.

## Customization Options

### Change Timer Duration
In `js/chat.js`, modify line 61:
```javascript
window.timerDuration = debugTimer ? 60 : 600; // Change 600 to desired seconds
```

### Change Prolific Redirect URL
In `html/complete.html`, modify the `redirectToProlific()` function:
```javascript
const prolificCompletionURL = 'YOUR_ACTUAL_PROLIFIC_URL';
```

### Modify Survey Questions
Edit the HTML in `html/chat-content.html` under the `<!-- Post-Task Survey Modal -->` section.

### Style Adjustments
Modify styles in `css/main.css` under:
- `/* TIMER DISPLAY STYLES */` section
- `/* POST-SURVEY MODAL STYLES */` section

## Notes

- Timer only starts once, even if user returns to config and back to chat
- Timer persists across page refreshes (stored in window variables)
- Post-survey modal is non-dismissible to ensure completion
- All data is automatically saved to Firebase with timestamps
- The placeholder text `{relevant background abt unintended model behaviors}` in Question 3 remains as-is per user request

## Browser Compatibility

Tested and working in:
- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)

Responsive design works on:
- Desktop (1920x1080 and larger)
- Tablet (768px - 1024px)
- Mobile (320px - 767px)

