# Environment Variables Setup

## Required Environment Variables

### For FastAPI Backend (`apps/api/.env`)

You need to create a `.env` file in `apps/api/` with:

```bash
# Supabase Configuration
SUPABASE_URL=https://aacivwtbynhahoqecfro.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key_here

# Google AI (for script generation)
GEMINI_API_KEY=your_gemini_api_key_here
```

### Where to find these values:

1. **Supabase Keys**: Go to your Supabase project settings → API

   - Copy the `URL` for `SUPABASE_URL`
   - Copy `anon` `public` key for `SUPABASE_ANON_KEY`
   - Copy `service_role` `secret` key for `SUPABASE_SERVICE_ROLE_KEY`

2. **Gemini API Key**:
   - Go to https://aistudio.google.com/app/apikey
   - Create a new API key
   - Copy it for `GEMINI_API_KEY`

### For Next.js Frontend

Your `.env.local` in `apps/web/` is already set up correctly:

```bash
NEXT_PUBLIC_SUPABASE_URL=https://aacivwtbynhahoqecfro.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key_here
```

## Testing Flow

Once environment variables are set:

1. **Sign Up**: http://localhost:3000/signup
2. **Log In**: http://localhost:3000/login
3. **Generate Script**: http://localhost:3000/script
4. **Create Voiceover**: http://localhost:3000/voiceover
5. **Generate Images**: http://localhost:3000/images
