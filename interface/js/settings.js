/**
 * Settings Configuration for Mech Chat IUI
 * 
 * This module centralizes all URL parameter-based settings for the experiment.
 * URL parameters override default values, and all feature flags should reference
 * these settings rather than reading URL parameters directly.
 * 
 * Usage:
 *   Import this file before other scripts, then access: window.experimentSettings
 */

/**
 * Get settings from URL parameters and merge with defaults
 * @returns {Object} Settings object with all experiment configuration
 */
function getExperimentSettingsFromURL() {
    const urlParams = new URLSearchParams(window.location.search);
    
    // Check for demo mode first - it will override multiple settings
    const isDemoMode = urlParams.get('demo') === 'true';
    
    // If demo mode is active, clear any previous sessionStorage assignments
    // to ensure demo mode settings take precedence
    if (isDemoMode) {
        sessionStorage.removeItem('visualizationCondition');
        sessionStorage.removeItem('conditionAssignmentMethod');
    }
    
    let settings = {
        /**
         * Demo mode - combines debug features, skips surveys, always shows visualization
         * Automatically enables: debug, skipSurvey, visualizationCondition=1
         * Keeps helpful instruction modals (avatar, prompt, chat, visualization, refinement)
         * URL: ?demo=true
         * Default: false
         */
        demo: isDemoMode,
        
        /**
         * Debug mode - enables debug features and test buttons
         * URL: ?debug=true
         * Default: false
         * Note: Automatically enabled when demo=true
         */
        debug: isDemoMode || urlParams.get('debug') === 'true',
        
        /**
         * Debug timer mode - shortens timer for testing (10 seconds vs 10 minutes)
         * URL: ?debugTimer=true
         * Default: false
         */
        debugTimer: urlParams.get('debugTimer') === 'true',
        
        /**
         * Fresh mode - clears all session/local storage on load
         * URL: ?fresh=true
         * Default: false
         */
        fresh: urlParams.get('fresh') === 'true',
        
        /**
         * Skip all surveys (pre-task and post-task) and instruction modals
         * URL: ?skipSurvey=true
         * Default: false
         * Note: Automatically enabled when demo=true, but demo mode keeps certain modals
         */
        skipSurvey: isDemoMode || urlParams.get('skipSurvey') === 'true',
        
        /**
         * Skip mode - auto-reveals all sentence/transcript reveals and unlocks all
         * gated next buttons immediately on load (for quick navigation during testing)
         * URL: ?skip=true
         * Default: false
         */
        skip: urlParams.get('skip') === 'true',

        /**
         * Current session number (1 = baseline, 2 = experimental)
         * Session 1: No visualization for ANY condition (baseline)
         * Session 2: Visualization conditions applied (experimental)
         * Persisted in sessionStorage across page navigations
         */
        currentSession: (() => {
            const stored = sessionStorage.getItem('currentSession');
            if (stored !== null) return parseInt(stored, 10);
            // Default to session 1
            sessionStorage.setItem('currentSession', '1');
            return 1;
        })(),

        /**
         * Prompt order counterbalancing — determines which prompt (asst/roleply) is shown in which session
         * 'asst_first': Session 1 = assistant prompt, Session 2 = role-play prompt
         * 'roleply_first': Session 1 = role-play prompt, Session 2 = assistant prompt
         * Random 50/50 assignment, persisted in sessionStorage
         */
        promptOrder: (() => {
            if (isDemoMode) {
                sessionStorage.setItem('promptOrder', 'asst_first');
                return 'asst_first';
            }
            const stored = sessionStorage.getItem('promptOrder');
            if (stored !== null) return stored;
            const order = Math.random() < 0.5 ? 'asst_first' : 'roleply_first';
            sessionStorage.setItem('promptOrder', order);
            return order;
        })(),

        /**
         * Shorten system prompt minimum character requirement (bypasses 100 char minimum)
         * URL: ?shortenPrompt=true
         * Default: false
         */
        shortenPrompt: urlParams.get('shortenPrompt') === 'true',
        
        /**
         * Use sunburst visualization for persona (vs bar chart)
         * URL: ?sunburst=true or ?sunburst=false
         * Default: false
         */
        sunburst: (() => {
            const sunburstParam = urlParams.get('sunburst');
            if (sunburstParam === null) {
                return false; // Default to false
            }
            return sunburstParam.toLowerCase() === 'true' || sunburstParam === '1';
        })(),

        /**
         * Cognitive forcing function highlights — blink the element that caused the biggest persona swing
         * Comma-separated list: 1=chat message bubble, 2=drift chart dot, 3=sunburst trait segment
         * URL: ?highlight=1  or  ?highlight=1,2,3
         * Default: [1,2,3] (all highlights enabled — only active when visualizationCondition=2)
         */
        highlight: (() => {
            const param = urlParams.get('highlight');
            if (!param) return [1, 2, 3];
            return param.split(',').map(s => parseInt(s.trim(), 10)).filter(n => !isNaN(n));
        })(),
        
        /**
         * Visualization condition - experimental control setting
         * 0 = Control condition (no visualization)
         * 1 = Experimental condition (with visualization)
         * URL: ?visualizationCondition=0 or ?visualizationCondition=1
         * Default: Random 50/50 assignment
         * Note: Demo mode always forces visualizationCondition=1
         */
        visualizationCondition: (() => {
            // Demo mode always shows visualization (condition 1)
            if (isDemoMode) {
                sessionStorage.setItem('visualizationCondition', '1');
                sessionStorage.setItem('conditionAssignmentMethod', 'demo_mode');
                return 1;
            }
            
            const conditionParam = urlParams.get('visualizationCondition');
            
            // Check for URL parameter override first
            if (conditionParam !== null) {
                const value = parseInt(conditionParam, 10);
                if (value === 0 || value === 1 || value === 2) {
                    // Store in sessionStorage to maintain across navigations
                    sessionStorage.setItem('visualizationCondition', value.toString());
                    sessionStorage.setItem('conditionAssignmentMethod', 'manual_url');
                    return value;
                }
            }
            
            // Check if already assigned in this session
            const storedCondition = sessionStorage.getItem('visualizationCondition');
            const storedMethod = sessionStorage.getItem('conditionAssignmentMethod');
            if (storedCondition !== null && storedMethod !== null) {
                return parseInt(storedCondition, 10);
            }
            
            // Forced control condition for run4
            sessionStorage.setItem('visualizationCondition', '0');
            sessionStorage.setItem('conditionAssignmentMethod', 'forced_control');
            return 0;
        })(),
    };
    
    return settings;
}

// ============================================
// DEFAULT SETTINGS (without URL parameters)
// ============================================
// Note: visualizationCondition uses random assignment, not a fixed default

let defaultSettings = {
    demo: false,
    debug: false,
    debugTimer: false,
    fresh: false,
    skip: false,
    skipSurvey: false,
    shortenPrompt: false,
    sunburst: false,
    visualizationCondition: null, // Random assignment (0=control, 1=single-turn, 2=multi-turn)
    highlight: [],
    currentSession: 1,
    promptOrder: null, // Random assignment (asst_first/roleply_first)
};

// ============================================
// INITIALIZE SETTINGS
// ============================================

// Create global settings object
window.experimentSettings = getExperimentSettingsFromURL();

// ============================================
// SESSION-AWARE HELPERS (must be defined before logging)
// ============================================

/**
 * Get the effective visualization condition for the current session.
 * Session 1 (baseline) ALWAYS returns 0 (no visualization) regardless of assigned condition.
 * Session 2 (experimental) returns the real assigned condition.
 * @returns {number} 0, 1, or 2
 */
window.getEffectiveVisualizationCondition = function() {
    const session = parseInt(sessionStorage.getItem('currentSession') || '1', 10);
    if (session === 1) return 0; // Baseline: no visualization for anyone
    return window.experimentSettings.visualizationCondition;
};

/**
 * Get the prompt type (asst/roleply) for a given session number.
 * @param {number} sessionNum - 1 or 2
 * @returns {string} 'ASST' or 'ROLEPLY'
 */
window.getSessionPromptType = function(sessionNum) {
    const order = sessionStorage.getItem('promptOrder') || 'asst_first';
    if (sessionNum === 1) return order === 'asst_first' ? 'ASST' : 'ROLEPLY';
    return order === 'asst_first' ? 'ROLEPLY' : 'ASST';
};

/**
 * Get the system prompt text for a given session number.
 * @param {number} sessionNum - 1 or 2
 * @returns {string} The system prompt text
 */
window.getSessionPromptText = function(sessionNum) {
    const type = window.getSessionPromptType(sessionNum);
    return (window.STUDY_CONTENT && window.STUDY_CONTENT.PROMPTS[type])
        ? window.STUDY_CONTENT.PROMPTS[type].text
        : '';
};

/**
 * Get the scripted conversation for a given session number.
 * @param {number} sessionNum - 1 or 2
 * @returns {Array} The conversation array
 */
window.getSessionConversation = function(sessionNum) {
    const type = window.getSessionPromptType(sessionNum);
    return (window.STUDY_CONTENT && window.STUDY_CONTENT.PROMPTS[type])
        ? window.STUDY_CONTENT.PROMPTS[type].conversation
        : [];
};

/**
 * Get the current session number from sessionStorage.
 * @returns {number} 1 or 2
 */
window.getCurrentSession = function() {
    return parseInt(sessionStorage.getItem('currentSession') || '1', 10);
};

/**
 * Advance to the next session (sets currentSession to 2).
 */
window.advanceToSession2 = function() {
    sessionStorage.setItem('currentSession', '2');
    window.experimentSettings.currentSession = 2;
    console.log('⏭️ Advanced to Session 2 (Experimental)');
};

// Debug: explicitly log demo flag and timestamp to verify new version is loaded
console.log('🔍 DEBUG [v2024-10-21-v2]: demo flag =', window.experimentSettings.demo);

// Log demo mode prominently if active
if (window.experimentSettings.demo) {
    console.log('');
    console.log('═══════════════════════════════════════════');
    console.log('   🎬 DEMO MODE ACTIVE');
    console.log('═══════════════════════════════════════════');
    console.log('Demo mode automatically enables:');
    console.log('  ✓ Skip consent page (go directly to avatar selection)');
    console.log('  ✓ Debug features enabled');
    console.log('  ✓ Skip surveys (pre-task and post-task)');
    console.log('  ✓ Visualization always shown');
    console.log('  ✓ Instruction modals kept (avatar, prompt, chat, viz, refinement)');
    console.log('═══════════════════════════════════════════');
    console.log('');
}

// Log settings on load (helpful for debugging)
console.log('⚙️ Experiment Settings Loaded:', window.experimentSettings);

// Log visualization condition prominently
const conditionName = ['CONTROL (No Visualization)', 'SINGLE-TURN (Static Visualization)', 'MULTI-TURN (Dynamic Visualization)'][window.experimentSettings.visualizationCondition] || 'UNKNOWN';
const conditionMethod = sessionStorage.getItem('conditionAssignmentMethod') || 'unknown';
console.log(`🔬 Visualization Condition: ${conditionName} (${conditionMethod})`);

// Log session state
const sessionNum = window.experimentSettings.currentSession;
const promptOrder = window.experimentSettings.promptOrder;
console.log(`📋 Session: ${sessionNum} (${sessionNum === 1 ? 'BASELINE' : 'EXPERIMENTAL'})`);
console.log(`🔀 Prompt Order: ${promptOrder} (Session 1 = ${window.getSessionPromptType(1)}, Session 2 = ${window.getSessionPromptType(2)})`);

// Log which settings were overridden by URL parameters
const urlParams = new URLSearchParams(window.location.search);
if (urlParams.toString()) {
    console.log('🔗 URL Parameters Active:', urlParams.toString());
    
    // Show which specific settings were changed from defaults
    const changedSettings = [];
    for (const [key, value] of Object.entries(window.experimentSettings)) {
        if (JSON.stringify(value) !== JSON.stringify(defaultSettings[key])) {
            changedSettings.push(`  • ${key}: ${JSON.stringify(value)} (default: ${JSON.stringify(defaultSettings[key])})`);
        }
    }
    
    if (changedSettings.length > 0) {
        console.log('📝 Settings Changed from Defaults:\n' + changedSettings.join('\n'));
    }
} else {
    console.log('✅ Using all default settings (no URL parameters)');
}

// ============================================
// UTILITY FUNCTIONS
// ============================================

/**
 * Get a specific setting value
 * @param {string} key - Setting key
 * @returns {*} Setting value
 */
window.getSetting = function(key) {
    return window.experimentSettings[key];
};

/**
 * Update a setting at runtime (useful for dynamic changes)
 * @param {string} key - Setting key
 * @param {*} value - New value
 */
window.updateSetting = function(key, value) {
    console.log(`⚙️ Setting updated: ${key} = ${JSON.stringify(value)}`);
    window.experimentSettings[key] = value;
};

// ============================================
// BACKWARD COMPATIBILITY HELPERS
// ============================================

/**
 * Legacy function for checking sunburst display mode
 * Kept for backward compatibility with existing code
 * @returns {boolean}
 */
window.useSunburstDisplay = function() {
    return window.experimentSettings.sunburst;
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        experimentSettings: window.experimentSettings,
        getSetting: window.getSetting,
        updateSetting: window.updateSetting,
        useSunburstDisplay: window.useSunburstDisplay
    };
}
