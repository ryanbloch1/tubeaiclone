#!/usr/bin/env python3
"""Apply the profile trigger to Supabase"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv('apps/api/.env')

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("=" * 70)
print("🔧 APPLYING PROFILE TRIGGER TO SUPABASE")
print("=" * 70)

# Read the migration file
with open('supabase/migrations/002_add_profile_trigger.sql', 'r') as f:
    sql = f.read()

print("\n📝 Executing SQL migration...")
print(sql)

try:
    # Execute the SQL
    result = supabase.rpc('exec_sql', {'query': sql}).execute()
    print("\n✅ Migration applied successfully!")
    
except Exception as e:
    print(f"\n⚠️  Note: This needs to be run manually in Supabase SQL Editor")
    print(f"\n📋 INSTRUCTIONS:")
    print(f"1. Go to: https://supabase.com/dashboard/project/aacivwtbynhahoqecfro/sql/new")
    print(f"2. Copy and paste the SQL from: supabase/migrations/002_add_profile_trigger.sql")
    print(f"3. Click 'RUN' to execute")
    print(f"\n✅ This will automatically create profiles for new users!")


