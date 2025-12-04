# RealEstate Video Pro - Technical Documentation

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Tech Stack](#tech-stack)
4. [Features](#features)
5. [User Flow](#user-flow)
6. [Database Schema](#database-schema)
7. [API Endpoints](#api-endpoints)
8. [Key Services](#key-services)
9. [Frontend Structure](#frontend-structure)
10. [Development Setup](#development-setup)
11. [Deployment](#deployment)

---

## Overview

**RealEstate Video Pro** is an AI-powered platform that transforms property listings into professional video content. The platform enables real estate agents to:

- Upload property photos with automatic AI analysis
- Generate professional video scripts based on property details and photos
- Create voiceovers using text-to-speech
- Compile final videos with visuals and narration

The application follows a **photo-first workflow** where agents upload property photos, the system automatically analyzes and categorizes them by room type, and then generates a script that's grounded in the actual property features visible in the photos.

---

## Architecture

The application is built as a **monorepo** with two main components:

```
tubeaiclone/
├── apps/
│   ├── api/          # FastAPI backend (Python)
│   └── web/          # Next.js frontend (TypeScript/React)
├── supabase/         # Database migrations
└── output/           # Generated assets (videos, images, voiceovers)
```

### Backend (FastAPI)

- **Location**: `apps/api/`
- **Port**: `8000` (default)
- **Purpose**: Handles all business logic, AI services, and database operations
- **Key Responsibilities**:
  - Photo analysis using BLIP vision model
  - Script generation using Google Gemini
  - Text-to-speech voiceover generation
  - Video compilation
  - Project and image management

### Frontend (Next.js)

- **Location**: `apps/web/`
- **Port**: `3000` (default, falls back to 3001, 3002, etc. if in use)
- **Purpose**: User interface and API proxy layer
- **Key Responsibilities**:
  - User authentication and session management
  - Project management UI
  - Photo upload and organization
  - Script editing interface
  - Video preview and download

### Database (Supabase/PostgreSQL)

- **Provider**: Supabase (PostgreSQL with Row Level Security)
- **Migrations**: `supabase/migrations/`
- **Purpose**: Stores projects, scripts, images, scenes, voiceovers, and videos

---

## Tech Stack

### Backend

- **Framework**: FastAPI (Python 3.11+)
- **Database Client**: Supabase Python client
- **AI Services**:
  - **Vision**: BLIP (Salesforce) for photo captioning and scene type inference
  - **LLM**: Google Gemini 2.0 Flash for script generation
  - **TTS**: Hugging Face Inference API (with fallback to FastAPI `/voiceovers/sync`)
- **Image Processing**: PIL/Pillow
- **ML Framework**: PyTorch (for BLIP model inference)

### Frontend

- **Framework**: Next.js 15.5.2 (App Router, Turbopack)
- **Language**: TypeScript
- **UI Library**: React 19.1.0
- **Styling**: Tailwind CSS 4.0
- **State Management**: Zustand
- **Icons**: Lucide React
- **Authentication**: Supabase Auth Helpers

### Database & Infrastructure

- **Database**: PostgreSQL (via Supabase)
- **Authentication**: Supabase Auth
- **Storage**: Supabase Storage (for images and videos)
- **Deployment**: Docker containers (optional)

---

## Features

### 1. Project Management

- Create, update, and delete property listing projects
- Support for multiple video types:
  - **Listing**: Property showcase videos
  - **Neighborhood Guide**: Area overview videos
  - **Market Update**: Market analysis videos
- Project status tracking: `draft` → `script` → `voiceover` → `images` → `complete`

### 2. Photo Upload & Analysis

- **Batch Upload**: Upload multiple property photos at once
- **AI Analysis**: Automatic photo analysis using BLIP model:
  - Generates descriptive captions
  - Infers room/scene types (kitchen, bathroom, bedroom, living room, exterior, etc.)
  - Extracts key features
- **Smart Grouping**: Photos automatically grouped by room type:
  - Exterior / Front of Property
  - Living & Dining Areas
  - Kitchen
  - Bedrooms
  - Bathrooms
  - Outdoor & Garden
  - Other
- **Auto-Ordering**: Intelligent photo ordering for optimal video flow
- **Manual Reordering**: Drag-and-drop to customize photo sequence
- **Lazy Loading**: Images loaded on-demand to prevent timeouts

### 3. Script Generation

- **Photo-Grounded Scripts**: Scripts generated based on actual property photos
- **Professional Tone**: Enforces confident, agent-style narration
- **Content Rules**:
  - Focuses on property structure and permanent features
  - Avoids mentioning furniture, decor, or temporary items
  - Aligns with provided property details (address, type, price, bedrooms, etc.)
- **Scene-by-Scene**: One scene per photo, with time ranges
- **Editable**: Generated scripts can be edited before proceeding

### 4. Voiceover Generation

- **TTS Integration**: Text-to-speech conversion
- **Primary**: Hugging Face Inference API (pre-trained models)
- **Fallback**: FastAPI `/voiceovers/sync` endpoint
- **Format**: WAV audio files

### 5. Video Compilation

- Combines voiceover audio with images
- Generates final MP4 video files
- Scene-by-scene assembly based on script structure

### 6. User Authentication

- Email/password authentication via Supabase
- Protected routes with `AuthGuard` component
- Session management across page refreshes

---

## User Flow

### 1. Authentication

1. User visits homepage (`/`)
2. If not signed in: sees landing page with "Sign In" / "Create Account" options
3. If signed in: automatically redirected to `/projects`

### 2. Project Creation

1. User clicks **"+ New Project"** on `/projects` page
2. Redirected to `/script?new=1` (fresh project state)
3. User fills in property details:
   - Property address
   - Property type (apartment, house, etc.)
   - Price, bedrooms, bathrooms, square feet
   - MLS number (optional)
   - Property features (checkboxes)
4. Project is automatically saved as `draft` status

### 3. Photo Upload

1. User uploads property photos (drag-and-drop or file picker)
2. Photos are uploaded to backend with base64 encoding
3. Backend processes each photo:
   - Stores in `images` table with `project_id`
   - Runs BLIP analysis to generate caption and infer `scene_type`
   - Updates `photo_analysis` JSONB field
4. Frontend displays photos grouped by room type
5. User can:
   - Drag photos to reorder within/between groups
   - Click "Auto-order for best flow" to apply intelligent ordering
   - See upload progress with percentage

### 4. Script Generation

1. **Prerequisites**: Minimum number of analyzed photos required (enforced by backend)
2. User clicks **"Generate Script"** button
3. Backend:
   - Fetches all project photos ordered by `sort_index`
   - Builds prompt with property details + photo captions
   - Calls Google Gemini to generate script
   - Parses script into scenes
   - Saves script to `scripts` table
   - Creates `scenes` records linked to script
   - Updates `scene_photo_map` JSONB to map scenes to photos
4. Frontend displays generated script in editable textarea
5. User can edit script before proceeding

### 5. Voiceover Generation

1. User navigates to `/voiceover?projectId={id}` (or continues from script page)
2. User clicks **"Generate Voiceover"**
3. Backend:
   - Fetches script text
   - Calls TTS service (Hugging Face or fallback)
   - Saves audio to `voiceovers` table
4. Frontend plays audio preview

### 6. Video Compilation

1. User navigates to `/video?projectId={id}`
2. User clicks **"Generate Video"**
3. Backend:
   - Fetches voiceover audio
   - Fetches images mapped to scenes
   - Assembles video using ffmpeg
   - Saves video file
4. Frontend displays video preview and download link

---

## Database Schema

### Core Tables

#### `projects`

Stores property listing projects.

**Key Fields**:

- `id` (UUID, primary key)
- `user_id` (UUID, foreign key to `auth.users`)
- `title` (text)
- `topic` (text)
- `status` (enum: `draft`, `script`, `voiceover`, `images`, `complete`)
- `video_type` (enum: `listing`, `neighborhood_guide`, `market_update`)
- `property_address` (text)
- `property_type` (text)
- `property_price` (numeric)
- `bedrooms` (integer)
- `bathrooms` (numeric)
- `square_feet` (integer)
- `mls_number` (text)
- `property_features` (text array)
- `created_at`, `updated_at` (timestamps)

#### `images`

Stores uploaded photos and generated images.

**Key Fields**:

- `id` (UUID, primary key)
- `user_id` (UUID, foreign key)
- `project_id` (UUID, nullable, foreign key to `projects`)
- `script_id` (UUID, nullable, foreign key to `scripts`)
- `scene_id` (UUID, nullable, foreign key to `scenes`)
- `source_type` (enum: `generated`, `uploaded`)
- `image_data` (text, base64-encoded)
- `image_url` (text, nullable)
- `photo_analysis` (JSONB) - Contains:
  - `caption`: AI-generated description
  - `scene_type`: Inferred room type
  - `features`: Extracted feature list
  - `confidence`: Analysis confidence score
- `scene_type` (text) - Canonical room type
- `sort_index` (integer) - Ordering for project photos
- `created_at` (timestamp)

**Indexes**:

- `idx_images_project_source_sort_created` on `(project_id, source_type, sort_index, created_at)`

#### `scripts`

Stores generated video scripts.

**Key Fields**:

- `id` (UUID, primary key)
- `user_id` (UUID, foreign key)
- `project_id` (UUID, foreign key to `projects`)
- `raw_script` (text) - Original generated script
- `edited_script` (text, nullable) - User-edited version
- `scene_photo_map` (JSONB) - Maps scene numbers to image IDs
- `created_at`, `updated_at` (timestamps)

#### `scenes`

Stores individual scenes parsed from scripts.

**Key Fields**:

- `id` (UUID, primary key)
- `user_id` (UUID, foreign key)
- `script_id` (UUID, foreign key to `scripts`)
- `scene_number` (integer)
- `text` (text) - Scene narration/content
- `created_at` (timestamp)

#### `voiceovers`

Stores generated audio files.

**Key Fields**:

- `id` (UUID, primary key)
- `user_id` (UUID, foreign key)
- `script_id` (UUID, foreign key to `scripts`)
- `audio_data` (text, base64-encoded WAV)
- `audio_url` (text, nullable)
- `created_at` (timestamp)

#### `videos`

Stores compiled video files.

**Key Fields**:

- `id` (UUID, primary key)
- `user_id` (UUID, foreign key)
- `script_id` (UUID, foreign key to `scripts`)
- `video_data` (text, base64-encoded MP4)
- `video_url` (text, nullable)
- `created_at` (timestamp)

### Row Level Security (RLS)

All tables have RLS policies ensuring users can only access their own data:

- `SELECT`: Users can only read their own records
- `INSERT`: Users can only create records with their own `user_id`
- `UPDATE`: Users can only update their own records
- `DELETE`: Users can only delete their own records

---

## API Endpoints

### Backend (FastAPI) - `http://127.0.0.1:8000`

#### Projects

- `POST /api/projects/save` - Create or update a project
- `GET /api/projects/{project_id}/photos-status` - Get photo upload/analysis status

#### Images

- `POST /api/images/project-photos/{project_id}` - Upload project photo
- `GET /api/images/project-photos/{project_id}` - List project photos
- `POST /api/images/project-photos/{project_id}/auto-order` - Auto-order photos
- `PATCH /api/images/project-photos/{image_id}/scene-type` - Update scene type
- `POST /api/images/project-photos/{project_id}/images` - Batch fetch image data
- `GET /api/images/project-photos/{project_id}/image/{image_id}` - Get single image data
- `POST /api/images/project-photos/{project_id}/reorder` - Reorder photos

#### Scripts

- `POST /api/script/generate` - Generate script from project
  - Requires: `project_id`, property details, photos
  - Returns: Generated script text and script ID

#### Voiceovers

- `POST /api/voiceover/generate` - Generate voiceover from script
- `POST /api/voiceover/sync` - Synchronous TTS (fallback)

#### Videos

- `POST /api/video/generate` - Compile video from voiceover and images

### Frontend (Next.js) - API Proxy Routes

All backend endpoints are proxied through Next.js API routes in `apps/web/app/api/` for:

- Authentication handling
- CORS management
- Request/response transformation

**Key Proxy Routes**:

- `/api/projects` - Project CRUD
- `/api/projects/[id]` - Individual project operations
- `/api/projects/save` - Save project
- `/api/project-photos/upload` - Upload photo
- `/api/project-photos/list` - List photos
- `/api/project-photos/auto-order` - Auto-order photos
- `/api/project-photos/update-scene-type` - Update scene type
- `/api/project-photos/images` - Batch fetch images
- `/api/script/generate` - Generate script
- `/api/voiceover/generate` - Generate voiceover
- `/api/video/generate` - Generate video

---

## Key Services

### 1. Photo Analysis Service (`apps/api/services/photo_analysis.py`)

**Purpose**: Analyze uploaded property photos using BLIP vision model.

**Key Functions**:

- `analyse_image_bytes(image_bytes: bytes) -> Dict`
  - Takes raw image bytes
  - Returns structured analysis:
    ```python
    {
        "caption": "A modern kitchen with white cabinets...",
        "scene_type": "kitchen",
        "features": ["white cabinets", "stainless steel appliances"],
        "confidence": 1.0
    }
    ```

**Scene Type Inference**:

- Uses keyword matching against predefined room categories
- Canonical types: `exterior`, `living_room`, `kitchen`, `dining`, `bedroom`, `bathroom`, `balcony`, `outdoor`, `other`
- Falls back to `living_room` for generic interior shots

**Model**: Salesforce BLIP Image Captioning Base

- Runs locally (no external API calls)
- Supports Apple Silicon GPU (MPS) acceleration
- Falls back to CPU if GPU unavailable

### 2. Script Generation Service (`apps/api/services/script_generation.py`)

**Purpose**: Generate professional property listing scripts using Google Gemini.

**Key Functions**:

- `build_prompt(...)` - Constructs detailed prompt for LLM
- `generate_script_with_gemini(...)` - Calls Gemini API and parses response

**Prompt Structure**:

1. **Property Information**: Address, type, price, bedrooms, bathrooms, features
2. **Photo Context**: Each photo's caption, scene type, and features
3. **Style Guidelines**:
   - Professional, confident, agent-style tone
   - Focus on property structure and permanent features
   - Avoid furniture, decor, temporary items
   - No hedging or weak language
4. **Output Format**: Scene-by-scene with time ranges

**Model**: Google Gemini 2.0 Flash

- Requires `GEMINI_API_KEY` environment variable
- Generates complete script in one response (all scenes)

### 3. System TTS Service (`apps/api/services/system_tts.py`)

**Purpose**: Generate text-to-speech audio (fallback when Hugging Face unavailable).

**Modes**:

- `gtts`: Google Text-to-Speech (requires internet)
- `say`: macOS `say` command (local, macOS only)
- `espeak`: eSpeak TTS (local, cross-platform)
- `placeholder`: Quick local WAV generation for testing

**Configuration**: Set `VOICE_TTS_MODE` environment variable.

---

## Frontend Structure

### Pages

#### `/` (Home)

- **Signed Out**: Landing page with sign in/sign up CTAs
- **Signed In**: Redirects to `/projects`

#### `/projects`

- Lists all user projects
- Filtering by video type (listing, neighborhood guide, market update)
- Sorting (recent, title, oldest)
- Project cards with status badges
- Delete with undo functionality
- **"+ New Project"** button → `/script?new=1`

#### `/script`

- Main project creation/editing interface
- **Property Form**: Address, type, price, bedrooms, bathrooms, etc.
- **Photo Upload Section**:
  - Drag-and-drop or file picker
  - Progress bar with percentage
  - Room-based grouping display
  - Drag-and-drop reordering
  - "Auto-order for best flow" button
- **Script Generation**:
  - Disabled until minimum photos analyzed
  - Generates script based on photos
  - Editable textarea
- **Navigation**: Continue to voiceover → images → video

#### `/voiceover`

- Displays script text
- Generates voiceover audio
- Audio preview player
- Continue to video compilation

#### `/video`

- Displays final compiled video
- Download link
- Video preview player

### Components

#### `AuthProvider` (`components/auth/AuthProvider.tsx`)

- Manages Supabase authentication state
- Provides `user`, `session`, `signIn`, `signOut` to app
- Wraps app in `AuthGuard` for protected routes

#### `Navbar` (`components/navigation/Navbar.tsx`)

- Top navigation bar
- Logo and branding
- Navigation links (Home, Projects)
- User menu (sign out)

#### `ToastProvider` (`components/providers/ToastProvider.tsx`)

- Global toast notification system
- Success, error, info toasts
- Undo functionality for destructive actions

### State Management

#### Zustand Store (`lib/store.ts`)

- **Persisted**: `currentProjectId` (localStorage)
- **In-Memory**: Form state, script text, audio URLs, etc.
- **Purpose**: Maintains project context across page navigations

---

## Development Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- Supabase account and project
- Google Gemini API key (for script generation)
- (Optional) Hugging Face API key (for TTS)

### Backend Setup

1. **Navigate to API directory**:

   ```bash
   cd apps/api
   ```

2. **Create virtual environment**:

   ```bash
   python -m venv ../.venv
   source ../.venv/bin/activate  # On macOS/Linux
   # or
   ..\.venv\Scripts\activate  # On Windows
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Set environment variables** (create `.env` in project root):

   ```env
   SUPABASE_URL=your_supabase_url
   SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
   GEMINI_API_KEY=your_gemini_api_key
   VOICE_TTS_MODE=gtts  # or say, espeak, placeholder
   ```

5. **Start FastAPI server**:
   ```bash
   uvicorn main:app --host 127.0.0.1 --port 8000 --reload
   ```

### Frontend Setup

1. **Navigate to web directory**:

   ```bash
   cd apps/web
   ```

2. **Install dependencies**:

   ```bash
   npm install
   ```

3. **Set environment variables** (create `.env.local`):

   ```env
   NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key
   NEXT_PUBLIC_API_BASE=http://127.0.0.1:8000
   ```

4. **Start Next.js dev server**:

   ```bash
   npm run dev
   ```

5. **Access application**:
   - Frontend: `http://localhost:3000` (or next available port)
   - Backend API: `http://127.0.0.1:8000`

### Database Setup

1. **Apply migrations** (if using Supabase CLI):

   ```bash
   supabase db push
   ```

   Or manually run SQL migrations from `supabase/migrations/` in Supabase SQL Editor.

2. **Key migrations**:
   - `001_initial_schema.sql` - Core tables
   - `007_add_photo_analysis.sql` - Photo analysis fields
   - `009_extend_images_for_projects.sql` - Project-level photos
   - `012_add_images_project_index.sql` - Performance index
   - `013_add_delete_project_cascade_function.sql` - Cascade delete function

---

## Deployment

### Backend (FastAPI)

**Docker**:

- `Dockerfile.api` - Production Docker image
- `docker-compose.yml` - Local development with Docker

**Environment Variables** (production):

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `GEMINI_API_KEY`
- `VOICE_TTS_MODE`
- `CORS_ORIGINS` (comma-separated frontend URLs)

### Frontend (Next.js)

**Build**:

```bash
cd apps/web
npm run build
npm start
```

**Environment Variables** (production):

- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- `NEXT_PUBLIC_API_BASE` (backend API URL)

**Deployment Platforms**:

- Vercel (recommended for Next.js)
- Netlify
- Self-hosted with Node.js

### Database (Supabase)

- Hosted on Supabase cloud
- Migrations applied via Supabase Dashboard SQL Editor or CLI
- RLS policies automatically enforced

---

## Performance Optimizations

### Database

- **Indexes**: Composite index on `images(project_id, source_type, sort_index, created_at)` for fast photo queries
- **Lazy Loading**: Image `base64` data fetched on-demand to prevent initial load timeouts
- **Batch Operations**: Photos deleted in batches of 500 to avoid statement timeouts

### Frontend

- **Lazy Image Loading**: Individual images loaded with loading states
- **Optimistic Updates**: UI updates immediately, API calls happen in background
- **Debouncing**: Form inputs debounced to reduce API calls

### Backend

- **Model Caching**: BLIP model loaded once and cached in memory
- **Async Processing**: Photo analysis runs asynchronously
- **Batch Deletes**: Cascade deletes handled in batches to prevent timeouts

---

## Security

### Authentication

- Supabase Auth handles all authentication
- JWT tokens validated on every API request
- Row Level Security (RLS) ensures users can only access their own data

### API Security

- CORS configured for specific origins
- Token verification on all protected endpoints
- Input validation using Pydantic models

### Data Privacy

- User data isolated by `user_id` foreign keys
- No cross-user data access possible
- Images stored as base64 in database (consider moving to Supabase Storage for large files)

---

## Known Limitations & Future Improvements

### Current Limitations

1. **Image Storage**: Base64 encoding in database (not scalable for large files)
   - **Future**: Migrate to Supabase Storage buckets
2. **Video Storage**: Videos stored as base64 (very large)
   - **Future**: Use cloud storage (S3, Supabase Storage)
3. **TTS Quality**: Fallback TTS (gTTS/say/espeak) has limited quality
   - **Future**: Integrate ElevenLabs or similar premium TTS
4. **Photo Analysis**: BLIP model is basic (not fine-tuned for real estate)
   - **Future**: Fine-tune or use specialized real estate vision model

### Planned Features

- [ ] Bulk project operations
- [ ] Project templates
- [ ] Video style presets
- [ ] Export to social media formats
- [ ] Analytics dashboard
- [ ] Team collaboration features
- [ ] API rate limiting
- [ ] Webhook support for external integrations

---

## Troubleshooting

### Common Issues

#### "Failed to load photos: statement timeout"

- **Cause**: Large base64 images in database
- **Fix**: Ensure index `idx_images_project_source_sort_created` exists, use lazy loading

#### "Could not find function delete_project_cascade"

- **Cause**: Migration not applied
- **Fix**: Run migration `013_add_delete_project_cascade_function.sql` in Supabase SQL Editor

#### "GEMINI_API_KEY not set"

- **Cause**: Missing environment variable
- **Fix**: Set `GEMINI_API_KEY` in `.env` file

#### "BLIP model loading slow"

- **Cause**: First load downloads model from Hugging Face
- **Fix**: Model is cached after first load, subsequent loads are fast

#### "Port 3000 already in use"

- **Cause**: Another Next.js instance running
- **Fix**: Next.js automatically uses next available port (3001, 3002, etc.)

---

## Contributing

### Code Style

- **Python**: Follow PEP 8, use type hints
- **TypeScript**: Use strict mode, prefer functional components
- **Commits**: Use conventional commit messages

### Testing

- **E2E Tests**: Playwright tests in `apps/web/`
- **Run**: `npm run test:e2e` (or `test:e2e:headed` for visual)

---

## License

[Add your license here]

---

## Support

For issues, questions, or contributions, please [add contact/support information].

---

**Last Updated**: January 2025
**Version**: 0.1.0
