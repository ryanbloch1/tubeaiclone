#!/usr/bin/env python3
"""
Image Generation Test Page
A dedicated page for testing image generation from script scenes.
"""

import streamlit as st
import os
import time
from pathlib import Path
import json

# Import image generation modules
try:
    from utils.image_generation import (
        analyze_script_for_scenes, 
        generate_image_prompt, 
        generate_images_for_script,
        generate_image_huggingface,
        generate_image_stability,
        create_mock_image
    )
    IMAGE_GEN_AVAILABLE = True
except ImportError as e:
    IMAGE_GEN_AVAILABLE = False
    st.error(f"Image generation modules not available: {e}")

# Page configuration
st.set_page_config(
    page_title="Image Generation Test",
    page_icon="🖼️",
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
    .scene-card {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .prompt-box {
        background-color: #e3f2fd;
        border: 1px solid #2196f3;
        border-radius: 5px;
        padding: 0.5rem;
        margin: 0.5rem 0;
        font-family: monospace;
    }
</style>
""", unsafe_allow_html=True)

def main():
    st.markdown('<h1 class="test-header">🖼️ Image Generation Test</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.1rem; color: #666;">Test scene analysis and image generation from scripts</p>', unsafe_allow_html=True)
    
    # Pre-filled test scripts with scene structure
    test_scripts = {
        "Simple Script": "This is a simple test script about technology and innovation. We explore the future of artificial intelligence and how it will change our world.",
        "Multi-Scene Script": """Scene 1: Introduction
Welcome to our exploration of artificial intelligence. Today we'll discover how AI is transforming our world.

Scene 2: The Laboratory
Inside a modern research laboratory, scientists work with advanced computer systems and robotic equipment. The room is filled with screens displaying complex data and algorithms.

Scene 3: Future City
A futuristic cityscape with flying cars, holographic displays, and smart buildings. The skyline glows with neon lights and digital advertisements.

Scene 4: Conclusion
As we conclude our journey, we see the potential for AI to create a better future for humanity.""",
        "Nature Documentary": """Scene 1: Mountain Landscape
Majestic mountains rise into the sky, covered in snow and surrounded by dense forests. The sun casts golden light across the peaks.

Scene 2: Ocean Depths
Beneath the ocean surface, colorful coral reefs teem with marine life. Fish swim through crystal clear waters while sunlight filters down from above.

Scene 3: Desert Sunset
A vast desert landscape stretches to the horizon. The setting sun paints the sky in brilliant oranges and purples, casting long shadows across the sand dunes.""",
        "Technology Story": """Scene 1: Modern Office
A sleek, modern office space with glass walls, ergonomic furniture, and multiple computer screens. Natural light streams through large windows.

Scene 2: Data Center
Rows of powerful servers and networking equipment in a climate-controlled facility. Blue LED lights pulse as data flows through the system.

Scene 3: Virtual Reality
A person wearing a VR headset in a minimalist room. Digital interfaces and holographic displays surround them in a virtual environment.""",
        "Custom": ""
    }
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown('<h3 class="test-subheader">📝 Test Script</h3>', unsafe_allow_html=True)
        
        # Script selection
        selected_script_type = st.selectbox(
            "Choose Test Script:",
            list(test_scripts.keys()),
            index=0
        )
        
        # Script input area
        if selected_script_type == "Custom":
            test_script = st.text_area(
                "Type your test script here:",
                value="Scene 1: Introduction\nThis is a custom test script for image generation. You can add scene markers like 'Scene 1:', 'Scene 2:' etc.\n\nScene 2: Main Content\nDescribe what you want to see in each scene for better image generation.",
                height=200,
                placeholder="Enter your script with scene markers..."
            )
        else:
            test_script = st.text_area(
                f"Script Preview ({selected_script_type}):",
                value=test_scripts[selected_script_type],
                height=200,
                help="You can edit this script or use it as-is"
            )
        
        # Script statistics
        words = len(test_script.split())
        chars = len(test_script)
        scenes_count = len([line for line in test_script.split('\n') if 'scene' in line.lower()])
        
        col1_1, col1_2, col1_3 = st.columns(3)
        with col1_1:
            st.metric("Words", words)
        with col1_2:
            st.metric("Characters", chars)
        with col1_3:
            st.metric("Scenes Detected", scenes_count)
    
    # Sidebar for configuration
    with st.sidebar:
        st.markdown('<h3 class="test-subheader">⚙️ Configuration</h3>', unsafe_allow_html=True)
        
        # Image generation settings
        st.markdown("### 🎨 Image Settings")
        image_service = st.selectbox(
            "Image Service:",
            ["Mock Images (Fast)", "Hugging Face (Free)", "Stability AI (API Key)"],
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
            value=3
        )
        
        # Output settings
        st.markdown("### 📁 Output Settings")
        output_dir = st.text_input(
            "Output Directory:",
            value="output/test_images"
        )
        
        # Generation button
        if st.button("🎨 Generate Images", type="primary", use_container_width=True):
            if not IMAGE_GEN_AVAILABLE:
                st.error("❌ Image generation modules not available.")
                return
            
            if not test_script.strip():
                st.error("❌ No script provided.")
                return
            
            # Ensure output directory exists
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate images
            with st.spinner("🎨 Analyzing script and generating images..."):
                try:
                    # Analyze script for scenes
                    scenes = analyze_script_for_scenes(test_script)
                    
                    if not scenes:
                        st.error("❌ No scenes detected in script.")
                        return
                    
                    st.success(f"✅ Detected {len(scenes)} scenes in script")
                    
                    # Generate images for each scene
                    generated_images = []
                    
                    for i, scene in enumerate(scenes[:num_images]):
                        # Generate image prompt
                        prompt = generate_image_prompt(scene["text"], scene["scene_number"])
                        
                        # Create output path
                        image_filename = f"scene_{scene['scene_number']}_{int(time.time())}.png"
                        image_path = os.path.join(output_dir, image_filename)
                        
                        # Generate image based on service
                        success = False
                        if image_service == "Mock Images (Fast)":
                            success = create_mock_image(prompt, image_path)
                        elif image_service == "Hugging Face (Free)":
                            success = generate_image_huggingface(prompt, image_path)
                        elif image_service == "Stability AI (API Key)":
                            success = generate_image_stability(prompt, image_path)
                        
                        if success and os.path.exists(image_path):
                            generated_images.append({
                                "scene": scene,
                                "prompt": prompt,
                                "path": image_path
                            })
                    
                    # Display results
                    if generated_images:
                        st.success(f"✅ Generated {len(generated_images)} images successfully!")
                        
                        # Save to session state
                        st.session_state.generated_images = generated_images
                        
                    else:
                        st.error("❌ Failed to generate any images.")
                        
                except Exception as e:
                    st.error(f"❌ Error generating images: {e}")
                    st.exception(e)
    
    with col2:
        st.markdown('<h3 class="test-subheader">🔍 Scene Analysis</h3>', unsafe_allow_html=True)
        
        if test_script.strip():
            # Analyze scenes
            scenes = analyze_script_for_scenes(test_script)
            
            if scenes:
                st.success(f"✅ Detected {len(scenes)} scenes")
                
                for i, scene in enumerate(scenes[:5]):  # Show first 5 scenes
                    with st.expander(f"Scene {scene['scene_number']}", expanded=i==0):
                        st.markdown(f"**Text:** {scene['text'][:100]}...")
                        
                        # Generate and show prompt
                        prompt = generate_image_prompt(scene["text"], scene["scene_number"])
                        st.markdown("**Generated Prompt:**")
                        st.markdown(f'<div class="prompt-box">{prompt}</div>', unsafe_allow_html=True)
            else:
                st.warning("⚠️ No scenes detected")
                st.info("Add 'Scene 1:', 'Scene 2:' etc. to your script for better analysis")
    
    # Display generated images
    if st.session_state.get("generated_images"):
        st.markdown('<h3 class="test-subheader">🎨 Generated Images</h3>', unsafe_allow_html=True)
        
        for i, img_data in enumerate(st.session_state.generated_images):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                if os.path.exists(img_data["path"]):
                    st.image(img_data["path"], caption=f"Scene {img_data['scene']['scene_number']}", use_column_width=True)
                else:
                    st.error(f"Image file not found: {img_data['path']}")
            
            with col2:
                st.markdown(f"**Scene {img_data['scene']['scene_number']}**")
                st.markdown(f"*{img_data['scene']['text'][:100]}...*")
                st.markdown("**Prompt:**")
                st.markdown(f'<div class="prompt-box">{img_data["prompt"]}</div>', unsafe_allow_html=True)
                
                # Download button
                if os.path.exists(img_data["path"]):
                    with open(img_data["path"], "rb") as f:
                        st.download_button(
                            label="📁 Download",
                            data=f.read(),
                            file_name=os.path.basename(img_data["path"]),
                            mime="image/png"
                        )
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.9rem;">
        <p>🖼️ Image Generation Test Page | Scene Analysis & AI Image Generation</p>
        <p>Automatically extract scenes from scripts and generate matching images</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main() 