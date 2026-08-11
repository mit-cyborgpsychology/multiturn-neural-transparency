# Simple Chat Interface

A simplified, clean chat interface for conversing with AI models (Claude or Modal).

## Features

- 💬 Clean, modern chat interface
- 🎨 Responsive design that works on desktop and mobile
- ⚡ Real-time message updates
- 🤖 Support for Claude and Modal AI backends
- 📝 Auto-resizing text input
- ⌨️ Keyboard shortcuts (Enter to send, Shift+Enter for new line)

## Setup

### 1. Configure the API

Open `js/config.js` and choose your AI backend:

**For Claude:**
```javascript
const API_CONFIG = {
    model: 'claude-3-5-sonnet-20241022',
    maxTokens: 1000,
    apiEndpoint: '/api/claude'
};
```

**For Modal:**
```javascript
const API_CONFIG = {
    maxTokens: 1000,
    apiEndpoint: '/api/modal'
};
```

### 2. Customize System Prompt (Optional)

In `js/config.js`, you can change the AI's behavior by editing:

```javascript
const DEFAULT_SYSTEM_PROMPT = "You are a helpful, friendly AI assistant...";
```

### 3. Run Locally

You can use any local server. For example:

**With Python:**
```bash
# Python 3
python -m http.server 8000

# Then open: http://localhost:8000
```

**With Node.js:**
```bash
npx http-server -p 8000

# Then open: http://localhost:8000
```

**With VS Code:**
- Install "Live Server" extension
- Right-click `index.html` and select "Open with Live Server"

### 4. Deploy to Vercel (Optional)

1. Make sure your parent project has the `/api/claude.js` or `/api/modal.js` endpoints
2. The chat will automatically work on Vercel domains

## File Structure

```
chat-only/
├── index.html          # Main HTML file
├── css/
│   └── chat.css        # Styles
├── js/
│   ├── config.js       # API configuration
│   └── chat.js         # Chat logic
└── README.md           # This file
```

## Customization

### Colors

Edit the CSS variables in `css/chat.css`:

```css
:root {
    --accent-color: #3b82f6;  /* Change primary color */
    --bg-primary: #ffffff;     /* Background color */
    /* ... more variables ... */
}
```

### Layout

The chat container is responsive and centered. Modify `.chat-container` in `css/chat.css` to adjust size:

```css
.chat-container {
    max-width: 900px;  /* Change max width */
    height: 90vh;      /* Change height */
}
```

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers (iOS Safari, Chrome Mobile)

## Dependencies

- jQuery 3.7.1 (loaded from CDN)
- Font Awesome 6.0.0 (loaded from CDN)

## License

Use freely for your projects!




