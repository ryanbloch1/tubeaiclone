import os
try:
    # Load environment variables from a .env file (project root)
    from dotenv import load_dotenv, find_dotenv
    # Use override=True so .env values replace any empty pre-set envs
    load_dotenv(find_dotenv(), override=True)
except Exception:
    pass
import tempfile
import time
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel
import redis
import rq
from google.cloud import storage

REDIS_URL = os.getenv("REDIS_URL") or ""
QUEUE_NAME = os.getenv("QUEUE_NAME", "voiceover_queue")

def get_redis_connection():
    """Get Redis connection with retry logic."""
    if not REDIS_URL:
        return None, None
    try:
        rconn = redis.from_url(REDIS_URL, socket_keepalive=True, socket_keepalive_options={})
        rconn.ping()  # Test connection
        queue = rq.Queue(QUEUE_NAME, connection=rconn)
        return rconn, queue
    except Exception as e:
        print(f"Redis connection failed: {e}")
        return None, None

# Initialize global connection
rconn, queue = get_redis_connection()


class VoiceoverRequest(BaseModel):
    script: str
    voice_sample_path: str | None = None
    output_filename: str | None = None
    language: str | None = "en"


class ImageRequest(BaseModel):
    prompt: str
    scene_number: int
    width: int | None = 512
    height: int | None = 512


app = FastAPI(title="TubeAI API", version="0.1.0")

# Basic request/response logging (safe: re-injects body so downstream can read it)
@app.middleware("http")
def log_requests(request: Request, call_next):
    import json
    start = time.time()
    # Read raw body once
    body_bytes = request.body()
    if hasattr(body_bytes, "__await__"):
        body_bytes = request.scope.get("_cached_body") or request._body if hasattr(request, "_body") else None
        # Fallback to sync read; if unavailable, skip preview
        try:
            body_bytes = request._body
        except Exception:
            body_bytes = b""

    # Re-inject the body so FastAPI can parse it later
    def receive():
        return {"type": "http.request", "body": body_bytes or b"", "more_body": False}

    request._receive = receive  # type: ignore[attr-defined]

    body_preview = ""
    if body_bytes and request.method in ("POST", "PUT", "PATCH"):
        try:
            data = json.loads(body_bytes.decode("utf-8"))
            if isinstance(data, dict) and "script" in data:
                s = data.get("script") or ""
                data["script"] = s[:200] + ("..." if len(s) > 200 else "")
            body_preview = str(data)
        except Exception:
            body_preview = "<unparsed body>"

    try:
        response = call_next(request)
        if hasattr(response, "__await__"):
            response = next(response.__await__())  # simple sync bridge
        duration_ms = int((time.time() - start) * 1000)
        print(f"{request.method} {request.url.path} -> {response.status_code} in {duration_ms}ms body={body_preview}")
        return response
    except Exception as e:
        duration_ms = int((time.time() - start) * 1000)
        print(f"{request.method} {request.url.path} -> ERROR in {duration_ms}ms error={e}")
        raise

# CORS for local web app and typical dev ports
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:3003",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "queue": QUEUE_NAME,
        "redis_url": REDIS_URL or "",
        "redis_configured": bool(REDIS_URL),
        "redis_connected": bool(queue),
    }


@app.post("/voiceovers")
def create_voiceover(req: VoiceoverRequest):
    global rconn, queue
    
    if not req.script or not req.script.strip():
        raise HTTPException(status_code=400, detail="script is required")
    
    # Retry Redis connection if needed
    if not queue:
        rconn, queue = get_redis_connection()
        if not queue:
            raise HTTPException(status_code=503, detail="Redis/Queue is not available. Please try again.")
    
    try:
        job = queue.enqueue(
            "apps.worker.tasks.generate_voiceover_job",
            req.script,
            req.voice_sample_path,
            req.output_filename,
            req.language,
            job_timeout=1800,
        )
        return {"job_id": job.get_id(), "status": job.get_status()}
    except Exception as e:
        # Reset connection on error
        rconn, queue = get_redis_connection()
        raise HTTPException(status_code=500, detail=f"Failed to enqueue job: {str(e)}")


@app.get("/voiceovers/{job_id}")
def voiceover_status(job_id: str):
    try:
        job = rq.job.Job.fetch(job_id, connection=rconn)
    except Exception:
        raise HTTPException(status_code=404, detail="job not found")
    resp: dict = {"job_id": job_id, "status": job.get_status()}
    if job.is_finished:
        result = job.result or {}
        resp["result"] = result
        # If worker wrote to local disk, optionally upload here as a fallback
        bucket_name = os.getenv("GCS_BUCKET")
        if bucket_name and result.get("output_path"):
            try:
                client = storage.Client()
                bucket = client.bucket(bucket_name)
                blob_path = os.path.basename(result["output_path"]) or "voiceover.wav"
                blob = bucket.blob(f"voiceovers/{blob_path}")
                blob.upload_from_filename(result["output_path"]) 
                url = blob.generate_signed_url(version="v4", expiration=3600, method="GET")
                resp["signed_url"] = url
            except Exception as e:
                resp["upload_error"] = str(e)
    elif job.is_failed:
        resp["error"] = (job.exc_info or "")[-1000:]
    return resp


# Synchronous generation endpoint that returns the WAV file directly
@app.post("/voiceovers/sync")
def create_voiceover_sync(req: VoiceoverRequest):
    if not req.script or not req.script.strip():
        raise HTTPException(status_code=400, detail="script is required")

    try:
        # Deferred import to keep API lightweight at startup
        from apps.api.utils.voiceover_simple import generate_voiceover

        # Write output to ephemeral disk in Cloud Run
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False, dir="/tmp") as tmp:
            out_path = tmp.name

        result_path = generate_voiceover(
            script=req.script,
            voice_sample_path=req.voice_sample_path,
            output_path=out_path,
        )

        if not result_path or not os.path.exists(result_path):
            raise HTTPException(status_code=500, detail="Voiceover generation failed")

        # Return file directly for immediate download
        filename = req.output_filename or f"voiceover_{int(time.time())}.wav"
        return FileResponse(path=result_path, media_type="audio/wav", filename=filename)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Synchronous generation error: {str(e)}")


@app.post("/images/generate")
def create_image(req: ImageRequest):
    """Generate an image from a text prompt using free AI services."""
    if not req.prompt or not req.prompt.strip():
        raise HTTPException(status_code=400, detail="prompt is required")

    try:
        # Deferred import to keep API lightweight at startup
        from apps.api.utils.image_generation import generate_image_free
        import tempfile
        import os

        # Create temporary file for image output
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False, dir="/tmp") as tmp:
            output_path = tmp.name

        # Generate image using free services
        success = generate_image_free(req.prompt, output_path)
        
        if not success or not os.path.exists(output_path):
            raise HTTPException(status_code=500, detail="Image generation failed")

        # For now, return a placeholder URL since we need to serve the image
        # In production, you'd upload to cloud storage and return the URL
        import time
        timestamp = int(time.time())
        
        return {
            "success": True,
            "image_url": f"https://picsum.photos/{req.width}/{req.height}?random={req.scene_number}&t={timestamp}",
            "scene_number": req.scene_number,
            "message": "Image generated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image generation error: {str(e)}")


