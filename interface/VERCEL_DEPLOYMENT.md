# Vercel Deployment Guide

## Overview
This guide will help you deploy the MIT Media Lab Chat Study to Vercel for serverless deployment. Vercel provides better performance, security, and reliability compared to GitHub Pages.

## Prerequisites
- Vercel account (free tier available)
- Anthropic API key
- Git repository (GitHub, GitLab, or Bitbucket)

## Quick Setup

### 1. Prepare Your Repository
1. Ensure all files are committed to your Git repository
2. The following files should be present:
   - `index.html` (main page)
   - `api/claude.js` (serverless function)
   - `vercel.json` (Vercel configuration)
   - `package.json` (dependencies)
   - All other static assets (js/, css/, html/, images/)

### 2. Deploy to Vercel

#### Option A: Deploy via Vercel Dashboard
1. Go to [vercel.com](https://vercel.com) and sign in
2. Click "New Project"
3. Import your Git repository
4. Vercel will automatically detect the configuration
5. Click "Deploy"

#### Option B: Deploy via Vercel CLI
1. Install Vercel CLI: `npm i -g vercel`
2. In your project directory, run: `vercel`
3. Follow the prompts to link your project
4. Run `vercel --prod` to deploy to production

### 3. Configure Environment Variables
1. Go to your project dashboard on Vercel
2. Navigate to Settings > Environment Variables
3. Add the following variable:
   - **Name**: `ANTHROPIC_API_KEY`
   - **Value**: Your Anthropic API key
   - **Environment**: Production, Preview, Development

### 4. Redeploy
After adding environment variables, redeploy your project:
- Via CLI: `vercel --prod`
- Via Dashboard: Go to Deployments tab and click "Redeploy"

## How It Works

### Serverless Architecture
- **Frontend**: Static files served from Vercel's CDN
- **API**: Serverless function at `/api/claude` handles Claude API calls
- **Security**: API key stored securely in environment variables
- **Performance**: Global CDN for fast loading worldwide

### Automatic Environment Detection
The application automatically detects whether it's running on:
- **Vercel (Production)**: Uses serverless API function (no API key needed on frontend)
- **Local Development**: Falls back to CORS proxies (API key required)

### File Structure
```
your-project/
├── index.html                 # Main application
├── api/
│   └── claude.js             # Serverless function for Claude API
├── js/
│   ├── config-unified.js     # Unified configuration
│   ├── chat.js              # Chat interface logic
│   └── ...                  # Other JS files
├── html/                     # HTML templates
├── css/                      # Stylesheets
├── images/                   # Static assets
├── vercel.json              # Vercel configuration
└── package.json             # Dependencies
```

## Configuration Details

### vercel.json
```json
{
  "version": 2,
  "builds": [
    {
      "src": "index.html",
      "use": "@vercel/static"
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "/api/$1"
    },
    {
      "src": "/(.*)",
      "dest": "/$1"
    }
  ],
  "env": {
    "ANTHROPIC_API_KEY": "@anthropic_api_key"
  }
}
```

### API Function (api/claude.js)
- Handles Claude API requests server-side
- Manages API key securely
- Provides proper error handling
- Supports CORS for frontend requests

## Benefits of Vercel Deployment

### Security
- API key never exposed to frontend
- Environment variables encrypted
- HTTPS by default
- No CORS issues

### Performance
- Global CDN
- Serverless functions scale automatically
- Fast cold starts
- Edge caching

### Reliability
- 99.99% uptime SLA
- Automatic failover
- Built-in monitoring
- Easy rollbacks

### Developer Experience
- Automatic deployments from Git
- Preview deployments for PRs
- Built-in analytics
- Easy environment management

## Local Development

### Using Vercel CLI
1. Install: `npm i -g vercel`
2. Run: `vercel dev`
3. Set environment variable: `vercel env add ANTHROPIC_API_KEY`
4. Access at `http://localhost:3000`

### Using Live Server (Fallback)
1. Use any static file server
2. Set your Anthropic API key in the settings modal
3. The app will use CORS proxies for API calls

## Troubleshooting

### Common Issues

#### 1. API Key Not Working
- Ensure `ANTHROPIC_API_KEY` is set in Vercel environment variables
- Check that the API key is valid and has sufficient credits
- Redeploy after adding environment variables

#### 2. CORS Errors
- These should not occur with Vercel deployment
- If they do, check that the API route is properly configured
- Ensure the frontend is making requests to `/api/claude`

#### 3. Function Timeout
- Vercel functions have a 10-second timeout on the free tier
- Consider upgrading to Pro for longer timeouts
- Optimize your API calls if needed

#### 4. Build Failures
- Check that all dependencies are in `package.json`
- Ensure `vercel.json` is properly formatted
- Check the build logs in Vercel dashboard

### Getting Help
- Check Vercel documentation: [vercel.com/docs](https://vercel.com/docs)
- View deployment logs in Vercel dashboard
- Check browser console for frontend errors
- Contact Vercel support for platform issues

## Migration from GitHub Pages

### What Changed
1. **API Calls**: Now use serverless function instead of CORS proxies
2. **Security**: API key stored server-side instead of client-side
3. **Performance**: Better caching and global CDN
4. **Reliability**: No dependency on external CORS proxy services

### Files to Remove
- `GITHUB_PAGES_SETUP.md` (no longer needed)
- Any GitHub Pages specific configurations

### Files Added
- `vercel.json` (Vercel configuration)
- `package.json` (dependencies)
- `api/claude.js` (serverless function)

## Cost Considerations

### Vercel Free Tier
- 100GB bandwidth per month
- 100 serverless function invocations per day
- Unlimited static deployments
- Perfect for research studies

### Upgrading
- Pro plan ($20/month) for higher limits
- Enterprise for advanced features
- Pay-as-you-go for additional usage

## Next Steps

1. **Deploy**: Follow the quick setup guide above
2. **Test**: Verify the chat interface works correctly
3. **Monitor**: Check Vercel dashboard for usage and errors
4. **Scale**: Upgrade plan if needed for higher usage

Your MIT Media Lab Chat Study is now ready for production deployment on Vercel!
