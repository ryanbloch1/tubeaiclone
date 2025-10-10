# Why Does Zustand Still Have All This State?

## TL;DR: **Backward Compatibility Only**

You're absolutely right! 🎯 When everything comes from the API, you **DON'T need** all those voiceover, script, and image states in Zustand.

## What You Actually Need (Production):

```typescript
// IDEAL MINIMAL STORE (after migration)
type StoreState = {
  currentProjectId: string | null;
  setCurrentProject: (id: string | null) => void;

  // Maybe some UI flags
  isGenerating: boolean;
  setIsGenerating: (value: boolean) => void;
};
```

## Why It Still Has Everything:

### Current State: **Backward Compatibility**

Your existing pages use Zustand directly:

- `apps/web/app/script/page.tsx` → reads `topic`, `style`, `editableScript` from Zustand
- `apps/web/app/voiceover/page.tsx` → reads `audioUrl`, `rawScript` from Zustand
- `apps/web/app/images/page.tsx` → reads `scenes`, `images` from Zustand

If we remove those states NOW, your app would **break immediately**.

## Migration Path:

### Phase 1: ✅ **Remove Persistence** (DONE)

```typescript
// Only persist currentProjectId
partialize: (state) => ({
  currentProjectId: state.currentProjectId,
});
```

### Phase 2: 🔄 **Migrate Pages to Use Supabase** (TODO)

**Example: Script Page**

**Before (uses Zustand):**

```typescript
const editableScript = useVideoStore((s) => s.editableScript);
const topic = useVideoStore((s) => s.topic);
```

**After (uses Supabase):**

```typescript
const { currentProjectId } = useVideoStore(); // Only get project ID
const [script, setScript] = useState(null);
const [formData, setFormData] = useState({ topic: "", style: "" });

useEffect(() => {
  async function loadFromDB() {
    if (currentProjectId) {
      const scriptData = await getScriptByProject(currentProjectId);
      const projectData = await getProject(currentProjectId);

      setScript(scriptData);
      setFormData({ topic: projectData.topic, style: projectData.style });
    }
  }
  loadFromDB();
}, [currentProjectId]);
```

### Phase 3: 🗑️ **Remove Unused State** (FINAL)

After all pages use Supabase, remove:

```typescript
// DELETE these types
type ScriptState = { ... }      // ❌ Delete
type VoiceoverState = { ... }   // ❌ Delete
type ImagesState = { ... }      // ❌ Delete

// KEEP only this
type ProjectState = {
  currentProjectId: string | null
  setCurrentProject: (id: string | null) => void
}
```

## The Real Architecture:

```
┌─────────────────────────────────────────┐
│         Next.js Component               │
│                                         │
│  Zustand: currentProjectId ✅           │
│           ↓                             │
│  useEffect(() => {                      │
│    const data = await getFromSupabase() │
│    setLocalState(data)                  │
│  })                                     │
│                                         │
│  Component State:                       │
│    - script ← from Supabase            │
│    - images ← from Supabase            │
│    - formInputs ← from Supabase        │
└─────────────────────────────────────────┘
```

## Why Not Remove Everything Now?

**Because your app would crash:**

1. Script page expects `topic`, `editableScript`, etc. from Zustand
2. Voiceover page expects `audioUrl`, `rawScript` from Zustand
3. Images page expects `scenes`, `images` from Zustand

## Summary:

**Current Zustand:**

- ✅ Only persists `currentProjectId` (fixed quota issues)
- ⏳ Still has all states for backward compatibility
- 🎯 Will be cleaned up after migrating pages to Supabase

**Your Intuition is Correct:**

> "Why would I have all these states if everything comes from API?"

**Answer:** You shouldn't! They're **temporary** until you migrate all pages to fetch from Supabase.

## Next Steps:

Follow `MIGRATION_GUIDE.md` to:

1. Update each page to fetch from Supabase using `currentProjectId`
2. Move form inputs to component local state
3. Remove Zustand slices as they become unused
4. End up with minimal store that only has `currentProjectId`

---

**End Goal:** Zustand with ONLY `currentProjectId` + everything else from Supabase! 🎯
