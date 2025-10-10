#!/usr/bin/env python3
"""Test Supabase database connection"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('apps/api/.env')

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

print("=" * 60)
print("🔍 SUPABASE CONNECTION TEST")
print("=" * 60)

print(f"\n📍 SUPABASE_URL: {SUPABASE_URL}")
print(f"📍 SUPABASE_ANON_KEY: {SUPABASE_ANON_KEY[:20]}..." if SUPABASE_ANON_KEY else "❌ NOT SET")
print(f"📍 SUPABASE_SERVICE_ROLE_KEY: {SUPABASE_SERVICE_KEY[:20] if SUPABASE_SERVICE_KEY and len(SUPABASE_SERVICE_KEY) > 20 else '❌ PLACEHOLDER/NOT SET'}")

print("\n" + "=" * 60)
print("⚠️  ISSUES FOUND:")
print("=" * 60)

if not SUPABASE_SERVICE_KEY or SUPABASE_SERVICE_KEY == 'your_service_role_key_from_supabase':
    print("""
❌ SERVICE ROLE KEY NOT SET!

The FastAPI backend needs the SERVICE ROLE KEY to write to Supabase.

WHERE TO FIND IT:
1. Go to: https://supabase.com/dashboard/project/aacivwtbynhahoqecfro/settings/api
2. Scroll to "Project API keys"
3. Copy the "service_role" secret key (NOT the anon key)
4. Update apps/api/.env:

   SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.ey...
   
5. Restart FastAPI server

WHY THIS MATTERS:
- ANON key: Read-only access, used by frontend
- SERVICE_ROLE key: Full access, used by backend to write data
""")
else:
    print("✅ All environment variables look good!")
    
    # Try to connect
    try:
        from supabase import create_client
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        
        # Test query
        result = supabase.table('profiles').select('*').limit(1).execute()
        print(f"\n✅ Successfully connected to Supabase!")
        print(f"   Tables are accessible")
        
    except Exception as e:
        print(f"\n❌ Connection failed: {e}")


