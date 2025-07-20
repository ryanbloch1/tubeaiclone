#!/usr/bin/env python3
"""
Quick Test Page
A dedicated page with pre-generated script for testing voiceover and image generation.
"""

import streamlit as st
import os
import time
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our utility modules
from utils.voiceover import generate_voiceover, get_available_voices, estimate_voiceover_duration
from utils.image_generation import generate_images_huggingface_only, generate_image_free, analyze_script_for_scenes

# Page configuration
st.set_page_config(
    page_title="Quick Test",
    page_icon="⚡",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .test-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .test-subheader {
        font-size: 1.3rem;
        font-weight: bold;
        color: #2c3e50;
        margin-bottom: 1rem;
    }
    .script-box {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
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
</style>
""", unsafe_allow_html=True)

def main():
    st.markdown('<h1 class="test-header">⚡ Quick Test Page</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.1rem; color: #666;">Test voiceover and image generation with a pre-generated script</p>', unsafe_allow_html=True)
    
    # Pre-generated script for testing
    test_script = """Scene 1: Introduction to Coffee Making

Welcome to the art of brewing the perfect cup of coffee. Today we'll explore the essential techniques and tools needed to create a delicious coffee experience at home. Whether you're a beginner or a coffee enthusiast, this guide will help you master the fundamentals of coffee brewing.

Scene 2: Coffee Beans and Grinding

The journey begins with selecting high-quality coffee beans. We'll learn about different bean varieties, from light to dark roasts, and the importance of proper grinding techniques for optimal flavor extraction. The grind size affects everything from brewing time to taste, so getting this right is crucial.

Scene 3: Brewing Methods

From pour-over to French press, we'll explore various brewing methods that can transform your coffee experience. Each method offers unique characteristics and flavors. The pour-over method emphasizes clarity and brightness, while the French press delivers a rich, full-bodied cup with natural oils intact.

Scene 4: Perfect Cup

Finally, we'll discover the secrets to achieving the perfect balance of flavor, aroma, and body in every cup of coffee you brew. Temperature control, water quality, and brewing time all play vital roles in creating that ideal cup that makes your morning truly special."""
    
    # Display the pre-generated script
    st.markdown('<h3 class="test-subheader">📝 Pre-Generated Script</h3>', unsafe_allow_html=True)
    st.markdown('<div class="script-box">', unsafe_allow_html=True)
    st.text_area("Script:", value=test_script, height=300, disabled=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Script statistics
    words = len(test_script.split())
    chars = len(test_script)
    scenes_count = len([line for line in test_script.split('\n') if 'scene' in line.lower()])
    estimated_duration = estimate_voiceover_duration(test_script)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Words", words)
    with col2:
        st.metric("Characters", chars)
    with col3:
        st.metric("Scenes", scenes_count)
    with col4:
        st.metric("Duration", f"{estimated_duration:.1f}s")
    
    st.markdown("---")
    
    # Voiceover Generation Section
    st.markdown('<h3 class="test-subheader">🎤 Voiceover Generation</h3>', unsafe_allow_html=True)
    
    # Get available voices
    voices = get_available_voices()
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Voiceover service selection
        service_options = [
            "ElevenLabs (High Quality)",
            "Hugging Face TTS (Free)",
            "Azure TTS (Free Tier)",
            "Google TTS (Free Tier)",
            "Local TTS (System)"
        ]
        selected_service = st.selectbox("Voiceover Service:", service_options, index=0)
        
        # Voice selection based on service
        if selected_service == "ElevenLabs (High Quality)":
            voice_options = list(voices.get("elevenlabs", {}).keys())
            service_info = "🎤 High-quality AI voices (requires API key)"
        elif selected_service == "Hugging Face TTS (Free)":
            voice_options = list(voices.get("huggingface", {}).keys())
            service_info = "🤗 FREE & FAST - No API key required!"
        elif selected_service == "Azure TTS (Free Tier)":
            voice_options = list(voices.get("azure", {}).keys())
            service_info = "☁️ Microsoft Neural voices (free tier available)"
        elif selected_service == "Google TTS (Free Tier)":
            voice_options = list(voices.get("google", {}).keys())
            service_info = "🔍 Google Cloud TTS (free tier available)"
        elif selected_service == "Local TTS (System)":
            voice_options = voices.get("local", [])
            service_info = "💻 System voices (works offline)"
        else:
            voice_options = []
            service_info = ""
        
        selected_voice = st.selectbox("Voice:", voice_options if voice_options else ["Default"])
        st.info(service_info)
    
    with col2:
        output_filename = st.text_input("Output Filename:", value="quick_test_voiceover.wav")
        
        if st.button("🎤 Generate Voiceover", type="primary", use_container_width=True):
            with st.spinner("🎵 Generating voiceover..."):
                try:
                    # Ensure output directory exists
                    os.makedirs("output/voiceovers", exist_ok=True)
                    
                    # Generate voiceover
                    voice_id = selected_voice
                    if selected_service == "ElevenLabs (High Quality)":
                        voice_id = voices.get("elevenlabs", {}).get(selected_voice, selected_voice)
                        use_elevenlabs = True
                    else:
                        use_elevenlabs = False
                    
                    output_path = generate_voiceover(
                        script=test_script,
                        voice_id=voice_id,
                        output_path=f"output/voiceovers/{output_filename}",
                        use_elevenlabs=use_elevenlabs
                    )
                    
                    if output_path and os.path.exists(output_path):
                        st.success("✅ Voiceover generated successfully!")
                        st.session_state.voiceover_path = output_path
                        
                        # Add delay and play audio
                        time.sleep(0.5)
                        st.audio(output_path)
                        
                        # Download button
                        with open(output_path, "rb") as f:
                            st.download_button(
                                label="📁 Download Voiceover",
                                data=f.read(),
                                file_name=os.path.basename(output_path),
                                mime="audio/wav"
                            )
                    else:
                        st.error("❌ Failed to generate voiceover")
                        
                except Exception as e:
                    st.error(f"❌ Error generating voiceover: {e}")
    
    # Show current voiceover if it exists
    if st.session_state.get("voiceover_path") and os.path.exists(st.session_state.voiceover_path):
        st.markdown("### 🎵 Current Voiceover")
        st.audio(st.session_state.voiceover_path)
        
        # Download button for current voiceover
        with open(st.session_state.voiceover_path, "rb") as f:
            st.download_button(
                label="📁 Download Current Voiceover",
                data=f.read(),
                file_name=os.path.basename(st.session_state.voiceover_path),
                mime="audio/wav"
            )
    
    st.markdown("---")
    
    # Image Generation Section
    st.markdown('<h3 class="test-subheader">🖼️ Image Generation</h3>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Image service selection
        image_service = st.selectbox(
            "Image Service:",
            ["Hugging Face (Free AI)", "Mock Images (Fast)", "Stability AI (API Key)"],
            index=0
        )
        
        image_size = st.selectbox(
            "Image Size:",
            ["512x512", "768x768", "1024x1024"],
            index=0
        )
        
        num_images = st.slider(
            "Number of Images:",
            min_value=1,
            max_value=10,
            value=4
        )
    
    with col2:
        output_dir = st.text_input(
            "Output Directory:",
            value="output/quick_test_images"
        )
        
        if st.button("🎨 Generate Images", type="primary", use_container_width=True):
            with st.spinner("🎨 Generating images..."):
                try:
                    # Ensure output directory exists
                    os.makedirs(output_dir, exist_ok=True)
                    
                    # Analyze script for scenes
                    scenes = analyze_script_for_scenes(test_script)
                    
                    if not scenes:
                        st.error("❌ No scenes detected in script")
                        return
                    
                    st.success(f"✅ Detected {len(scenes)} scenes in script")
                    
                    # Generate images based on service
                    if image_service == "Hugging Face (Free AI)":
                        st.info("🤗 Using Hugging Face for AI image generation...")
                        generated_images = generate_images_huggingface_only(
                            script=test_script,
                            output_dir=output_dir
                        )
                    else:
                        # Use the general function for other services
                        from utils.image_generation import generate_images_for_script
                        generated_images = generate_images_for_script(
                            script=test_script,
                            output_dir=output_dir
                        )
                    
                    if generated_images:
                        st.success(f"✅ Generated {len(generated_images)} images successfully!")
                        st.session_state.generated_images = generated_images
                        
                        # Display images
                        st.markdown("### 🖼️ Generated Images")
                        for i, image_path in enumerate(generated_images):
                            if os.path.exists(image_path):
                                st.image(image_path, caption=f"Scene {i+1}", use_column_width=True)
                                
                                # Download button for each image
                                with open(image_path, "rb") as f:
                                    st.download_button(
                                        label=f"📁 Download Scene {i+1}",
                                        data=f.read(),
                                        file_name=os.path.basename(image_path),
                                        mime="image/png"
                                    )
                    else:
                        st.error("❌ Failed to generate images")
                        
                except Exception as e:
                    st.error(f"❌ Error generating images: {e}")
                    st.exception(e)
    
    # Show current images if they exist
    if st.session_state.get("generated_images"):
        st.markdown("### 🖼️ Current Images")
        for i, image_path in enumerate(st.session_state.generated_images):
            if os.path.exists(image_path):
                st.image(image_path, caption=f"Scene {i+1}", use_column_width=True)
                
                # Download button for each image
                with open(image_path, "rb") as f:
                    st.download_button(
                        label=f"📁 Download Scene {i+1}",
                        data=f.read(),
                        file_name=os.path.basename(image_path),
                        mime="image/png"
                    )
    
    # Summary Section
    if st.session_state.get("voiceover_path") or st.session_state.get("generated_images"):
        st.markdown("---")
        st.markdown('<h3 class="test-subheader">📊 Test Summary</h3>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.session_state.get("voiceover_path") and os.path.exists(st.session_state.voiceover_path):
                st.success("✅ Voiceover Generated")
                st.metric("Voiceover File", os.path.basename(st.session_state.voiceover_path))
            else:
                st.info("⏳ No voiceover generated yet")
        
        with col2:
            if st.session_state.get("generated_images"):
                st.success("✅ Images Generated")
                st.metric("Number of Images", len(st.session_state.generated_images))
            else:
                st.info("⏳ No images generated yet")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.9rem;">
        <p>⚡ Quick Test Page | Pre-generated script for testing voiceover and image generation</p>
        <p>Perfect for testing your AI pipeline without script generation delays</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main() 