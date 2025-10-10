# FastAPI Authentication Setup

This guide explains how to set up Supabase authentication in FastAPI.

## 📋 Prerequisites

1. Supabase project set up (see `apps/web/SUPABASE_SETUP.md`)
2. Python 3.9+ installed
3. Virtual environment activated

## 🔧 Installation

```bash
cd apps/api
pip install -r requirements.txt
```

## 🌍 Environment Variables

Create a `.env` file in `apps/api`:

```bash
# Supabase Configuration
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
# Optional: Service role key for admin operations (keep secret!)
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Other API keys
GEMINI_API_KEY=your-gemini-key
IMAGE_SD_MODEL=stabilityai/stable-diffusion-2-1-base
```

⚠️ **Important:**

- Use `SUPABASE_ANON_KEY` for most operations (respects RLS)
- Use `SUPABASE_SERVICE_ROLE_KEY` only for admin operations (bypasses RLS)

## 📁 File Structure

```
apps/api/
├── auth/
│   ├── __init__.py
│   └── verify.py         # Token verification functions
├── db/
│   ├── __init__.py
│   └── client.py         # Supabase client
├── main.py               # FastAPI app
└── requirements.txt
```

## 🎯 Usage Examples

### Protected Endpoint (Requires Authentication)

```python
from fastapi import Depends
from auth import verify_token_async
from db import get_supabase

@app.post("/api/generate-script")
async def generate_script(
    request: ScriptRequest,
    user_id: str = Depends(verify_token_async)
):
    """Generate script and save to database."""

    # Verify user owns this project
    supabase = get_supabase()
    project = supabase.table('projects') \\
        .select('*') \\
        .eq('id', request.project_id) \\
        .eq('user_id', user_id) \\
        .single() \\
        .execute()

    if not project.data:
        raise HTTPException(status_code=404, detail="Project not found")

    # Generate script using AI
    script_content = await generate_with_gemini(request.settings)

    # Save to database
    result = supabase.table('scripts').insert({
        'project_id': request.project_id,
        'user_id': user_id,
        'content': script_content,
        'raw_script': script_content
    }).execute()

    return {"script": script_content, "script_id": result.data[0]['id']}
```

### Optional Authentication

```python
from auth import get_optional_user

@app.get("/api/public-data")
async def get_public_data(user_id: str | None = Depends(get_optional_user)):
    """Endpoint that works with or without authentication."""

    if user_id:
        # Return personalized data
        return {"message": f"Hello user {user_id}"}
    else:
        # Return public data
        return {"message": "Hello guest"}
```

### Frontend → FastAPI Request

```typescript
// Next.js API route or client-side code
import { createClient } from "@/lib/supabase/client";

async function callFastAPI(endpoint: string, data: any) {
  const supabase = createClient();

  // Get current session token
  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (!session) {
    throw new Error("Not authenticated");
  }

  // Call FastAPI with Bearer token
  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL}${endpoint}`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${session.access_token}`,
      },
      body: JSON.stringify(data),
    }
  );

  return response.json();
}
```

## 🔐 How Authentication Works

### Flow:

1. **User logs in via Next.js** → Gets JWT token from Supabase
2. **Frontend calls FastAPI** → Sends JWT in `Authorization: Bearer <token>` header
3. **FastAPI verifies token** → Uses `verify_token()` to validate with Supabase
4. **Extract user_id** → Use for database queries
5. **Database enforces RLS** → Only returns data belonging to that user

### Token Verification:

```python
# In verify.py
def verify_token(credentials: HTTPAuthorizationCredentials) -> str:
    token = credentials.credentials

    # Verify with Supabase GoTrue
    user = auth_client.get_user(token)

    if not user:
        raise HTTPException(status_code=401)

    return user.user.id  # Return user_id for database queries
```

## 🚀 Complete Example: Image Generation Endpoint

```python
from fastapi import Depends, HTTPException
from pydantic import BaseModel
from auth import verify_token_async
from db import get_supabase

class ImageGenerationRequest(BaseModel):
    scene_id: str
    prompt: str

@app.post("/api/images/generate")
async def generate_image(
    request: ImageGenerationRequest,
    user_id: str = Depends(verify_token_async)
):
    """Generate image and save to database."""
    supabase = get_supabase()

    # 1. Verify user owns this scene
    scene = supabase.table('scenes') \\
        .select('*') \\
        .eq('id', request.scene_id) \\
        .eq('user_id', user_id) \\
        .single() \\
        .execute()

    if not scene.data:
        raise HTTPException(status_code=404, detail="Scene not found")

    # 2. Create image record (status: generating)
    image_record = supabase.table('images').insert({
        'scene_id': request.scene_id,
        'user_id': user_id,
        'prompt': request.prompt,
        'status': 'generating'
    }).execute()

    image_id = image_record.data[0]['id']

    try:
        # 3. Generate image using Stable Diffusion
        image_data = await generate_sd_image(request.prompt)

        # 4. Update record with result
        supabase.table('images').update({
            'image_data': image_data,  # base64 string
            'status': 'completed'
        }).eq('id', image_id).execute()

        return {
            "success": True,
            "image_id": image_id,
            "image_data": image_data
        }

    except Exception as e:
        # 5. Update record with error
        supabase.table('images').update({
            'status': 'error',
            'error_message': str(e)
        }).eq('id', image_id).execute()

        raise HTTPException(status_code=500, detail=str(e))
```

## 🧪 Testing Authentication

### 1. Get a test token from Next.js:

```typescript
// In browser console or test script
const supabase = createClient(...)
const { data } = await supabase.auth.getSession()
console.log(data.session.access_token)
```

### 2. Test with cURL:

```bash
curl -X POST http://localhost:8000/api/generate-script \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \\
  -d '{"project_id": "...", "settings": {...}}'
```

### 3. Test with Python requests:

```python
import requests

token = "your-supabase-jwt-token"
response = requests.post(
    "http://localhost:8000/api/generate-script",
    headers={"Authorization": f"Bearer {token}"},
    json={"project_id": "...", "settings": {...}}
)
print(response.json())
```

## 🔒 Security Best Practices

1. **Always verify ownership** - Check that `user_id` matches the resource owner
2. **Use RLS policies** - Let Supabase enforce access control at the database level
3. **Never trust client input** - Always verify project_id, scene_id, etc. belong to the user
4. **Service Role Key** - Only use for admin operations, never expose to client
5. **Token expiry** - Supabase tokens expire, handle 401 errors gracefully

## 📚 Resources

- [Supabase Auth Docs](https://supabase.com/docs/guides/auth)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [GoTrue Python Client](https://github.com/supabase-community/gotrue-py)
