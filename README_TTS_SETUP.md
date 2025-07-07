# Free TTS API Setup Guide

This guide will help you set up free text-to-speech APIs to replace the slow local TTS and rate-limited ElevenLabs.

## 🚀 Quick Start - Azure TTS (Recommended)

**Azure TTS** offers the best free tier with high-quality neural voices.

### Setup Steps:

1. **Create Azure Account**: Go to [Azure Portal](https://portal.azure.com) and create a free account
2. **Create Speech Service**:
   - Search for "Speech service" in Azure Portal
   - Click "Create" and choose "Free" tier
   - Select your region (e.g., "East US")
   - Complete the setup
3. **Get API Key**:
   - Go to your Speech service resource
   - Click "Keys and Endpoint" in the left menu
   - Copy "Key 1" and your region
4. **Add to .env file**:
   ```
   AZURE_TTS_KEY=your_azure_key_here
   AZURE_TTS_REGION=eastus
   ```

### Benefits:

- ✅ 500,000 characters per month free
- ✅ High-quality neural voices
- ✅ Fast generation
- ✅ No credit card required for free tier

---

## 🎯 Alternative: Google Cloud TTS

**Google Cloud TTS** also has a generous free tier.

### Setup Steps:

1. **Create Google Cloud Account**: Go to [Google Cloud Console](https://console.cloud.google.com)
2. **Enable Text-to-Speech API**:
   - Search for "Text-to-Speech API" in the console
   - Click "Enable"
3. **Create Service Account**:
   - Go to "IAM & Admin" > "Service Accounts"
   - Click "Create Service Account"
   - Download the JSON key file
4. **Set Environment Variable**:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="path/to/your/service-account-key.json"
   ```
5. **Install Library**:
   ```bash
   pip install google-cloud-texttospeech
   ```

### Benefits:

- ✅ 4 million characters per month free
- ✅ Multiple voice options
- ✅ Good quality

---

## 🤗 Alternative: Hugging Face TTS

**Hugging Face** offers completely free TTS models.

### Setup Steps:

1. **Get API Key** (optional but recommended):
   - Go to [Hugging Face](https://huggingface.co)
   - Create account and go to Settings > Access Tokens
   - Create a new token
2. **Add to .env file**:
   ```
   HUGGINGFACE_API_KEY=your_hf_token_here
   ```

### Benefits:

- ✅ Completely free
- ✅ No rate limits (with API key)
- ✅ Open-source models

---

## 📋 How to Use in the App

1. **Open the Voiceover Page** in your app
2. **Select TTS Service** from the dropdown:
   - Choose "Azure TTS" for best quality
   - Choose "Hugging Face TTS" for completely free
   - Choose "Google TTS" for high limits
3. **Select a Voice** from the available options
4. **Click "Generate Voiceover"**

## 🔧 Troubleshooting

### Azure TTS Issues:

- **401 Error**: Check your API key and region
- **Quota Exceeded**: Upgrade to paid tier or wait for next month

### Google TTS Issues:

- **Authentication Error**: Check your service account key
- **Import Error**: Install with `pip install google-cloud-texttospeech`

### Hugging Face Issues:

- **401 Error**: Add your API key to .env file
- **Model Loading**: Wait a moment, models load on first use

## 💡 Tips

1. **Start with Azure TTS** - it's the easiest to set up and has great quality
2. **Keep ElevenLabs as backup** - for when you need premium voices
3. **Use shorter scripts** - faster generation and lower costs
4. **Test with small scripts first** - to verify your setup works

## 📊 Service Comparison

| Service      | Free Tier        | Quality    | Speed      | Setup Difficulty |
| ------------ | ---------------- | ---------- | ---------- | ---------------- |
| Azure TTS    | 500K chars/month | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐             |
| Google TTS   | 4M chars/month   | ⭐⭐⭐⭐   | ⭐⭐⭐⭐   | ⭐⭐⭐           |
| Hugging Face | Unlimited        | ⭐⭐⭐     | ⭐⭐⭐     | ⭐               |
| ElevenLabs   | 10K chars/month  | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐             |
| Local TTS    | Unlimited        | ⭐⭐       | ⭐         | ⭐⭐⭐⭐⭐       |

## 🎉 Next Steps

Once you have TTS working, you can:

1. Generate voiceovers for your scripts
2. Move to image generation
3. Create timestamp mappings
4. Assemble your final video

Happy voiceover generation! 🎤
