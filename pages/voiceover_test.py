#!/usr/bin/env python3
"""
Voiceover Test Page
A dedicated page for testing XTTS voice generation with pre-filled content.
"""

import streamlit as st
import os
import time
from pathlib import Path

# Import XTTS voice generator
try:
    from utils.xtts_voice_generator import XTTSVoiceGenerator
    XTTS_AVAILABLE = True
except ImportError:
    XTTS_AVAILABLE = False

# Page configuration
st.set_page_config(
    page_title="XTTS Voiceover Test",
    page_icon="🎤",
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

def main():
    st.markdown('<h1 class="test-header">🎤 XTTS Voiceover Test</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.1rem; color: #666;">Test the XTTS voice generation with your own text</p>', unsafe_allow_html=True)
    
    # Pre-filled test content
    test_scripts = {
        "Short Test": "Hello, this is a short test of the XTTS voice generation system. How does it sound?",
        "Medium Test": "Welcome to our comprehensive test of the XTTS voice cloning technology. This system uses advanced AI to generate natural-sounding speech that mimics your voice. The quality should be quite impressive!",
        "Long Test": "In this extended test, we're exploring the full capabilities of the Coqui XTTS voice generation system. This technology represents a significant advancement in text-to-speech synthesis, offering high-quality voice cloning that can be used for various applications including content creation, accessibility tools, and entertainment. The system processes text input and generates audio that sounds remarkably similar to the provided voice sample, making it perfect for creating personalized voiceovers and audio content.",
        "YouTube Style": "Hey everyone! Welcome back to another exciting video. Today we're going to explore something absolutely fascinating - the world of AI voice generation. Whether you're a content creator, developer, or just curious about the future of technology, this is going to be an amazing journey. So grab your favorite beverage, get comfortable, and let's dive deep into the incredible world of XTTS voice cloning. Trust me, by the end of this, you'll have a whole new perspective on what's possible with AI. Don't forget to like, subscribe, and hit that notification bell if you want to stay updated with our latest content. Now, let's get started!",
        "Custom": ""
    }
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown('<h3 class="test-subheader">📝 Test Script</h3>', unsafe_allow_html=True)
        
        # Script selection
        selected_script_type = st.selectbox(
            "Choose Test Script Type:",
            list(test_scripts.keys()),
            index=0
        )
        
        # Script input area
        if selected_script_type == "Custom":
            test_script = st.text_area(
                "Type your test script here:",
                value="This is a custom test script for XTTS voice generation. You can type anything you want to test the voice cloning capabilities.",
                height=200,
                placeholder="Enter your text here to test XTTS voice generation..."
            )
        else:
            # Show pre-filled script but allow editing
            test_script = st.text_area(
                f"Script Preview ({selected_script_type}):",
                value=test_scripts[selected_script_type],
                height=200,
                help="You can edit this script or use it as-is"
            )
        
        # Script statistics
        words = len(test_script.split())
        chars = len(test_script)
        estimated_duration = words * 0.4  # Rough estimate
        
        col1_1, col1_2, col1_3, col1_4 = st.columns(4)
        with col1_1:
            st.metric("Words", words)
        with col1_2:
            st.metric("Characters", chars)
        with col1_3:
            st.metric("Est. Duration", f"{estimated_duration:.1f}s")
        with col1_4:
            st.metric("Language", "EN")
    
    # Sidebar for configuration
    with st.sidebar:
        st.markdown('<h3 class="test-subheader">⚙️ Configuration</h3>', unsafe_allow_html=True)
        
        # Voice sample management
        st.markdown("### 🎯 Voice Sample")
        voice_sample_path = "voice_sample.wav"
        
        if os.path.exists(voice_sample_path):
            file_size = os.path.getsize(voice_sample_path) / 1024  # KB
            st.success(f"✅ Voice sample found")
            st.info(f"📊 Size: {file_size:.1f} KB")
            
            # Play voice sample
            st.audio(voice_sample_path)
        else:
            st.warning("⚠️ No voice sample found")
            st.info("Upload a voice sample to test voice cloning:")
            
            uploaded_file = st.file_uploader(
                "Upload Voice Sample", 
                type=['wav', 'mp3', 'm4a', 'aac'],
                key="voice_sample_upload"
            )
            
            if uploaded_file:
                with open(voice_sample_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.success(f"✅ Voice sample saved")
                st.rerun()
        
        # Output settings
        st.markdown("### 📁 Output Settings")
        output_filename = st.text_input(
            "Output Filename:",
            value=f"test_voiceover_{int(time.time())}.wav"
        )
        
        # Language selection
        language = st.selectbox(
            "Language:",
            ["en", "es", "fr", "de", "it", "pt", "pl", "tr", "ru", "nl", "cs", "ar", "zh-cn", "ja", "ko", "hi"],
            index=0
        )
        
        # XTTS status
        st.markdown("### 🤖 XTTS Status")
        if XTTS_AVAILABLE:
            st.success("✅ XTTS Available")
            
            # Test XTTS setup
            if st.button("🧪 Test XTTS Setup"):
                with st.spinner("Testing XTTS..."):
                    try:
                        generator = XTTSVoiceGenerator(voice_sample_path)
                        info = generator.get_processing_info()
                        
                        st.json(info)
                        
                        if info["voice_sample_exists"]:
                            st.success("✅ XTTS setup is ready!")
                        else:
                            st.error("❌ Voice sample not found")
                    except Exception as e:
                        st.error(f"❌ XTTS test failed: {e}")
        else:
            st.error("❌ XTTS Not Available")
            st.info("Install with: pip install TTS")
    
    with col2:
        st.markdown('<h3 class="test-subheader">🎤 Generation</h3>', unsafe_allow_html=True)
        
        # Generate button
        if st.button("🚀 Generate Voiceover", type="primary", use_container_width=True):
            if not XTTS_AVAILABLE:
                st.error("❌ XTTS not available. Please install the TTS package.")
                return
            
            if not os.path.exists(voice_sample_path):
                st.error("❌ Voice sample not found. Please upload a voice sample first.")
                return
            
            if not test_script.strip():
                st.error("❌ No script provided.")
                return
            
            # Ensure output directory exists
            os.makedirs("output/voiceovers", exist_ok=True)
            output_path = f"output/voiceovers/{output_filename}"
            
            # Generate voiceover
            with st.spinner("🎵 Generating voiceover with XTTS..."):
                try:
                    generator = XTTSVoiceGenerator(voice_sample_path)
                    result = generator.generate_voiceover(
                        test_script,
                        output_path,
                        language=language
                    )
                    
                    if result and os.path.exists(output_path):
                        file_size = os.path.getsize(output_path)
                        duration_seconds = file_size / (16000 * 2)  # Rough estimate
                        
                        st.success("✅ Voiceover generated successfully!")
                        st.info(f"📊 File: {output_path}")
                        st.info(f"📊 Size: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")
                        st.info(f"⏱️ Duration: ~{duration_seconds:.1f} seconds")
                        
                        # Play the generated audio
                        st.markdown("### 🎵 Generated Voiceover")
                        st.audio(output_path)
                        
                        # Download button
                        with open(output_path, "rb") as f:
                            st.download_button(
                                label="📁 Download Voiceover",
                                data=f.read(),
                                file_name=output_filename,
                                mime="audio/wav"
                            )
                        
                        # Save to session state for other pages
                        st.session_state.voiceover_path = output_path
                        
                    else:
                        st.error("❌ Failed to generate voiceover")
                        
                except Exception as e:
                    st.error(f"❌ Error generating voiceover: {e}")
                    st.exception(e)
    
    # Recent generations
    if st.session_state.get("voiceover_path") and os.path.exists(st.session_state.voiceover_path):
        st.markdown('<h3 class="test-subheader">🎵 Recent Generation</h3>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.audio(st.session_state.voiceover_path)
        with col2:
            with open(st.session_state.voiceover_path, "rb") as f:
                st.download_button(
                    label="📁 Download",
                    data=f.read(),
                    file_name=os.path.basename(st.session_state.voiceover_path),
                    mime="audio/wav"
                )
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.9rem;">
        <p>🎤 XTTS Voiceover Test Page | Powered by Coqui XTTS</p>
        <p>High-quality local voice cloning with your own voice sample</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main() 