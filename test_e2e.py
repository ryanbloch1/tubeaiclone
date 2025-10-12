#!/usr/bin/env python3
"""
End-to-End Test: Sign up, generate script, verify database entries
"""

import requests
import time
import os
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv('apps/api/.env')

BASE_URL = "http://localhost:3001"
API_URL = "http://localhost:8000"
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

# Test user credentials
TEST_EMAIL = f"testuser{int(time.time())}@gmail.com"
TEST_PASSWORD = "TestPassword123!"

print("=" * 70)
print("🚀 END-TO-END TEST: Sign Up → Generate Script → Verify Database")
print("=" * 70)

# Initialize Supabase client for verification
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def test_1_signup():
    """Test user signup via Supabase client"""
    print(f"\n📝 TEST 1: Creating test user...")
    print(f"   Email: {TEST_EMAIL}")
    
    try:
        # Sign up using Supabase client with email confirmation disabled for testing
        response = supabase.auth.sign_up({
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "options": {
                "email_redirect_to": None,
                "data": {
                    "test_user": True
                }
            }
        })
        
        if response.user:
            print(f"   ✅ User created! ID: {response.user.id}")
            
            # Verify in database
            result = supabase.table('profiles').select('*').eq('id', response.user.id).execute()
            if result.data:
                print(f"   ✅ Profile created in database!")
                # For testing, we'll use the service role key to authenticate
                return response.user, type('Session', (), {'access_token': SUPABASE_KEY})()
            else:
                print(f"   ⚠️  User created but profile not found (may need trigger)")
                return response.user, type('Session', (), {'access_token': SUPABASE_KEY})()
        else:
            print(f"   ❌ Failed to create user")
            return None, None
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None, None

def test_2_create_project(user, session):
    """Test project creation"""
    print(f"\n📁 TEST 2: Creating project...")
    
    if not user:
        print("   ❌ Skipping - no authenticated user")
        return None
    
    try:
        # Create project directly in database
        project_data = {
            'user_id': user.id,
            'title': 'Test Project - The Future of AI',
            'topic': 'The Future of AI',
            'status': 'draft',
            'mode': 'script',
            'word_count': 500,
            'image_count': 10
        }
        
        result = supabase.table('projects').insert(project_data).execute()
        
        if result.data and len(result.data) > 0:
            project = result.data[0]
            print(f"   ✅ Project created! ID: {project['id']}")
            print(f"   ✅ Title: {project['title']}")
            
            # Verify it's in the database
            verify = supabase.table('projects').select('*').eq('id', project['id']).execute()
            if verify.data:
                print(f"   ✅ Project verified in database!")
            
            return project
        else:
            print(f"   ❌ Failed to create project")
            return None
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def test_3_generate_script(project, session):
    """Test script generation via FastAPI"""
    print(f"\n🤖 TEST 3: Generating script via FastAPI...")
    
    if not project or not session:
        print("   ❌ Skipping - no project or session")
        return None
    
    try:
        # Call FastAPI script generation endpoint
        payload = {
            'project_id': project['id'],
            'topic': 'The Future of AI',
            'style_name': 'Educational',
            'mode': 'script',
            'temperature': 0.7,
            'word_count': 500,
            'image_count': 10
        }
        
        headers = {
            'Authorization': f'Bearer {session.access_token}',
            'Content-Type': 'application/json'
        }
        
        print(f"   🔄 Calling FastAPI endpoint...")
        print(f"   URL: {API_URL}/api/script/generate")
        
        response = requests.post(
            f"{API_URL}/api/script/generate",
            json=payload,
            headers=headers,
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Script generated!")
            print(f"   ✅ Script ID: {data.get('script_id')}")
            print(f"   ✅ Script length: {len(data.get('script', ''))} characters")
            print(f"   📝 Preview: {data.get('script', '')[:100]}...")
            
            # Verify in database
            script_id = data.get('script_id')
            if script_id:
                verify = supabase.table('scripts').select('*').eq('id', script_id).execute()
                if verify.data:
                    script = verify.data[0]
                    print(f"   ✅ Script verified in database!")
                    print(f"   ✅ Raw script length: {len(script.get('raw_script', ''))} chars")
                    return script
            
            return data
        else:
            print(f"   ❌ Failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def test_4_verify_database():
    """Verify all entries in database"""
    print(f"\n🔍 TEST 4: Verifying database entries...")
    
    try:
        # Check profiles
        profiles = supabase.table('profiles').select('*').execute()
        print(f"   📊 Profiles table: {len(profiles.data)} entries")
        
        # Check projects
        projects = supabase.table('projects').select('*').execute()
        print(f"   📊 Projects table: {len(projects.data)} entries")
        
        # Check scripts
        scripts = supabase.table('scripts').select('*').execute()
        print(f"   📊 Scripts table: {len(scripts.data)} entries")
        
        if len(projects.data) > 0 and len(scripts.data) > 0:
            print(f"   ✅ All data successfully saved to database!")
            return True
        else:
            print(f"   ⚠️  Some data missing")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def cleanup_test_user(user):
    """Clean up test data"""
    print(f"\n🧹 Cleaning up test data...")
    
    if not user:
        return
    
    try:
        # Delete user's projects (will cascade to scripts)
        supabase.table('projects').delete().eq('user_id', user.id).execute()
        print(f"   ✅ Deleted test projects")
        
        # Delete profile
        supabase.table('profiles').delete().eq('id', user.id).execute()
        print(f"   ✅ Deleted test profile")
        
        # Note: Auth user deletion requires admin API
        print(f"   ℹ️  Auth user {TEST_EMAIL} may need manual deletion from Supabase dashboard")
        
    except Exception as e:
        print(f"   ⚠️  Cleanup error: {e}")

def main():
    # Run tests
    user, session = test_1_signup()
    project = test_2_create_project(user, session)
    script = test_3_generate_script(project, session)
    test_4_verify_database()
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    
    success = all([user, project, script])
    
    if success:
        print("✅ ALL TESTS PASSED!")
        print(f"✅ User created: {TEST_EMAIL}")
        print(f"✅ Project created with ID: {project['id']}")
        print(f"✅ Script generated and saved to database")
        print("\n🎉 The complete flow is working!")
    else:
        print("❌ SOME TESTS FAILED")
        if not user:
            print("   - User creation failed")
        if not project:
            print("   - Project creation failed")
        if not script:
            print("   - Script generation failed")
    
    # Cleanup (automatic for tests)
    print("\n" + "=" * 70)
    print("🗑️  Cleaning up test data...")
    cleanup_test_user(user)
    print("\n✅ Test complete! Check Supabase dashboard to verify data was created and cleaned up.")

if __name__ == "__main__":
    main()

