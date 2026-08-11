# MIT Media Lab Chat Study

A streamlined research study interface for conducting chat-based experiments using Claude AI, designed exclusively for Vercel serverless deployment with zero configuration required for participants.

## 🚀 Quick Start

### Deploy to Vercel (One-Click Setup)

1. **Fork or clone this repository**
2. **Connect to Vercel**:
   - Go to [vercel.com](https://vercel.com)
   - Import your repository
   - Deploy with one click

3. **Set up environment variables**:
   - In Vercel dashboard: Settings → Environment Variables
   - Add: `ANTHROPIC_API_KEY` = your Anthropic API key
   - Redeploy the project

4. **Access your study**: Your study will be live at `https://your-project.vercel.app`

**That's it!** No additional configuration needed - participants can start using the chat interface immediately.

### Local Development

1. **Install Vercel CLI**: `npm i -g vercel`
2. **Clone and setup**: 
   ```bash
   git clone <your-repo>
   cd mech-chat-iui
   vercel dev
   ```
3. **Set environment variable**: `vercel env add ANTHROPIC_API_KEY`
4. **Access locally**: `http://localhost:3000`

## 📋 Features

- **Zero Configuration**: Participants can start chatting immediately - no API key setup required
- **Serverless Architecture**: Deployed on Vercel with automatic scaling
- **Secure API Handling**: API keys stored server-side, never exposed to frontend
- **Clean Interface**: Streamlined chat interface without settings or configuration UI
- **Research-Ready**: Built for academic studies with consent flow and data collection
- **Firebase Integration**: Optional data collection and analytics
- **Mobile Responsive**: Works on all devices

## 🏗️ Architecture

### Frontend
- **Static Files**: HTML, CSS, JavaScript served from Vercel CDN
- **Framework**: Vanilla JavaScript with jQuery
- **Styling**: Custom CSS with modern design system
- **Responsive**: Mobile-first design

### Backend
- **Serverless Function**: `/api/claude` handles Claude API calls
- **Security**: API key stored in environment variables
- **CORS**: Properly configured for frontend requests
- **Error Handling**: Comprehensive error management

### Data Flow
```
User Input → Frontend → /api/claude → Anthropic API → Response → Frontend → User
```

## 📁 Project Structure

```
├── index.html                 # Main application entry point
├── api/
│   └── modal.js             # Serverless function for Modal Chat API
│   └── persona-vector.js    # Serverless function for Persona Vector Generation API
├── js/
│   ├── config-unified.js     # Unified configuration (Vercel + local)
│   ├── chat.js              # Chat interface logic
│   ├── consent.js           # Consent form handling
│   ├── metadata.js          # Study metadata
│   └── firebasepsych1.1.js  # Firebase integration
├── html/
│   ├── consent.html         # Consent page
│   └── chat-content.html    # Chat interface
├── css/
│   └── consent.css          # Consent page styles
├── images/
│   └── ml_logo.png          # MIT Media Lab logo
├── vercel.json              # Vercel configuration
├── package.json             # Dependencies
└── VERCEL_DEPLOYMENT.md     # Detailed deployment guide
```

## ⚙️ Configuration

### Environment Variables
- `ANTHROPIC_API_KEY`: Your Anthropic API key (required)

### API Configuration
The application is designed exclusively for Vercel deployment:
- **Vercel Production**: Uses serverless function (API key handled server-side)
- **Local Development**: Uses Vercel CLI for development environment

### Customization
- **Study Title**: Edit `#experiment-title` in `index.html`
- **Chat System Prompt**: Modify in `js/chat.js`
- **Styling**: Update CSS variables in `index.html`
- **Firebase**: Configure in `js/firebasepsych1.1.js`

## 🔧 Development

### Prerequisites
- Node.js 18+ (for Vercel CLI)
- Anthropic API key
- Git

### Local Setup
1. Clone the repository
2. Install Vercel CLI: `npm i -g vercel`
3. Run `vercel dev` for local development
4. Set environment variables as needed

### Testing
- Test locally with `vercel dev`
- Test production deployment
- Verify API functionality
- Check mobile responsiveness

## 👥 User Experience

### For Study Participants
- **Zero Setup Required**: No API keys, accounts, or configuration needed
- **Immediate Access**: Start chatting as soon as they visit the site
- **Clean Interface**: No distracting settings or configuration options
- **Mobile Friendly**: Works seamlessly on all devices

### For Researchers
- **Easy Deployment**: One-click setup on Vercel
- **Secure by Default**: API keys handled server-side automatically
- **Scalable**: Handles any number of participants automatically
- **Maintenance-Free**: No server management or updates needed

## 📊 Research Features

### Consent Management
- IRB-compliant consent flow
- Participant information display
- Consent tracking

### Data Collection
- Optional Firebase integration
- Conversation logging
- Participant analytics
- Export capabilities

### Study Flow
1. **Consent Page**: Participant agreement
2. **Instructions**: Study guidelines
3. **Chat Interface**: Main experiment (zero configuration)
4. **Survey**: Optional post-study questions
5. **Completion**: Thank you and next steps

## 🚀 Deployment

### Vercel (Exclusively Supported)
- **Pros**: Serverless, secure, fast, free tier, zero configuration
- **Setup**: Connect GitHub repo, add API key, deploy
- **Cost**: Free for research studies
- **Why Vercel Only**: Simplified architecture, better security, easier maintenance

**Note**: This application is optimized specifically for Vercel's serverless architecture. Other platforms are not supported due to the simplified design approach.

## 🔒 Security

### API Key Protection
- Stored in Vercel environment variables
- Never exposed to frontend
- Encrypted at rest

### Data Privacy
- No data stored on frontend
- Optional Firebase for research data
- GDPR compliant design

### CORS Security
- Properly configured for your domain
- No wildcard origins
- Secure headers

## 📈 Performance

### Vercel Benefits
- **Global CDN**: Fast loading worldwide
- **Serverless**: Automatic scaling
- **Edge Functions**: Low latency
- **Caching**: Optimized delivery

### Optimization
- Minified assets
- Optimized images
- Efficient API calls
- Responsive design

## 🐛 Troubleshooting

### Common Issues

#### API Not Working
- Check environment variables in Vercel dashboard
- Verify `ANTHROPIC_API_KEY` is set correctly
- Check function logs in Vercel dashboard
- Ensure you've redeployed after setting environment variables

#### Chat Interface Not Loading
- Check browser console for JavaScript errors
- Verify all static files are loading (no 404 errors)
- Ensure Vercel deployment completed successfully

#### Build Failures
- Check `package.json` dependencies
- Verify `vercel.json` configuration
- Review build logs in Vercel dashboard

### Getting Help
- Check [VERCEL_DEPLOYMENT.md](VERCEL_DEPLOYMENT.md) for detailed guide
- Review Vercel documentation
- Check browser console for errors
- Contact Vercel support for platform issues

## 📚 Documentation

- [VERCEL_DEPLOYMENT.md](VERCEL_DEPLOYMENT.md) - Detailed deployment guide
- [API_KEY_SETUP.md](API_KEY_SETUP.md) - API key configuration
- [SECURE_DEPLOYMENT.md](SECURE_DEPLOYMENT.md) - Security best practices

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🏛️ MIT Media Lab

This project is developed for research at the MIT Media Lab. For questions about the study or research purposes, please contact the study administrators.

---

**Ready to deploy?** Follow the [Vercel Deployment Guide](VERCEL_DEPLOYMENT.md) to get started!
