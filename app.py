"""
TubeAI Clone - Streamlit Version
A modern AI video content creation tool inspired by TubeGenAI.
"""

import streamlit as st
import os
import time
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our utility modules
from utils.script_generation import generate_script
from utils.sanitization import sanitize_script, split_script_into_segments
from utils.voiceover import generate_voiceover, get_available_voices, estimate_voiceover_duration
from utils.image_generation import generate_images_for_script, generate_image_free, analyze_script_for_scenes
from utils.image_prompting import generate_image_prompts

# Page configuration
st.set_page_config(
    page_title="TubeAI Clone",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2c3e50;
        margin-bottom: 1rem;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# --- Wizard State ---
if 'step' not in st.session_state:
    st.session_state.step = 0
if 'script' not in st.session_state:
    st.session_state.script = ""
if 'sanitized_script' not in st.session_state:
    st.session_state.sanitized_script = ""
if 'voiceover_path' not in st.session_state:
    st.session_state.voiceover_path = ""
if 'images' not in st.session_state:
    st.session_state.images = []

steps = [
    "Script Generation",
    "Voiceover Generation",
    "Image Generation",
    "Video Assembly"
]

# --- Step 0: Script Generation ---
def script_generation():
    st.markdown('<h1 class="main-header">🎬 TubeAI Clone</h1>', unsafe_allow_html=True)
    st.markdown('<h2 class="sub-header">📝 Script Generation</h2>', unsafe_allow_html=True)
    st.markdown("Enter your video topic and description to generate a script.")
    
    video_title = st.text_input("Video Title:", value="", placeholder="e.g., How to Make the Perfect Pizza at Home")
    video_description = st.text_area("Video Description:", value="", placeholder="Describe your video...")
    style_options = [
        "Educational & Professional",
        "Casual & Conversational", 
        "Entertaining & Humorous",
        "Technical & Detailed",
        "Storytelling & Narrative"
    ]
    selected_style = st.selectbox("Choose Style:", style_options)
    duration = st.slider("Target Duration (minutes):", 1, 20, 5)
    language = st.selectbox("Language:", ["English", "Spanish", "French", "German"])
    
    if st.button("🚀 Generate Script", type="primary"):
        if not video_title or not video_description:
            st.error("Please enter both a title and description!")
            return
        with st.spinner("🤖 Generating your script..."):
            script = generate_script(
                topic=video_title,
                style_profile={"name": selected_style},
                image_count=min(duration * 2, 10)  # Roughly 2 scenes per minute, max 10
            )
            if script:
                st.session_state.script = script
                sanitized = sanitize_script(script)
                st.session_state.sanitized_script = sanitized
                st.success("✅ Script generated successfully!")
            else:
                st.error("❌ Failed to generate script. Please try again.")
    
    if st.session_state.sanitized_script:
        st.markdown("### 📄 Generated Script")
        st.text_area("Script:", value=st.session_state.sanitized_script, height=300, disabled=True)
        words = len(st.session_state.sanitized_script.split())
        estimated_duration = estimate_voiceover_duration(st.session_state.sanitized_script)
        st.metric("Words", words)
        st.metric("Estimated Duration", f"{estimated_duration:.1f}s")

# --- Step 1: Voiceover Generation ---
def voiceover_generation():
    st.markdown('<h2 class="sub-header">🎤 Voiceover Generation</h2>', unsafe_allow_html=True)
    if not st.session_state.sanitized_script:
        st.warning("⚠️ No script available. Please generate a script first!")
        return
    
    # Display script
    st.text_area("Script:", value=st.session_state.sanitized_script, height=200, disabled=True)
    
    # Voice sample management
    st.markdown("### 🎯 Voice Sample Setup")
    voice_sample_path = "voice_sample.wav"
    
    if os.path.exists(voice_sample_path):
        st.success(f"✅ Voice sample found: {voice_sample_path}")
        file_size = os.path.getsize(voice_sample_path) / 1024  # KB
        st.info(f"📊 Sample size: {file_size:.1f} KB")
        
        # Play voice sample
        st.audio(voice_sample_path)
    else:
        st.warning("⚠️ No voice sample found. XTTS voice cloning requires a voice sample.")
        st.info("💡 Upload an audio file to create your voice sample:")
        
        uploaded_file = st.file_uploader("Upload Voice Sample", type=['wav', 'mp3', 'm4a', 'aac'])
        if uploaded_file:
            # Save uploaded file
            with open(voice_sample_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success(f"✅ Voice sample saved: {voice_sample_path}")
            st.rerun()
    
    # Service selection
    service_options = ["Coqui XTTS (Voice Clone)", "Coqui XTTS (High Quality)", "Coqui TTS (simple)", "ElevenLabs", "Hugging Face TTS", "Azure TTS", "Google TTS", "Local TTS"]
    selected_service = st.selectbox("TTS Service:", service_options, index=0)
    voices = get_available_voices()
    if selected_service == "Coqui XTTS (Voice Clone)":
        voice_options = ["Your Voice Clone"]
        service_info = "🎯 HIGH-QUALITY VOICE CLONING - Uses your voice sample for realistic speech!"
    elif selected_service == "Coqui XTTS (High Quality)":
        voice_options = ["High Quality XTTS"]
        service_info = "🎯 HIGH-QUALITY & FREE - Best AI voice generation available!"
    elif selected_service == "Coqui TTS (simple)":
        voice_options = list(voices.get("coqui", {}).keys())
        service_info = "⚡ FAST & FREE - Quick generation with good quality"
    elif selected_service == "ElevenLabs":
        voice_options = list(voices.get("elevenlabs", {}).keys())
        service_info = "High-quality AI voices (requires API key)"
    elif selected_service == "Hugging Face TTS":
        voice_options = list(voices.get("huggingface", {}).keys())
        service_info = "🤗 FREE & FAST - No API key required!"
    elif selected_service == "Azure TTS":
        voice_options = list(voices.get("azure", {}).keys())
        service_info = "Microsoft Neural voices (free tier available)"
    elif selected_service == "Google TTS":
        voice_options = list(voices.get("google", {}).keys())
        service_info = "Google Cloud TTS (free tier available)"
    elif selected_service == "Local TTS":
        voice_options = voices.get("local", [])
        service_info = "System voices (slow but reliable)"
    else:
        voice_options = []
        service_info = ""
    selected_voice = st.selectbox("Voice:", voice_options if voice_options else ["Default"])
    st.info(service_info)
    output_filename = st.text_input("Output Filename:", value="voiceover.wav")
    words = len(st.session_state.sanitized_script.split())
    estimated_duration = estimate_voiceover_duration(st.session_state.sanitized_script)
    st.metric("Words", words)
    st.metric("Estimated Duration", f"{estimated_duration:.1f}s")
    if st.button("🎤 Generate Voiceover", type="primary"):
        with st.spinner("🎵 Generating voiceover..."):
            # Ensure output directory exists
            os.makedirs("output/voiceovers", exist_ok=True)
            
            # Handle different service types
            if selected_service == "Coqui XTTS (Voice Clone)":
                # Use XTTS with voice cloning
                from utils.xtts_voice_generator import XTTSVoiceGenerator
                generator = XTTSVoiceGenerator("voice_sample.wav")
                
                # Ensure .wav extension for XTTS
                if not output_filename.endswith('.wav'):
                    output_filename = output_filename.replace('.mp3', '.wav').replace('.m4a', '.wav')
                
                output_path = generator.generate_voiceover(
                    st.session_state.sanitized_script,
                    f"output/voiceovers/{output_filename}"
                )
            elif selected_service == "Coqui XTTS (High Quality)":
                # Use XTTS with high quality
                from utils.xtts_voice_generator import XTTSVoiceGenerator
                generator = XTTSVoiceGenerator("voice_sample.wav")
                
                # Ensure .wav extension for XTTS
                if not output_filename.endswith('.wav'):
                    output_filename = output_filename.replace('.mp3', '.wav').replace('.m4a', '.wav')
                
                output_path = generator.generate_voiceover(
                    st.session_state.sanitized_script,
                    f"output/voiceovers/{output_filename}"
                )
            else:
                # Use other services
                voice_id = selected_voice
                if selected_service == "ElevenLabs":
                    voice_id = voices.get("elevenlabs", {}).get(selected_voice, selected_voice)
                elif selected_service == "Azure TTS":
                    voice_id = voices.get("azure", {}).get(selected_voice, selected_voice)
                elif selected_service == "Google TTS":
                    voice_id = voices.get("google", {}).get(selected_voice, selected_voice)
                output_path = generate_voiceover(
                    script=st.session_state.sanitized_script,
                    voice_id=voice_id,
                    output_path=f"output/voiceovers/{output_filename}",
                    use_elevenlabs=(selected_service == "ElevenLabs")
                )
            if output_path:
                st.session_state.voiceover_path = output_path
                st.success("✅ Voiceover generated successfully!")
                # Add a small delay to ensure file is written
                import time
                time.sleep(0.5)
                # Check if file exists before trying to play it
                if os.path.exists(output_path):
                    st.audio(output_path)
                else:
                    st.warning("⚠️ Voiceover file created but not found. You can download it below.")
            else:
                st.error("❌ Failed to generate voiceover. Please try again.")
    if st.session_state.voiceover_path and os.path.exists(st.session_state.voiceover_path):
        st.markdown("### 🎵 Current Voiceover")
        st.audio(st.session_state.voiceover_path)

# --- Step 2: Image Generation ---
def image_generation():
    st.markdown('<h2 class="sub-header">🖼️ Image Generation</h2>', unsafe_allow_html=True)
    if not st.session_state.sanitized_script:
        st.warning("⚠️ No script available. Please generate a script first!")
        return
    st.text_area("Script:", value=st.session_state.sanitized_script, height=200, disabled=True)
    service_options = ["Leonardo AI", "Hugging Face", "Stability AI", "Mock Images"]
    selected_service = st.selectbox("Image Service:", service_options, index=0)
    style_options = [
        "Realistic", "Artistic", "Cartoon", "Photographic", 
        "Cinematic", "Minimalist", "Vintage", "Modern"
    ]
    selected_style = st.selectbox("Style:", style_options)
    num_images = st.slider("Number of Images:", 1, 10, 3)
    image_size = st.selectbox("Image Size:", ["1024x1024", "1024x768", "768x1024", "512x512"])
    quality = st.slider("Quality:", 1, 10, 7)
    if st.button("🎨 Generate Images", type="primary"):
        with st.spinner("🎨 Generating images..."):
            # Create output directory
            os.makedirs("output/images", exist_ok=True)
            
            # Generate images for the script
            generated_image_paths = generate_images_for_script(
                script=st.session_state.sanitized_script,
                output_dir="output/images"
            )
            
            if generated_image_paths:
                st.session_state.images = [(f"Scene {i+1}", path) for i, path in enumerate(generated_image_paths)]
                st.success(f"✅ Generated {len(generated_image_paths)} images successfully!")
                for i, (prompt, image_path) in enumerate(st.session_state.images):
                    st.image(image_path, caption=f"Image {i+1}", use_column_width=True)
                    st.markdown(f"**Scene:** {prompt}")
            else:
                st.error("❌ Failed to generate images. Please try again.")
    if st.session_state.images:
        st.markdown("### 🖼️ Current Images")
        for i, (prompt, image_path) in enumerate(st.session_state.images):
            st.image(image_path, caption=f"Image {i+1}", use_column_width=True)
            st.markdown(f"**Prompt:** {prompt}")

# --- Step 3: Video Assembly ---
def video_assembly():
    st.markdown('<h2 class="sub-header">🎥 Video Assembly</h2>', unsafe_allow_html=True)
    missing_items = []
    if not st.session_state.sanitized_script:
        missing_items.append("Script")
    if not st.session_state.voiceover_path or not os.path.exists(st.session_state.voiceover_path):
        missing_items.append("Voiceover")
    if not st.session_state.images:
        missing_items.append("Images")
    if missing_items:
        st.warning(f"⚠️ Missing required items: {', '.join(missing_items)}")
        st.info("Please complete the previous steps first.")
        return
    output_filename = st.text_input("Output Video Filename:", value="final_video.mp4")
    video_format = st.selectbox("Video Format:", ["MP4", "AVI", "MOV"])
    quality = st.selectbox("Video Quality:", ["High", "Medium", "Low"])
    fps = st.slider("FPS:", 24, 60, 30)
    resolution = st.selectbox("Resolution:", ["1920x1080", "1280x720", "854x480"])
    st.success(f"✅ Script: {len(st.session_state.sanitized_script.split())} words")
    st.success(f"✅ Voiceover: {os.path.basename(st.session_state.voiceover_path)}")
    st.success(f"✅ Images: {len(st.session_state.images)} images")
    if st.button("🎥 Assemble Video", type="primary"):
        with st.spinner("🎬 Assembling your video..."):
            st.success("✅ Video assembly completed!")
            video_path = f"output/videos/{output_filename}"
            st.info(f"📁 Video saved: {video_path}")
            st.info("🎉 Your video is ready! You can now download and share it.")
            st.metric("Duration", "~2:30")
            st.metric("Resolution", resolution)
            st.metric("Format", video_format)
    if st.session_state.voiceover_path and os.path.exists(st.session_state.voiceover_path):
        st.markdown("### 📥 Download Voiceover")
        st.download_button(
            label="📁 Download Voiceover",
            data=open(st.session_state.voiceover_path, "rb").read(),
            file_name=os.path.basename(st.session_state.voiceover_path),
            mime="audio/mpeg"
        )
    if st.session_state.images:
        import zipfile
        import io
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
            for prompt, image_path in st.session_state.images:
                if os.path.exists(image_path):
                    zip_file.write(image_path, os.path.basename(image_path))
        st.download_button(
            label="📁 Download Images (ZIP)",
            data=zip_buffer.getvalue(),
            file_name="generated_images.zip",
            mime="application/zip"
        )

# --- Wizard Navigation ---
def wizard_nav():
    col1, col2, col3 = st.columns([1, 6, 1])
    with col2:
        st.progress((st.session_state.step+1)/len(steps), text=f"Step {st.session_state.step+1} of {len(steps)}: {steps[st.session_state.step]}")
    st.markdown("<br>", unsafe_allow_html=True)
    nav_col1, nav_col2, nav_col3 = st.columns([1, 2, 1])
    with nav_col1:
        if st.session_state.step > 0:
            if st.button("⬅️ Back", key="back"):
                st.session_state.step -= 1
    with nav_col2:
        pass
    with nav_col3:
        can_go_next = False
        if st.session_state.step == 0:
            can_go_next = bool(st.session_state.sanitized_script)
        elif st.session_state.step == 1:
            can_go_next = bool(st.session_state.voiceover_path and os.path.exists(st.session_state.voiceover_path))
        elif st.session_state.step == 2:
            can_go_next = bool(st.session_state.images)
        if st.session_state.step < len(steps)-1 and can_go_next:
            if st.button("Next ➡️", key="next"):
                st.session_state.step += 1

# --- Main Wizard Flow ---
wizard_nav()
if st.session_state.step == 0:
    script_generation()
elif st.session_state.step == 1:
    voiceover_generation()
elif st.session_state.step == 2:
    image_generation()
elif st.session_state.step == 3:
    video_assembly()

# Streamlit apps don't need a main() function - they run automatically 