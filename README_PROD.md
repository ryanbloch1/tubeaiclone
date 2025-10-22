Production scaffold (API + Worker + Redis)

Run locally with Docker:

1. docker compose up --build
2. API: http://localhost:8000/health
3. Create job:
   curl -X POST http://localhost:8000/voiceovers -H 'Content-Type: application/json' \
    -d '{"script":"Hello world","voice_sample_path":"voice_sample.wav","output_filename":"hello.wav"}'
4. Poll status:
   curl http://localhost:8000/voiceovers/<job_id>

Notes:

- Worker uses utils.voiceover.generate_voiceover (XTTS v2 local if available).
- Media saved under output/voiceovers.
- Set VOICE_SAMPLE_PATH env or pass voice_sample_path in the request.

Monorepo layout:

- apps/
  - api/ (FastAPI entry)
  - web/ (Next.js frontend)
- utils/ shared modules
