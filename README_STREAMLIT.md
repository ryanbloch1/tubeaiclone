# 🎬 TubeAI Clone - Streamlit Version

A modern, web-based AI video content creation tool inspired by TubeGenAI, built with Streamlit.

## 🚀 Features

- **📝 AI Script Generation** - Create engaging video scripts using Google Gemini
- **🎤 Multi-Service Voiceover** - Generate audio using Hugging Face TTS, ElevenLabs, Azure TTS, and more
- **🖼️ AI Image Generation** - Create visuals with Leonardo AI, Hugging Face, and Stability AI
- **🎥 Video Assembly** - Combine everything into professional videos
- **💻 Modern Web Interface** - Beautiful, responsive UI built with Streamlit

## 🎯 Why Streamlit?

- **🌐 Web-based** - Access from any browser, no desktop app needed
- **📱 Responsive** - Works on desktop, tablet, and mobile
- **⚡ Fast Development** - Easy to modify and extend
- **🎨 Beautiful UI** - Modern, professional interface
- **🔄 Real-time Updates** - Live preview and instant feedback

## 🛠️ Installation

1. **Clone the repository:**

   ```bash
   git clone <your-repo-url>
   cd tubeaiclone
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   Create a `.env` file in the project root:

   ```env
   GEMINI_API_KEY=your_gemini_key_here
   ELEVENLABS_API_KEY=your_elevenlabs_key_here
   LEONARDO_API_KEY=your_leonardo_key_here
   AZURE_TTS_KEY=your_azure_key_here
   AZURE_TTS_REGION=eastus
   HUGGINGFACE_API_KEY=your_hf_key_here
   ```

4. **Run the app:**

   ```bash
   streamlit run app.py
   ```

5. **Open your browser:**
   Navigate to `http://localhost:8501`

## 🎬 How to Use

### 1. **Script Generation**

- Enter your video title and description
- Choose style, duration, and language
- Click "Generate Script" to create engaging content

### 2. **Voiceover Creation**

- Select from multiple TTS services:
  - **Hugging Face TTS** (FREE - no API key needed)
  - **ElevenLabs** (High quality, requires API key)
  - **Azure TTS** (Free tier available)
  - **Google TTS** (Free tier available)
  - **Local TTS** (System voices)
- Choose your preferred voice
- Generate professional audio narration

### 3. **Image Generation**

- Select image service and style
- Choose number of images and quality
- Generate visuals for your video scenes

### 4. **Video Assembly**

- Combine script, voiceover, and images
- Choose output format and quality
- Generate your final video

## 🔧 API Setup Guide

### **Required (Free):**

- **Google Gemini** - For script generation
  - Get free API key at [Google AI Studio](https://makersuite.google.com/app/apikey)

### **Optional (Free Alternatives Available):**

- **ElevenLabs** - High-quality voiceovers

  - Free tier: 10,000 characters/month
  - Get key at [ElevenLabs](https://elevenlabs.io/)

- **Leonardo AI** - Professional image generation

  - Free tier: 150 images/day
  - Get key at [Leonardo AI](https://leonardo.ai/)

- **Azure TTS** - Microsoft neural voices
  - Free tier: 500,000 characters/month
  - Get key at [Azure Portal](https://portal.azure.com/)

## 🎨 UI Features

- **📱 Responsive Design** - Works on all devices
- **🎨 Modern Interface** - Clean, professional look
- **⚡ Real-time Updates** - Live progress and feedback
- **📊 Status Indicators** - See which APIs are ready
- **🔄 Session Management** - Your work is saved between steps
- **📥 Download Assets** - Easy export of generated files

## 🚀 Quick Start

1. **Start the app:**

   ```bash
   streamlit run app.py
   ```

2. **Generate a script:**

   - Go to "Script Generation"
   - Enter a topic like "How to Make Perfect Coffee"
   - Click "Generate Script"

3. **Create voiceover:**

   - Go to "Voiceover"
   - Select "Hugging Face TTS" (free)
   - Click "Generate Voiceover"

4. **Generate images:**

   - Go to "Image Generation"
   - Select "Mock Images" for testing
   - Click "Generate Images"

5. **Assemble video:**
   - Go to "Video Assembly"
   - Click "Assemble Video"

## 🔍 Troubleshooting

### **App won't start:**

- Check if all dependencies are installed: `pip install -r requirements.txt`
- Ensure you're in the correct directory
- Check Python version (3.8+ required)

### **API errors:**

- Verify your API keys in the `.env` file
- Check API quotas and limits
- Use free alternatives if paid services fail

### **Voiceover issues:**

- Try different TTS services
- Check audio file permissions
- Use Hugging Face TTS for free, reliable generation

### **Image generation fails:**

- Use "Mock Images" for testing
- Check image service API keys
- Verify output directory permissions

## 🎯 Benefits Over Tkinter Version

| Feature         | Tkinter            | Streamlit              |
| --------------- | ------------------ | ---------------------- |
| **Platform**    | Desktop only       | Web-based              |
| **Access**      | Local installation | Any browser            |
| **UI**          | Basic widgets      | Modern, responsive     |
| **Updates**     | Manual restart     | Live reload            |
| **Sharing**     | Difficult          | Easy (deploy to cloud) |
| **Mobile**      | No                 | Yes                    |
| **Development** | Complex            | Simple                 |

## 🚀 Deployment

### **Local Development:**

```bash
streamlit run app.py
```

### **Cloud Deployment:**

- **Streamlit Cloud** (Free)
- **Heroku**
- **AWS/GCP/Azure**
- **Railway**

## 📁 Project Structure

```
tubeaiclone/
├── app.py                 # Main Streamlit app
├── requirements.txt       # Python dependencies
├── .env                  # API keys (create this)
├── utils/                # Utility modules
│   ├── script_generation.py
│   ├── sanitization.py
│   ├── voiceover.py
│   └── image_generation.py
├── output/               # Generated files
│   ├── voiceovers/
│   ├── images/
│   └── videos/
└── README_STREAMLIT.md   # This file
```

## 🎉 Next Steps

1. **Test the workflow** with a simple script
2. **Set up your API keys** for better quality
3. **Customize the UI** to match your brand
4. **Deploy to cloud** for easy sharing
5. **Add more features** like video editing tools

## 🤝 Contributing

Feel free to contribute improvements:

- Add new TTS services
- Improve the UI design
- Add video editing features
- Optimize performance

## 📄 License

This project is open source. Feel free to use and modify as needed.

---

**🎬 Happy video creating!** 🎬
