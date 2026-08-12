# API Key Setup for Vercel Deployment

This guide explains how to securely set up your Anthropic API key for the MIT Media Lab Chat Study on Vercel.

## 🔑 Getting Your Anthropic API Key

1. **Visit Anthropic Console**: Go to [console.anthropic.com](https://console.anthropic.com/)
2. **Sign in or create account**: Use your email to create an account
3. **Navigate to API Keys**: Click on "API Keys" in the sidebar
4. **Create new key**: Click "Create Key" and give it a descriptive name
5. **Copy the key**: Save it securely (starts with `sk-ant-...`)

## 🚀 Setting Up in Vercel

### Method 1: Vercel Dashboard (Recommended)

1. **Go to your project** in [vercel.com](https://vercel.com)
2. **Navigate to Settings**: Click "Settings" tab
3. **Go to Environment Variables**: Click "Environment Variables" in the sidebar
4. **Add new variable**:
   - **Name**: `ANTHROPIC_API_KEY`
   - **Value**: Your API key (paste the full key)
   - **Environments**: Check all three boxes:
     - ✅ Production
     - ✅ Preview  
     - ✅ Development
5. **Save**: Click "Save" button
6. **Redeploy**: Go to "Deployments" tab and click "Redeploy"

### Method 2: Vercel CLI

1. **Install Vercel CLI**: `npm i -g vercel`
2. **Login**: `vercel login`
3. **Add environment variable**:
   ```bash
   vercel env add ANTHROPIC_API_KEY
   ```
4. **Enter your API key** when prompted
5. **Deploy**: `vercel --prod`

## ✅ Verifying Setup

### Check Environment Variable
1. **Visit your Vercel site**
2. **Open browser console** (F12)
3. **Send a test message** in the chat
4. **Check for errors** - should work without API key prompts

### Test API Function
Visit: `https://your-project.vercel.app/api/test-env`

You should see:
```json
{
  "hasApiKey": true,
  "apiKeyLength": 108,
  "apiKeyPrefix": "sk-ant-api...",
  "allEnvVars": ["ANTHROPIC_API_KEY", ...]
}
```

## 🔒 Security Features

### What Vercel Provides
- **Encrypted storage**: API keys are encrypted at rest
- **Server-side only**: Keys never exposed to frontend
- **Environment isolation**: Separate keys for dev/preview/production
- **Access control**: Only project team members can view/modify

### Best Practices
- **Use separate keys**: Different keys for development and production
- **Monitor usage**: Check Anthropic dashboard regularly
- **Rotate keys**: Update keys periodically for security
- **Team access**: Only give Vercel access to trusted team members

## 🐛 Troubleshooting

### Common Issues

#### "API key not configured" Error
- **Check name**: Ensure it's exactly `ANTHROPIC_API_KEY` (case-sensitive)
- **Check environments**: Make sure all environments are selected
- **Redeploy**: You must redeploy after adding environment variables

#### API Key Not Working
- **Verify key**: Check the key is valid in Anthropic console
- **Check logs**: Look at Vercel function logs for errors
- **Test endpoint**: Use the test endpoint to verify setup

#### Function Timeout
- **Check key format**: Ensure no extra spaces or characters
- **Verify permissions**: Check Anthropic account has API access
- **Monitor usage**: Check if you've hit rate limits

## 📊 Monitoring Usage

### Anthropic Dashboard
1. **Visit**: [console.anthropic.com](https://console.anthropic.com/)
2. **Go to Usage**: Check your API usage and costs
3. **Set alerts**: Configure usage notifications
4. **Monitor patterns**: Watch for unusual activity

### Vercel Analytics
1. **Go to Vercel dashboard**
2. **Click "Analytics"** tab
3. **Monitor function calls**: Track API function usage
4. **Check performance**: Monitor response times

## 💡 Tips for Research Studies

### Cost Management
- **Set usage limits**: Configure spending limits in Anthropic
- **Monitor daily**: Check usage during active studies
- **Optimize prompts**: Use efficient system prompts to reduce tokens

### Study Preparation
- **Test thoroughly**: Verify everything works before study launch
- **Have backup**: Keep a second API key ready
- **Monitor during study**: Watch for any issues during data collection

## 🆘 Getting Help

### If You're Stuck
1. **Check Vercel docs**: [vercel.com/docs](https://vercel.com/docs)
2. **Anthropic support**: [support.anthropic.com](https://support.anthropic.com)
3. **Test endpoint**: Use `/api/test-env` to debug
4. **Check logs**: Review Vercel function logs

### Emergency Backup
If your API key stops working during a study:
1. **Quick fix**: Add a new key in Vercel dashboard
2. **Redeploy**: Trigger immediate redeployment
3. **Verify**: Test the chat interface works
4. **Continue study**: Minimal disruption to participants

---

**Ready to deploy?** Once your API key is set up, your chat study will be ready for participants with zero configuration required on their end!