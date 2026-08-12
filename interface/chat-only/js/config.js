// API Configuration
// Switch between Claude and Modal by commenting/uncommenting the appropriate config

// Claude API Configuration
// const API_CONFIG = {
//     model: 'claude-3-5-sonnet-20241022',
//     maxTokens: 1000,
//     apiEndpoint: '/api/claude'
// };

// Modal AI Configuration
const API_CONFIG = {
    maxTokens: 1000,
    apiEndpoint: '/api/modal'
};

// System prompt - customize this to change the AI's behavior
const DEFAULT_SYSTEM_PROMPT = "You are a helpful, friendly AI assistant. Provide clear, concise, and informative responses. Be conversational and engaging.";

// Make API request
async function makeAPIRequest(requestData) {
    try {
        const response = await fetch(API_CONFIG.apiEndpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });

        if (response.ok) {
            return await response.json();
        } else {
            const errorData = await response.json();
            throw new Error(errorData.error || `API request failed with status: ${response.status}`);
        }
    } catch (error) {
        console.error('API error:', error);
        throw error;
    }
}




