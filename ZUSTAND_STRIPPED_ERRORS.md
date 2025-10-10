# 🔥 Zustand Stripped - TypeScript Errors to Fix

## What We Did:

**Removed ALL unnecessary state from Zustand** - only keeping `currentProjectId`

This is the **correct production architecture**, but existing pages need to be updated to use Supabase instead.

## TypeScript Errors Found:

### 1. ❌ `apps/web/app/images/hooks/useImageGeneration.ts`

**Error:** `Property 'scenes' does not exist on type 'StoreState'`

### 2. ❌ `apps/web/app/images/hooks/useScenes.ts`

**Error:** Will have similar errors for `scenes`, `images`, `scenePrompts`, `imagesScriptHash`, `setImagesState`

### 3. ❌ `apps/web/app/images/hooks/useScenePrompts.ts`

**Error:** Will have similar errors for `scenePrompts`, `setImagesState`

### 4. ❌ `apps/web/app/images/page.tsx`

**Error:** Will have errors for `cameFromVoiceover`

### 5. ❌ `apps/web/app/voiceover/page.tsx`

**Error:** Will have errors for `rawScript`, `audioUrl`, `setVoiceoverState`, `setImagesState`

### 6. ❌ `apps/web/app/script/page.tsx`

**Error:** Will have errors for `topic`, `style`, `mode`, `editableScript`, `setScriptState`

## Quick Fix Options:

### Option 1: **Temporarily Add Back Just What's Needed** (Band-aid)

Add minimal state back to Zustand (not persisted) to make it compile.

### Option 2: **Fix Pages Properly** (Recommended)

Update each page to use Supabase and component local state.

### Option 3: **Comment Out Broken Pages** (Nuclear)

Comment out imports in broken files to get app running, then fix one by one.

## Recommended Fix: Update Pages to Use Supabase

### Example Fix for `script/page.tsx`:

**OLD (Broken):**

```typescript
const topic = useVideoStore((s) => s.topic); // ❌ Doesn't exist
const editableScript = useVideoStore((s) => s.editableScript); // ❌ Doesn't exist
const setScriptState = useVideoStore((s) => s.setScriptState); // ❌ Doesn't exist
```

**NEW (Fixed with Supabase):**

```typescript
const { currentProjectId } = useVideoStore();
const [topic, setTopic] = useState("");
const [editableScript, setEditableScript] = useState("");
const [formData, setFormData] = useState({
  topic: "",
  style: "",
  mode: "script",
  temperature: 0.7,
  // ... other form fields
});

useEffect(() => {
  async function loadProject() {
    if (currentProjectId) {
      const project = await getProject(currentProjectId);
      const script = await getScriptByProject(currentProjectId);

      setFormData({
        topic: project.topic || "",
        style: project.style || "",
        // ... load other fields
      });
      setEditableScript(script?.content || "");
    }
  }
  loadProject();
}, [currentProjectId]);
```

## What You Need to Do:

1. **For each broken page:**

   - Replace Zustand state with component `useState`
   - Add `useEffect` to load data from Supabase using `currentProjectId`
   - Update form handlers to use local state
   - Save changes to Supabase via API calls

2. **Delete these hooks (they use old state):**

   - `apps/web/app/images/hooks/useScenes.ts`
   - `apps/web/app/images/hooks/useScenePrompts.ts`
   - `apps/web/app/images/hooks/useImageGeneration.ts`

3. **Rewrite images page to:**
   - Load scenes from Supabase `scenes` table
   - Load images from Supabase `images` table
   - Use component state for UI flags

## Alternative: Quick Restore (if you want the old store back)

If you want to revert temporarily:

```bash
git checkout apps/web/lib/store.ts
```

Then migrate pages one by one while keeping old store.

---

**Your instinct was correct** - this is the right architecture. Now we just need to update the pages to match! 🚀
