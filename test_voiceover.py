#!/usr/bin/env python3

import requests
import json
import time

# Test voiceover generation and retrieval
def test_voiceover_flow():
    base_url = "http://localhost:8000"
    headers = {"Authorization": "Bearer test-token", "Content-Type": "application/json"}
    
    project_id = "b76adeed-3548-4c95-8359-ddb24ef3b4a5"
    script_id = "707e4c83-ed5d-41db-9ce1-f370efa10131"
    
    print("🎤 Testing voiceover generation...")
    
    # Step 1: Generate voiceover
    generate_data = {
        "script": "This is a test script for voiceover generation. It should work properly.",
        "project_id": project_id,
        "script_id": script_id
    }
    
    try:
        print("📤 Sending generation request...")
        response = requests.post(
            f"{base_url}/api/voiceover/generate",
            headers=headers,
            json=generate_data,
            timeout=60
        )
        
        print(f"📥 Generation response: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Generation successful: {result}")
            voiceover_id = result.get('voiceover_id')
            audio_data_url = result.get('audio_data_url')
            print(f"🎵 Voiceover ID: {voiceover_id}")
            print(f"🔗 Audio Data URL length: {len(audio_data_url) if audio_data_url else 'None'}")
        else:
            print(f"❌ Generation failed: {response.text}")
            return
            
    except Exception as e:
        print(f"❌ Generation error: {e}")
        return
    
    # Step 2: Retrieve voiceovers for project
    print("\n🔍 Testing voiceover retrieval...")
    
    try:
        print("📤 Sending retrieval request...")
        response = requests.get(
            f"{base_url}/api/voiceover/project/{project_id}",
            headers=headers,
            timeout=30
        )
        
        print(f"📥 Retrieval response: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Retrieval successful: {result}")
            voiceovers = result.get('voiceovers', [])
            print(f"🎵 Found {len(voiceovers)} voiceovers")
            for i, v in enumerate(voiceovers):
                print(f"  {i+1}. ID: {v.get('id')}, Script: {v.get('script_id')}")
        else:
            print(f"❌ Retrieval failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Retrieval error: {e}")

if __name__ == "__main__":
    test_voiceover_flow()

