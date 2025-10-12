# TubeAI Clone - Testing Checklist

## 🎯 **Test in This Order:**

### **Phase 1: Authentication (DONE ✅)**

- [x] Sign up page loads
- [x] User can create account
- [x] Login page loads
- [x] User can sign in
- [x] Middleware refreshes tokens
- [x] Database creates profile on signup

---

### **Phase 2: Projects & Database**

#### Test 2.1: View Projects List

1. Go to: http://localhost:3000/script
2. **Expected:** You should see "Recent Projects" section
3. **What to check:**
   - ✅ Projects load from database
   - ✅ Shows project titles, dates, video length
   - ✅ No errors in browser console

#### Test 2.2: Load Existing Project

1. On script page, click on a recent project
2. **Expected:** Form fields populate with project data
3. **What to check:**
   - ✅ Topic fills in
   - ✅ Video length selector shows correct value
   - ✅ If project has a script, it appears in editor

---

### **Phase 3: Script Generation**

**BEFORE TESTING:** Fix these first!

#### Fix 3.1: Gemini API Key

```bash
# Check your API key
cat apps/api/.env | grep GEMINI_API_KEY

# If it says "your_api_key_here" or is invalid, get a real one:
# 1. Go to: https://makersuite.google.com/app/apikey
# 2. Create API key
# 3. Update apps/api/.env:
GEMINI_API_KEY=YOUR_REAL_KEY_HERE
```

#### Fix 3.2: FastAPI Server

```bash
# Kill any existing process on port 8000
lsof -ti:8000 | xargs kill -9

# Start FastAPI
cd apps/api
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

#### Test 3.3: Generate Script

1. Go to: http://localhost:3000/script
2. Enter topic: "The Future of AI"
3. Select video length: "1:00"
4. Click "Generate"
5. **Expected:**
   - ✅ Loading indicator appears
   - ✅ Script appears in editor after ~5-10 seconds
   - ✅ No errors
   - ✅ "Save Changes" button appears

#### Test 3.4: Verify Database

```bash
# Check Supabase dashboard:
# https://supabase.com/dashboard/project/YOUR_PROJECT/editor

# Check these tables:
# - projects: Should have new entry
# - scripts: Should have script content
```

---

### **Phase 4: Script Editing**

#### Test 4.1: Edit Script

1. After generating script, modify the text in editor
2. Click "Save Changes"
3. **Expected:**
   - ✅ Button changes to "Saved!" (green)
   - ✅ Changes persist in database

#### Test 4.2: Refresh Page

1. Refresh browser (F5)
2. **Expected:**
   - ✅ Project still selected
   - ✅ Script still shows your edits
   - ✅ No data loss!

---

### **Phase 5: Navigation to Voiceover**

#### Test 5.1: Pass Project to Voiceover

1. After generating script, click "Use for Voiceover →"
2. **Expected:**
   - ✅ Navigates to: `/voiceover?projectId=xxx`
   - ✅ Voiceover page loads
   - ✅ (Future: Script will load from database)

---

## 🚨 **Current Issues to Fix:**

### Issue 1: Gemini API Key

**Location:** `apps/api/.env`
**Error:** `API key not valid`
**Fix:** Get real API key from https://makersuite.google.com/app/apikey

### Issue 2: FastAPI Not Running

**Error:** `Address already in use`
**Fix:**

```bash
lsof -ti:8000 | xargs kill -9
cd apps/api && python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

---

## 🎯 **Quick Sanity Check:**

Run this simple test to verify everything is connected:

```bash
# 1. Check Next.js
curl http://localhost:3000

# 2. Check FastAPI
curl http://localhost:8000/health

# 3. Check if logged in (from browser console)
# Open browser DevTools → Console → Run:
# await fetch('/api/projects').then(r => r.json())
# Should return your projects, not 401 error
```

---

## 📝 **What You've Built So Far:**

✅ **Authentication** - Supabase Auth with auto-refresh
✅ **Database** - PostgreSQL with proper schema
✅ **Projects API** - CRUD operations working
✅ **Script Page** - Video length selector, projects list
✅ **Middleware** - Token refresh on every request
✅ **RLS Policies** - User data is protected

**Next Steps:**

1. Fix Gemini API key
2. Restart FastAPI
3. Test script generation end-to-end
4. Then move to voiceover/images pages

---

## 🆘 **If You're Stuck:**

**Start with the simplest test:**

1. Open http://localhost:3000/script
2. Can you see your recent projects?
   - YES → Database connection works! ✅
   - NO → Check browser console for errors

**Then:**

1. Can you click on a project and see it load?
   - YES → API routes work! ✅
   - NO → Check Network tab in DevTools

**Finally:**

1. Try to generate a script
   - If it fails, check FastAPI logs
   - If API key error, update the key
   - If server not running, restart it

---

## 💡 **Remember:**

You don't need to test EVERYTHING at once. Test one piece at a time:

1. Auth ✅ (Already working)
2. Projects ← Start here
3. Script generation
4. Voiceover (later)
5. Images (later)

**Focus on getting script generation working first!** 🎯
