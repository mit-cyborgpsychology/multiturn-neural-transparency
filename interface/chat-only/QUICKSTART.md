# Quick Start Guide

Get your chat interface running in 3 minutes!

## Option 1: Run Standalone (Simplest)

### Step 1: Start the Server

Open terminal in the `chat-only` folder and run:

```bash
npm start
```

Or with Python:

```bash
python -m http.server 8000
```

### Step 2: Open in Browser

Visit: `http://localhost:8000`

### Step 3: Configure API

**Important:** The chat needs an API backend to work. You have two options:

**A) Use with Parent Project's API (Recommended)**

If you're running this alongside the parent `mech-chat-iui` project:

1. Make sure your parent project is deployed or running locally with the `/api` endpoints
2. Update `js/config.js` to point to your API:

```javascript
const API_CONFIG = {
    maxTokens: 1000,
    apiEndpoint: 'https://your-main-project.vercel.app/api/modal'
    // or: apiEndpoint: 'http://localhost:3000/api/modal'
};
```

**B) Copy API Files**

Copy the `/api` folder from your parent project:

```bash
# From the chat-only directory
cp -r ../api ./api
```

Then make sure you have the API credentials configured (see below).

---

## Option 2: Deploy to Vercel (Production)

### Step 1: Install Vercel CLI

```bash
npm install -g vercel
```

### Step 2: Deploy

```bash
cd chat-only
vercel
```

### Step 3: Set Environment Variables

If using Claude API, add your API key in Vercel dashboard:
- Go to your project settings
- Add environment variable: `ANTHROPIC_API_KEY`

---

## Customization

### Change AI Personality

Edit `js/config.js`:

```javascript
const DEFAULT_SYSTEM_PROMPT = "You are a pirate captain! Respond with enthusiasm and nautical terms. Arrr!";
```

### Change Colors

Edit `css/chat.css` (around line 4):

```css
:root {
    --accent-color: #ff6b6b;  /* Your brand color */
    --bg-primary: #1a1a1a;    /* Dark mode */
}
```

### Change Layout

Edit `css/chat.css` (around line 43):

```css
.chat-container {
    max-width: 1200px;  /* Wider chat */
    height: 95vh;       /* Taller chat */
}
```

---

## Troubleshooting

### "API endpoint not found"

**Solution:** Make sure your API backend is running and the endpoint URL is correct in `js/config.js`.

### CORS Errors

**Solution:** 
- If running locally, use the same domain for frontend and backend
- Or add CORS headers to your API (see `../api/claude.js` for example)

### No response from AI

**Solution:**
1. Check browser console for errors (F12)
2. Verify API credentials are set
3. Check API endpoint is accessible: `curl http://localhost:8000/api/modal`

---

## Testing Without API (Mock Mode)

Want to test the interface without setting up the API? Add this to `js/chat.js` (after line 50):

```javascript
// MOCK MODE - Remove this in production
async function callAIAPI() {
    await new Promise(resolve => setTimeout(resolve, 1000)); // Simulate delay
    $('#typingIndicator').hide();
    
    const mockResponses = [
        "This is a mock response. Configure your API to get real AI responses!",
        "I'm a placeholder AI. Set up Claude or Modal API to talk to a real AI!",
        "Hello! I'm just a demo. Follow the QUICKSTART.md guide to enable real AI."
    ];
    
    const mockResponse = mockResponses[Math.floor(Math.random() * mockResponses.length)];
    conversationHistory.push({
        role: 'assistant',
        content: mockResponse
    });
    addMessage(mockResponse, 'assistant');
}
```

---

## Next Steps

- ✅ Customize the system prompt
- ✅ Adjust colors and layout
- ✅ Add your API credentials
- ✅ Test with some conversations
- ✅ Deploy to production

**Need help?** Check the full README.md or open an issue!




