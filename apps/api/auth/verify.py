"""
Supabase Authentication Verification for FastAPI
"""

import os
from typing import Optional
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from gotrue import SyncGoTrueClient

# Initialize Supabase GoTrue client
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("WARNING: SUPABASE_URL or SUPABASE_ANON_KEY not set. Authentication will fail.")

# Create GoTrue client for token verification
auth_client = SyncGoTrueClient(
    url=f"{SUPABASE_URL}/auth/v1",
    headers={
        "apiKey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }
)

security = HTTPBearer()


def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    """
    Verify Supabase JWT token and return user_id.
    
    Args:
        credentials: HTTP Authorization Bearer token
        
    Returns:
        user_id: The authenticated user's ID
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        if not SUPABASE_URL or not SUPABASE_KEY:
            print(f"[AUTH] ERROR: Supabase credentials not configured. URL: {bool(SUPABASE_URL)}, KEY: {bool(SUPABASE_KEY)}")
            raise HTTPException(
                status_code=500,
                detail="Authentication service not configured",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        token = credentials.credentials
        print(f"[AUTH] Verifying token (length: {len(token)} chars)")
        
        # Verify the token with Supabase
        user = auth_client.get_user(token)
        
        if not user or not user.user:
            print(f"[AUTH] ERROR: Invalid user response from Supabase")
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        print(f"[AUTH] ✓ Token verified for user: {user.user.id}")
        return user.user.id
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        print(f"[AUTH] ERROR: Token verification failed: {error_msg}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


async def verify_token_async(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    """
    Async version of verify_token for use in async endpoints.
    
    Args:
        credentials: HTTP Authorization Bearer token
        
    Returns:
        user_id: The authenticated user's ID
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    # GoTrue Python client is sync-only, so we just call the sync version
    return verify_token(credentials)


def get_optional_user(credentials: Optional[HTTPAuthorizationCredentials] = Security(security)) -> Optional[str]:
    """
    Optional authentication - returns user_id if authenticated, None otherwise.
    
    Args:
        credentials: Optional HTTP Authorization Bearer token
        
    Returns:
        user_id or None
    """
    if not credentials:
        return None
    
    try:
        return verify_token(credentials)
    except HTTPException:
        return None

