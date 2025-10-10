# Migration Guide: From Client State to Supabase Backend

This guide outlines the step-by-step migration from Zustand-only state management to a Supabase-backed architecture.

## 📊 Architecture Overview

### Before (Current):

```
Next.js Frontend
    ↓
Zustand Store (localStorage)
    ↓
FastAPI (AI generation only)
```

### After (Target):

```
Next.js Frontend
    ↓
Supabase (Database + Auth) ← → FastAPI (AI generation + DB writes)
```

## 🎯 Migration Strategy

### Phase 1: Setup Infrastructure ✅ COMPLETED

- [x] Create Supabase project
- [x] Apply database migrations
- [x] Install Supabase client in Next.js
- [x] Set up FastAPI authentication middleware
- [x] Create CRUD operations for database tables
- [x] Create minimal Zustand store

### Phase 2: Migrate Authentication (NEXT STEP)

**Goal:** Replace mock auth with real Supabase authentication

**Steps:**

1. Create login/signup pages in Next.js
2. Set up Supabase Auth UI
3. Add auth guards to protected routes
4. Test user flow: signup → login → dashboard

**Files to create:**

- `apps/web/app/login/page.tsx`
- `apps/web/app/signup/page.tsx`
- `apps/web/app/dashboard/page.tsx`
- `apps/web/components/auth/AuthProvider.tsx`

### Phase 3: Migrate Script Generation

**Goal:** Save scripts to Supabase instead of Zustand only

**Changes needed:**

#### 1. Update Script Page (`apps/web/app/script/page.tsx`)

```typescript
// OLD: Direct Gemini call, save to Zustand
const response = await fetch('/api/script', { ... })
const { text } = await response.json()
setScriptState({ editableScript: text })

// NEW: Call FastAPI with auth, saves to DB
const session = await supabase.auth.getSession()
const response = await fetch(`${API_URL}/api/script/generate`, {
  headers: {
    'Authorization': `Bearer ${session.data.session.access_token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    project_id: currentProjectId,
    topic, style, mode, ...
  })
})
const { script_id, content } = await response.json()
// Load from DB on page refresh
```

#### 2. Create Project Management

```typescript
// When user starts, create a project first
const project = await createProject({ title: topic })
setCurrentProject(project.id)

// Then generate script for that project
await generateScript({ project_id: project.id, ... })
```

### Phase 4: Migrate Voiceover

**Changes:**

1. Save voiceover to Supabase Storage (for audio files) or `audio_data_url` (for base64)
2. Associate with script_id
3. Update status in database

**Files to update:**

- `apps/web/app/voiceover/page.tsx`
- Create `apps/api/routes/voiceover.py`

### Phase 5: Migrate Images

**Changes:**

1. Save scenes to database when script is parsed
2. Generate image prompts → save to `scene_prompts` table
3. Generate images → save to `images` table
4. Optional: Upload images to Supabase Storage

**Files to update:**

- `apps/web/app/images/page.tsx`
- `apps/web/app/images/hooks/*`
- Create `apps/api/routes/images.py`

### Phase 6: Final Cleanup

**Tasks:**

- Remove old Zustand store (`lib/store.ts`)
- Rename `lib/store-minimal.ts` → `lib/store.ts`
- Remove old API routes that don't use Supabase
- Update all imports
- Test complete flow

## 🔄 Data Flow Examples

### Script Generation Flow

**Client → FastAPI → Supabase:**

```typescript
// 1. Frontend: Create project
const { data: project } = await createProject({
  title: topic,
  style,
  mode,
  temperature,
  word_count
})

// 2. Frontend: Call FastAPI to generate script
const response = await fetch('/api/script/generate', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    project_id: project.id,
    topic,
    style,
    ...
  })
})

// 3. FastAPI: Verify auth, generate script, save to DB
// (see apps/api/routes/script.py)

// 4. Frontend: Load script from DB
const script = await getScriptByProject(project.id)
```

### Page Load Flow

**Before (Zustand only):**

```typescript
const script = useVideoStore((s) => s.editableScript); // From localStorage
```

**After (Supabase):**

```typescript
const { currentProjectId } = useVideoStore();
const [script, setScript] = useState(null);

useEffect(() => {
  async function loadScript() {
    if (currentProjectId) {
      const data = await getScriptByProject(currentProjectId);
      setScript(data);
    }
  }
  loadScript();
}, [currentProjectId]);
```

## 🗂️ File Structure After Migration

```
apps/
├── web/                          # Next.js Frontend
│   ├── app/
│   │   ├── login/page.tsx        # ✨ NEW: Auth pages
│   │   ├── signup/page.tsx
│   │   ├── dashboard/page.tsx    # ✨ NEW: Project list
│   │   ├── script/page.tsx       # 🔄 UPDATED: Use Supabase
│   │   ├── voiceover/page.tsx    # 🔄 UPDATED
│   │   └── images/page.tsx       # 🔄 UPDATED
│   ├── lib/
│   │   ├── store.ts              # 🔄 REPLACED: Minimal version
│   │   ├── supabase/             # ✨ NEW
│   │   │   ├── client.ts
│   │   │   ├── server.ts
│   │   │   └── middleware.ts
│   │   ├── db/                   # ✨ NEW: CRUD operations
│   │   │   ├── projects.ts
│   │   │   ├── scripts.ts
│   │   │   ├── scenes.ts
│   │   │   ├── images.ts
│   │   │   └── voiceovers.ts
│   │   └── auth/                 # ✨ NEW
│   │       └── user.ts
│   └── middleware.ts             # ✨ NEW: Auth refresh
│
└── api/                          # FastAPI Backend
    ├── auth/                     # ✨ NEW
    │   └── verify.py
    ├── db/                       # ✨ NEW
    │   └── client.py
    ├── routes/                   # ✨ NEW
    │   ├── script.py
    │   ├── images.py
    │   └── voiceover.py
    ├── services/                 # ✨ NEW
    │   └── gemini.py
    └── main.py                   # 🔄 UPDATED
```

## 🧪 Testing Checklist

After migration, test these flows:

### Authentication

- [ ] User can sign up
- [ ] User can log in
- [ ] User can log out
- [ ] Protected routes redirect to login
- [ ] Session persists across browser refresh

### Script Generation

- [ ] User can create new project
- [ ] User can generate script
- [ ] Script saves to database
- [ ] Script loads on page refresh
- [ ] User can edit script
- [ ] Edits save to database

### Voiceover

- [ ] User can generate voiceover
- [ ] Audio saves to database/storage
- [ ] Audio loads on page refresh

### Images

- [ ] Scenes save to database
- [ ] Prompts generate and save
- [ ] Images generate and save
- [ ] Progress persists across refresh

### Multi-User

- [ ] User A cannot see User B's projects
- [ ] RLS policies work correctly
- [ ] Each user has isolated data

## 🚨 Common Issues & Solutions

### Issue: "Invalid JWT" error

**Solution:** Ensure you're passing the access_token correctly:

```typescript
const {
  data: { session },
} = await supabase.auth.getSession();
const token = session?.access_token;
```

### Issue: "Project not found" but it exists

**Solution:** Check RLS policies are enabled and user_id matches:

```sql
-- In Supabase SQL Editor
SELECT * FROM projects WHERE id = 'your-project-id';
```

### Issue: localStorage quota exceeded

**Solution:** This should be fixed with minimal store, but if it persists:

```typescript
// Clear old large store
localStorage.removeItem("tubeai_store");
```

### Issue: Stale data after generation

**Solution:** Refetch from database after mutations:

```typescript
await generateScript(...)
const updatedScript = await getScriptByProject(projectId)
setScript(updatedScript)
```

## 📚 Additional Resources

- [Supabase Setup Guide](apps/web/SUPABASE_SETUP.md)
- [FastAPI Auth Setup](apps/api/FASTAPI_AUTH_SETUP.md)
- [Database Schema](supabase/migrations/001_initial_schema.sql)

## 🎉 Benefits After Migration

✅ **Persistent Data** - Projects saved across devices/sessions  
✅ **Multi-User** - Each user has isolated data  
✅ **Real-time** - Can add live collaboration  
✅ **Scalable** - Database handles complex queries  
✅ **Secure** - Row Level Security enforces access control  
✅ **Fast** - No localStorage quota issues  
✅ **Professional** - Production-ready architecture
