// Simple Chat Interface JavaScript

// Initialize conversation history
let conversationHistory = [];
let messageIdCounter = 1;
let isWaiting = false;

$(document).ready(function() {
    initializeChat();
});

function initializeChat() {
    const messageInput = $('#messageInput');
    const sendBtn = $('#sendBtn');
    const messagesContainer = $('#messagesContainer');
    const typingIndicator = $('#typingIndicator');

    // Update model info in header
    $('#modelInfo').text(API_CONFIG.model || 'Modal AI');

    // Enable/disable send button based on input
    messageInput.on('input', function() {
        sendBtn.prop('disabled', isWaiting || messageInput.val().trim() === '');
        
        // Auto-resize textarea
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 128) + 'px';
    });

    // Send message on button click
    sendBtn.on('click', sendMessage);

    // Send message on Enter (but allow Shift+Enter for new line)
    messageInput.on('keypress', function(e) {
        if (e.which === 13 && !e.shiftKey && !isWaiting) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Clear button functionality (if you add one)
    $('#clearBtn').on('click', function() {
        if (confirm('Clear conversation history?')) {
            clearConversation();
        }
    });
}

// Send message function
async function sendMessage() {
    const messageInput = $('#messageInput');
    const message = messageInput.val().trim();
    
    if (message === '') return;

    // Add user message to conversation history
    conversationHistory.push({
        role: 'user',
        content: message
    });

    // Add user message to UI
    addMessage(message, 'user');
    
    // Clear input and reset height
    messageInput.val('');
    messageInput.css('height', 'auto');
    isWaiting = true;
    messageInput.prop('disabled', true);
    $('#sendBtn').prop('disabled', true);

    // Show typing indicator
    $('#typingIndicator').show();

    // Call AI API
    await callAIAPI();
}

function unlockInput() {
    isWaiting = false;
    const messageInput = $('#messageInput');
    messageInput.prop('disabled', false);
    $('#sendBtn').prop('disabled', messageInput.val().trim() === '');
    messageInput.focus();
}

// Call AI API
async function callAIAPI() {
    try {
        const requestData = {
            model: API_CONFIG.model,
            max_tokens: API_CONFIG.maxTokens,
            messages: conversationHistory,
            system: DEFAULT_SYSTEM_PROMPT
        };

        const data = await makeAPIRequest(requestData);

        // Hide typing indicator and re-enable input
        $('#typingIndicator').hide();
        unlockInput();

        // Extract assistant's response
        const assistantMessage = data.content[0].text;
        
        // Add assistant message to conversation history
        conversationHistory.push({
            role: 'assistant',
            content: assistantMessage
        });

        // Add assistant message to UI
        addMessage(assistantMessage, 'assistant');

    } catch (error) {
        console.error('Error calling AI API:', error);
        
        // Hide typing indicator and re-enable input
        $('#typingIndicator').hide();
        unlockInput();

        // Show error message
        let errorMessage = 'Sorry, I encountered an error. Please try again.';
        
        if (error.message.includes('API key')) {
            errorMessage = 'API configuration error. Please check your API settings.';
        } else if (error.message.includes('Rate limit')) {
            errorMessage = 'Rate limit exceeded. Please wait a moment and try again.';
        } else if (error.message.includes('CORS')) {
            errorMessage = 'Connection error. Please check your network connection.';
        }
        
        addMessage(errorMessage, 'assistant', true);
    }
}

// Add message to UI
function addMessage(text, sender, isError = false) {
    const messageId = messageIdCounter++;
    const messageClass = sender === 'user' ? 'user-message' : 'assistant-message';
    const messageHtml = `
        <div class="message ${messageClass}" data-message-id="${messageId}">
            <div class="message-content ${isError ? 'error-message' : ''}">
                <div class="message-text">${text}</div>
            </div>
        </div>
    `;
    
    const messagesContainer = $('#messagesContainer');
    messagesContainer.append(messageHtml);
    
    // Scroll to bottom
    messagesContainer.scrollTop(messagesContainer[0].scrollHeight);
    
    return messageId;
}

// Clear conversation
function clearConversation() {
    conversationHistory = [];
    $('#messagesContainer').empty();
    
    // Add welcome message back
    const welcomeHtml = `
        <div class="message assistant-message">
            <div class="message-avatar">
                <i class="fas fa-robot"></i>
            </div>
            <div class="message-content">
                <div class="message-text">Hi there! How can I help you today?</div>
            </div>
        </div>
    `;
    $('#messagesContainer').append(welcomeHtml);
    messageIdCounter = 1;
}




