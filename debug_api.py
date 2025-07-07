#!/usr/bin/env python3
"""
Debug script to check ElevenLabs API
"""

import os
import requests

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, continue without it

def debug_elevenlabs_api():
    """Debug the ElevenLabs API call"""
    print("Debugging ElevenLabs API...")
    print("=" * 50)
    
    # Check if API key exists
    api_key = os.getenv('ELEVENLABS_API_KEY')
    print(f"API Key found: {'Yes' if api_key else 'No'}")
    if api_key:
        print(f"API Key starts with: {api_key[:10]}...")
    
    if not api_key:
        print("No API key found in environment variables")
        return
    
    # Try to fetch voices
    try:
        url = "https://api.elevenlabs.io/v1/voices"
        headers = {
            "Accept": "application/json",
            "xi-api-key": api_key
        }
        
        print(f"Making request to: {url}")
        response = requests.get(url, headers=headers)
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            voices_data = response.json()
            voices = voices_data.get("voices", [])
            print(f"Success! Found {len(voices)} voices")
            
            print("\nFirst 5 voices:")
            for i, voice in enumerate(voices[:5], 1):
                name = voice.get("name", "Unknown")
                voice_id = voice.get("voice_id", "")
                print(f"{i}. {name} (ID: {voice_id})")
                
        else:
            print(f"Error response: {response.text}")
            
    except Exception as e:
        print(f"Exception occurred: {e}")

if __name__ == "__main__":
    debug_elevenlabs_api() 