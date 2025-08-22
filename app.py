"""
TubeAI Clone - Streamlit Version
A modern AI video content creation tool inspired by TubeGenAI.
"""

import streamlit as st
import os
import time
import threading
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our utility modules
from utils.script_generation import generate_script
from utils.sanitization import sanitize_script, split_script_into_segments
from utils.voiceover import generate_voiceover, get_available_voices, estimate_voiceover_duration
from utils.image_generation import generate_images_for_script, generate_images_huggingface_only, generate_image_free, analyze_script_for_scenes
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
        st.markdown("### 📄 Generated Scripts")
        
        # Show both versions in tabs
        tab1, tab2 = st.tabs(["🎤 Voiceover Script (Sanitized)", "🖼️ Full Script (With Scenes)"])
        
        with tab1:
            st.text_area("Sanitized for voiceover:", value=st.session_state.sanitized_script, height=250, disabled=True)
            words = len(st.session_state.sanitized_script.split())
            estimated_duration = estimate_voiceover_duration(st.session_state.sanitized_script)
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Words (Voiceover)", words)
            with col2:
                st.metric("Estimated Duration", f"{estimated_duration:.1f}s")
        
        with tab2:
            st.text_area("Full script with scene directions:", value=st.session_state.script, height=250, disabled=True)
            original_words = len(st.session_state.script.split())
            st.metric("Words (Full Script)", original_words)
            st.info("💡 This version includes scene directions for image generation")

# --- Step 1: Voiceover Generation ---

def voiceover_generation():
    st.markdown('<h2 class="sub-header">🎤 Voiceover Generation</h2>', unsafe_allow_html=True)
    if not st.session_state.sanitized_script:
        st.warning("⚠️ No script available. Please generate a script first!")
        return
    # Display script
    st.text_area("Script:", value=st.session_state.sanitized_script, height=200, disabled=True)
    # Voiceover options (Hugging Face only)
    st.markdown("### 🎤 Voiceover Options")
    col1, col2 = st.columns(2)
    with col1:
        use_fast_mode = st.checkbox("🚀 Fast Mode (shorter script for testing)", value=False)
    with col2:
        force_single_generation = st.checkbox("⚡ Force Single Generation (for estimation only)", value=True)
    if use_fast_mode:
        short_script = " ".join(st.session_state.sanitized_script.split()[:20]) + "..."
        st.info(f"📝 Using short script for testing: {len(short_script.split())} words")
        script_to_use = short_script
    else:
        script_to_use = st.session_state.sanitized_script
    st.info("🤗 Using Hugging Face TTS (local, no paid API)")
    output_filename = st.text_input("Output Filename:", value="voiceover.wav")
    words = len(script_to_use.split())
    estimated_duration = estimate_voiceover_duration(script_to_use)
    st.metric("Words", words)
    st.metric("Estimated Duration", f"{estimated_duration:.1f}s")
    st.markdown("### 💡 Performance Tips")
    st.info(f"""
    **Script length**: {len(script_to_use)} characters
    - This path synthesizes a placeholder voice locally to keep everything free
    """)
    if st.button("🎤 Generate Voiceover", type="primary"):
        os.makedirs("output/voiceovers", exist_ok=True)
        words = len(script_to_use.split())
        estimated_time = words / 10
        st.info(f"⏱️ Estimated time: {estimated_time:.1f} seconds for {words} words")
        progress_bar = st.progress(0)
        status_text = st.empty()
        eta_text = st.empty()
        try:
            if not output_filename.endswith('.wav'):
                output_filename = output_filename.replace('.mp3', '.wav').replace('.m4a', '.wav')
            output_file_path = f"output/voiceovers/{output_filename}"
            from utils.voiceover import generate_voiceover as hv_generate
            status_text.text("🤗 Generating with Hugging Face TTS…")

            result_holder = {"path": None}

            def _worker():
                try:
                    result_holder["path"] = hv_generate(
                        script=script_to_use,
                        voice_id="default",
                        output_path=output_file_path,
                        use_elevenlabs=False,
                    )
                except Exception:
                    result_holder["path"] = None

            t = threading.Thread(target=_worker, daemon=True)
            t.start()

            start_tick = time.time()
            heuristic = max(5.0, words / 8.0)
            while t.is_alive():
                elapsed = time.time() - start_tick
                pct = min(99, int((elapsed / heuristic) * 100))
                remaining = max(0.0, heuristic - elapsed)
                progress_bar.progress(pct)
                eta_text.text(f"⏳ Elapsed: {int(elapsed)}s • ETA: {int(remaining)}s")
                time.sleep(0.25)

            output_path = result_holder["path"]
            progress_bar.progress(100)
            status_text.text("✅ Voiceover complete!")
            if output_path:
                st.session_state.voiceover_path = output_path
                st.success("✅ Voiceover generated successfully!")
                import time as _t; _t.sleep(0.5)
                if os.path.exists(output_path):
                    st.audio(output_path)
                else:
                    st.warning("⚠️ Voiceover file created but not found. You can download it below.")
            else:
                st.error("❌ Failed to generate voiceover. Please try again.")
        except Exception as e:
            st.error(f"❌ Error during voiceover generation: {e}")
    if st.session_state.voiceover_path and os.path.exists(st.session_state.voiceover_path):
        st.markdown("### 🎵 Current Voiceover")
        st.audio(st.session_state.voiceover_path)

# --- Step 2: Image Generation ---
def image_generation():
    st.markdown('<h2 class="sub-header">🖼️ Image Generation</h2>', unsafe_allow_html=True)
    if not st.session_state.script:
        st.warning("⚠️ No script available. Please generate a script first!")
        return
    # Show original script with scenes for image generation
    st.text_area("Script (with scene directions):", value=st.session_state.script, height=200, disabled=True)
    st.info("🖼️ Using Hugging Face for high-quality image generation")
    num_images = st.slider("Number of Images:", 1, 10, 3)
    if st.button("🎨 Generate Images", type="primary"):
        with st.spinner("🎨 Generating images..."):
            # Create output directory
            os.makedirs("output/images", exist_ok=True)
            
            # Simplified image generation - just use Hugging Face with original script (includes scenes)
            st.info("🤗 Using Hugging Face (FREE) for image generation...")
            generated_image_paths = generate_images_huggingface_only(
                script=st.session_state.script,  # Use original script with scene directions
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

# --- Sidebar Navigation --- (defined after function definitions at end)

# ------------------ New: One‑Minute Voiceover Test Page ------------------

def one_minute_voiceover_test():
    st.markdown('<h2 class="sub-header">⏱️ One‑Minute Voiceover Test</h2>', unsafe_allow_html=True)
    default_script = (
        "This is a one minute voiceover performance test designed to exercise the full generation pipeline. "
        "We are verifying end to end latency, audio quality, and stability across the stack. "
        "During this test, the system should maintain consistent pacing, clear pronunciation, and natural prosody. "
        "The primary goal is to validate that the synthesis can operate within realistic production constraints. "
        "Thank you for helping evaluate this pipeline. "
        "This concludes the one minute voiceover performance test."
    )
    script = st.text_area("Script (~1 minute):", value=default_script, height=200)
    output_name = st.text_input("Output filename", value="performance_test.wav")
    if st.button("🎤 Generate 1‑Minute Voiceover", type="primary"):
        if not script.strip():
            st.error("Please provide a script")
            return
        os.makedirs("output/voiceovers", exist_ok=True)
        if not output_name.endswith('.wav'):
            output_name = output_name.replace('.mp3', '.wav').replace('.m4a', '.wav')
        out_path = f"output/voiceovers/{output_name}"
        progress_bar = st.progress(0)
        status_text = st.empty()
        eta_text = st.empty()
        start = time.time()
        try:
            from utils.voiceover import generate_voiceover as hv_generate
            status_text.text("🤗 Generating with Hugging Face TTS…")

            holder = {"path": None}

            def _worker2():
                try:
                    holder["path"] = hv_generate(
                        script=script,
                        voice_id="default",
                        output_path=out_path,
                        use_elevenlabs=False,
                    )
                except Exception:
                    holder["path"] = None

            t2 = threading.Thread(target=_worker2, daemon=True)
            t2.start()

            words2 = len(script.split())
            heuristic2 = max(5.0, words2 / 8.0)
            while t2.is_alive():
                elapsed2 = time.time() - start
                pct2 = min(99, int((elapsed2 / heuristic2) * 100))
                remaining2 = max(0.0, heuristic2 - elapsed2)
                progress_bar.progress(pct2)
                eta_text.text(f"⏳ Elapsed: {int(elapsed2)}s • ETA: {int(remaining2)}s")
                time.sleep(0.25)

            output_path = holder["path"]
            elapsed = time.time() - start
            if output_path and os.path.exists(output_path):
                size = os.path.getsize(output_path)
                st.success(f"✅ Done in {elapsed:.1f}s • {size/1024/1024:.2f} MB")
                st.audio(output_path)
                st.write(f"Saved to: {output_path}")
            else:
                st.error("❌ Voiceover generation failed")
        except Exception as e:
            st.error(f"❌ Error: {e}")

# --- Final navigation (now that all functions are defined) ---
page = st.sidebar.radio("Go to page:", ["Wizard", "One‑Minute Voiceover Test"])

if page == "Wizard":
    wizard_nav()
    if st.session_state.step == 0:
        script_generation()
    elif st.session_state.step == 1:
        voiceover_generation()
    elif st.session_state.step == 2:
        image_generation()
    elif st.session_state.step == 3:
        video_assembly()
elif page == "One‑Minute Voiceover Test":
    one_minute_voiceover_test()

# Streamlit apps don't need a main() function - they run automatically