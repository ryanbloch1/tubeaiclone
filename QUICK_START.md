# 🚀 Quick Start Guide

## Your Question Answered:

### **Do I still need Zustand if every page has an API call?**

**Answer: YES, but only for minimal UI state.**

You **DON'T** persist:

- ❌ Scripts, scenes, images (in Zustand)
- ❌ User data (in Zustand)
- ❌ Generated content (in Zustand)

You **DO** persist:

- ✅ `currentProjectId` (which project user is working on)
- ✅ Navigation flags (`cameFromVoiceover`, etc.)
- ✅ Loading states (`isGenerating`, `isLoading`)

### **User ID Handling:**

**Answer: NO, don't persist userId in Zustand.**

- Supabase automatically persists the **session** (in cookies/storage)
- Get `userId` when needed:
  ```typescript
  const {
    data: { user },
  } = await supabase.auth.getUser();
  const userId = user?.id;
  ```
- For FastAPI: Send the **access token**, not the userId:
  ```typescript
  const {
    data: { session },
  } = await supabase.auth.getSession();
  fetch("/api/endpoint", {
    headers: { Authorization: `Bearer ${session.access_token}` },
  });
  ```

## 🏗️ Architecture Decision

### ✅ Use Supabase Direct (from Next.js):

```typescript
// CRUD operations
import { getProjects, createProject } from "@/lib/db";

const projects = await getProjects(); // Auto-filtered by user_id via RLS
const project = await createProject({ title: "My Video" });
```

### ✅ Use FastAPI (for AI generation):

```typescript
// AI-heavy tasks
const response = await fetch("/api/script/generate", {
  headers: { Authorization: `Bearer ${token}` },
  body: JSON.stringify({ project_id, topic, style }),
});
// FastAPI generates script → Saves to Supabase → Returns result
```

### ✅ Use Zustand (minimal UI state):

```typescript
// Just track current project and UI flags
const { currentProjectId, setCurrentProject } = useVideoStore();
const { cameFromVoiceover, setUIState } = useVideoStore();
```

## 📝 Environment Setup

### 1. Get Supabase Credentials

1. Go to https://supabase.com/dashboard
2. Select your project
3. Settings → API
4. Copy:
   - **Project URL**
   - **Anon public key**

### 2. Configure Next.js

Create `apps/web/.env.local`:

```bash
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJxxxx...
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Configure FastAPI

Create `apps/api/.env`:

```bash
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJxxxx...
GEMINI_API_KEY=your-gemini-key
```

### 4. Apply Database Migration

In Supabase dashboard:

1. SQL Editor → New Query
2. Copy/paste `supabase/migrations/001_initial_schema.sql`
3. Run

### 5. Install Dependencies

```bash
# FastAPI
cd apps/api
pip install -r requirements.txt

# Next.js (already installed)
cd apps/web
npm install  # Supabase packages already added
```

### 6. Run the Apps

```bash
# Terminal 1: FastAPI
cd apps/api
uvicorn main:app --reload

# Terminal 2: Next.js
cd apps/web
npm run dev
```

## 🎯 Usage Examples

### Client-Side (Page Component):

```typescript
"use client";
import { useEffect, useState } from "react";
import { useVideoStore } from "@/lib/store-minimal";
import { getProject, getScriptByProject } from "@/lib/db";

export default function ScriptPage() {
  const { currentProjectId } = useVideoStore();
  const [project, setProject] = useState(null);
  const [script, setScript] = useState(null);

  useEffect(() => {
    async function load() {
      if (currentProjectId) {
        const proj = await getProject(currentProjectId);
        const scr = await getScriptByProject(currentProjectId);
        setProject(proj);
        setScript(scr);
      }
    }
    load();
  }, [currentProjectId]);

  return <div>{script?.content}</div>;
}
```

### Server-Side (API Route):

```typescript
import { createClient } from "@/lib/supabase/server";

export async function GET() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { data } = await supabase
    .from("projects")
    .select("*")
    .eq("user_id", user.id);

  return NextResponse.json(data);
}
```

### FastAPI (Protected Endpoint):

```python
from fastapi import Depends
from auth import verify_token_async
from db import get_supabase

@app.post("/api/script/generate")
async def generate_script(
    request: ScriptRequest,
    user_id: str = Depends(verify_token_async)
):
    # user_id automatically extracted from JWT
    supabase = get_supabase()

    # Verify ownership
    project = supabase.table('projects') \
        .select('*') \
        .eq('id', request.project_id) \
        .eq('user_id', user_id) \
        .single() \
        .execute()

    # Generate script
    script = await generate_with_ai(...)

    # Save to DB
    result = supabase.table('scripts').insert({
        'project_id': request.project_id,
        'user_id': user_id,
        'content': script
    }).execute()

    return {"script_id": result.data[0]['id'], "content": script}
```

## 🔑 Key Concepts

### 1. User Authentication Flow

```
User logs in (Supabase Auth)
    ↓
Session stored (cookies/localStorage)
    ↓
Access token used for API calls
    ↓
FastAPI verifies token → Extracts user_id
    ↓
Database queries filtered by user_id (RLS)
```

### 2. Data Persistence

```
Old Way (Zustand only):
  localStorage → 5MB limit, client-only, no sharing

New Way (Supabase):
  Database → Unlimited, server-backed, multi-device
```

### 3. State Management

```
Zustand (UI only):
  - currentProjectId
  - cameFromVoiceover
  - isGenerating

Supabase (Data):
  - Projects
  - Scripts
  - Images
  - Scenes
  - Voiceovers
```

## 📚 Documentation Files

- **[SETUP_COMPLETE.md](SETUP_COMPLETE.md)** - What's been set up
- **[MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)** - How to migrate existing code
- **[apps/web/SUPABASE_SETUP.md](apps/web/SUPABASE_SETUP.md)** - Next.js details
- **[apps/api/FASTAPI_AUTH_SETUP.md](apps/api/FASTAPI_AUTH_SETUP.md)** - FastAPI details

## 🎉 You're Ready!

Your architecture is now production-ready with:

- ✅ Database persistence (Supabase)
- ✅ User authentication (Supabase Auth)
- ✅ Row-level security (RLS policies)
- ✅ AI generation (FastAPI + Gemini)
- ✅ Minimal state (Zustand for UI only)

**Next Step:** Follow the [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) to update your existing pages!
