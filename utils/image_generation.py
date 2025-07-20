"""Image generation module: generates images for video scenes using free AI services."""

import os
import requests
import json
import time
from pathlib import Path
import re
from typing import List, Dict, Optional
import base64
from io import BytesIO

def analyze_script_for_scenes(script: str) -> List[Dict]:
    """
    Analyze a script and break it down into visual scenes.
    Args:
        script (str): The script to analyze.
    Returns:
        List[Dict]: List of scenes with text and metadata.
    """
    if not script:
        return []
    
    scenes = []
    lines = script.split('\n')
    current_scene = {"text": "", "scene_number": 0, "description": ""}
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check if this is a scene header
        if re.match(r'^Scene\s+\d+', line, re.IGNORECASE):
            # Save previous scene if it has content
            if current_scene["text"].strip():
                scenes.append(current_scene.copy())
            
            # Start new scene
            scene_match = re.match(r'^Scene\s+(\d+)', line, re.IGNORECASE)
            scene_num = int(scene_match.group(1)) if scene_match else len(scenes) + 1
            current_scene = {
                "text": line,
                "scene_number": scene_num,
                "description": line
            }
        else:
            # Add line to current scene
            if current_scene["text"]:
                current_scene["text"] += "\n" + line
            else:
                current_scene["text"] = line
    
    # Add the last scene
    if current_scene["text"].strip():
        scenes.append(current_scene)
    
    # If no scenes were found, create one scene from the entire script
    if not scenes:
        scenes = [{
            "text": script,
            "scene_number": 1,
            "description": "Main scene"
        }]
    
    return scenes

def generate_image_prompt(scene_text: str, scene_number: int) -> str:
    """
    Generate an image prompt for a scene.
    Args:
        scene_text (str): The scene text.
        description (str): Scene description.
    Returns:
        str: Generated image prompt.
    """
    # Clean up the scene text
    clean_text = re.sub(r'Scene\s+\d+.*?:', '', scene_text, flags=re.IGNORECASE)
    clean_text = clean_text.strip()
    
    # Extract key visual elements
    visual_keywords = [
        'space', 'planet', 'stars', 'galaxy', 'spaceship', 'rocket', 'satellite',
        'earth', 'moon', 'sun', 'asteroid', 'nebula', 'black hole', 'cosmos',
        'technology', 'computer', 'robot', 'ai', 'artificial intelligence',
        'future', 'futuristic', 'modern', 'digital', 'virtual reality',
        'laboratory', 'research', 'scientist', 'experiment', 'discovery',
        'nature', 'landscape', 'mountain', 'ocean', 'forest', 'desert',
        'city', 'building', 'architecture', 'urban', 'street', 'traffic',
        'people', 'person', 'human', 'face', 'emotion', 'expression',
        'light', 'dark', 'shadow', 'color', 'bright', 'vibrant', 'dramatic'
    ]
    
    # Find visual elements in the text
    found_elements = []
    text_lower = clean_text.lower()
    for keyword in visual_keywords:
        if keyword in text_lower:
            found_elements.append(keyword)
    
    # Create a base prompt
    if found_elements:
        base_prompt = f"Professional video scene: {', '.join(found_elements[:5])}"
    else:
        base_prompt = "Professional video scene"
    
    # Add style modifiers
    style_modifiers = [
        "high quality", "cinematic", "professional", "detailed", "realistic",
        "4K resolution", "vibrant colors", "dramatic lighting", "modern style"
    ]
    
    # Create final prompt
    prompt = f"{base_prompt}, {', '.join(style_modifiers[:3])}"
    
    # Limit prompt length
    if len(prompt) > 500:
        prompt = prompt[:497] + "..."
    
    return prompt

def generate_image_huggingface(prompt: str, output_path: str, api_key: Optional[str] = None) -> bool:
    """
    Generate an image using Hugging Face (FREE).
    Args:
        prompt (str): The image prompt.
        output_path (str): Path to save the generated image.
        api_key (str): Hugging Face API key (optional for some models).
    Returns:
        bool: True if successful, False otherwise.
    """
    if not api_key:
        api_key = os.getenv('HUGGINGFACE_API_KEY')
    
    # Use FLUX.1-dev model for better quality images
    model_id = "black-forest-labs/FLUX.1-dev"
    
    # Hugging Face Inference API endpoint
    url = f"https://api-inference.huggingface.co/models/{model_id}"
    
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    
    data = {
        "inputs": prompt,
        "parameters": {
            "num_inference_steps": 20,
            "guidance_scale": 7.5,
            "width": 512,
            "height": 512
        }
    }
    
    try:
        print(f"Generating image with Hugging Face: {prompt[:50]}...")
        
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code == 200:
            # Save the image
            with open(output_path, "wb") as f:
                f.write(response.content)
            print(f"Image saved to: {output_path}")
            return True
        else:
            print(f"Hugging Face API error: {response.status_code} - {response.text}")
            if response.status_code == 401:
                print("⚠️  Hugging Face requires authentication. Try getting a free API key at https://huggingface.co/settings/tokens")
            elif response.status_code == 503:
                print("⚠️  Model is loading. Please wait a moment and try again.")
            return False
            
    except Exception as e:
        print(f"Error generating image with Hugging Face: {e}")
        return False

def generate_image_stability(prompt: str, output_path: str, api_key: Optional[str] = None) -> bool:
    """
    Generate an image using Stability AI (FREE tier available).
    Args:
        prompt (str): The image prompt.
        output_path (str): Path to save the generated image.
        api_key (str): Stability AI API key.
    Returns:
        bool: True if successful, False otherwise.
    """
    if not api_key:
        api_key = os.getenv('STABILITY_API_KEY')
        if not api_key:
            print("Warning: No Stability AI API key provided.")
            return False
    
    url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "text_prompts": [
            {
                "text": prompt,
                "weight": 1
            }
        ],
        "cfg_scale": 7,
        "height": 1024,
        "width": 1024,
        "samples": 1,
        "steps": 30
    }
    
    try:
        print(f"Generating image with Stability AI: {prompt[:50]}...")
        
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code == 200:
            response_data = response.json()
            
            # Save the image
            image_data = response_data["artifacts"][0]["base64"]
            image_bytes = base64.b64decode(image_data)
            
            with open(output_path, "wb") as f:
                f.write(image_bytes)
            print(f"Image saved to: {output_path}")
            return True
        else:
            print(f"Stability AI API error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"Error generating image with Stability AI: {e}")
        return False

def create_mock_image(prompt: str, output_path: str) -> bool:
    """
    Create a mock image for testing (completely free).
    Args:
        prompt (str): The image prompt.
        output_path (str): Path to save the mock image.
    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Create a simple mock image
        width, height = 512, 512
        image = Image.new('RGB', (width, height), color='#2c3e50')
        draw = ImageDraw.Draw(image)
        
        # Add some visual elements based on the prompt
        if 'space' in prompt.lower() or 'galaxy' in prompt.lower():
            # Space theme
            for i in range(100):
                x = (i * 37) % width
                y = (i * 73) % height
                draw.ellipse([x, y, x+2, y+2], fill='white')
        elif 'nature' in prompt.lower() or 'landscape' in prompt.lower():
            # Nature theme
            draw.rectangle([0, height//2, width, height], fill='#27ae60')
            draw.ellipse([width//4, height//4, 3*width//4, 3*height//4], fill='#f39c12')
        elif 'technology' in prompt.lower() or 'future' in prompt.lower():
            # Tech theme
            for i in range(0, width, 50):
                draw.line([(i, 0), (i, height)], fill='#3498db', width=2)
            for i in range(0, height, 50):
                draw.line([(0, i), (width, i)], fill='#3498db', width=2)
        else:
            # Default theme
            draw.rectangle([width//4, height//4, 3*width//4, 3*height//4], fill='#e74c3c')
        
        # Add text
        try:
            font = ImageFont.truetype("Arial", 20)
        except:
            font = ImageFont.load_default()
        
        # Split prompt into lines
        words = prompt.split()
        lines = []
        current_line = ""
        for word in words:
            if len(current_line + " " + word) < 30:
                current_line += " " + word if current_line else word
            else:
                lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        
        # Draw text
        y_offset = 20
        for line in lines[:3]:  # Limit to 3 lines
            draw.text((20, y_offset), line, fill='white', font=font)
            y_offset += 30
        
        # Save the image
        image.save(output_path, 'PNG')
        print(f"Mock image saved to: {output_path}")
        return True
        
    except Exception as e:
        print(f"Error creating mock image: {e}")
        return False

def generate_image_free(prompt: str, output_path: str) -> bool:
    """
    Generate an image using free services in order of preference.
    Args:
        prompt (str): The image prompt.
        output_path (str): Path to save the generated image.
    Returns:
        bool: True if successful, False otherwise.
    """
    # Try Hugging Face first (completely free)
    print("Trying Hugging Face (free)...")
    if generate_image_huggingface(prompt, output_path):
        return True
    
    # Try Stability AI if API key is available
    stability_key = os.getenv('STABILITY_API_KEY')
    if stability_key:
        print("Trying Stability AI...")
        if generate_image_stability(prompt, output_path):
            return True
    
    # Fallback to mock image
    print("Using mock image generation...")
    return create_mock_image(prompt, output_path)

def generate_images_for_script(script: str, output_dir: str = "output/images") -> List[str]:
    """
    Generate images for all scenes in a script using free services.
    Args:
        script (str): The script to generate images for.
        output_dir (str): Directory to save images.
    Returns:
        List[str]: List of paths to generated images.
    """
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Analyze script for scenes
    scenes = analyze_script_for_scenes(script)
    
    if not scenes:
        print("No scenes found in script")
        return []
    
    generated_images = []
    
    for i, scene in enumerate(scenes):
        print(f"\nProcessing scene {scene['scene_number']}...")
        
        # Generate prompt for this scene
        prompt = generate_image_prompt(scene["text"], scene["scene_number"])
        print(f"Generated prompt: {prompt}")
        
        # Generate image
        timestamp = int(time.time())
        image_filename = f"scene_{scene['scene_number']:02d}_{timestamp}.png"
        image_path = output_path / image_filename
        
        success = generate_image_free(prompt, str(image_path))
        
        if success:
            generated_images.append(str(image_path))
            print(f"✅ Scene {scene['scene_number']} image generated successfully")
        else:
            print(f"❌ Failed to generate image for scene {scene['scene_number']}")
    
    return generated_images

def generate_images_huggingface_only(script: str, output_dir: str = "output/images") -> List[str]:
    """
    Generate images for all scenes in a script using ONLY Hugging Face (free).
    Args:
        script (str): The script to generate images for.
        output_dir (str): Directory to save images.
    Returns:
        List[str]: List of paths to generated images.
    """
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Analyze script for scenes
    scenes = analyze_script_for_scenes(script)
    
    if not scenes:
        print("No scenes found in script")
        return []
    
    generated_images = []
    
    for i, scene in enumerate(scenes):
        print(f"\nProcessing scene {scene['scene_number']} with Hugging Face...")
        
        # Generate prompt for this scene
        prompt = generate_image_prompt(scene["text"], scene["scene_number"])
        print(f"Generated prompt: {prompt}")
        
        # Generate image using Hugging Face only
        timestamp = int(time.time())
        image_filename = f"scene_{scene['scene_number']:02d}_{timestamp}.png"
        image_path = output_path / image_filename
        
        success = generate_image_huggingface(prompt, str(image_path))
        
        if success:
            generated_images.append(str(image_path))
            print(f"✅ Scene {scene['scene_number']} image generated successfully with Hugging Face")
        else:
            print(f"❌ Failed to generate image for scene {scene['scene_number']} with Hugging Face")
    
    return generated_images

def get_available_services() -> List[Dict]:
    """
    Get available free image generation services.
    Returns:
        List[Dict]: List of available services.
    """
    services = [
        {
            "name": "Hugging Face",
            "description": "Free AI models, no API key required",
            "status": "Available"
        },
        {
            "name": "Stability AI",
            "description": "Free tier available with API key",
            "status": "Available" if os.getenv('STABILITY_API_KEY') else "API key needed"
        },
        {
            "name": "Mock Generation",
            "description": "Simple placeholder images for testing",
            "status": "Always available"
        }
    ]
    
    return services
