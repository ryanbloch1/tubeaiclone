# TubeAI Clone - AI Video Content Creation Tool

A desktop AI video content creation tool inspired by TubeGenAI, built with Python and Streamlit. Create professional videos with AI-generated scripts, voiceovers, and images.

## Features

- 🎬 **Script Generation** - AI-powered script creation using Google Gemini
- 🎤 **Voiceover Generation** - Multiple TTS services with improved speech-like audio
  - Coqui XTTS (high-quality voice cloning)
  - ElevenLabs (premium voices)
  - Local TTS (pyttsx3 - works offline)
  - Hugging Face TTS (free alternative)
  - Fallback speech-like audio generation
- 🖼️ **Image Generation** - Free AI image generation with Hugging Face and Stability AI
- 🎥 **Video Assembly** - Complete video creation workflow
- 🧙‍♂️ **Wizard Interface** - Step-by-step guided process

## Quick Start

1. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

2. **Install FFmpeg** (required for audio/video processing)

   ```bash
   # macOS
   brew install ffmpeg

   # Ubuntu/Debian
   sudo apt update && sudo apt install ffmpeg

   # Windows
   # Download from https://ffmpeg.org/download.html
   ```

3. **Set up API Keys** (Optional but recommended)
   Create a `.env` file in the project root with your API keys:

   ```
   # Google Gemini API (Free tier available)
   GEMINI_API_KEY=your_gemini_api_key_here

   # ElevenLabs API (Optional - for high-quality voiceover)
   ELEVENLABS_API_KEY=your_elevenlabs_api_key_here

   # Stability AI API (Optional - for image generation)
   STABILITY_API_KEY=your_stability_api_key_here
   ```

4. **Run the App**

   ```bash
   streamlit run app.py
   ```

   The app will open in your browser at `http://localhost:8501`

5. **Open in Browser**
   Navigate to `http://localhost:8501`

## API Keys Setup

### Required (for best experience):

- **Google Gemini API**: Free tier available at https://makersuite.google.com/app/apikey
  - Provides AI script generation
  - 15 requests/minute free tier

### Optional (for enhanced features):

- **ElevenLabs API**: High-quality AI voices at https://elevenlabs.io/

  - Professional voiceover generation
  - Free tier: 10,000 characters/month

- **Stability AI API**: AI image generation at https://platform.stability.ai/

  - High-quality image generation
  - Free tier available

- **Hugging Face API**: Free AI models at https://huggingface.co/settings/tokens
  - Free image and voice generation
  - No credit card required

## How to Use

1. **Script Generation**

   - Enter your video title and description
   - Choose style and duration
   - Generate AI-powered script

2. **Voiceover Generation**

   - Select from multiple TTS services
   - Choose voice and settings
   - Generate professional voiceover

3. **Image Generation**

   - Select image service (free options available)
   - Choose style and settings
   - Generate scene images

4. **Video Assembly**
   - Review all components
   - Assemble final video
   - Download your creation

## Free Services Available

- **Script Generation**: Google Gemini (free tier)
- **Voiceover**: Coqui XTTS, Hugging Face TTS, Local TTS
- **Images**: Hugging Face, Mock generation
- **No API keys required** for basic functionality

## Troubleshooting

- **Import Errors**: Make sure all dependencies are installed
- **API Quota Exceeded**: Wait 24 hours or upgrade to paid plan
- **Voice Generation Issues**: Try different TTS services
- **Image Generation Fails**: Use mock images as fallback

## Project Structure

```
tubeaiclone/
├── app.py                 # Main Streamlit application
├── utils/                 # Utility modules
│   ├── script_generation.py
│   ├── voiceover.py
│   ├── image_generation.py
│   ├── sanitization.py
│   └── image_prompting.py
├── output/                # Generated files
│   ├── voiceovers/
│   ├── images/
│   └── videos/
└── README.md
```

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is open source and available under the MIT License.
 