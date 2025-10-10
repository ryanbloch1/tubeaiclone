# Supabase Setup Guide

This guide will help you configure Supabase for your Next.js application.

## 📋 Prerequisites

1. A Supabase account (sign up at https://supabase.com)
2. A Supabase project created

## 🔧 Setup Steps

### 1. Get Your Supabase Credentials

1. Go to your Supabase project dashboard
2. Click on the **Settings** icon (⚙️) in the sidebar
3. Navigate to **API** section
4. Copy the following values:
   - **Project URL** (looks like: `https://xxxxx.supabase.co`)
   - **Anon/Public Key** (starts with `eyJ...`)

### 2. Configure Environment Variables

Create a `.env.local` file in the `apps/web` directory:

```bash
# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=https://your-project-ref.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key-here

# FastAPI Backend (if not already set)
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**⚠️ Important:** Never commit `.env.local` to git!

### 3. Apply Database Migrations

Run the migration file located at `supabase/migrations/001_initial_schema.sql`:

#### Option A: Using Supabase Dashboard (Recommended for first time)

1. Go to your Supabase project dashboard
2. Click on **SQL Editor** in the sidebar
3. Click **New Query**
4. Copy and paste the contents of `supabase/migrations/001_initial_schema.sql`
5. Click **Run** to execute the migration

#### Option B: Using Supabase CLI

```bash
# If you haven't installed the CLI yet
npm install -g supabase

# Login to Supabase
supabase login

# Link your project
supabase link --project-ref your-project-ref

# Push migrations
supabase db push
```

### 4. Verify Setup

1. Check that all tables are created:

   - Go to **Table Editor** in your Supabase dashboard
   - You should see: `profiles`, `projects`, `scripts`, `scenes`, `scene_prompts`, `images`, `voiceovers`, `job_queue`

2. Verify Row Level Security (RLS) policies:
   - Go to **Authentication** → **Policies**
   - Each table should have policies for SELECT, INSERT, UPDATE, DELETE

## 📁 File Structure

```
apps/web/
├── lib/
│   ├── supabase/
│   │   ├── client.ts          # Client-side Supabase client
│   │   ├── server.ts          # Server-side Supabase client
│   │   └── middleware.ts      # Auth session refresh
│   ├── db/
│   │   ├── projects.ts        # Project CRUD operations
│   │   ├── scripts.ts         # Script CRUD operations
│   │   ├── scenes.ts          # Scene CRUD operations
│   │   ├── images.ts          # Image CRUD operations
│   │   ├── voiceovers.ts      # Voiceover CRUD operations
│   │   └── index.ts           # Barrel export
│   └── auth/
│       └── user.ts            # User authentication utilities
└── middleware.ts              # Next.js middleware for auth
```

## 🎯 Usage Examples

### Client-Side (React Components)

```typescript
"use client";
import { getProjects, createProject } from "@/lib/db";
import { getCurrentUser } from "@/lib/auth/user";

export default function ProjectsPage() {
  const [projects, setProjects] = useState([]);

  useEffect(() => {
    async function loadProjects() {
      const user = await getCurrentUser();
      if (user) {
        const data = await getProjects();
        setProjects(data);
      }
    }
    loadProjects();
  }, []);

  // ... rest of component
}
```

### Server-Side (Server Components, API Routes)

```typescript
import { createClient } from "@/lib/supabase/server";
import { getProjects } from "@/lib/db";

export default async function ProjectsPage() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login");
  }

  const projects = await getProjects();

  return <div>{/* Render projects */}</div>;
}
```

### API Routes

```typescript
// app/api/projects/route.ts
import { createClient } from "@/lib/supabase/server";
import { getProjects } from "@/lib/db";
import { NextResponse } from "next/server";

export async function GET() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  try {
    const projects = await getProjects();
    return NextResponse.json(projects);
  } catch (error) {
    return NextResponse.json(
      { error: "Failed to fetch projects" },
      { status: 500 }
    );
  }
}
```

## 🔐 Authentication Flow

1. **Sign Up / Sign In**: Use Supabase Auth UI or custom forms
2. **Session Management**: Middleware automatically refreshes tokens
3. **Protected Routes**: Check `user` in server components
4. **RLS Policies**: Database automatically filters data by `user_id`

## 🚀 Next Steps

1. ✅ Install Supabase packages
2. ✅ Configure environment variables
3. ✅ Apply database migrations
4. ✅ Verify setup in Supabase dashboard
5. ⏭️ Implement authentication UI
6. ⏭️ Connect your app pages to Supabase
7. ⏭️ Set up FastAPI to use Supabase

## 📚 Resources

- [Supabase Docs](https://supabase.com/docs)
- [Next.js + Supabase Guide](https://supabase.com/docs/guides/getting-started/quickstarts/nextjs)
- [Row Level Security](https://supabase.com/docs/guides/auth/row-level-security)
