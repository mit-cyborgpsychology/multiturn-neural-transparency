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
import { 
    writeRealtimeDatabase, writeURLParameters, readRealtimeDatabase,
    blockRandomization, finalizeBlockRandomization, firebaseUserId 
} from "./firebasepsych1.0.js";

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
studyId='multiturn_debug';
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
    currentSession: window.getCurrentSession(),
    timestamp: new Date().toISOString()
};

// IMPORTANT: Log experiment condition explicitly
console.log('=== EXPERIMENT CONDITION ===');
console.log('Condition:', conditionData.conditionName.toUpperCase());
console.log('Visualization:', ['DISABLED (Control)', 'STATIC (Single-turn)', 'DYNAMIC (Multi-turn)'][conditionData.visualizationCondition] || 'UNKNOWN');
console.log('Assignment Method:', conditionData.assignmentMethod);
console.log('============================');

await writeRealtimeDatabase(conditionPath, conditionData);

// Enhanced Chat Interface JavaScript with System Prompt Configuration
// Always reset chat state on load so each session starts fresh
window.messageIdCounter = 2;
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

// Timer variables — always reset on chat load so each session gets a fresh timer
window.timerStartTime = null;
if (window.timerInterval) { clearInterval(window.timerInterval); }
window.timerInterval = null;
window.timerExpired = false;
{
    const urlParams = new URLSearchParams(window.location.search);
    const debugTimer = urlParams.get('debugTimer') === 'true';
    window.timerDuration = debugTimer ? 45 : 600; // 45 seconds for debug, 10 minutes for production
}

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

        // Log to Firebase
        try {
            const avatarLogPath = studyId + '/participantData/' + firebaseUserId + '/selectedAvatar';
            await writeRealtimeDatabase(avatarLogPath, {
                avatar: avatarPath,
                assignmentMethod: 'random',
                timestamp: new Date().toISOString()
            });
        } catch (e) {
            console.warn('Could not log avatar to Firebase:', e);
        }

        // Go directly to system prompt config (hide avatar screen, show prompt screen)
        $('#avatarSelectionInterface').hide();
        switchToSystemPromptConfig();
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

        // Fire persona analysis in the background immediately for data collection
        if (sessionPrompt) {
            fetch('/api/persona-vector', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ system: sessionPrompt })
            }).then(r => r.ok ? r.json() : null).then(data => {
                if (data) {
                    window.backgroundPersonaData = data;
                    console.log('✅ Background persona analysis complete');
                }
            }).catch(e => console.warn('Background persona analysis failed:', e));
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
                
                // Add welcome message back
                const welcomeMessage = `
                    <div class="message assistant-message" data-message-id="1">
                        <div class="message-content">
                            <div class="message-text">
                                Hi there!
                            </div>
                        </div>
                    </div>
                `;
                messagesContainer.append(welcomeMessage);
                // Reset message counter
                window.messageIdCounter = 2;
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
            
            // Start timer if not already started
            if (window.timerStartTime === null) {
                startTimer();
            }
            
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
            checkPersona(systemPrompt);
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

        $(document).on('click', '#closeDriftBtn', function() {
            d3.select('#driftAxisContainer').selectAll('*').remove();
            $('#driftTraitLabel').text('Click a trait to see drift');
            $('#closeDriftBtn').hide();
            window.activeDriftTrait = null;
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
    async function sendMessage() {
        const message = messageInput.val().trim();
        if (message === '') return;

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
                "You are a helpful research assistant for the MIT Media Lab Chat Study. Provide thoughtful, informative responses to help participants with their research questions. Be conversational and engaging while maintaining a professional tone.";

            const requestData = {
                model: API_CONFIG.model,
                max_tokens: API_CONFIG.maxTokens,
                messages: window.conversationHistory,
                system: customSystemPrompt
            };

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

            // Calculate persona scores for all conditions; only update visualization for multi-turn
            const _vc = window.getEffectiveVisualizationCondition();
            checkPersona(customSystemPrompt, window.conversationHistory, _vc !== 2);

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
            "You are a helpful research assistant for the MIT Media Lab Chat Study. Provide thoughtful, informative responses to help participants with their research questions. Be conversational and engaging while maintaining a professional tone.";
        
        const messageHtml = `
            <div class="message ${messageClass}" data-message-id="${messageId}">
                <div class="message-content">
                    <div class="message-text">${text}</div>
                </div>
            </div>
        `;
        
        messagesContainer.append(messageHtml);
        messagesContainer.scrollTop(messagesContainer[0].scrollHeight);
        
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
        const conversationPath = studyId + '/participantData/' + firebaseUserId + '/conversationHistory';
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
                            <h5 style="margin: 0 0 0.2rem 0; font-size: clamp(0.8rem, 1.6vh, 1.2rem); color: #2c3e50;">Opinionated</h5>
                            <p style="margin: 0; font-size: clamp(0.7rem, 1.3vh, 1rem); color: #555; line-height: 1.3;"><strong>Non-committal ↔ Opinionated</strong></p>
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

        // Single-turn condition: hide trait drift panel (visualization is static, drift is meaningless)
        if (chatVizCondition === 1) {
            $('#traitDriftPanel').hide();
        }

        // Show chat instruction modal
        window.showInstructionModal('chat');

        // Enable user input for live conversation
        $('#messageInput').prop('disabled', false);
        $('#messageInput').attr('placeholder', 'Type your message here...');
    }

    // Replay session-specific scripted conversation with a typing delay between turns
    async function playScriptedConversation() {
        const currentSession = window.getCurrentSession();
        const script = window.getSessionConversation(currentSession);
        if (!script || script.length === 0) {
            console.warn('No scripted conversation found for session', currentSession);
            return;
        }

        const TURN_DELAY_MS    = 2200;  // pause between turns
        const TYPING_DELAY_MS  = 900;   // typing indicator duration

        for (let i = 0; i < script.length; i++) {
            const turn = script[i];

            if (turn.role === 'assistant') {
                // Show typing indicator briefly
                $('#typingIndicator').show();
                await new Promise(r => setTimeout(r, TYPING_DELAY_MS));
                $('#typingIndicator').hide();
            }

            // Render message using existing addMessage helper
            window.messageIdCounter = (window.messageIdCounter || 2) + 1;
            const msgId = window.messageIdCounter;
            const timestamp = new Date().toISOString();
            const sender = turn.role === 'user' ? 'user' : 'assistant';
            const messageClass = sender === 'user' ? 'user-message' : 'assistant-message';

            const messageHtml = `
                <div class="message ${messageClass}" data-message-id="${msgId}">
                    <div class="message-content"><div class="message-text">${turn.content.replace(/\n/g, '<br>')}</div></div>
                </div>`;

            messagesContainer.append(messageHtml);
            messagesContainer.scrollTop(messagesContainer[0].scrollHeight);

            // Record in conversation history for persona scoring
            window.conversationHistory.push({ role: turn.role, content: turn.content });

            // After each assistant turn, calculate persona scores for all conditions
            if (turn.role === 'assistant') {
                const currentPrompt = localStorage.getItem('customSystemPrompt') || '';
                const _scriptVc = window.getEffectiveVisualizationCondition();
                checkPersona(currentPrompt, window.conversationHistory, _scriptVc !== 2).catch(console.warn);
            }

            // Wait before next turn
            if (i < script.length - 1) {
                await new Promise(r => setTimeout(r, TURN_DELAY_MS));
            }
        }

        // All turns played — note completion in chat area
        const doneHtml = `
            <div style="text-align:center; color:#6c757d; font-size:0.85rem; padding:1rem 0; border-top:1px solid #dee2e6; margin-top:0.5rem;">
                <i class="fas fa-check-circle" style="color:#4caf50;"></i> Conversation complete. The timer is still running — feel free to reflect on what you observed.
            </div>`;
        messagesContainer.append(doneHtml);
        messagesContainer.scrollTop(messagesContainer[0].scrollHeight);

        console.log('✅ Scripted conversation playback complete');
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
        
        // Add welcome message back
        const welcomeMessage = `
            <div class="message assistant-message" data-message-id="1">
                <div class="message-content">
                    <div class="message-text">
                       Hi there!
                    </div>
                </div>
            </div>
        `;
        messagesContainer.append(welcomeMessage);
        window.messageIdCounter = 2;
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
            "You are a helpful research assistant for the MIT Media Lab Chat Study. Provide thoughtful, informative responses to help participants with their research questions. Be conversational and engaging while maintaining a professional tone.";

        const requestData = {
            model: API_CONFIG.model,
            max_tokens: API_CONFIG.maxTokens,
            messages: window.conversationHistory,
            system: customSystemPrompt
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

                <!-- Opinionated (neutral) -->
                <div style="padding: 0.5rem 0.6rem; border-left: 3px solid #9e9e9e; background: #f8f9fa;">
                    <h5 style="margin: 0 0 0.25rem 0; font-size: 0.8rem; color: #2c3e50;">Opinionated</h5>
                    <p style="margin: 0; font-size: 0.7rem; color: #555; line-height: 1.3;">
                        <strong>Non-committal ↔ Opinionated:</strong> Ranges from remaining neutral or purely informational to expressing strong, confident viewpoints and personal stances on topics.
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
        "You are a helpful research assistant for the MIT Media Lab Chat Study. Provide thoughtful, informative responses to help participants with their research questions. Be conversational and engaging while maintaining a professional tone.";

    // Always enable Start Chat and show trait definitions (API is just for background data collection)
    window.personaCheckedForCurrentPrompt = true;
    $('#startChatBtn').prop('disabled', false);
    showTraitDefinitionsNoViz();

    // Try to call API in background for data collection (don't block user on API errors)
    try {
        const response = await fetch('/api/persona-vector', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                system: promptToUse
            })
        });

        if (response.ok) {
            const data = await response.json();
            
            // Log raw persona vector response
            console.log('Persona Vector API Response:', data);
            
            // Save persona vector to history log
            const personaLogPath = studyId + '/participantData/' + firebaseUserId + '/personaVectorLog/' + Date.now();
            await writeRealtimeDatabase(personaLogPath, {
                personaVector: data.content,
                systemPrompt: promptToUse,
                timestamp: new Date().toISOString(),
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
            const errorText = await response.text();
            console.error('Persona Vector API Error (no-viz):', response.status, errorText);
        }
    } catch (error) {
        console.error('Error calling persona-vector endpoint (no-viz):', error);
    }
}

// Check Persona function - calls persona-vector endpoint
// silent=true: background data collection only, no UI updates (used for control and single-turn conditions)
async function checkPersona(systemPrompt, messages, silent = false) {
    try {
        // Use provided system prompt or get from localStorage
        const promptToUse = systemPrompt ||
            localStorage.getItem('customSystemPrompt') ||
            "You are a helpful research assistant for the MIT Media Lab Chat Study. Provide thoughtful, informative responses to help participants with their research questions. Be conversational and engaging while maintaining a professional tone.";

        // Show loading state (only in multi-turn condition)
        if (!silent) {
            showPersonaVisualization();
            $('#personaChart').html('<div style="text-align: center; color: var(--text-secondary);"><i class="fas fa-spinner fa-spin"></i> Analyzing persona...</div>');
            showCenterLoadingIndicator('chatPersonaChart');
        }

        // Build request body — include messages if provided
        const requestBody = { system: promptToUse };
        if (messages && messages.length > 0) {
            requestBody.messages = messages;
        }

        // Call the persona-vector endpoint
        const response = await fetch('/api/persona-vector', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });

        if (response.ok) {
            const data = await response.json();
            
            // Log raw persona vector response
            console.log('Persona Vector API Response:', data);
            
            // Save persona vector to history log (session-prefixed)
            const _currentSession = window.getCurrentSession();
            const personaLogPath = studyId + '/participantData/' + firebaseUserId + '/session' + _currentSession + '/personaVectorLog/' + Date.now();
            await writeRealtimeDatabase(personaLogPath, {
                personaVector: data.content,
                systemPrompt: promptToUse,
                timestamp: new Date().toISOString(),
                session: _currentSession,
                condition: ['control_no_visualization', 'single_turn_static_visualization', 'multi_turn_with_visualization'][window.getEffectiveVisualizationCondition()] || 'unknown'
            });

            // Record snapshot for drift tracking (all conditions)
            window.personaHistory.push({ turn: window.personaHistory.length + 1, scores: data.content });
            window.personaTurnMessageIds.push(window.lastUserMessageId);

            if (!silent) {
                // Render to config panel and (if visible) chat panel
                renderPersonaChart(data.content);
                renderPersonaChart(data.content, 'chatPersonaChart');

                // Compute biggest swing and apply cognitive forcing highlights (multi-turn only)
                const highlightModes = (window.experimentSettings && window.experimentSettings.highlight) || [];
                if (window.getEffectiveVisualizationCondition() === 2) {
                    const swing = computeBiggestSwing();
                    if (swing) applyHighlights(swing);
                }

                // Re-render drift panel if it's open and highlight mode 2 isn't handling it
                if (!highlightModes.includes(2) && window.activeDriftTrait && $('#traitDriftPanel').is(':visible')) {
                    renderTraitDrift(window.activeDriftTrait);
                }
            }
        } else {
            const errorData = await response.json();
            console.error('Persona Vector Error:', errorData);
            if (!silent) {
                personaChart.html(`<div style="text-align: center; color: var(--error-color);">Error: ${errorData.error}</div>`);
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
        .attr('fill', '#2196F3')
        .attr('class', 'center-loading-arc');
}

// Render persona vector chart (sunburst or bar chart based on URL parameter)
// Uses ?sunburst=true or ?sunburst=false URL parameter (defaults to true if not specified)
// containerId: the ID of the container div to render into (default: 'personaChart')
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
                const w = Math.max(chartEl ? chartEl.clientWidth : 700, 300);
                const h = Math.max(chartEl ? chartEl.clientHeight : 700, 300);
                createPersonaSunburst(personaData, sunburstId, {
                    width: w,
                    height: h,
                    innerRadius: 65,
                    animate: true,
                    oppositeLayout: window.sunburstOppositeLayout
                });
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
        $(`${sel} path[data-trait-name]`).each(function() {
            const attrName = $(this).attr('data-trait-name') || '';
            const isMatch = attrName.toLowerCase() === swing.traitKey.toLowerCase();
            $(this).toggleClass('highlight-swing-segment', isMatch);
        });
    });
}

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
            // Use canonical insertion order so poles are stable regardless of which arc was clicked
            const keys = Object.keys(traits);
            leftTrait = keys[0];
            rightTrait = keys[1];
            oppositeKey = Object.keys(traits).find(t => t !== traitName);
            break;
        }
    }
    if (!categoryKey || !oppositeKey || !leftTrait || !rightTrait) return;

    const capitalize = s => s.charAt(0).toUpperCase() + s.slice(1);
    $('#driftTraitLabel').text(`${capitalize(traitName)}  ↔  ${capitalize(oppositeKey)}`);
    $('#closeDriftBtn').show();

    // Build history array: position 0 = dot at left (leftTrait pole), position 1 = dot at right (rightTrait pole)
    const history = window.personaHistory.map((entry, i) => {
        const cat = entry.scores[categoryKey] || {};
        const lVal = cat[leftTrait] || 0;
        const rVal = cat[rightTrait] || 0;
        const position = 0.5 - (lVal - rVal) * 0.5;
        return { turn: i + 1, position };
    });

    // Render vertical SVG axis
    const container = document.getElementById('driftAxisContainer');
    if (!container) return;
    d3.select('#driftAxisContainer').selectAll('*').remove();

    const panelWidth = $('#chatPersonaPanel').width() || 380;
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

    // Pole labels
    svg.append('text')
        .attr('x', leftX).attr('y', 18)
        .attr('text-anchor', 'middle')
        .attr('font-size', '11px').attr('font-weight', '600')
        .attr('fill', '#888').attr('letter-spacing', '0.05em')
        .text(capitalize(leftTrait).toUpperCase());

    svg.append('text')
        .attr('x', rightX).attr('y', 18)
        .attr('text-anchor', 'middle')
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
            .attr('stroke', '#2196F3')
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

        // Dot — scales in from 0
        const dot = svg.append('circle')
            .attr('cx', dotX).attr('cy', y)
            .attr('r', 0)
            .attr('class', `drift-dot drift-dot-turn-${i}`)
            .attr('fill', isLatest ? '#2196F3' : '#bbb')
            .attr('stroke', 'white').attr('stroke-width', 2);
        dot.transition().delay(delay).duration(300)
            .ease(d3.easeBackOut)
            .attr('r', isLatest ? 9 : 6);

        // Click dot → scroll to & blink the user+assistant message pair
        dot.on('click', function() {
            const msgId = window.personaTurnMessageIds[i];
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

            // Remove highlight after 2 seconds
            setTimeout(() => {
                $user.removeClass('drift-click-highlight');
                if ($assistant.length) $assistant.removeClass('drift-click-highlight');
            }, 2000);
        });

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
    });
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
            opinionated: {
                opinionated: 0.68,     // Moderately opinionated
                'non-committal': 0
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
// TIMER FUNCTIONS
// ============================================

// Start the timer
async function startTimer() {
    if (window.timerStartTime !== null) {
        return;
    }
    
    window.timerStartTime = Date.now();
    const startTimeISO = new Date().toISOString();
    
    // Save timer start to Firebase
    const timerPath = studyId + '/participantData/' + firebaseUserId + '/session' + window.getCurrentSession() + '/timer';
    await writeRealtimeDatabase(timerPath + '/startTime', startTimeISO);
    await writeRealtimeDatabase(timerPath + '/duration', window.timerDuration);
    
    // Show timer display
    $('#timerDisplay').show();
    
    // Update timer every second
    window.timerInterval = setInterval(updateTimer, 1000);
    
    // Initial update
    updateTimer();
}

// Update timer display
function updateTimer() {
    if (window.timerStartTime === null || window.timerExpired) {
        return;
    }
    
    const elapsed = Math.floor((Date.now() - window.timerStartTime) / 1000);
    const remaining = Math.max(0, window.timerDuration - elapsed);
    
    // Format time as M:SS
    const minutes = Math.floor(remaining / 60);
    const seconds = remaining % 60;
    const timeString = `${minutes}:${seconds.toString().padStart(2, '0')}`;
    
    $('#timerText').text(timeString);
    
    // Check if timer has expired
    if (remaining <= 0 && !window.timerExpired) {
        timerExpired();
    }
}

// Timer has expired
async function timerExpired() {
    window.timerExpired = true;
    
    // Stop the interval
    if (window.timerInterval) {
        clearInterval(window.timerInterval);
        window.timerInterval = null;
    }
    
    // Save timer end to Firebase
    const endTimeISO = new Date().toISOString();
    const timerPath = studyId + '/participantData/' + firebaseUserId + '/session' + window.getCurrentSession() + '/timer';
    await writeRealtimeDatabase(timerPath + '/endTime', endTimeISO);

    // Disable chat interface
    $('#messageInput').prop('disabled', true);
    $('#sendBtn').prop('disabled', true);

    // Go directly to MBE (post-interaction trait evaluation)
    completePostSurvey();
}

// ============================================
// POST-SURVEY FUNCTIONS
// ============================================

// Show post-survey modal
function showPostSurvey() {
    // Skip post-survey in demo mode
    const isDemoMode = window.experimentSettings.demo;
    
    if (isDemoMode) {
        console.log('🎬 Demo mode: Skipping post-task survey');
        // In demo mode, just show a completion message or allow continued chatting
        // For now, just redirect to completion page
        completePostSurvey();
        return;
    }
    
    // Disable chat interface
    $('#messageInput').prop('disabled', true);
    $('#sendBtn').prop('disabled', true);
    $('#attachBtn').prop('disabled', true);
    $('#imageBtn').prop('disabled', true);
    $('#backToConfigBtn').prop('disabled', true);
    
    // Show/hide viz-specific questions based on effective condition
    const visualizationCondition = window.getEffectiveVisualizationCondition();
    if (visualizationCondition >= 1) {
        // Viz condition (single-turn or multi-turn): show questions 5 and 6
        $('#post_q5_container').show();
        $('#post_q6_container').show();
    } else {
        // Control condition: hide and clear questions 5 and 6
        $('#post_q5_container').hide();
        $('#post_q6_container').hide();
        $('input[name="post_q5"]').prop('checked', false);
        $('input[name="post_q6"]').prop('checked', false);
    }
    
    // Show modal
    $('#postSurveyModal').fadeIn(300);
    
    // Initialize post-survey event listeners
    initializePostSurvey();
}

// Initialize post-survey event listeners
function initializePostSurvey() {

    const visualizationCondition = window.getEffectiveVisualizationCondition();
    
    // Phase 1: Listen to radio button changes
    $('input[name="post_q1"], input[name="post_q2"], input[name="post_q3"], input[name="post_q4"], input[name="post_q5"], input[name="post_q6"]').on('change', function() {
        const q1Answered = $('input[name="post_q1"]:checked').length > 0;
        const q2Answered = $('input[name="post_q2"]:checked').length > 0;
        const q3Answered = $('input[name="post_q3"]:checked').length > 0;
        const q4Answered = $('input[name="post_q4"]:checked').length > 0;
        
        let allAnswered = q1Answered && q2Answered && q3Answered && q4Answered;
        
        // For viz condition (single-turn or multi-turn), also require q5 and q6
        if (visualizationCondition >= 1) {
            const q5Answered = $('input[name="post_q5"]:checked').length > 0;
            const q6Answered = $('input[name="post_q6"]:checked').length > 0;
            allAnswered = allAnswered && q5Answered && q6Answered;
        }
        
        $('#postPhase1ProceedBtn').prop('disabled', !allAnswered);
    });
    
    // Phase 1 Proceed button
    $('#postPhase1ProceedBtn').off('click').on('click', async function() {
        await savePostPhase1Data();
        $('#postSurveyPhase1').hide();
        $('#postSurveyPhase2').show();
    });
    
    // Phase 2: Listen to textarea input
    $('#postOpenEndedResponse').on('input', function() {
        const hasText = $(this).val().trim().length > 0;
        $('#postPhase2SubmitBtn').prop('disabled', !hasText);
    });
    
    // Phase 2 Back button
    $('#postPhase2BackBtn').off('click').on('click', function() {
        $('#postSurveyPhase2').hide();
        $('#postSurveyPhase1').show();
    });
    
    // Phase 2 Submit button
    $('#postPhase2SubmitBtn').off('click').on('click', async function() {
        await savePostPhase2Data();
        completePostSurvey();
    });
}

// Save Phase 1 data from post-survey
async function savePostPhase1Data() {
    try {
        const timestamp = new Date().toISOString();
        const visualizationCondition = window.getEffectiveVisualizationCondition();
        const _sess = window.getCurrentSession();

        const phase1Data = {
            "How well could you predict unintended behaviors from your system prompt?": parseInt($('input[name="post_q1"]:checked').val()),
            "How well could you predict negative unintended behaviors from your system prompt?": parseInt($('input[name="post_q2"]:checked').val()),
            "Given the {relevant background abt unintended model behaviors}, how much do you trust this model?": parseInt($('input[name="post_q3"]:checked').val()),
            "Did you arrive at your desired character?": parseInt($('input[name="post_q4"]:checked').val())
        };

        // Add viz-specific questions if in single-turn or multi-turn condition
        if (visualizationCondition >= 1) {
            phase1Data["Did the visualization help you understand model behavior?"] = parseInt($('input[name="post_q5"]:checked').val());
            phase1Data["Would you like to see this visualization again in future interactions?"] = parseInt($('input[name="post_q6"]:checked').val());
        }

        const basePath = `${studyId}/participantData/${firebaseUserId}/session${_sess}/chatPostSurvey`;
        const postPhase1WriteData = {
            responses: phase1Data,
            timestamp: timestamp,
            session: _sess,
            condition: ['control', 'single_turn', 'multi_turn'][visualizationCondition] || 'unknown'
        };
        await writeRealtimeDatabase(`${basePath}/phase1`, postPhase1WriteData);
        
    } catch (error) {
        console.error('❌ Error saving post-survey Phase 1 data:', error);
    }
}

// Save Phase 2 data from post-survey
async function savePostPhase2Data() {
    try {
        const timestamp = new Date().toISOString();
        
        const phase2Data = {
            "openEndedFeedback": $('#postOpenEndedResponse').val().trim()
        };
        
        const _sess2 = window.getCurrentSession();
        const basePath = `${studyId}/participantData/${firebaseUserId}/session${_sess2}/chatPostSurvey`;
        const postPhase2WriteData = {
            responses: phase2Data,
            timestamp: timestamp,
            session: _sess2
        };
        await writeRealtimeDatabase(`${basePath}/phase2`, postPhase2WriteData);
        
        // Update metadata with completion time
        await writeRealtimeDatabase(`${basePath}/metadata/completion_timestamp`, timestamp);
        await writeRealtimeDatabase(`${basePath}/metadata/completion_time`, Date.now());
        
    } catch (error) {
        console.error('❌ Error saving post-survey Phase 2 data:', error);
    }
}

// Complete post-survey and show inline MBE below the chat log
function completePostSurvey() {
    // Hide modal if it was shown
    $('#postSurveyModal').fadeOut(300);

    // Hide chat input area
    $('.input-container').hide();

    // Show transition modal, then inject MBE form when dismissed
    $('#mbeTransitionModal').fadeIn(300);
    $('#dismissMbeTransition').off('click').on('click', function() {
        $('#mbeTransitionModal').fadeOut(300, function() {
            injectInlineMBE();
        });
    });
}

// Inject the MBE trait rating form below the chat log
function injectInlineMBE() {
    // Gather session info
    const session = window.getCurrentSession();
    const promptText = window.getSessionPromptText(session);
    const promptType = window.getSessionPromptType(session);
    const prefix = 's' + session + 'mbe_';
    const nextLabel = session === 1 ? 'Submit & Continue to Session 2 →' : 'Submit & Continue to Final Survey →';

    // Inject MBE form below the chat log
    const mbeHtml = `
        <div id="mbeInlinePanel" style="border-top: 2px solid #667eea; margin-top: 1rem; padding: 1.25rem 0.5rem;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 12px 16px; border-radius: 8px; color: white; margin-bottom: 1rem;">
                <h5 style="margin: 0 0 4px 0; font-size: 1.05rem;">Model Behavior Evaluation</h5>
                <p style="margin: 0; font-size: 0.85rem; opacity: 0.9;">Now that you've observed the conversation, rate the activation level (0-10) for each behavioral trait.</p>
            </div>
            <details class="toggle-prompt" style="margin-bottom: 1rem; background: #ffffff; border: 1px solid #dee2e6; border-radius: 8px; padding: 0.75rem;">
                <summary style="cursor: pointer; font-size: 0.875rem; font-weight: 700; color: #2c3e50;">Show system prompt</summary>
                <p style="margin: 0.75rem 0 0 0; font-size: 0.875rem; line-height: 1.6; color: #2c3e50; white-space: pre-wrap; font-family: 'Courier New', monospace;">${promptText.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</p>
            </details>
            <div id="mbeInlineTraitForm"></div>
            <div style="text-align: right; margin-top: 1.25rem;">
                <button type="button" class="btn btn-primary" id="mbeInlineSubmitBtn" disabled>${nextLabel}</button>
            </div>
        </div>`;

    const messagesContainer = $('#messagesContainer');
    messagesContainer.append(mbeHtml);

    // Build trait form
    const form = window.buildTraitForm('mbeInlineTraitForm', prefix);

    // Skip mode: auto-fill
    if (window.experimentSettings && window.experimentSettings.skip) {
        form.autoFill();
        $('#mbeInlineSubmitBtn').prop('disabled', false);
    }

    // Validate on change
    $('#mbeInlineTraitForm').on('change', function() {
        $('#mbeInlineSubmitBtn').prop('disabled', !form.validate());
    });

    // Submit handler
    $('#mbeInlineSubmitBtn').on('click', async function() {
        if (!form.validate()) return;
        $(this).prop('disabled', true).text('Saving...');

        const data = {
            timestamp: new Date().toISOString(),
            session: session,
            promptType: promptType,
            systemPromptShown: promptText,
            traitPredictions: form.collect()
        };

        try {
            if (typeof window.writeTaskData === 'function') {
                await window.writeTaskData('session' + session + '/mbe', data);
            }
        } catch (e) {
            console.warn('MBE save error:', e);
        }

        // Route based on session
        if (session === 1) {
            if (typeof window.showSessionTransition === 'function') {
                window.showSessionTransition();
            }
        } else {
            if (typeof window.showFinalSurvey === 'function') {
                window.showFinalSurvey();
            }
        }
    });

    // Scroll to the MBE form
    setTimeout(function() {
        const panel = document.getElementById('mbeInlinePanel');
        if (panel) panel.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 400);
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
