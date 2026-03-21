# Files Overview

Quick reference guide for all files in the chat-only folder.

## 📁 Project Structure

```
chat-only/
├── 📄 index.html              # Main chat interface (REQUIRED)
├── 📄 index-demo.html         # Demo version with mock responses (NO API NEEDED)
│
├── 📁 css/
│   └── 📄 chat.css            # All styling (REQUIRED)
│
├── 📁 js/
│   ├── 📄 config.js           # API configuration (REQUIRED)
│   └── 📄 chat.js             # Chat logic (REQUIRED)
│
├── 📄 package.json            # NPM scripts for easy dev server
├── 📄 vercel.json            # Vercel deployment config
├── 📄 .gitignore             # Git ignore rules
│
└── 📁 docs/
    ├── 📄 README.md           # Full documentation
    ├── 📄 QUICKSTART.md       # Get started in 3 minutes
    ├── 📄 WHAT_WAS_SIMPLIFIED.md  # What changed from original
    └── 📄 FILES_OVERVIEW.md   # This file!
```

## 🔧 Required Files (Can't Delete)

### `index.html` 
- **Size:** ~2 KB
- **Purpose:** Main HTML structure
- **Edit if:** You want to change layout or add elements
- **Don't touch if:** You just want to customize colors/API

### `css/chat.css`
- **Size:** ~13 KB  
- **Purpose:** All visual styling
- **Edit if:** You want to change colors, fonts, layout
- **Key sections:**
  - Lines 4-23: CSS variables (colors, spacing)
  - Lines 43-80: Chat container sizing
  - Lines 240-310: Message styling
  - Lines 550+: Responsive mobile styles

### `js/config.js`
- **Size:** ~1 KB
- **Purpose:** API configuration
- **Edit if:** Switching between Claude/Modal or changing system prompt
- **Key parts:**
  - Lines 6-10: Claude config (commented out)
  - Lines 13-16: Modal config (active)
  - Line 19: System prompt

### `js/chat.js`
- **Size:** ~4 KB
- **Purpose:** All chat functionality
- **Edit if:** Adding features or changing behavior
- **Key functions:**
  - `initializeChat()` - Sets up event listeners
  - `sendMessage()` - Handles user input
  - `callAIAPI()` - Makes API requests
  - `addMessage()` - Adds messages to UI

## 📚 Documentation Files

### `README.md`
- Complete documentation
- Feature list
- Setup instructions
- Customization guide

### `QUICKSTART.md` ⭐ START HERE
- 3-minute setup guide
- Multiple deployment options
- Troubleshooting tips
- Mock mode for testing

### `WHAT_WAS_SIMPLIFIED.md`
- Explains what was removed from original
- Size comparison
- Feature breakdown
- When to use which version

## 🚀 Optional Files

### `index-demo.html` ⭐ TRY THIS FIRST
- **Purpose:** Test the UI without setting up API
- **How to use:** 
  ```bash
  # Open directly in browser or:
  python -m http.server 8000
  # Visit: http://localhost:8000/index-demo.html
  ```
- **No API needed!** Uses mock responses

### `package.json`
- **Purpose:** NPM scripts for development
- **Usage:**
  ```bash
  npm start    # Starts dev server on port 8000
  ```
- **Can delete if:** You use Python or other server

### `vercel.json`
- **Purpose:** Vercel deployment configuration
- **Can delete if:** Not deploying to Vercel

### `.gitignore`
- **Purpose:** Tells Git which files to ignore
- **Can delete if:** Not using Git

## 🎯 Quick Edits Guide

### Change Colors
**File:** `css/chat.css` (lines 4-23)
```css
--accent-color: #3b82f6;  /* Your brand color */
```

### Change AI Personality  
**File:** `js/config.js` (line 19)
```javascript
const DEFAULT_SYSTEM_PROMPT = "Your custom prompt here";
```

### Switch API Provider
**File:** `js/config.js` (lines 6-16)
- Comment out current config
- Uncomment desired config

### Change Size
**File:** `css/chat.css` (lines 43-48)
```css
.chat-container {
    max-width: 900px;  /* Width */
    height: 90vh;      /* Height */
}
```

## 📊 File Sizes

| File | Size | Loading Time |
|------|------|--------------|
| index.html | 2 KB | Instant |
| chat.css | 13 KB | <50ms |
| config.js | 1 KB | Instant |
| chat.js | 4 KB | Instant |
| **Total** | **~20 KB** | **<100ms** |

*Plus CDN libraries (jQuery + Font Awesome loaded once, cached forever)*

## 🔄 Update Strategy

When updating, check these files in order:

1. **`js/config.js`** - API changes, system prompt updates
2. **`css/chat.css`** - Visual updates, theming
3. **`js/chat.js`** - Feature additions, bug fixes
4. **`index.html`** - Structure changes (rare)

## 💾 Backup Essentials

Before making changes, backup:
- ✅ `js/config.js` (your API settings)
- ✅ `css/chat.css` (your custom styles)
- ✅ `index.html` (if you modified structure)

## 🐛 Debugging Checklist

| Issue | Check This File | Line Numbers |
|-------|----------------|--------------|
| Wrong colors | css/chat.css | 4-23 |
| API not working | js/config.js | 6-16 |
| Messages not sending | js/chat.js | 50-70 |
| Layout broken | css/chat.css | 43-80 |
| Mobile issues | css/chat.css | 550+ |

## 📱 Mobile-Specific Files

All mobile styling is in `css/chat.css` starting at line 550.

**Media queries handle:**
- Smaller avatars
- Full-screen layout  
- Adjusted padding
- Hidden hints text

## 🎨 Customization Targets

**Beginner Level:**
- Colors: `css/chat.css` lines 4-23
- System prompt: `js/config.js` line 19
- Title: `index.html` line 20

**Intermediate Level:**
- Message styling: `css/chat.css` lines 240-310
- Layout: `css/chat.css` lines 43-80
- API endpoint: `js/config.js` lines 6-16

**Advanced Level:**
- Add features: `js/chat.js`
- Custom animations: `css/chat.css`
- New API provider: `js/config.js` + `js/chat.js`

---

**Need help?** Check the corresponding section in README.md or QUICKSTART.md!




