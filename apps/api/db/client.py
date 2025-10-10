"""
Supabase client for FastAPI backend
"""

import os
from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "") or os.getenv("SUPABASE_ANON_KEY", "")

# Create Supabase client only if environment variables are available
supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Supabase client initialized successfully")
    except Exception as e:
        print(f"⚠️  Failed to initialize Supabase client: {e}")
        supabase = None
else:
    print("⚠️  SUPABASE_URL or SUPABASE_KEY not set. Database operations will fail.")


def get_supabase() -> Client:
    """
    Get the Supabase client instance.
    
    Returns:
        Supabase client
        
    Raises:
        Exception: If Supabase client is not initialized
    """
    if supabase is None:
        raise Exception("Supabase client not initialized. Check environment variables.")
    return supabase

