import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import redis
import rq

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
QUEUE_NAME = os.getenv("QUEUE_NAME", "voiceovers")

rconn = redis.from_url(REDIS_URL)
queue = rq.Queue(QUEUE_NAME, connection=rconn)


class VoiceoverRequest(BaseModel):
    script: str
    voice_sample_path: str | None = None
    output_filename: str | None = None
    language: str | None = "en"


app = FastAPI(title="TubeAI API", version="0.1.0")


@app.get("/health")
def health():
    return {"status": "ok", "queue": QUEUE_NAME, "redis": REDIS_URL}


@app.post("/voiceovers")
def create_voiceover(req: VoiceoverRequest):
    if not req.script or not req.script.strip():
        raise HTTPException(status_code=400, detail="script is required")
    job = queue.enqueue(
        "worker.tasks.generate_voiceover_job",
        req.script,
        req.voice_sample_path,
        req.output_filename,
        req.language,
        job_timeout=1800,
    )
    return {"job_id": job.get_id(), "status": job.get_status()}


@app.get("/voiceovers/{job_id}")
def voiceover_status(job_id: str):
    try:
        job = rq.job.Job.fetch(job_id, connection=rconn)
    except Exception:
        raise HTTPException(status_code=404, detail="job not found")
    resp: dict = {"job_id": job_id, "status": job.get_status()}
    if job.is_finished:
        resp["result"] = job.result
    elif job.is_failed:
        resp["error"] = (job.exc_info or "")[-1000:]
    return resp


