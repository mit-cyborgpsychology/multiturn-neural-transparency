// initialize firebase
// Your web app's Firebase configuration
const firebaseConfig = {
    apiKey: "AIzaSyBnlqrGcIfgo59WCzure6azGQitEQaGhZg",
    authDomain: "mech-chat-ee0c5.firebaseapp.com",
    databaseURL: "https://mech-chat-ee0c5-default-rtdb.firebaseio.com",
    projectId: "mech-chat-ee0c5",
    storageBucket: "mech-chat-ee0c5.firebasestorage.app",
    messagingSenderId: "1027129084043",
    appId: "1:1027129084043:web:ece77d746e79110f98ec8e"
};

// Import Firebase functions from v1.0 (auto-initializes)
// Conditional: when FIREBASE_ENABLED is false, provide no-op stubs
let writeRealtimeDatabase, writeURLParameters, readRealtimeDatabase,
    blockRandomization, finalizeBlockRandomization, firebaseUserId;
if (window.FIREBASE_ENABLED !== false) {
    ({ writeRealtimeDatabase, writeURLParameters, readRealtimeDatabase,
       blockRandomization, finalizeBlockRandomization, firebaseUserId
    } = await import("./firebasepsych1.0.js"));
} else {
    writeRealtimeDatabase = async () => {};
    writeURLParameters = async () => {};
    readRealtimeDatabase = async () => ({});
    blockRandomization = async () => 0;
    finalizeBlockRandomization = async () => {};
    firebaseUserId = 'demo-user-' + Date.now();
    console.log('🔥 Firebase DISABLED — all writes are no-ops');
}

// Clear only chat-related sessionStorage keys to ensure fresh chat experience.
// IMPORTANT: Do NOT clear experiment-level keys (firebaseUserId, visualizationCondition,
// conditionAssignmentMethod, currentSession, promptOrder) — these must persist across
// page navigations within the experiment.
const chatSessionKeys = ['instructionsShown'];
chatSessionKeys.forEach(key => sessionStorage.removeItem(key));

// Ensure firebaseUserId is in sessionStorage for access by other pages
if (!sessionStorage.getItem('firebaseUserId') && firebaseUserId) {
    sessionStorage.setItem('firebaseUserId', firebaseUserId);
}

// Clear localStorage states so each session starts fresh
localStorage.removeItem('selectedAvatar');
localStorage.removeItem('customSystemPrompt');

// Write a simple test case to the database
let studyId;
// studyId='multiturn-pilot1';
studyId='multiturn-run4'
// if (DEBUG){
//     studyId = 'multiturn';
// } else {
//     studyId = 'exp2';
// }
// Expose globally so task1/task3/task4 pages can write to the same study path
window.studyId = studyId;

const testPath = studyId + '/participantData/' + firebaseUserId + '/testMessage';
const testValue = {
    message: "Hello from chat.js!",
    timestamp: new Date().toISOString(),
    value: 42
};

await writeRealtimeDatabase(testPath, testValue);

// Write URL parameters to Firebase
const urlParamsPath = studyId + '/participantData/' + firebaseUserId + '/urlParameters';
await writeURLParameters(urlParamsPath);

// Write visualization condition assignment to Firebase
const conditionPath = studyId + '/participantData/' + firebaseUserId + '/experimentCondition';
const conditionData = {
    visualizationCondition: window.experimentSettings.visualizationCondition,
    conditionName: ['control', 'single_turn', 'multi_turn'][window.experimentSettings.visualizationCondition] || 'unknown',
    assignmentMethod: sessionStorage.getItem('conditionAssignmentMethod') || 'unknown',
    promptOrder: window.experimentSettings.promptOrder,
    session1PromptType: window.getSessionPromptType(1),
    session2PromptType: window.getSessionPromptType(2),
    timestamp: new Date().toISOString()
};

// IMPORTANT: Log experiment condition explicitly
console.log('=== EXPERIMENT CONDITION ===');
console.log('Condition:', conditionData.conditionName.toUpperCase());
console.log('Visualization:', ['DISABLED (Control)', 'STATIC (Single-turn)', 'DYNAMIC (Multi-turn)'][conditionData.visualizationCondition] || 'UNKNOWN');
console.log('Assignment Method:', conditionData.assignmentMethod);
console.log('============================');

await writeRealtimeDatabase(conditionPath, conditionData);

// ── Flush pending writes from pre-chat pages (preSurvey, promptReading, MBA) ──
// These were queued in sessionStorage because those pages can't import modules.
const pendingWrites = JSON.parse(sessionStorage.getItem('_pendingWrites') || '[]');
if (pendingWrites.length > 0) {
    console.log('📤 Flushing ' + pendingWrites.length + ' pending writes to Firebase...');
    for (const entry of pendingWrites) {
        const fullPath = studyId + '/participantData/' + firebaseUserId + '/' + entry.path;
        try {
            await writeRealtimeDatabase(fullPath, entry.data);
            console.log('  ✅ Flushed:', entry.path);
        } catch (e) {
            console.error('  ❌ Failed to flush:', entry.path, e);
        }
    }
    // Clear the queue
    sessionStorage.removeItem('_pendingWrites');
    window._pendingWrites = [];
    console.log('📤 Flush complete');
}

// Replace queuing writeTaskData with direct version now that we have module access
window.writeTaskData = async function(path, data) {
    var uid = firebaseUserId || sessionStorage.getItem('firebaseUserId') || 'uid-unknown';
    var fullPath = studyId + '/participantData/' + uid + '/' + path;
    console.log('writeTaskData (direct):', fullPath);
    await writeRealtimeDatabase(fullPath, data);
};

// ── Interaction logger: lightweight Firebase writes for UI analytics ──
window.logInteraction = async function(event, detail) {
    try {
        const session = window.getCurrentSession ? window.getCurrentSession() : null;
        const path = studyId + '/participantData/' + firebaseUserId + '/session' + session + '/interactionLog/' + Date.now();
        await writeRealtimeDatabase(path, {
            event: event,
            detail: detail || {},
            timestamp: new Date().toISOString()
        });
    } catch (e) {
        // Silent fail — don't disrupt UX for analytics
    }
};

// Enhanced Chat Interface JavaScript with System Prompt Configuration
// Always reset chat state on load so each session starts fresh
window.messageIdCounter = 1;
window.conversationHistory = [];
window.personaHistory = [];
window.personaTurnMessageIds = [];
window.lastUserMessageId = null;
window.currentSwing = null;
window.activeDriftTrait = null;
window.sunburstOppositeLayout = false;
window.currentPersonaData = null;
window.lastSystemPrompt = null;
window.systemPromptSubmitted = false;
window.personaCheckedForCurrentPrompt = false;
window.promptHasChangedSinceSubmit = false;

// Chat ended flag — tracks whether predict-behavior flow has been triggered
window.chatEnded = false;

// Note: API configuration is loaded from config-unified.js file

// Avatar selection state
window.selectedAvatar = null; // Will store the avatar image path

$(document).ready(function() {
    // Initialize the dynamic interface
    initializeDynamicInterface();
});

function initializeDynamicInterface() {
    const avatarSelectionInterface = $('#avatarSelectionInterface');
    const systemPromptInterface = $('#systemPromptInterface');
    const chatInterface = $('#chatInterface');
    const messagesContainer = $('#messagesContainer');
    const messageInput = $('#messageInput');
    const sendBtn = $('#sendBtn');
    const typingIndicator = $('#typingIndicator');
    const attachBtn = $('#attachBtn');
    const imageBtn = $('#imageBtn');
    let isWaiting = false;

    // System prompt configuration elements
    const resetConfig = $('#resetConfig');
    const startChatBtn = $('#startChatBtn');
    const backToConfigBtn = $('#backToConfigBtn');

    // Check for URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    const debugMode = urlParams.get('debug') === 'true';
    const skipSurvey = urlParams.get('skipSurvey') === 'true';
    const freshMode = urlParams.get('fresh') === 'true';
    
    // Fresh mode: Already handled in index.html, but keep for direct navigation to chat
    if (freshMode) {
        // If somehow we got here with fresh=true still in URL, clear it
        const newUrl = new URL(window.location);
        if (newUrl.searchParams.has('fresh')) {
            newUrl.searchParams.delete('fresh');
            window.history.replaceState({}, '', newUrl);
        }
    }
    
    // SessionStorage is already cleared at the top of this file for fresh experience on every load
    
    // Auto-assign a random avatar and go straight to system prompt config
    initializeAvatarSelection();

    // Initialize system prompt configuration
    initializeSystemPromptConfig();

    // Initialize chat functionality
    initializeChatFunctionality();

    async function initializeAvatarSelection() {
        // Avatar selection step removed — pick randomly and proceed immediately
        const avatarCount = 12;
        const randomIndex = Math.floor(Math.random() * avatarCount) + 1;
        const avatarPath = `Avatar/avatar-${randomIndex}.jpg`;

        window.selectedAvatar = avatarPath;
        localStorage.setItem('selectedAvatar', avatarPath);

        // Go directly to system prompt config (hide avatar screen, show prompt screen)
        $('#avatarSelectionInterface').hide();
        // switchToSystemPromptConfig(); // "Your System Prompt" page skipped — go straight to chat
        switchToChat();
    }

    function initializeSystemPromptConfig() {
        // Get the system prompt input
        const systemPromptInput = $('#systemPromptInput');

        // LocalStorage already cleared at the top of this file for fresh experience

        // Get effective visualization condition (Session 1 = always 0, Session 2 = real condition)
        const visualizationCondition = window.getEffectiveVisualizationCondition();
        const currentSession = window.getCurrentSession();

        // IMPORTANT: Log condition explicitly
        console.log('=== SYSTEM PROMPT CONFIG INITIALIZATION ===');
        console.log('Session:', currentSession, currentSession === 1 ? '(BASELINE)' : '(EXPERIMENTAL)');
        console.log('Effective Visualization Condition:', ['CONTROL (no-viz)', 'SINGLE-TURN (static viz)', 'MULTI-TURN (dynamic viz)'][visualizationCondition] || 'UNKNOWN');
        console.log('==========================================');

        // ── Pre-fill system prompt from session-specific content ──────────────
        const sessionPrompt = window.getSessionPromptText(currentSession);
        systemPromptInput.val(sessionPrompt).prop('readonly', true);

        // Hide editing controls — prompt is pre-determined
        $('#characterCounter').hide();
        $('#resetConfig').hide();

        // Persona vectors are pre-loaded and cached in preloadModels() — no extra fetch needed here
        if (sessionPrompt && window.cachedPersonaVectors && window.cachedPersonaVectors[sessionPrompt]) {
            window.backgroundPersonaData = window.cachedPersonaVectors[sessionPrompt];
            console.log('✅ Using cached persona analysis from preload');
        }

        // Always start with Check/Test Persona buttons hidden
        $('.persona-check-buttons').hide();

        // Hide visualization elements if in control condition
        if (visualizationCondition === 0) {
            // Hide persona visualization container permanently
            $('#personaVisualization').remove();
            // Hide visualization help button
            $('#visualizationHelpBtn').remove();
            // Hide toggle layout button
            $('#toggleLayoutBtn').remove();
        }

        // Check for debug mode - hide Test Persona button if not in debug mode
        const urlParams = new URLSearchParams(window.location.search);
        const debugMode = urlParams.get('debug') === 'true';
        if (!debugMode) {
            $('#testPersonaBtn').hide();
        }

        // Character counter functionality
        const MIN_CHAR_LENGTH = 100;
        const shortenPrompt = urlParams.get('shortenPrompt') === 'true';
        
        const updateCharacterCounter = function() {
            const currentLength = systemPromptInput.val().length;
            $('#charCount').text(currentLength);

            if (shortenPrompt || currentLength >= MIN_CHAR_LENGTH) {
                $('#characterCounter').css('color', 'var(--success-color, #28a745)');
            } else {
                $('#characterCounter').css('color', 'var(--text-secondary)');
            }
        };
        
        // Update counter text if bypass is enabled
        if (shortenPrompt) {
            $('#characterCounter').html('<span id="charCount">0</span> characters (minimum bypassed)');
        }
        
        // Initialize character counter on page load
        updateCharacterCounter();

        // Update character counter on input
        systemPromptInput.on('input', updateCharacterCounter);

        // Preload everything based on condition — no Submit Prompt button needed
        window.systemPromptSubmitted = true;
        window.promptHasChangedSinceSubmit = false;

        if (visualizationCondition === 0) {
            // Control: auto-run persona check, show trait definitions, enable Start Chat
            $('#initialPlaceholder').show();
            $('#personaVisualization').hide();
            autoSubmitPersonaCheck(sessionPrompt);
        } else {
            // Viz conditions: show Check Persona button immediately
            $('#initialPlaceholder').show();
            $('#initialPlaceholder').html(`
                <div style="text-align: center; color: var(--text-muted); padding: 3rem 2rem;">
                    <i class="fas fa-arrow-right" style="font-size: 3rem; margin-bottom: 1rem; opacity: 0.3;"></i>
                    <p style="margin: 0; font-size: 1.1rem;">Click "Check Persona" to see your persona analysis</p>
                </div>
            `);
            $('#personaVisualization').hide();
            $('.persona-check-buttons').show();
            $('#startChatBtn').prop('disabled', true);
        }

        // Reset configuration
        resetConfig.on('click', async function() {
            systemPromptInput.val('');
            updateCharacterCounter(); // Update the counter to show 0
            
            // Reset state flags
            window.systemPromptSubmitted = false;
            window.personaCheckedForCurrentPrompt = false;
            window.promptHasChangedSinceSubmit = false;
            
            // Hide Check/Test Persona buttons
            $('.persona-check-buttons').hide();
            
            // Disable Start Chat button
            $('#startChatBtn').prop('disabled', true);
            
            // Reset visualizations (only if in viz condition)
            const visualizationCondition = window.getEffectiveVisualizationCondition();
            if (visualizationCondition >= 1) {
                $('#personaVisualization').hide();
            }
            
            $('#initialPlaceholder').show();

            // Log this reset action to Firebase
            const promptLogPath = studyId + '/participantData/' + firebaseUserId + '/session' + window.getCurrentSession() + '/systemPromptLog/' + Date.now();
            await writeRealtimeDatabase(promptLogPath, {
                prompt: '',
                action: 'reset_to_empty',
                timestamp: new Date().toISOString()
            });
        });

        // Submit Prompt button removed — persona preloaded automatically on init

        // Start chat
        startChatBtn.on('click', async function() {
            window.logInteraction('prompt_toggle', { direction: 'prompt_to_chat' });
            const systemPrompt = $('#systemPromptInput').val();
            
            // Check if system prompt has changed
            const promptChanged = window.lastSystemPrompt !== null && window.lastSystemPrompt !== systemPrompt;
            
            if (promptChanged) {
                // Log the chat history clear event to Firebase
                const clearLogPath = studyId + '/participantData/' + firebaseUserId + '/session' + window.getCurrentSession() + '/chatHistoryClearLog/' + Date.now();
                await writeRealtimeDatabase(clearLogPath, {
                    previousPrompt: window.lastSystemPrompt,
                    newPrompt: systemPrompt,
                    timestamp: new Date().toISOString(),
                    reason: 'system_prompt_changed'
                });
                
                // Clear conversation history
                window.conversationHistory = [];
                // Clear chat UI
                const messagesContainer = $('#messagesContainer');
                messagesContainer.empty();
                // Reset message counter
                window.messageIdCounter = 1;
            }
            
            // Update last system prompt
            window.lastSystemPrompt = systemPrompt;
            
            // Store system prompt in localStorage for the chat interface
            localStorage.setItem('customSystemPrompt', systemPrompt);
            
            // Log this system prompt attempt to Firebase
            const promptLogPath = studyId + '/participantData/' + firebaseUserId + '/session' + window.getCurrentSession() + '/systemPromptLog/' + Date.now();
            await writeRealtimeDatabase(promptLogPath, {
                prompt: systemPrompt,
                action: 'start_chat',
                timestamp: new Date().toISOString()
            });
            
            // Save system prompt to Firebase
            const systemPromptPath = studyId + '/participantData/' + firebaseUserId + '/session' + window.getCurrentSession() + '/systemPrompt';
            await writeRealtimeDatabase(systemPromptPath, {
                prompt: systemPrompt,
                timestamp: new Date().toISOString()
            });
            
            // Show the End Chat button
            $('#endChatBar').show();

            // Switch to chat interface
            switchToChat();
        });

        // Check Persona button - analyze persona with API (disabled after first use to prevent duplicate history entries)
        $('#checkPersonaBtn').on('click', async function() {
            // Remove focus from button to return to default state
            $(this).blur();

            // Prevent multiple calls — disable immediately on first click
            $(this).prop('disabled', true).text('Analyzing...');

            // Get the current system prompt from the input
            const systemPrompt = $('#systemPromptInput').val();

            // Log this system prompt attempt to Firebase
            const promptLogPath = studyId + '/participantData/' + firebaseUserId + '/session' + window.getCurrentSession() + '/systemPromptLog/' + Date.now();
            await writeRealtimeDatabase(promptLogPath, {
                prompt: systemPrompt,
                action: 'check_persona',
                timestamp: new Date().toISOString()
            });

            // Mark that persona has been checked for current prompt
            window.personaCheckedForCurrentPrompt = true;

            // Enable Start Chat button now that persona is checked
            $('#startChatBtn').prop('disabled', false);

            // Hide placeholder, show persona visualization area
            $('#initialPlaceholder').hide();
            $('#personaVisualization').show();

            // Show visualization explanation modal
            window.showVisualizationExplanation();

            // Call persona check
            await checkPersona(systemPrompt);
            $('#checkPersonaBtn').text('Persona Analyzed');
        });

        // Test Persona button - generate mock data
        $('#testPersonaBtn').on('click', async function() {
            // Remove focus from button to return to default state
            $(this).blur();
            
            // Get the current system prompt from the input
            const systemPrompt = $('#systemPromptInput').val();
            
            // Log this system prompt attempt to Firebase
            const promptLogPath = studyId + '/participantData/' + firebaseUserId + '/session' + window.getCurrentSession() + '/systemPromptLog/' + Date.now();
            await writeRealtimeDatabase(promptLogPath, {
                prompt: systemPrompt,
                action: 'test_persona',
                timestamp: new Date().toISOString()
            });
            
            // Mark that persona has been checked for current prompt (test counts as check)
            window.personaCheckedForCurrentPrompt = true;
            
            // Enable Start Chat button now that persona is checked
            $('#startChatBtn').prop('disabled', false);
            
            // Hide placeholder, show persona visualization area
            $('#initialPlaceholder').hide();
            $('#personaVisualization').show();
            
            // Show visualization explanation modal
            window.showVisualizationExplanation();
            
            // Generate test persona
            testPersonaWithMockData();
        });

        // Visualization Help button - show explanation modal
        // Use event delegation since the button is loaded asynchronously
        $(document).on('click', '#visualizationHelpBtn', function() {
            // Remove focus from button to return to default state
            $(this).blur();
            
            // Show the visualization explanation modal (force show)
            window.showVisualizationExplanation(true);
        });

        // Dismiss visualization explanation modal
        $(document).on('click', '#dismissVisualizationExplanation', function() {
            window.dismissVisualizationExplanation();
        });

        // Dismiss prompt refinement modal
        $(document).on('click', '#dismissPromptRefinement', function() {
            window.dismissPromptRefinementModal();
        });

        // Toggle Layout button - switch between opposite and mirrored layouts
        // Use event delegation since the button is loaded asynchronously
        $(document).on('click', '#toggleLayoutBtn', function() {
            // Remove focus from button to return to default state
            $(this).blur();
            
            // Toggle the layout mode
            window.sunburstOppositeLayout = !window.sunburstOppositeLayout;
            
            // Update button text
            const modeText = window.sunburstOppositeLayout ? 'Opposite' : 'Mirrored';
            $('#layoutModeText').text(modeText);
            
            // Redraw the sunburst if we have persona data
            if (window.currentPersonaData && typeof createPersonaSunburst === 'function') {
                const configChartEl = document.getElementById('personaChart');
                const cw = Math.max(configChartEl ? configChartEl.clientWidth : 700, 300);
                const ch = Math.max(configChartEl ? configChartEl.clientHeight : 700, 300);
                createPersonaSunburst(window.currentPersonaData, 'personaChartSunburst', {
                    width: cw,
                    height: ch,
                    innerRadius: 65,
                    animate: true,
                    oppositeLayout: window.sunburstOppositeLayout
                });
            }
        });

        // Helper function to show/hide persona sections
        window.showPersonaVisualization = function() {
            $('#personaVisualization').show();
            $('#personaPlaceholder').hide();
        };

        window.hidePersonaVisualization = function() {
            $('#personaVisualization').hide();
            $('#personaPlaceholder').show();
        };

        // The drift panel's close (✕) handler was removed along with the button — the panel
        // stays open for the whole conversation.

        // Drift panel info button
        $(document).on('click', '#driftInfoBtn', function() {
            $(this).blur();
            $('#driftInfoInstructionModal').fadeIn(300);
        });

        // Delegated click on any sunburst trait segment or label — survives re-renders
        $(document).on('click', '#chatPersonaPanel [data-trait-name]', function() {
            const rawName = $(this).attr('data-trait-name').toLowerCase();
            window.activeDriftTrait = rawName;
            renderTraitDrift(rawName);
        });

        // Click a highlighted message → jump to drift panel + sunburst for that swing
        $(document).on('click', '.message.highlight-swing-msg', function() {
            const swing = window.currentSwing;
            if (!swing) return;
            // Open drift panel to the swung trait and highlight the dot
            applyDriftDotHighlight(swing);
            // Highlight the sunburst segment
            applySunburstHighlight(swing);
            // Scroll the persona panel into view
            const panel = document.getElementById('chatPersonaPanel');
            if (panel) panel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        });

        // Back to configuration
        backToConfigBtn.on('click', function() {
            window.logInteraction('prompt_toggle', { direction: 'chat_to_prompt' });
            switchToSystemPromptConfig();
        });

    }

    function initializeChatFunctionality() {
        // Enable/disable send button based on input
        messageInput.on('input', function() {
            sendBtn.prop('disabled', isWaiting || messageInput.val().trim() === '');
        });

        // Auto-resize textarea
        messageInput.on('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 120) + 'px';
        });

        // Event listeners
        sendBtn.on('click', sendMessage);

        messageInput.on('keypress', function(e) {
            if (e.which === 13 && !e.shiftKey && !isWaiting) {
                e.preventDefault();
                sendMessage();
            }
        });

        // End Chat button
        $('#endChatBtn').on('click', function() {
            endChatAndPredict();
        });

        // Skip straight to the prediction quiz from the visualization panel header
        $('#skipToPredictBtn').on('click', function() {
            $(this).blur();
            window.logInteraction('skip_to_predict', { turnsCompleted: window.conversationHistory ? window.conversationHistory.filter(function(m) { return m.role === 'user'; }).length : 0 });
            endChatAndPredict();
        });

        // Attach button functionality
        attachBtn.on('click', function() {
            // Placeholder for file attachment
            alert('File attachment feature would be implemented here');
        });

        // Image button functionality
        imageBtn.on('click', function() {
            // Placeholder for image sending
            alert('Image sending feature would be implemented here');
        });
    }

    // Send message function
    const MAX_USER_TURNS = window.MAX_CHAT_TURNS || 10;
    async function sendMessage() {
        const message = messageInput.val().trim();
        if (message === '') return;

        // Count user turns so far
        const userTurnCount = window.conversationHistory.filter(m => m.role === 'user').length;
        if (userTurnCount >= MAX_USER_TURNS) {
            messageInput.prop('disabled', true).attr('placeholder', 'Chat complete (' + MAX_USER_TURNS + ' turns reached)');
            sendBtn.prop('disabled', true);
            return;
        }

        // Add user message to conversation history first
        window.conversationHistory.push({
            role: 'user',
            content: message
        });

        // Add user message to UI and save to Firebase
        const userMessageId = await addMessage(message, 'user');
        window.lastUserMessageId = userMessageId; // record for persona-turn correlation
        messageInput.val('');
        messageInput.css('height', 'auto');
        isWaiting = true;
        messageInput.prop('disabled', true);
        sendBtn.prop('disabled', true);

        // Show typing indicator
        typingIndicator.show();

        // Call AI API for response
        callAIAPI(message);
    }

    function unlockInput() {
        isWaiting = false;
        messageInput.prop('disabled', false);
        sendBtn.prop('disabled', messageInput.val().trim() === '');
        messageInput.focus();
    }

    // Function to call AI API (generalized for both Claude and Modal)
    async function callAIAPI(userMessage) {
        try {
            // Get custom system prompt from localStorage, fallback to default
            const customSystemPrompt = localStorage.getItem('customSystemPrompt') || 
                window.getSessionPromptText(window.getCurrentSession());

            const requestData = {
                model: API_CONFIG.model,
                max_tokens: API_CONFIG.maxTokens,
                messages: window.conversationHistory
                // system: customSystemPrompt // system prompt no longer injected into API calls
            };

            // Score persona on context up to and including the user's message (before assistant responds)
            const _vc = window.getEffectiveVisualizationCondition();
            checkPersona(customSystemPrompt, window.conversationHistory, _vc !== 2, window.lastUserMessageId);

            const data = await makeAPIRequest(requestData);

            // Hide typing indicator and re-enable input
            typingIndicator.hide();
            unlockInput();

            // Extract the assistant's response
            const assistantMessage = data.content[0].text;

            // Add assistant message to conversation history
            window.conversationHistory.push({
                role: 'assistant',
                content: assistantMessage
            });

            // Add assistant message to chat and save to Firebase
            await addMessage(assistantMessage, 'assistant');

            // Update turn counter and check if limit reached
            const turnsUsed = window.conversationHistory.filter(m => m.role === 'user').length;
            const counterEl = document.getElementById('np-turn-counter');
            if (counterEl) {
                counterEl.textContent = 'Turn ' + turnsUsed + ' / ' + MAX_USER_TURNS;
                if (turnsUsed >= MAX_USER_TURNS) {
                    counterEl.textContent = 'Complete';
                    counterEl.style.color = 'var(--green)';
                }
            }
            if (turnsUsed >= MAX_USER_TURNS) {
                messageInput.prop('disabled', true).attr('placeholder', 'Chat complete (' + MAX_USER_TURNS + ' turns reached)');
                sendBtn.prop('disabled', true);
                // Auto-trigger predict behavior flow after a brief pause
                if (!window.chatEnded) {
                    setTimeout(function() { endChatAndPredict(); }, 800);
                }
            }

        } catch (error) {
            console.error('Error calling AI API:', error);
            
            // Hide typing indicator and re-enable input
            typingIndicator.hide();
            unlockInput();

            // Show appropriate error message based on error type
            let errorMessage;
            if (error.message.includes('API key not found') || error.message.includes('not configured')) {
                errorMessage = `API configuration error: ${error.message}. Please check your API settings.`;
            } else if (error.message.includes('CORS')) {
                errorMessage = `CORS Error: ${error.message}. This might be due to network restrictions. Please try again or contact the study administrator.`;
            } else if (error.message.includes('Rate limit exceeded')) {
                errorMessage = `Rate limit exceeded. Please wait a moment and try again.`;
            } else if (error.message.includes('Invalid API key') || error.message.includes('Invalid')) {
                errorMessage = `Invalid configuration: ${error.message}. Please check your API settings and try again.`;
            } else {
                errorMessage = `Error: ${error.message}. Please try again or contact the study administrator.`;
            }
            
            // Add error message to conversation history
            window.conversationHistory.push({
                role: 'assistant',
                content: errorMessage
            });
            
            // Add error message to chat and save to Firebase
            await addMessage(errorMessage, 'assistant');
        }
    }

    // Add message to chat with enhanced features
    async function addMessage(text, sender) {
        const messageId = window.messageIdCounter++;
        const messageClass = sender === 'user' ? 'user-message' : 'assistant-message';
        const senderName = sender === 'user' ? 'You' : 'Assistant';
        const currentTime = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        const timestamp = new Date().toISOString();
        
        // Get the current system prompt being used
        const currentSystemPrompt = localStorage.getItem('customSystemPrompt') || 
            window.getSessionPromptText(window.getCurrentSession());
        
        const messageHtml = `
            <div class="message ${messageClass}" data-message-id="${messageId}">
                <div class="message-content">
                    <div class="message-text">${text}</div>
                </div>
            </div>
        `;
        
        messagesContainer.append(messageHtml);
        messagesContainer.scrollTop(messagesContainer[0].scrollHeight);

        // Apply persona-based gradient to this specific assistant message
        if (sender === 'assistant' && window._pendingGradientScores) {
            updateAssistantMessageGradient(window._pendingGradientScores, messageId);
            window._pendingGradientScores = null;
        }
        
        // Save message to Firebase with system prompt
        const messagePath = studyId + '/participantData/' + firebaseUserId + '/session' + window.getCurrentSession() + '/messages/' + messageId;
        const messageData = {
            messageId: messageId,
            role: sender,
            content: text,
            timestamp: timestamp,
            systemPrompt: currentSystemPrompt
        };
        await writeRealtimeDatabase(messagePath, messageData);
        
        // Also save the full conversation history after each message
        const conversationPath = studyId + '/participantData/' + firebaseUserId + '/session' + window.getCurrentSession() + '/conversationHistory';
        await writeRealtimeDatabase(conversationPath, window.conversationHistory);
        
        return messageId;
    }


    // Interface switching functions
    function switchToChat() {
        avatarSelectionInterface.hide();
        systemPromptInterface.hide();
        chatInterface.show();
        document.body.classList.add('chat-active');

        const chatVizCondition = window.getEffectiveVisualizationCondition();

        $('#chatPersonaPanel h4').first().text(chatVizCondition === 0 ? 'Traits to Monitor' : 'Internal Behavior Analysis');

        // Control condition: shrink left panel and show trait reference list
        if (chatVizCondition === 0) {
            $('#chatPersonaPanel').css({ width: '30%', minWidth: '220px' });
            $('#chatPersonaChart').html(`
                <div style="flex: 1; min-height: 0; display: flex; flex-direction: column; overflow: hidden; padding: 1rem;">
                    <p style="flex-shrink: 0; font-size: clamp(0.7rem, 1.3vh, 0.95rem); margin-bottom: 0.85rem; color: var(--text-secondary); line-height: 1.3;">
                        Monitor these personality dimensions as you interact:
                    </p>
                    <div style="flex: 1; min-height: 0; display: flex; flex-direction: column;">
                        <div style="flex: 1; padding: 0.45rem 0.6rem; border-left: 3px solid #4caf50; background: #f8f9fa; display: flex; flex-direction: column; justify-content: center;">
                            <h5 style="margin: 0 0 0.2rem 0; font-size: clamp(0.8rem, 1.6vh, 1.2rem); color: #2c3e50;">Empathy</h5>
                            <p style="margin: 0; font-size: clamp(0.7rem, 1.3vh, 1rem); color: #555; line-height: 1.3;"><strong>Unempathetic ↔ Empathetic</strong></p>
                        </div>
                        <div style="flex: 1; padding: 0.45rem 0.6rem; border-left: 3px solid #9e9e9e; background: #f8f9fa; display: flex; flex-direction: column; justify-content: center; margin-top: 0.4rem;">
                            <h5 style="margin: 0 0 0.2rem 0; font-size: clamp(0.8rem, 1.6vh, 1.2rem); color: #2c3e50;">Sophisticated</h5>
                            <p style="margin: 0; font-size: clamp(0.7rem, 1.3vh, 1rem); color: #555; line-height: 1.3;"><strong>Simplistic ↔ Sophisticated</strong></p>
                        </div>
                        <div style="flex: 1; padding: 0.45rem 0.6rem; border-left: 3px solid #9e9e9e; background: #f8f9fa; display: flex; flex-direction: column; justify-content: center; margin-top: 0.4rem;">
                            <h5 style="margin: 0 0 0.2rem 0; font-size: clamp(0.8rem, 1.6vh, 1.2rem); color: #2c3e50;">Robotic</h5>
                            <p style="margin: 0; font-size: clamp(0.7rem, 1.3vh, 1rem); color: #555; line-height: 1.3;"><strong>Human-like ↔ Robotic</strong></p>
                        </div>
                        <div style="flex: 1; padding: 0.45rem 0.6rem; border-left: 3px solid #f44336; background: #f8f9fa; display: flex; flex-direction: column; justify-content: center; margin-top: 0.4rem;">
                            <h5 style="margin: 0 0 0.2rem 0; font-size: clamp(0.8rem, 1.6vh, 1.2rem); color: #2c3e50;">Romantic</h5>
                            <p style="margin: 0; font-size: clamp(0.7rem, 1.3vh, 1rem); color: #555; line-height: 1.3;"><strong>Platonic ↔ Romantic</strong></p>
                        </div>
                        <div style="flex: 1; padding: 0.45rem 0.6rem; border-left: 3px solid #f44336; background: #f8f9fa; display: flex; flex-direction: column; justify-content: center; margin-top: 0.4rem;">
                            <h5 style="margin: 0 0 0.2rem 0; font-size: clamp(0.8rem, 1.6vh, 1.2rem); color: #2c3e50;">Sycophantic</h5>
                            <p style="margin: 0; font-size: clamp(0.7rem, 1.3vh, 1rem); color: #555; line-height: 1.3;"><strong>Honest ↔ Sycophantic</strong></p>
                        </div>
                        <div style="flex: 1; padding: 0.45rem 0.6rem; border-left: 3px solid #f44336; background: #f8f9fa; display: flex; flex-direction: column; justify-content: center; margin-top: 0.4rem;">
                            <h5 style="margin: 0 0 0.2rem 0; font-size: clamp(0.8rem, 1.6vh, 1.2rem); color: #2c3e50;">Toxic</h5>
                            <p style="margin: 0; font-size: clamp(0.7rem, 1.3vh, 1rem); color: #555; line-height: 1.3;"><strong>Respectful ↔ Toxic</strong></p>
                        </div>
                    </div>
                </div>
            `);
            $('#traitDriftPanel').hide();
        }

        // Single-turn condition: hide trait drift panel (no dynamic updates)
        if (chatVizCondition === 1) {
            $('#traitDriftPanel').hide();
        }

        // Before any user message, show the sunburst with every trait at 0% rather than
        // leaving the panel blank. Turn 0 is no longer pushed into personaHistory (the
        // drift panel intentionally only shows real chat turns) — the first real push
        // happens after the user's first message, at which point renderPersonaChart /
        // renderTraitDrift take over with real data.
        if (chatVizCondition === 2) {
            var zeroScores = {
                empathy: { empathetic: 0, unempathetic: 0 },
                erudite: { sophisticated: 0, simplistic: 0 },
                robotic: { robotic: 0, 'human-like': 0 },
                romantic: { romantic: 0, platonic: 0 },
                sycophantic: { sycophancy: 0, honest: 0 },
                toxic: { toxic: 0, respectful: 0 }
            };
            renderPersonaChart(zeroScores, 'chatPersonaChart');
            // Default-select a trait so the drift panel populates immediately once real
            // turn data starts arriving, without requiring the user to click a segment first.
            window.activeDriftTrait = 'honest';
        }
        /* Old flow: seeded Turn 0 in personaHistory from cached system-prompt-only persona
           data and rendered the drift panel from it immediately. Removed because the drift
           panel no longer displays turn 0 at all — kept here for reference / easy revert.
        if (chatVizCondition === 2 && window.personaHistory.length === 0) {
            var initialScores = null;
            // Try cached persona vectors (preloaded by config-unified.js)
            if (window.currentPersonaData) {
                initialScores = window.currentPersonaData;
            } else if (window.backgroundPersonaData) {
                initialScores = window.backgroundPersonaData.content || window.backgroundPersonaData;
            } else if (window.cachedPersonaVectors) {
                var prompt = localStorage.getItem('customSystemPrompt') ||
                    (window.getSessionPromptText ? window.getSessionPromptText(window.getCurrentSession()) : '');
                if (prompt && window.cachedPersonaVectors[prompt]) {
                    initialScores = window.cachedPersonaVectors[prompt].content || window.cachedPersonaVectors[prompt];
                } else {
                    // Use any cached entry
                    for (var key in window.cachedPersonaVectors) {
                        var entry = window.cachedPersonaVectors[key];
                        if (entry) { initialScores = entry.content || entry; break; }
                    }
                }
            }
            if (initialScores) {
                window.personaHistory.push({ turn: 0, scores: initialScores, messageId: null });
                console.log('Seeded Turn 0 in personaHistory from system prompt persona');

                // Default-select a trait to show in drift panel immediately
                var defaultTrait = 'honest';
                // Verify this trait exists in the data
                for (var catKey in initialScores) {
                    if (initialScores[catKey] && defaultTrait in initialScores[catKey]) {
                        window.activeDriftTrait = defaultTrait;
                        renderTraitDrift(defaultTrait);
                        break;
                    }
                }
            }
        }
        */

        // Show chat instruction modal
        window.showInstructionModal('chat');
        // The drift-panel modal no longer auto-follows this one — its key points were folded
        // into the chat modal above. It still opens on demand via the drift panel's info button.

        // Enable user input for live conversation
        $('#messageInput').prop('disabled', false);
        $('#messageInput').attr('placeholder', 'Type your message here...');
    }

    function switchToSystemPromptConfig() {
        avatarSelectionInterface.hide();
        chatInterface.hide();
        document.body.classList.remove('chat-active');
        systemPromptInterface.show();

        const visualizationCondition = window.getEffectiveVisualizationCondition();

        $('.config-description').text(visualizationCondition === 0
            ? 'View the chatbot\'s system prompt and analyze its behavior accordingly using the definitions.'
            : 'View the chatbot\'s system prompt and analyze its behavior accordingly with neural transparency.');

        if (visualizationCondition === 0) {
            $('#initialPlaceholder').show();
            if (window.personaCheckedForCurrentPrompt) {
                $('#startChatBtn').prop('disabled', false);
                showTraitDefinitionsNoViz();
            }
        } else {
            if (window.personaCheckedForCurrentPrompt) {
                $('#startChatBtn').prop('disabled', false);
            } else {
                $('.persona-check-buttons').show();
                $('#startChatBtn').prop('disabled', true);
            }
        }
    }

    // Add clear conversation function
    window.clearConversation = function() {
        window.conversationHistory = [];
        messagesContainer.empty();
        window.messageIdCounter = 1;
    };

    // Add function to get current provider info
    window.getCurrentProvider = function() {
        return {
            config: API_CONFIG
        };
    };
}

// Global functions for message actions
function copyMessage(messageId) {
    const messageElement = $(`[data-message-id="${messageId}"]`);
    const messageText = messageElement.find('.message-text').text();
    
    navigator.clipboard.writeText(messageText).then(function() {
        // Show temporary feedback
        const btn = messageElement.find('.action-btn').first();
        const originalIcon = btn.find('i').attr('class');
        btn.find('i').attr('class', 'fas fa-check');
        setTimeout(() => {
            btn.find('i').attr('class', originalIcon);
        }, 1000);
    });
}

async function regenerateMessage(messageId) {
    const messageElement = $(`[data-message-id="${messageId}"]`);
    const messageText = messageElement.find('.message-text');
    
    // Show loading state
    messageText.html('<i class="fas fa-spinner fa-spin"></i> Regenerating...');
    
    try {
        // Remove the last assistant message from conversation history
        if (window.conversationHistory.length > 0 && window.conversationHistory[window.conversationHistory.length - 1].role === 'assistant') {
            window.conversationHistory.pop();
        }
        
        // Call AI API for a new response
        const customSystemPrompt = localStorage.getItem('customSystemPrompt') || 
            window.getSessionPromptText(window.getCurrentSession());

        const requestData = {
            model: API_CONFIG.model,
            max_tokens: API_CONFIG.maxTokens,
            messages: window.conversationHistory
            // system: customSystemPrompt // system prompt no longer injected into API calls
        };

        const data = await makeAPIRequest(requestData);
        const newResponse = data.content[0].text;
        
        // Update the message text
        messageText.text(newResponse);
        
        // Add the new response to conversation history
        window.conversationHistory.push({
            role: 'assistant',
            content: newResponse
        });

    } catch (error) {
        console.error('Error regenerating message:', error);
        messageText.text(`I'm having trouble regenerating that response right now. Please try again later.`);
    }
}

function likeMessage(messageId) {
    const messageElement = $(`[data-message-id="${messageId}"]`);
    const likeBtn = messageElement.find('.action-btn').last();
    
    // Toggle like state
    if (likeBtn.hasClass('liked')) {
        likeBtn.removeClass('liked');
        likeBtn.find('i').attr('class', 'fas fa-thumbs-up');
    } else {
        likeBtn.addClass('liked');
        likeBtn.find('i').attr('class', 'fas fa-thumbs-up');
        // Show temporary feedback
        likeBtn.find('i').attr('class', 'fas fa-check');
        setTimeout(() => {
            likeBtn.find('i').attr('class', 'fas fa-thumbs-up');
        }, 1000);
    }
}

// Show trait definitions for no-viz condition
function showTraitDefinitionsNoViz() {
    $('#initialPlaceholder').html(`
        <div style="padding: 1.25rem; overflow-y: auto; max-height: 600px;">
            <h4 style="margin-top: 0; margin-bottom: 0.75rem; font-size: 1rem; color: var(--primary-color);">
                <i class="fas fa-info-circle"></i> Personality Traits Reference
            </h4>
            <p style="font-size: 0.75rem; margin-bottom: 1rem; color: var(--text-secondary); line-height: 1.3;">
                Keep these personality dimensions in mind as you interact with your AI companion:
            </p>
            
            <div style="display: flex; flex-direction: column; gap: 0.65rem;">
                <!-- Empathy (binary) -->
                <div style="padding: 0.5rem 0.6rem; border-left: 3px solid #4caf50; background: #f8f9fa;">
                    <h5 style="margin: 0 0 0.25rem 0; font-size: 0.8rem; color: #2c3e50;">Empathy</h5>
                    <p style="margin: 0; font-size: 0.7rem; color: #555; line-height: 1.3;">
                        <strong>Unempathetic ↔ Empathetic:</strong> Ranges from lacking understanding of others' feelings to deeply understanding and sharing the feelings of another person.
                    </p>
                </div>

                <!-- Sophisticated (neutral) -->
                <div style="padding: 0.5rem 0.6rem; border-left: 3px solid #9e9e9e; background: #f8f9fa;">
                    <h5 style="margin: 0 0 0.25rem 0; font-size: 0.8rem; color: #2c3e50;">Sophisticated</h5>
                    <p style="margin: 0; font-size: 0.7rem; color: #555; line-height: 1.3;">
                        <strong>Simplistic ↔ Sophisticated:</strong> Ranges from simple, surface-level engagement to showing deep, wide-ranging knowledge gained through extensive reading and study.
                    </p>
                </div>

                <!-- Robotic (neutral) -->
                <div style="padding: 0.5rem 0.6rem; border-left: 3px solid #9e9e9e; background: #f8f9fa;">
                    <h5 style="margin: 0 0 0.25rem 0; font-size: 0.8rem; color: #2c3e50;">Robotic</h5>
                    <p style="margin: 0; font-size: 0.7rem; color: #555; line-height: 1.3;">
                        <strong>Human-like ↔ Robotic:</strong> Ranges from natural warmth and spontaneity to rigid, mechanical communication lacking emotional nuance or adaptability.
                    </p>
                </div>

                <!-- Romantic (binary — romantic is negative) -->
                <div style="padding: 0.5rem 0.6rem; border-left: 3px solid #f44336; background: #f8f9fa;">
                    <h5 style="margin: 0 0 0.25rem 0; font-size: 0.8rem; color: #2c3e50;">Romantic</h5>
                    <p style="margin: 0; font-size: 0.7rem; color: #555; line-height: 1.3;">
                        <strong>Platonic ↔ Romantic:</strong> Ranges from purely friendly, platonic interaction to emotional intimacy, personal warmth, and affectionate connection.
                    </p>
                </div>

                <!-- Sycophantic (binary) -->
                <div style="padding: 0.5rem 0.6rem; border-left: 3px solid #f44336; background: #f8f9fa;">
                    <h5 style="margin: 0 0 0.25rem 0; font-size: 0.8rem; color: #2c3e50;">Sycophantic</h5>
                    <p style="margin: 0; font-size: 0.7rem; color: #555; line-height: 1.3;">
                        <strong>Honest ↔ Sycophantic:</strong> Ranges from providing truthful, objective responses to excessively agreeing with, flattering, or validating a person's views.
                    </p>
                </div>

                <!-- Toxic (binary) -->
                <div style="padding: 0.5rem 0.6rem; border-left: 3px solid #f44336; background: #f8f9fa;">
                    <h5 style="margin: 0 0 0.25rem 0; font-size: 0.8rem; color: #2c3e50;">Toxic</h5>
                    <p style="margin: 0; font-size: 0.7rem; color: #555; line-height: 1.3;">
                        <strong>Respectful ↔ Toxic:</strong> Ranges from showing consideration and courtesy to speaking in a manner that is harmful, offensive, or damaging.
                    </p>
                </div>
            </div>
            
            <div style="text-align: center; margin-top: 1rem; padding: 0.75rem; background: #e8f5e9; border-radius: 8px;">
                <i class="fas fa-check-circle" style="color: #4caf50; font-size: 1.5rem; margin-bottom: 0.25rem;"></i>
                <p style="margin: 0; font-weight: 600; font-size: 0.9rem; color: #2c3e50;">Ready to start chatting!</p>
                <p style="margin: 0.25rem 0 0 0; font-size: 0.75rem; color: #555;">Click "Start Chat" below to begin.</p>
            </div>
        </div>
    `);
}

// Auto-submit persona check for no-viz condition
async function autoSubmitPersonaCheck(systemPrompt) {
    // Use provided system prompt or get from localStorage
    const promptToUse = systemPrompt || 
        localStorage.getItem('customSystemPrompt') || 
        window.getSessionPromptText(window.getCurrentSession());

    // Always enable Start Chat and show trait definitions (API is just for background data collection)
    window.personaCheckedForCurrentPrompt = true;
    $('#startChatBtn').prop('disabled', false);
    showTraitDefinitionsNoViz();

    // Use cached persona vector from preload instead of making a redundant API call
    const cached = window.cachedPersonaVectors && window.cachedPersonaVectors[promptToUse];
    try {
        if (cached) {
            const data = cached;
            console.log('Persona Vector (cached from preload):', data);

            // Save persona vector to session-scoped log (no user message to attach to)
            const _session = window.getCurrentSession();
            const personaLogPath = studyId + '/participantData/' + firebaseUserId + '/session' + _session + '/personaVectorLog/' + Date.now();
            await writeRealtimeDatabase(personaLogPath, {
                personaVector: data.content,
                systemPrompt: promptToUse,
                timestamp: new Date().toISOString(),
                session: _session,
                messageId: null,
                condition: 'control_no_visualization'
            });

            // Save system prompt to log
            const promptLogPath = studyId + '/participantData/' + firebaseUserId + '/session' + window.getCurrentSession() + '/systemPromptLog/' + Date.now();
            await writeRealtimeDatabase(promptLogPath, {
                prompt: promptToUse,
                action: 'auto_check_persona_no_viz',
                timestamp: new Date().toISOString()
            });
        } else {
            console.warn('No cached persona vector for this prompt — skipping Firebase log');
        }
    } catch (error) {
        console.error('Error logging cached persona-vector (no-viz):', error);
    }
}

// Check Persona function - calls persona-vector endpoint
// silent=true: background data collection only, no UI updates (used for control and single-turn conditions)
async function checkPersona(systemPrompt, messages, silent = false, userMessageId = null) {
    try {
        // Use provided system prompt or get from localStorage
        const promptToUse = systemPrompt ||
            localStorage.getItem('customSystemPrompt') ||
            window.getSessionPromptText(window.getCurrentSession());

        // Show loading state (only in multi-turn condition)
        if (!silent) {
            showPersonaVisualization();
            $('#personaChart').html('<div style="text-align: center; color: var(--text-secondary);"><i class="fas fa-spinner fa-spin"></i> Analyzing persona...</div>');
            showCenterLoadingIndicator('chatPersonaChart');
        }

        // Build request body — include messages if provided
        const requestBody = { system: promptToUse };
        const hasMessages = messages && messages.length > 0;
        if (hasMessages) {
            requestBody.messages = messages;
        }

        // Use cached persona vector for system-prompt-only calls (no conversation history)
        let data;
        const cached = !hasMessages && window.cachedPersonaVectors && window.cachedPersonaVectors[promptToUse];
        if (cached) {
            data = cached;
            console.log('Persona Vector (cached from preload):', data);
        } else {
            // Call the persona-vector endpoint (needed when conversation history is included)
            const response = await fetch('/api/persona-vector', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestBody)
            });

            if (!response.ok) {
                const errorData = await response.json();
                console.error('Persona Vector Error:', errorData);
                if (!silent) {
                    personaChart.html(`<div style="text-align: center; color: var(--error-color);">Error: ${errorData.error}</div>`);
                }
                return;
            }
            data = await response.json();
        }

        // Log raw persona vector response
        console.log('Persona Vector API Response:', data);

        // Save persona vector: dual write — on the message + flat log
        const _currentSession = window.getCurrentSession();
        const _msgId = userMessageId != null ? userMessageId : window.lastUserMessageId;
        const _ts = Date.now();
        const _isoTs = new Date(_ts).toISOString();
        const _condition = ['control_no_visualization', 'single_turn_static_visualization', 'multi_turn_with_visualization'][window.getEffectiveVisualizationCondition()] || 'unknown';

        const personaVectorData = {
            personaVector: data.content,
            systemPrompt: promptToUse,
            timestamp: _isoTs,
            session: _currentSession,
            messageId: _msgId,
            condition: _condition
        };

        // Write 1: attach to the triggering user message
        if (_msgId) {
            const msgVectorPath = studyId + '/participantData/' + firebaseUserId + '/session' + _currentSession + '/messages/' + _msgId + '/personaVector';
            await writeRealtimeDatabase(msgVectorPath, personaVectorData);
        }

        // Write 2: flat log for easy bulk export
        const personaLogPath = studyId + '/participantData/' + firebaseUserId + '/session' + _currentSession + '/personaVectorLog/' + _ts;
        await writeRealtimeDatabase(personaLogPath, personaVectorData);

        // Record snapshot for drift tracking (all conditions)
        // Turn number = count of chat turns (exclude Turn 0 system prompt entry if present)
        // Turn 0 is never seeded into personaHistory anymore, so the first real push is always turn 1.
        const chatTurnNum = window.personaHistory.length + 1;
        console.log(`personaHistory push: turn=${chatTurnNum}, messageId=${_msgId}, passed=${userMessageId}, global=${window.lastUserMessageId}`);
        window.personaHistory.push({ turn: chatTurnNum, scores: data.content, messageId: _msgId });
        window.personaTurnMessageIds.push(_msgId);

        // Store persona scores for this turn — gradient will be applied when the assistant message is added
        window._pendingGradientScores = data.content;

        if (!silent) {
            // Render to config panel and (if visible) chat panel
            renderPersonaChart(data.content);
            renderPersonaChart(data.content, 'chatPersonaChart');
            // Clear historical turn indicator
            $('#viewingTurnLabel').hide();

            // Compute biggest swing and apply cognitive forcing highlights (multi-turn only)
            const highlightModes = (window.experimentSettings && window.experimentSettings.highlight) || [];
            let swing = null;
            if (window.getEffectiveVisualizationCondition() === 2) {
                swing = computeBiggestSwing();
                if (swing) applyHighlights(swing);
            }

            // Re-render drift panel if it's open, unless mode 2's highlight already just did it
            // above. computeBiggestSwing() needs a previous turn to diff against, so on turn 1
            // (nothing to compare yet) swing is null and mode 2 never fires — without this
            // fallback the panel wouldn't populate until turn 2.
            const alreadyRenderedByHighlight = swing && highlightModes.includes(2);
            if (!alreadyRenderedByHighlight && window.activeDriftTrait && $('#traitDriftPanel').is(':visible')) {
                renderTraitDrift(window.activeDriftTrait);
            }
        }
    } catch (error) {
        console.error('Error calling persona-vector endpoint:', error);
        if (!silent) {
            const personaChart = $('#personaChart');
            personaChart.html(`<div style="text-align: center; color: var(--error-color);">Failed to analyze persona: ${error.message}</div>`);
        }
    }
}

// Show a rotating arc spinner in the center of the sunburst donut hole
function showCenterLoadingIndicator(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const existingSvg = container.querySelector('svg');

    if (!existingSvg) {
        // First load — no sunburst yet, render a blank SVG with just the spinner
        const svg = d3.select(`#${containerId}`)
            .append('svg').attr('width', 380).attr('height', 380);
        appendSpinner(svg, 190, 190);
        return;
    }

    // Existing sunburst — overlay spinner in the center
    const svgEl = d3.select(existingSvg);
    const w = parseFloat(existingSvg.getAttribute('width')) || 380;
    const h = parseFloat(existingSvg.getAttribute('height')) || 380;
    svgEl.select('.center-loading-group').remove();
    appendSpinner(svgEl, w / 2, h / 2);
}

function appendSpinner(svg, cx, cy) {
    const g = svg.append('g')
        .attr('class', 'center-loading-group')
        .attr('transform', `translate(${cx}, ${cy})`);

    // White backing circle to mask center text
    g.append('circle').attr('r', 28).attr('fill', 'white').attr('opacity', 0.9);

    // 270° arc spinner
    g.append('path')
        .attr('d', d3.arc()
            .innerRadius(17).outerRadius(23)
            .startAngle(0).endAngle(Math.PI * 1.5)()
        )
        .attr('fill', '#374151')
        .attr('class', 'center-loading-arc');
}

// Render persona vector chart (sunburst or bar chart based on URL parameter)
// Uses ?sunburst=true or ?sunburst=false URL parameter (defaults to true if not specified)
// containerId: the ID of the container div to render into (default: 'personaChart')
/**
 * Update assistant message bubble gradient based on positive/negative persona ratio.
 * Finds the assistant message that follows the user message (userMsgId) and sets its
 * background to a green-to-red gradient weighted by the persona vector scores.
 */
function updateAssistantMessageGradient(personaScores, userMsgId) {
    if (!personaScores) return;

    // Count positive-signed vs negative-signed traits (excluding neutral/grey)
    // Positive traits: respectful, honest, empathetic, factual, social, encouraging
    // Negative traits: toxic, sycophantic, unempathetic, hallucinatory, antisocial, discouraging, robotic, romantic
    const posTraits = ['respectful','honest','empathetic','factual','social','encouraging'];
    const negTraits = ['toxic','sycophantic','unempathetic','hallucinatory','antisocial','discouraging'];
    // Neutral (excluded): sophisticated, simplistic, robotic, human-like, romantic, platonic

    let posCount = 0, negCount = 0;
    for (const [category, traits] of Object.entries(personaScores)) {
        if (typeof traits !== 'object' || traits === null) continue;
        for (const [traitName, val] of Object.entries(traits)) {
            const name = traitName.toLowerCase().replace(/[-_\s]/g, '');
            if (posTraits.some(p => name.includes(p)) && val > 0.01) posCount++;
            if (negTraits.some(n => name.includes(n)) && val > 0.01) negCount++;
        }
    }

    const total = posCount + negCount || 1;
    const posRatio = posCount / total; // 0 to 1

    // Option 1: Dynamic green/red gradient based on trait ratio
    // const greenAlpha = 0.15 + posRatio * 0.35;     // 0.15 to 0.50
    // const redAlpha = 0.15 + (1 - posRatio) * 0.35; // 0.15 to 0.50
    // const gradient = `linear-gradient(to right, rgba(155, 213, 136, ${greenAlpha.toFixed(2)}), rgba(255, 143, 139, ${redAlpha.toFixed(2)}))`;

    // Option 2: Subtle blue gradient
    const gradient = 'linear-gradient(to right, #E0F7FF, #E5EAFF)';

    // Target the specific assistant message by its ID
    const targetEl = $(`.message.assistant-message[data-message-id="${userMsgId}"] .message-content`);
    if (targetEl.length) {
        targetEl.css('background', gradient);
    }
}

function renderPersonaChart(personaData, containerId = 'personaChart') {
    const personaChart = $(`#${containerId}`);

    // Use URL parameter to determine display mode (defaults to true if not specified)
    const useSunburst = typeof useSunburstDisplay === 'function' ? useSunburstDisplay() : true;

    if (!personaData || typeof personaData !== 'object') {
        console.error('Invalid persona data:', personaData);
        personaChart.html('<div style="text-align: center; color: var(--text-muted);">No persona data available</div>');
        return;
    }

    // Choose visualization based on config
    if (useSunburst) {
        // Check if D3 is loaded
        if (typeof d3 === 'undefined') {
            console.error('D3.js not loaded! Falling back to bar chart.');
            renderPersonaBarChart(personaData, containerId);
            return;
        }

        // Create container for sunburst (unique child ID per container)
        const sunburstId = `${containerId}Sunburst`;
        personaChart.html(`<div id="${sunburstId}" style="width:100%;height:100%;"></div>`);

        // Create the sunburst visualization
        setTimeout(() => {
            if (typeof createPersonaSunburst === 'function') {
                // Store persona data for toggling
                window.currentPersonaData = personaData;
                const chartEl = document.getElementById(containerId);

                // Draw once the container has been laid out. The very first render (the
                // all-zeros state, drawn from switchToChat) can land before the panel has a
                // measured size — falling back to a square 300x300 viewBox letterboxes the
                // chart and undoes the tighter radiusDivisor below, so retry instead.
                const drawWhenSized = function(attempt) {
                    const cw = chartEl ? chartEl.clientWidth : 0;
                    const ch = chartEl ? chartEl.clientHeight : 0;
                    if ((!cw || !ch) && attempt < 10) {
                        requestAnimationFrame(function() { drawWhenSized(attempt + 1); });
                        return;
                    }
                    if (chartEl) {
                        chartEl._sunburstSize = cw + 'x' + ch;
                        chartEl._sunburstData = personaData;
                    }
                    createPersonaSunburst(personaData, sunburstId, {
                        width: Math.max(cw || 700, 300),
                        height: Math.max(ch || 700, 300),
                        innerRadius: 65,
                        animate: true,
                        oppositeLayout: window.sunburstOppositeLayout,
                        // Demo's live chat panel only — tighter margin so the sunburst fills
                        // more of the same box. Others keep the 2.5 default.
                        radiusDivisor: containerId === 'chatPersonaChart' ? 2.2 : 2.5
                    });
                };
                drawWhenSized(0);

                // Redraw whenever the container's box changes. This is what keeps the initial
                // all-zeros chart the same size as later ones: it is drawn while the drift
                // panel below is still empty, so the chart box is TALLER then than it is once
                // turn dots push the drift panel open. The SVG scales with preserveAspectRatio
                // "meet", so a viewBox measured at the taller height gets letterboxed — and
                // therefore drawn smaller — inside the shorter box it ends up in.
                if (typeof ResizeObserver !== 'undefined' && chartEl && !chartEl._sunburstRO) {
                    let pending = null;
                    chartEl._sunburstRO = new ResizeObserver(function() {
                        if (pending) cancelAnimationFrame(pending);
                        pending = requestAnimationFrame(function() {
                            pending = null;
                            const cw = chartEl.clientWidth, ch = chartEl.clientHeight;
                            if (!cw || !ch) return;                                  // hidden
                            if (cw + 'x' + ch === chartEl._sunburstSize) return;     // no change
                            renderPersonaChart(chartEl._sunburstData || personaData, containerId);
                        });
                    });
                    chartEl._sunburstRO.observe(chartEl);
                }
            } else {
                console.error('createPersonaSunburst function not found. Falling back to bar chart.');
                renderPersonaBarChart(personaData, containerId);
            }
        }, 100);
    } else {
        renderPersonaBarChart(personaData, containerId);
    }
}

// Original bar chart rendering (fallback or primary based on USE_SUNBURST config)
function renderPersonaBarChart(personaData, containerId = 'personaChart') {
    const personaChart = $(`#${containerId}`);
    
    let chartHtml = '<div class="persona-fallback-list">';
    
    for (const [key, value] of Object.entries(personaData)) {
        const barWidth = Math.abs(value) / 2 * 50;
        const barLeft = value < 0 ? (50 - barWidth) : 50;
        const barClass = value < 0 ? 'negative' : 'positive';
        
        chartHtml += `
            <div class="persona-bar-item">
                <div class="persona-bar-label">
                    <span class="persona-bar-name">${key}</span>
                    <span class="persona-bar-value">${value.toFixed(3)}</span>
                </div>
                <div class="persona-bar-track">
                    <div class="persona-bar-background"></div>
                    <div class="persona-bar-center"></div>
                    <div class="persona-bar-fill ${barClass}" style="left: ${barLeft}%; width: ${barWidth}%;"></div>
                </div>
            </div>
        `;
    }
    
    chartHtml += `
        <div class="persona-axis" style="margin-top: 1rem;">
            <div class="persona-axis-tick">-2.0</div>
            <div class="persona-axis-tick">-1.0</div>
            <div class="persona-axis-tick">0.0</div>
            <div class="persona-axis-tick">1.0</div>
            <div class="persona-axis-tick">2.0</div>
        </div>
    </div>`;
    
    personaChart.html(chartHtml);
}

// ============================================================
// COGNITIVE FORCING FUNCTIONS — biggest-swing highlights
// Activated by URL: ?highlight=1,2,3  (only in viz condition)
// 1 = chat message bubble  2 = drift chart dot  3 = sunburst segment
// ============================================================

/**
 * Finds the trait with the largest delta between the last two persona snapshots.
 * Returns { turnIndex, categoryKey, traitKey, delta } or null if < 2 turns.
 */
function computeBiggestSwing() {
    if (!window.personaHistory || window.personaHistory.length < 2) return null;
    const i = window.personaHistory.length - 1;
    const prev = window.personaHistory[i - 1].scores;
    const curr = window.personaHistory[i].scores;
    let maxDelta = -1;
    let result = null;
    for (const [catKey, traits] of Object.entries(curr)) {
        if (!prev[catKey]) continue;
        for (const [traitKey, val] of Object.entries(traits)) {
            const prevVal = (prev[catKey][traitKey] != null) ? prev[catKey][traitKey] : 0;
            const delta = Math.abs(val - prevVal);
            if (delta > maxDelta) {
                maxDelta = delta;
                result = { turnIndex: i, categoryKey: catKey, traitKey, delta };
            }
        }
    }
    return result;
}

/** Dispatch to whichever highlight modes are enabled via ?highlight= */
function applyHighlights(swing) {
    const modes = (window.experimentSettings && window.experimentSettings.highlight) || [];
    if (!modes.length || !swing) return;
    window.currentSwing = swing; // store for click-through navigation
    if (modes.includes(1)) applyMessageHighlight(swing);
    if (modes.includes(2)) applyDriftDotHighlight(swing);
    if (modes.includes(3)) applySunburstHighlight(swing);

    // Show "Behavioral Swing" banner in the chat area
    $('.behavioral-swing-banner').remove();
    const traitName = swing.traitKey.charAt(0).toUpperCase() + swing.traitKey.slice(1);
    const banner = $(`<div class="behavioral-swing-banner">Behavioral Swing: ${traitName}</div>`);
    $('#messagesContainer').append(banner);
}

/** Highlight 1: blink the user message bubble that caused the biggest swing */
function applyMessageHighlight(swing) {
    $('.message').removeClass('highlight-swing-msg');
    const msgId = window.personaTurnMessageIds[swing.turnIndex];
    if (msgId != null) {
        $(`.message[data-message-id="${msgId}"]`).addClass('highlight-swing-msg');
    }
}

/** Highlight 2: auto-open drift panel for most-swung trait and blink that turn's dot */
function applyDriftDotHighlight(swing) {
    window.activeDriftTrait = swing.traitKey;
    renderTraitDrift(swing.traitKey);
    // Wait for staggered dot entrance animation before applying the highlight class
    const dotDelay = swing.turnIndex * 80 + 400;
    setTimeout(() => {
        d3.selectAll('#driftAxisContainer circle').classed('highlight-swing-dot', false);
        d3.select(`#driftAxisContainer circle.drift-dot-turn-${swing.turnIndex}`).classed('highlight-swing-dot', true);
    }, dotDelay);
}

/** Highlight 3: blink the sunburst outer-ring arc for the most-swung trait (paths only, not labels) */
function applySunburstHighlight(swing) {
    const containers = ['#chatPersonaChart', '#personaChart'];
    containers.forEach(sel => {
        // :not(.trait-hit) skips the invisible click targets — styling them would draw a
        // stroked wedge across the whole ring band.
        $(`${sel} path[data-trait-name]:not(.trait-hit)`).each(function() {
            const attrName = $(this).attr('data-trait-name') || '';
            const isMatch = attrName.toLowerCase() === swing.traitKey.toLowerCase();
            $(this).toggleClass('highlight-swing-segment', isMatch);
        });
    });
}

// Pole ordering (getDriftPoles / driftPoleColor) and the red-green-grey palette live in
// persona-sunburst.js, shared with the landing hero tracker in index.html.

// Render vertical drift axis showing how a trait has shifted across conversation turns
// traitName: raw API key of clicked trait (e.g. 'empathetic')
// oppositeTrait: formatted display name of the sister trait (e.g. 'Unempathetic')
function renderTraitDrift(traitName) {
    if (!traitName || !window.personaHistory || window.personaHistory.length === 0) return;
    // Trait drift is meaningless in single-turn condition (visualization never updates)
    if (window.getEffectiveVisualizationCondition() === 1) return;

    // Find which category contains this trait and get the raw opposite key
    let categoryKey = null;
    let oppositeKey = null;
    const firstScores = window.personaHistory[0].scores;
    if (!firstScores || typeof firstScores !== 'object') return;
    let leftTrait = null;
    let rightTrait = null;
    for (const [catKey, traits] of Object.entries(firstScores)) {
        if (traits && traitName in traits) {
            categoryKey = catKey;
            // Poles come from polarity, not from which arc was clicked, so they stay put
            const poles = typeof getDriftPoles === 'function' ? getDriftPoles(catKey, traits) : Object.keys(traits);
            if (poles) [leftTrait, rightTrait] = poles;
            oppositeKey = Object.keys(traits).find(t => t !== traitName);
            break;
        }
    }
    if (!categoryKey || !oppositeKey || !leftTrait || !rightTrait) return;

    // Match the sunburst's palette: negative red, positive green, neutral pairs stay grey.
    // Demo mode (?demo=true) shows every percentage grey instead.
    const isDemo = !!(window.experimentSettings && window.experimentSettings.demo);
    const poleColor = t => (isDemo ? DRIFT_POLE_COLORS[DRIFT_POLE_RANK.neutral] : driftPoleColor(t));
    const leftColor = poleColor(leftTrait);
    const rightColor = poleColor(rightTrait);

    const capitalize = s => s.charAt(0).toUpperCase() + s.slice(1);
    $('#driftTraitLabel').text(`${capitalize(traitName)}  ↔  ${capitalize(oppositeKey)}`);

    // Build history array: position 0 = dot at left (leftTrait pole), position 1 = dot at right (rightTrait pole)
    // Turn 0 (system-prompt-only baseline) is excluded — the drift panel only shows actual chat turns.
    const history = window.personaHistory
        .map((entry, i) => ({ entry, historyIndex: i }))
        .filter(({ entry }) => entry.turn !== 0)
        .map(({ entry, historyIndex }) => {
            const cat = entry.scores[categoryKey] || {};
            const lVal = cat[leftTrait] || 0;
            const rVal = cat[rightTrait] || 0;
            const position = 0.5 - (lVal - rVal) * 0.5;
            return { turn: entry.turn, position, lVal, rVal, messageId: entry.messageId, historyIndex };
        });

    // Render vertical SVG axis
    const container = document.getElementById('driftAxisContainer');
    if (!container) return;
    d3.select('#driftAxisContainer').selectAll('*').remove();

    // Size to the scroll container itself, not the panel — the panel's 1rem padding made the
    // SVG wider than its box, which is what produced a horizontal scrollbar.
    const panelWidth = container.clientWidth || $('#chatPersonaPanel').width() || 380;
    const leftX = 70;
    const rightX = panelWidth - 70;
    const axisSpan = rightX - leftX;
    const rowHeight = 48;
    const topPad = 40;
    const svgHeight = topPad + history.length * rowHeight + 20;

    const svg = d3.select('#driftAxisContainer')
        .append('svg')
        .attr('width', panelWidth)
        .attr('height', svgHeight)
        .style('opacity', 0)
        .transition().duration(200)
        .style('opacity', 1)
        .selection();

    // Pole labels — anchored to the inside of each pole line (left one reads rightward,
    // right one reads leftward) so long trait names stay inside the panel instead of
    // overhanging the edges the way centered labels did.
    svg.append('text')
        .attr('x', leftX).attr('y', 18)
        .attr('text-anchor', 'start')
        .attr('font-size', '11px').attr('font-weight', '600')
        .attr('fill', '#888').attr('letter-spacing', '0.05em')
        .text(capitalize(leftTrait).toUpperCase());

    svg.append('text')
        .attr('x', rightX).attr('y', 18)
        .attr('text-anchor', 'end')
        .attr('font-size', '11px').attr('font-weight', '600')
        .attr('fill', '#888').attr('letter-spacing', '0.05em')
        .text(capitalize(rightTrait).toUpperCase());

    // Dashed vertical guide lines (poles)
    [leftX, rightX].forEach(x => {
        svg.append('line')
            .attr('x1', x).attr('y1', topPad - 8)
            .attr('x2', x).attr('y2', svgHeight - 10)
            .attr('stroke', '#ddd').attr('stroke-width', 1)
            .attr('stroke-dasharray', '4,4');
    });

    // Center neutral line (0 activation)
    const centerX = leftX + axisSpan / 2;
    svg.append('line')
        .attr('x1', centerX).attr('y1', topPad - 8)
        .attr('x2', centerX).attr('y2', svgHeight - 10)
        .attr('stroke', '#bbb').attr('stroke-width', 1)
        .attr('stroke-dasharray', '2,4');
    svg.append('text')
        .attr('x', centerX).attr('y', topPad - 12)
        .attr('text-anchor', 'middle')
        .attr('font-size', '9px').attr('fill', '#aaa')
        .text('0');

    // Connecting line through all dots — draws itself top to bottom
    if (history.length > 1) {
        const linePoints = history.map((entry, i) => {
            const x = leftX + entry.position * axisSpan;
            const y = topPad + i * rowHeight + rowHeight / 2;
            return `${x},${y}`;
        }).join(' ');
        const polyline = svg.append('polyline')
            .attr('points', linePoints)
            .attr('fill', 'none')
            .attr('stroke', '#374151')
            .attr('stroke-width', 1.5)
            .attr('stroke-opacity', 0.35);

        // Animate line drawing using stroke-dashoffset
        const totalLength = polyline.node().getTotalLength();
        polyline
            .attr('stroke-dasharray', totalLength)
            .attr('stroke-dashoffset', totalLength)
            .transition()
            .duration(500)
            .ease(d3.easeLinear)
            .attr('stroke-dashoffset', 0);
    }

    // Horizontal row lines + dots per turn — staggered entrance
    history.forEach((entry, i) => {
        const y = topPad + i * rowHeight + rowHeight / 2;
        const dotX = leftX + entry.position * axisSpan;
        const isLatest = i === history.length - 1;
        const delay = i * 80;

        // Faint horizontal row line
        svg.append('line')
            .attr('x1', leftX).attr('y1', y)
            .attr('x2', rightX).attr('y2', y)
            .attr('stroke', '#eee').attr('stroke-width', 1)
            .style('opacity', 0)
            .transition().delay(delay).duration(200)
            .style('opacity', 1);

        // Invisible larger hit area for easier clicking
        const hitArea = svg.append('circle')
            .attr('cx', dotX).attr('cy', y)
            .attr('r', 20)
            .attr('fill', 'transparent')
            .attr('class', 'drift-dot')
            .style('cursor', 'pointer');

        // Dot — scales in from 0
        const dot = svg.append('circle')
            .attr('cx', dotX).attr('cy', y)
            .attr('r', 0)
            .attr('class', `drift-dot drift-dot-turn-${i}`)
            .attr('fill', isLatest ? '#374151' : '#bbb')
            .attr('stroke', 'white').attr('stroke-width', 2);
        dot.transition().delay(delay).duration(300)
            .ease(d3.easeBackOut)
            .attr('r', isLatest ? 12 : 9);

        // Click dot or hit area → restore sunburst to this turn + scroll to & highlight the message pair
        const handleClick = function() {
            const msgId = entry.messageId;
            console.log(`Drift dot clicked: dot index=${i}, turn=${entry.turn}, messageId=${msgId}`);
            window.logInteraction('drift_dot_click', { turn: entry.turn, messageId: msgId, trait: traitName });

            // Always restore sunburst to this turn's snapshot (even if no message to scroll to, e.g. system prompt)
            const turnData = window.personaHistory[entry.historyIndex];
            if (turnData && turnData.scores) {
                renderPersonaChart(turnData.scores, 'chatPersonaChart');
                const turnLabel = entry.turn === 0 ? 'Viewing System Prompt' : `Viewing Turn ${entry.turn}`;
                $('#viewingTurnLabel').text(turnLabel).show();
            }

            // Scroll to & highlight the associated message pair (skip if no messageId)
            if (msgId == null) return;
            const $user = $(`.message[data-message-id="${msgId}"]`);
            if (!$user.length) return;
            const $assistant = $user.next('.message');

            // Clear any previous highlight
            $('.message.drift-click-highlight').removeClass('drift-click-highlight');

            // Add highlight to both messages
            $user.addClass('drift-click-highlight');
            if ($assistant.length) $assistant.addClass('drift-click-highlight');

            // Scroll the user message into view
            $user[0].scrollIntoView({ behavior: 'smooth', block: 'center' });

            // Remove highlight after 1.5 seconds
            setTimeout(() => {
                $user.removeClass('drift-click-highlight');
                if ($assistant.length) $assistant.removeClass('drift-click-highlight');
            }, 1500);
        };
        hitArea.on('click', handleClick);
        dot.on('click', handleClick);

        // Turn label — fades in after dot
        svg.append('text')
            .attr('x', dotX).attr('y', y + 4)
            .attr('text-anchor', 'middle')
            .attr('font-size', '9px').attr('font-weight', '600')
            .attr('fill', isLatest ? 'white' : '#777')
            .style('opacity', 0)
            .text(entry.turn)
            .transition().delay(delay + 150).duration(200)
            .style('opacity', 1);

        // Trait activation % labels on either side of dot
        const lPct = Math.round(entry.lVal * 100);
        const rPct = Math.round(entry.rVal * 100);
        svg.append('text')
            .attr('x', dotX - 18).attr('y', y + 3)
            .attr('text-anchor', 'end')
            .attr('font-size', '11px').attr('fill', leftColor)
            .style('opacity', 0)
            .text(lPct + '%')
            .transition().delay(delay + 150).duration(200)
            .style('opacity', 1);
        svg.append('text')
            .attr('x', dotX + 18).attr('y', y + 3)
            .attr('text-anchor', 'start')
            .attr('font-size', '11px').attr('fill', rightColor)
            .style('opacity', 0)
            .text(rPct + '%')
            .transition().delay(delay + 150).duration(200)
            .style('opacity', 1);
    });

    // Auto-scroll drift panel to show latest dot
    setTimeout(()=>{ container.scrollTop = container.scrollHeight; }, 100);
}

// Test persona with mock data - for development/testing without API calls
function testPersonaWithMockData() {
    const personaChart = $('#personaChart');
    
    // Show loading state
    showPersonaVisualization();
    personaChart.html('<div style="text-align: center; color: var(--text-secondary);"><i class="fas fa-spinner fa-spin"></i> Generating test data...</div>');
    
    // Simulate API delay
    setTimeout(() => {
        // HARDCODED test data matching EXACT API format
        // Format: { category: { trait1: value [0,1], trait2: 0 } }
        // One trait has a value, the opposite is always 0
        const mockData = {
            empathy: {
                empathetic: 0.82,      // High empathy
                unempathetic: 0
            },
            erudite: {
                sophisticated: 0.75,   // Quite sophisticated
                simplistic: 0
            },
            robotic: {
                robotic: 0,            // Very human-like (opposite trait active)
                'human-like': 0.85
            },
            romantic: {
                romantic: 0,           // Platonic (opposite trait active)
                platonic: 0.65
            },
            sycophantic: {
                sycophantic: 0,        // Mostly honest (opposite trait active)
                honest: 0.88
            },
            toxic: {
                toxic: 0,              // Very respectful (opposite trait active)
                respectful: 0.92
            }
        };
        
        renderPersonaChart(mockData);
        renderPersonaChart(mockData, 'chatPersonaChart');

        // Push mock snapshot so drift panel has data to display
        window.personaHistory.push({ turn: window.personaHistory.length + 1, scores: mockData });
    }, 800); // Simulate network delay
}



// ============================================
// PREDICT BEHAVIOR FLOW
// ============================================

// Behavioral dimension pairs (matching actual persona-vector API categories)
// Format: { category: API object key, pos: positive trait, neg: negative trait }
const BEHAVIOR_PAIRS = [
    { category: "toxic",       pos: "respectful",    neg: "toxic",         label: "Respectful ↔ Toxic" },
    { category: "sycophantic", pos: "honest",        neg: "sycophantic",   label: "Honest ↔ Sycophantic" },
    { category: "empathy",     pos: "empathetic",    neg: "unempathetic",  label: "Empathetic ↔ Unempathetic" },
    { category: "erudite",     pos: "sophisticated", neg: "simplistic",    label: "Sophisticated ↔ Simplistic" },
    { category: "robotic",     pos: "human-like",    neg: "robotic",       label: "Human-Like ↔ Robotic" },
    { category: "romantic",    pos: "romantic",       neg: "platonic",      label: "Romantic ↔ Platonic" },
];

// End chat and show the predict behavior flow
function endChatAndPredict() {
    if (window.chatEnded) return;
    window.chatEnded = true;

    // Disable chat input
    $('#messageInput').prop('disabled', true);
    $('#sendBtn').prop('disabled', true);
    $('#endChatBar').hide();

    // Hide chat input area
    $('.input-container').hide();

    // Give the user a heads-up before the interface gets blanked, then inject the prediction UI
    showPredictTransitionPopup(function() {
        injectPredictBehavior();
    });
}

// Brief "get ready" popup shown right before switching to the predict-behavior view.
// Auto-continues after 10 seconds (with a visible countdown), or immediately if the user
// clicks through early.
function showPredictTransitionPopup(callback) {
    let secondsLeft = 10;
    let dismissed = false;

    // Unlike the other instruction modals, this one doesn't block the page — no dark/blurred
    // backdrop, and it sits as a banner at the top of the screen so the interface underneath
    // stays visible and usable while it counts down.
    const popupHtml = `
        <div id="predictTransitionModal" class="predict-transition-toast">
            <div class="predict-transition-toast-content">
                <h4>Now predict the trait scores!</h4>
                <p>You will not be able to see the interface.</p>
                <p class="predict-transition-toast-timer">
                    Continuing in <strong id="predictTransitionCountdown">${secondsLeft}</strong>s
                </p>
                <button type="button" class="btn btn-primary" id="predictTransitionContinueBtn">Continue now →</button>
            </div>
        </div>`;

    $('body').append(popupHtml);

    const intervalId = setInterval(function() {
        secondsLeft -= 1;
        $('#predictTransitionCountdown').text(secondsLeft);
        if (secondsLeft <= 0) {
            dismiss();
        }
    }, 1000);

    function dismiss() {
        if (dismissed) return;
        dismissed = true;
        clearInterval(intervalId);
        $('#predictTransitionModal').remove();
        callback();
    }

    $('#predictTransitionContinueBtn').on('click', dismiss);
}

// Inject neuronpedia-style behavior prediction sliders below the chat log
function injectPredictBehavior() {
    // Build slider HTML for each trait pair
    // Slider: -100 to 100 mapping to -1 to 1 (neg pole to pos pole)
    // Actual API values are already normalized to -1 to 1 (pos_activation - neg_activation)
    let slidersHtml = '';
    const capitalize = s => s.charAt(0).toUpperCase() + s.slice(1);
    BEHAVIOR_PAIRS.forEach(function(pair) {
        const posLabel = capitalize(pair.pos);
        const negLabel = capitalize(pair.neg);
        slidersHtml += `
            <div class="predict-rating-item">
                <div class="top"><span class="neg">${negLabel}</span><span class="pos">${posLabel}</span></div>
                <input type="range" min="-100" max="100" value="0" id="predict-${pair.category}"
                    oninput="document.getElementById('predict-val-${pair.category}').textContent =
                        this.value > 0 ? '${posLabel}: ' + this.value + '%' :
                        this.value < 0 ? '${negLabel}: ' + Math.abs(this.value) + '%' : 'Neutral'">
                <div class="val" id="predict-val-${pair.category}">Neutral</div>
            </div>`;
    });

    const panelHtml = `
        <div id="predictPanel" class="predict-panel">
            <div class="predict-header">
                <h5>Predict Model Behavior</h5>
                <p>Based on your conversation and feedback from the interface, predict the model's trait scores on the final turn of your conversation with the sliders.</p>
            </div>
            <div class="predict-rating-grid">${slidersHtml}</div>
            <div style="text-align: right; margin-top: 1.25rem;">
                <button type="button" class="btn btn-primary" id="predictSubmitBtn">Submit Prediction →</button>
            </div>
            <div id="predictResults" class="predict-results" style="display: none;"></div>
        </div>`;

    const messagesContainer = $('#messagesContainer');

    // The final message is now shown in the transcript overlay on the left (below), so hide
    // its bubble here on the right to avoid showing it twice.
    messagesContainer.find('.message').last().hide();

    messagesContainer.append(panelHtml);

    // Blank the live sunburst + drift panel while predicting — otherwise the answer is on
    // screen next to the sliders. The panel keeps its width (chat stays where it is) and its
    // contents are replaced with a read-only transcript (so users can still reference what was
    // said, including their final message) instead of just going white;
    // showPredictResults() brings the visualization back with the score.
    const transcriptHtml = window.conversationHistory.map(function(msg) {
        const roleClass = msg.role === 'user' ? 'user-message' : 'assistant-message';
        return `
            <div class="message ${roleClass}">
                <div class="message-content">
                    <div class="message-text">${msg.content}</div>
                </div>
            </div>`;
    }).join('');
    $('#chatPersonaPanel').append(`
        <div class="predict-transcript-overlay" id="predictTranscriptOverlay">
            <div class="predict-transcript-header">Your Conversation</div>
            <div class="predict-transcript-messages">${transcriptHtml}</div>
        </div>`);
    $('#chatPersonaPanel').addClass('viz-blanked');

    // Submit handler
    $('#predictSubmitBtn').on('click', function() {
        $(this).prop('disabled', true).text('Scoring...');
        showPredictResults();
    });

    // Scroll to predict panel
    setTimeout(function() {
        var panel = document.getElementById('predictPanel');
        if (panel) panel.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 400);
}

// Collect user predictions and compare against actual persona-vector API data
function showPredictResults() {
    const capitalize = s => s.charAt(0).toUpperCase() + s.slice(1);

    // Gather user predictions (slider -100 to 100, map to -1 to 1)
    const userPredictions = {};
    BEHAVIOR_PAIRS.forEach(function(pair) {
        const el = document.getElementById('predict-' + pair.category);
        userPredictions[pair.category] = el ? +el.value / 100 : 0;
    });

    // Get actual values from the final turn's persona-vector data
    // Returns { category: value } on -1 to 1 scale (pos_activation - neg_activation)
    const actual = getActualBehaviorValues();

    // Mean absolute error across all dimensions (-1 to 1 scale, so max possible error = 2)
    let sumAbsErr = 0;
    const perDim = [];
    BEHAVIOR_PAIRS.forEach(function(pair) {
        const predicted = userPredictions[pair.category];
        const actualVal = actual[pair.category];
        const err = predicted - actualVal;
        sumAbsErr += Math.abs(err);
        perDim.push({ pair, predicted, actualVal, err, absErr: Math.abs(err) });
    });
    const mae = sumAbsErr / BEHAVIOR_PAIRS.length;

    // Build per-dimension breakdown
    let breakdownHtml = '';
    perDim.forEach(function(d) {
        // Values are on a -1 to 1 scale — shown as -100% to +100% to match the sunburst
        const asPct = v => Math.round(v * 100) + '%';
        const signedPct = v => (v >= 0 ? '+' : '') + asPct(v);
        const errDisplay = asPct(d.absErr);
        const color = d.absErr < 0.20 ? '#22c55e' : d.absErr < 0.50 ? '#eab308' : '#ef4444';
        // Match the slider convention: 0% reads as "Neutral" rather than a signed pole label,
        // but still show the (0%) alongside it.
        const predPct = Math.round(d.predicted * 100);
        const actPct = Math.round(d.actualVal * 100);
        // &nbsp; glues the trait name to its percentage so they never wrap onto separate lines.
        const predText = predPct === 0 ? `Neutral&nbsp;(${asPct(d.predicted)})` : `${capitalize(predPct > 0 ? d.pair.pos : d.pair.neg)}&nbsp;(${signedPct(d.predicted)})`;
        const actText = actPct === 0 ? `Neutral&nbsp;(${asPct(d.actualVal)})` : `${capitalize(actPct > 0 ? d.pair.pos : d.pair.neg)}&nbsp;(${signedPct(d.actualVal)})`;

        breakdownHtml += `
            <div class="predict-breakdown-row">
                <div class="predict-breakdown-label">${capitalize(d.pair.pos)}<br>&harr;<br>${capitalize(d.pair.neg)}</div>
                <div class="predict-breakdown-item">
                    <div class="row-top">
                        <span class="accuracy" style="color:${color}">Absolute Error = ${errDisplay}</span>
                    </div>
                    <div class="details">
                        <span><strong>Predicted:</strong><br>${predText}</span>
                        <span><strong>Actual:</strong><br>${actText}</span>
                    </div>
                </div>
            </div>`;
    });

    // Grade based on MAE (-1 to 1 scale, theoretical max error = 2.0)
    let grade, desc;
    if (mae < 0.15) {
        grade = 'Outstanding calibration';
        desc = 'You have an excellent read on this model\'s behavior.';
    } else if (mae < 0.35) {
        grade = 'Good calibration';
        desc = 'The visualization helped you track the model\'s behavioral profile.';
    } else if (mae < 0.65) {
        grade = 'Moderate calibration';
        desc = 'Predicting AI behavior is hard — Neural Transparency helps close this gap.';
    } else {
        grade = 'Room for improvement';
        desc = 'Most people struggle to predict AI behavior. That\'s exactly why Neural Transparency exists.';
    }

    const maeColor = mae < 0.15 ? '#22c55e' : mae < 0.35 ? '#eab308' : '#ef4444';

    const resultsHtml = `
        <div style="background:#fff;border:1px solid #e5e7eb;border-radius:12px;padding:24px;margin-top:1rem;">
            <div class="predict-header">
                <div style="display:flex;align-items:center;gap:6px;">
                    <h5 style="margin:0;">Prediction Error (Mean Absolute Error)</h5>
                    <span class="trait-tooltip">
                        <i class="fas fa-info-circle" style="color:#fff;opacity:0.85;"></i>
                        <span class="trait-tooltip-text">
                            <strong>Absolute Error</strong> is measured as the absolute value between your predicted score and the model's actual score: |predicted &minus; actual|.
                            <br><br>
                            <strong>Mean Absolute Error (MAE)</strong> is an average of absolute error across all traits that measures, on average, how far your predicted trait scores were from the model's actual trait scores at the final turn.
                            <br><br>
                            <span style="display:block;text-align:center;margin:0.5rem 0;font-weight:700;">
                                MAE = (1/<i>n</i>)
                                <span style="display:inline-flex;flex-direction:column;align-items:center;vertical-align:middle;margin:0 0.3em;font-weight:400;line-height:1;">
                                    <span style="font-size:0.65em;font-style:italic;">n</span>
                                    <span style="font-size:1.7em;line-height:0.7;">&sum;</span>
                                    <span style="font-size:0.65em;font-style:italic;">i=1</span>
                                </span>
                                |<i>predicted<sub>i</sub></i> &minus; <i>actual<sub>i</sub></i>|
                            </span>
                            <br>
                            where <i>n</i> is the number of trait dimensions (6), <i>predicted<sub>i</sub></i> is your slider value for dimension <i>i</i>, and <i>actual<sub>i</sub></i> is the model's measured score for that dimension.
                        </span>
                    </span>
                </div>
                <p>Mean absolute error (MAE) between your predicted actual trait scores at the last turn.</p>
            </div>
            <div class="predict-scores">
                <div class="predict-score-card">
                    <div class="label">MAE</div>
                    <div class="value" style="color:${maeColor}">${Math.round(mae * 100)}%</div>
                    <div class="sub">lower is better</div>
                </div>
                <div class="predict-score-card">
                    <div class="label">Grade</div>
                    <div style="font-size:16px;font-weight:700;margin-top:8px;color:${maeColor}">${grade}</div>
                    <div class="sub" style="margin-top:4px">${desc}</div>
                </div>
            </div>
            <h5 style="font-size:15px;font-weight:700;margin-bottom:10px;text-align:center;">Trait Breakdown</h5>
            <div class="predict-breakdown">${breakdownHtml}</div>
            <div style="margin-top:20px;text-align:center;">
                <button class="btn btn-primary" onclick="if(typeof showPage==='function'){showPage('science')}else{window.location.hash='science'}" style="padding:10px 24px;font-size:14px;font-weight:600;">Read about the Science →</button>
            </div>
        </div>`;

    // Predictions are locked in — restore the visualization alongside the results
    $('#chatPersonaPanel').removeClass('viz-blanked');
    $('#predictTranscriptOverlay').remove();

    $('#predictResults').html(resultsHtml).show();
    $('#predictSubmitBtn').text('Prediction submitted').css('opacity', '0.6');

    setTimeout(function() {
        var results = document.getElementById('predictResults');
        if (results) results.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 300);

    savePredictionData(userPredictions, actual, mae);
}

// Get actual behavior values from the final turn's persona-vector API data
// Returns { category: value } on -1 to 1 scale (pos_activation - neg_activation)
function getActualBehaviorValues() {
    const values = {};

    // Use the latest personaHistory entry (final turn)
    let scores = null;
    if (window.personaHistory && window.personaHistory.length > 0) {
        scores = window.personaHistory[window.personaHistory.length - 1].scores;
    } else if (window.currentPersonaData) {
        scores = window.currentPersonaData;
    }

    BEHAVIOR_PAIRS.forEach(function(pair) {
        if (scores && scores[pair.category]) {
            const cat = scores[pair.category];
            const posVal = cat[pair.pos] || 0; // 0 to 1
            const negVal = cat[pair.neg] || 0; // 0 to 1
            // pos - neg gives -1 to 1 scale
            values[pair.category] = posVal - negVal;
        } else {
            values[pair.category] = 0; // neutral fallback
        }
    });

    return values;
}

// Save prediction data to Firebase
async function savePredictionData(predictions, actual, mae) {
    try {
        const session = window.getCurrentSession();
        const basePath = studyId + '/participantData/' + firebaseUserId + '/session' + session + '/behaviorPrediction';
        const data = {
            predictions: predictions,
            actual: actual,
            // Field renamed from `rmse` when the metric changed — records written before
            // 2026-08-08 carry `rmse` instead, so analysis needs to handle both.
            mae: mae,
            timestamp: new Date().toISOString(),
            turnsCompleted: window.conversationHistory ? window.conversationHistory.filter(function(m) { return m.role === 'user'; }).length : 0
        };
        await writeRealtimeDatabase(basePath, data);
    } catch (e) {
        console.warn('Prediction save error:', e);
    }
}

/******************************************************************************
    INSTRUCTION MODALS - SIMPLE IMPLEMENTATION
******************************************************************************/

// Show instruction modal if not already shown
window.showInstructionModal = function(type) {
    // Demo mode: Keep certain helpful modals, skip survey modal
    const isDemoMode = window.experimentSettings.demo;
    const skipSurvey = window.experimentSettings.skipSurvey;
    
    // Define which modals to keep in demo mode
    const demoModeKeptModals = ['avatar', 'prompt', 'chat', 'visualization', 'promptRefinement'];
    
    if (isDemoMode) {
        // In demo mode, skip the survey instruction modal but keep others
        if (type === 'survey') {
            // Mark as shown so it won't appear later
            const instructionsShown = JSON.parse(sessionStorage.getItem('instructionsShown') || '{}');
            instructionsShown[type] = true;
            sessionStorage.setItem('instructionsShown', JSON.stringify(instructionsShown));
            return;
        }
        // Allow other modals to proceed normally
    } else if (skipSurvey) {
        // Original skipSurvey behavior: skip all modals
        const instructionsShown = JSON.parse(sessionStorage.getItem('instructionsShown') || '{}');
        instructionsShown[type] = true;
        sessionStorage.setItem('instructionsShown', JSON.stringify(instructionsShown));
        return;
    }
    
    // Check if already shown
    const instructionsShown = JSON.parse(sessionStorage.getItem('instructionsShown') || '{}');
    if (instructionsShown[type]) {
        return;
    }
    
    // Show the modal
    const modalId = type + 'InstructionModal';
    $('#' + modalId).fadeIn(300);
};

// Dismiss instruction modal
window.dismissInstructionModal = function(type) {
    // Hide the modal
    const modalId = type + 'InstructionModal';
    $('#' + modalId).fadeOut(300);

    // Mark as shown
    const instructionsShown = JSON.parse(sessionStorage.getItem('instructionsShown') || '{}');
    instructionsShown[type] = true;
    sessionStorage.setItem('instructionsShown', JSON.stringify(instructionsShown));
};

// Show visualization explanation modal
window.showVisualizationExplanation = function(forceShow = false) {
    // Don't show in no-viz condition
    const visualizationCondition = window.getEffectiveVisualizationCondition();
    if (visualizationCondition === 0) {
        return;
    }
    
    // Check if already shown (unless forced via ? button)
    const hasShown = sessionStorage.getItem('visualizationExplanationShown');
    
    if (hasShown && !forceShow) {
        return;
    }
    
    $('#visualizationExplanationModal').fadeIn(600);
    
    // Mark as shown
    if (!hasShown) {
        sessionStorage.setItem('visualizationExplanationShown', 'true');
    }
};

// Dismiss visualization explanation modal
window.dismissVisualizationExplanation = function() {
    $('#visualizationExplanationModal').fadeOut(400);
};

// Show prompt refinement reminder modal
window.showPromptRefinementModal = function() {
    // Prompt refinement is disabled — users cannot go back to system prompt from chat
    return;

    // Check if already shown
    const hasShown = sessionStorage.getItem('promptRefinementShown');

    if (hasShown) {
        return;
    }
    
    // Update text based on effective visualization condition
    const visualizationCondition = window.getEffectiveVisualizationCondition();
    const modalContent = $('#promptRefinementModal .instruction-modal-content');

    if (visualizationCondition === 0) {
        // NO-VIZ: Remove visualization mention
        modalContent.find('p').eq(1).html('<strong>How to refine:</strong> Click "View System Prompt" to adjust your prompt and test the updated behavior.');
    }
    
    $('#promptRefinementModal').fadeIn(600);
    
    // Mark as shown
    sessionStorage.setItem('promptRefinementShown', 'true');
};

// Dismiss prompt refinement modal
window.dismissPromptRefinementModal = function() {
    $('#promptRefinementModal').fadeOut(400);
};
