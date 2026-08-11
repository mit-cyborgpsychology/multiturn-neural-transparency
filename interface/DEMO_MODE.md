# Demo Mode Documentation

## Overview

Demo mode (`?demo=true`) provides a streamlined experience for demonstrating the mech-chat-iui system to members and stakeholders. It combines debug features while maintaining educational UI elements about system prompts.

## Usage

Simply append `?demo=true` to any URL:

```
https://your-domain.com/?demo=true
```

Or combine with other parameters:

```
https://your-domain.com/?demo=true&debugTimer=true
```

## What Demo Mode Does

### Automatic Settings

When `?demo=true` is enabled, the following settings are automatically configured:

| Setting | Value | Effect |
|---------|-------|--------|
| `demo` | `true` | Activates demo-specific logic |
| `debug` | `true` | Enables debug features, skips consent page |
| `skipSurvey` | `true` | Bypasses pre-task and post-task surveys |
| `visualizationCondition` | `1` | Always shows persona visualization |

### User Experience Changes

#### 🚀 Entry Point

Demo mode **skips the consent page** and goes **directly to avatar selection** (same as debug mode). This means:
- No consent form is shown
- User immediately sees the chat interface with avatar selection
- Study can be demonstrated without the consent workflow

#### ✅ What's Kept

Demo mode preserves these helpful instruction modals:

1. **Avatar Selection Modal** - Explains how to choose an AI avatar
2. **System Prompt Modal** - Educational content about system prompts (includes examples and starter prompts)
3. **Chat Instruction Modal** - Tips for interacting with the AI
4. **Visualization Explanation Modal** - How to read the sunburst chart
5. **Prompt Refinement Modal** - How to iterate on the system prompt

#### ❌ What's Skipped

Demo mode removes these elements:

1. **Pre-Task Survey** (3 phases)
   - Initial assessment questions
   - Trait prediction sliders (8 traits)
   - Trust assessment question

2. **Survey Instruction Modal** - Explaining the survey process

3. **Post-Task Survey** (2 phases)
   - Likert scale questions about experience
   - Open-ended feedback

4. **Consent Page** (skipped via debug mode)

#### 🔄 Modified Behavior

- **Visualization**: Always shows the persona sunburst chart (doesn't matter what random condition would have been assigned)
- **Timer**: Can be shortened to 10 seconds with `?debugTimer=true`
- **All buttons remain interactive**: Users can test all functionality

## Implementation Details

### Files Modified

#### 1. `js/settings.js`

Added demo mode detection and automatic configuration:

```javascript
// Check for demo mode first - it will override multiple settings
const isDemoMode = urlParams.get('demo') === 'true';

let settings = {
    demo: isDemoMode,
    debug: isDemoMode || urlParams.get('debug') === 'true',
    skipSurvey: isDemoMode || urlParams.get('skipSurvey') === 'true',
    visualizationCondition: (() => {
        if (isDemoMode) {
            sessionStorage.setItem('visualizationCondition', '1');
            sessionStorage.setItem('conditionAssignmentMethod', 'demo_mode');
            return 1;
        }
        // ... rest of logic
    })(),
    // ... other settings
};
```

Prominent logging when demo mode is active:

```
═══════════════════════════════════════════
   🎬 DEMO MODE ACTIVE
═══════════════════════════════════════════
Demo mode automatically enables:
  ✓ Debug features
  ✓ Skip surveys (pre-task and post-task)
  ✓ Visualization always shown
  ✓ Instruction modals kept (avatar, prompt, chat, viz, refinement)
═══════════════════════════════════════════
```

#### 2. `js/chat.js`

**Modal Display Logic** (line ~1908):

```javascript
window.showInstructionModal = function(type) {
    const isDemoMode = window.experimentSettings.demo;
    const skipSurvey = window.experimentSettings.skipSurvey;
    
    // Define which modals to keep in demo mode
    const demoModeKeptModals = ['avatar', 'prompt', 'chat', 'visualization', 'promptRefinement'];
    
    if (isDemoMode) {
        // In demo mode, skip the survey instruction modal but keep others
        if (type === 'survey') {
            // Mark as shown and don't display
            return;
        }
    } else if (skipSurvey) {
        // Original skipSurvey behavior: skip all modals
        return;
    }
    // ... show modal logic
};
```

**Post-Survey Skip Logic** (line ~1752):

```javascript
function showPostSurvey() {
    const isDemoMode = window.experimentSettings.demo;
    
    if (isDemoMode) {
        console.log('🎬 Demo mode: Skipping post-task survey');
        completePostSurvey();
        return;
    }
    // ... rest of post-survey logic
}
```

**Pre-Survey Skip Logic** (line ~393):

```javascript
// Uses window.experimentSettings.skipSurvey which is automatically true in demo mode
const skipSurvey = window.experimentSettings.skipSurvey;
if (surveyCompleted || skipSurvey) {
    if (skipSurvey && isDemoMode) {
        console.log('🎬 Demo mode: Skipping pre-task survey, proceeding to visualization');
    }
    // Proceed directly to visualization
}
```

### Console Logging

Demo mode provides clear console feedback:

```javascript
// On page load
console.log('🎬 DEMO MODE ACTIVE');
console.log('Demo mode automatically enables: ...');

// When skipping pre-task survey
console.log('🎬 Demo mode: Skipping pre-task survey, proceeding to visualization');

// When skipping post-task survey
console.log('🎬 Demo mode: Skipping post-task survey');
```

## Testing

A test page is provided at `demo-test.html` with:

- Links to launch demo mode with various configurations
- Comparison links to normal, debug, and skipSurvey modes
- Expected behavior checklist
- Implementation details reference

### Test Checklist

- [ ] Page skips consent and loads directly to avatar selection (chat interface)
- [ ] Avatar selection modal appears
- [ ] System prompt instruction modal appears
- [ ] After submitting prompt, pre-task survey is skipped
- [ ] Visualization always shows (regardless of condition)
- [ ] Chat instruction modal appears
- [ ] Visualization explanation modal can be triggered
- [ ] Prompt refinement modal appears when going back to config
- [ ] After timer expires, post-task survey is skipped
- [ ] All buttons remain interactive throughout

## Browser Compatibility

Demo mode uses standard URL parameters and sessionStorage, compatible with:

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)

## Security Considerations

- Demo mode is controlled purely by URL parameter
- No sensitive data is exposed
- Survey responses are not collected (but conversation data may still be logged)
- Same Firebase authentication as normal mode

## Future Enhancements

Potential improvements for demo mode:

1. **Custom timer duration**: `?demo=true&demoTimer=120` for 2-minute demos
2. **Demo-specific completion message**: Custom ending text for demos
3. **Demo analytics**: Separate tracking for demo sessions
4. **Shareable demo links**: Pre-configured system prompts
5. **Demo mode badge**: Visual indicator in UI that demo mode is active

## Troubleshooting

### Demo mode not activating

- Check URL parameter is exactly `?demo=true` (case-sensitive)
- Open browser console and look for "🎬 DEMO MODE ACTIVE" message
- Verify `window.experimentSettings.demo === true` in console

### Surveys still appearing

- Clear browser cache and localStorage
- Check console for any JavaScript errors
- Verify settings.js and chat.js have been updated

### Visualization not showing

- Check console for visualization condition assignment
- Should see `conditionAssignmentMethod: 'demo_mode'`
- Verify `window.experimentSettings.visualizationCondition === 1`

### Modals not appearing

- Demo mode keeps certain modals - verify you're testing the correct ones
- Survey modal should NOT appear in demo mode
- Check sessionStorage `instructionsShown` to see what's been marked

## Changelog

### Version 1.0 (Initial Implementation)

- Added `?demo=true` parameter support
- Automatic configuration of debug, skipSurvey, visualizationCondition
- Selective modal display (keep helpful ones, skip surveys)
- Comprehensive logging
- Test page and documentation

---

**Last Updated**: October 2025  
**Maintainer**: Mech Chat IUI Team  
**Related Files**: `js/settings.js`, `js/chat.js`, `demo-test.html`

