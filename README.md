# TubeAI Clone

TubeAI Clone is a full-stack app for generating real estate marketing videos from property details, scripts, voiceovers, and images.

## Tech Stack

- Frontend: Next.js 15 (App Router), TypeScript, Tailwind CSS
- Backend: FastAPI, Pydantic, Supabase
- Media: FFmpeg pipeline for video compilation
- AI providers (script generation): Groq, Gemini, OpenAI, Anthropic

## Monorepo Layout

- `apps/web`: Next.js frontend + API route layer
- `apps/api`: FastAPI backend services/routes
- `supabase/migrations`: schema migrations
- `apps/api/tests`: backend sanity tests
- `apps/web/tests/e2e`: Playwright smoke tests

## Core Workflow

1. Create or load a project
2. Generate a script (select AI provider/model on Script page)
3. Generate voiceover
4. Upload/generate images
5. Compile final video

## Prerequisites

- Node.js 20+
- Python 3.10+
- FFmpeg installed and available in `PATH`
- Supabase project and keys

## Environment

### Backend (`apps/api/.env`)

Start from `apps/api/.env.example`.

Required for auth/data:

- `SUPABASE_URL`
- `SUPABASE_ANON_KEY` (or `SUPABASE_SERVICE_ROLE_KEY`)

Script provider keys (set at least one):

- `GROQ_API_KEY` (+ optional `GROQ_MODEL`)
- `GEMINI_API_KEY` or `GOOGLE_API_KEY` (+ optional `GEMINI_MODEL`)
- `OPENAI_API_KEY` (+ optional `OPENAI_MODEL`, `OPENAI_BASE_URL`)
- `ANTHROPIC_API_KEY` (+ optional `ANTHROPIC_MODEL`)

### Frontend (`apps/web/.env.local`)

- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- `NEXT_PUBLIC_API_BASE` (example: `http://127.0.0.1:8000`)

## Local Development

### 1) API

```bash
cd apps/api
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 2) Web

```bash
cd apps/web
npm install
npm run dev
```

Web runs on `http://localhost:3000` by default.

## Quality Checks

### Web

```bash
cd apps/web
npm run lint
npm run build
npm run test:e2e -- --list
npm run test:e2e -- tests/e2e
```

### API

```bash
cd apps/api
python -m unittest discover -s tests
python -c "import main, routes.images, routes.video, routes.script, routes.voiceover, routes.projects"
```

From repo root:

```bash
python -c "import apps.api.main"
```

## Docker

A basic API service is defined in `docker-compose.yml`.

```bash
docker compose up --build api
```

## Notes

- Script generation supports provider/model selection from the Script page.
- In `auto` mode, backend tries providers in this order: Groq -> Gemini -> OpenAI -> Anthropic.
- If no provider is configured, local mock script fallback is used.
