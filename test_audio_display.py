#!/usr/bin/env python3
"""
Test audio display functionality.
"""

import streamlit as st
import os

def test_audio_display():
    """Test audio display functionality."""
    
    st.title("Audio Display Test")
    
    # Test with existing voice sample
    voice_sample_path = "voice_sample.wav"
    
    if os.path.exists(voice_sample_path):
        st.success(f"✅ Voice sample found: {voice_sample_path}")
        
        # Test audio display without caption
        st.subheader("Testing st.audio() without caption:")
        st.audio(voice_sample_path)
        
        # Test with file object
        st.subheader("Testing st.audio() with file object:")
        with open(voice_sample_path, "rb") as f:
            st.audio(f.read(), format="audio/wav")
            
    else:
        st.error(f"❌ Voice sample not found: {voice_sample_path}")
    
    # Test with other audio files if they exist
    test_files = ["youtube_voiceover.wav", "coqui_xtts_test.wav"]
    
    for test_file in test_files:
        if os.path.exists(test_file):
            st.subheader(f"Testing {test_file}:")
            st.audio(test_file)

if __name__ == "__main__":
    test_audio_display() 