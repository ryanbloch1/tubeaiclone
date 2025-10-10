#!/usr/bin/env python3
"""
Test the complete authentication and content generation flow
"""

import requests
import json
import time

BASE_URL = "http://localhost:3001"  # Next.js is on 3001
API_URL = "http://localhost:8000"

def test_health():
    """Test API health"""
    print("\n1. Testing API Health...")
    response = requests.get(f"{API_URL}/health")
    print(f"   ✅ API Status: {response.json()['status']}")
    return response.status_code == 200

def test_signup():
    """Test user signup"""
    print("\n2. Testing User Signup...")
    # This would be done via the UI at http://localhost:3001/signup
    print("   ℹ️  Go to: http://localhost:3001/signup")
    print("   ℹ️  Create an account with your email")
    return True

def test_login():
    """Test user login"""
    print("\n3. Testing User Login...")
    # This would be done via the UI at http://localhost:3001/login
    print("   ℹ️  Go to: http://localhost:3001/login")
    print("   ℹ️  Login with your credentials")
    return True

def test_script_generation():
    """Test script generation"""
    print("\n4. Testing Script Generation...")
    print("   ℹ️  Go to: http://localhost:3001/script")
    print("   ℹ️  Enter a topic and generate a script")
    print("   ℹ️  This will:")
    print("      - Create a project in Supabase")
    print("      - Call FastAPI to generate script with Gemini")
    print("      - Save script to Supabase database")
    return True

def test_voiceover():
    """Test voiceover generation"""
    print("\n5. Testing Voiceover Generation...")
    print("   ℹ️  Go to: http://localhost:3001/voiceover")
    print("   ℹ️  Generate voiceover from your script")
    print("   ℹ️  This will:")
    print("      - Load script from Supabase")
    print("      - Generate audio (needs voiceover API)")
    print("      - Save audio to Supabase")
    return True

def test_images():
    """Test image generation"""
    print("\n6. Testing Image Generation...")
    print("   ℹ️  Go to: http://localhost:3001/images")
    print("   ℹ️  Generate scene images")
    print("   ℹ️  This will:")
    print("      - Parse script into scenes")
    print("      - Generate image prompts with Gemini")
    print("      - Generate images")
    print("      - Save to Supabase")
    return True

def main():
    print("="*60)
    print("TubeAI Clone - Complete Flow Test")
    print("="*60)
    
    # Test API health first
    if not test_health():
        print("\n❌ API is not running! Start it with:")
        print("   cd apps/api && python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000")
        return
    
    # Check if Next.js is running
    print("\n🔍 Checking Next.js app...")
    try:
        response = requests.get(BASE_URL, timeout=2)
        print("   ✅ Next.js app is running")
    except:
        print("   ❌ Next.js app is NOT running! Start it with:")
        print("   cd apps/web && npm run dev")
        return
    
    # Run manual tests
    test_signup()
    test_login()
    test_script_generation()
    test_voiceover()
    test_images()
    
    print("\n" + "="*60)
    print("📋 MANUAL TESTING CHECKLIST")
    print("="*60)
    print("""
1. ✅ Sign Up: http://localhost:3001/signup
   - Create account with email/password
   - Check Supabase Auth dashboard for new user

2. ✅ Log In: http://localhost:3001/login
   - Login with credentials
   - Should redirect to home page

3. ✅ Generate Script: http://localhost:3001/script
   - Enter topic (e.g., "The Future of AI")
   - Click Generate
   - Check Supabase 'projects' and 'scripts' tables

4. ✅ Create Voiceover: http://localhost:3001/voiceover
   - Should load script from previous step
   - Generate voiceover
   - Check Supabase 'voiceovers' table

5. ✅ Generate Images: http://localhost:3001/images
   - Should parse scenes from script
   - Generate image prompts
   - Generate images
   - Check Supabase 'scenes' and 'images' tables
    """)
    
    print("\n⚠️  IMPORTANT NOTES:")
    print("   - Make sure you've set up Supabase environment variables")
    print("   - FastAPI needs SUPABASE_URL, SUPABASE_ANON_KEY, GEMINI_API_KEY")
    print("   - Check apps/api/.env file")
    print("\n")

if __name__ == "__main__":
    main()

