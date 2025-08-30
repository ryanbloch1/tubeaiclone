#!/usr/bin/env python3
"""
HTTP wrapper for RQ worker to run on Cloud Run.
Cloud Run requires containers to listen on HTTP, so this provides a health endpoint
while running the RQ worker in a background thread.
"""

import os
import threading
import time
from flask import Flask, jsonify
import redis
import rq

# Environment variables
REDIS_URL = os.getenv("REDIS_URL")
QUEUE_NAME = os.getenv("QUEUE_NAME", "voiceover_queue")
PORT = int(os.getenv("PORT", 8080))

app = Flask(__name__)

# Global worker status
worker_status = {
    "status": "starting",
    "jobs_processed": 0,
    "last_activity": None,
    "redis_connected": False
}

def run_worker():
    """Run the RQ worker in a background thread."""
    global worker_status
    
    if not REDIS_URL:
        worker_status["status"] = "error"
        worker_status["error"] = "REDIS_URL not configured"
        return
    
    try:
        # Connect to Redis
        rconn = redis.from_url(REDIS_URL)
        rconn.ping()  # Test connection
        worker_status["redis_connected"] = True
        
        # Create queue and worker with unique name
        queue = rq.Queue(QUEUE_NAME, connection=rconn)
        import uuid
        worker_name = f"tubeai-worker-{uuid.uuid4().hex[:8]}"
        worker = rq.Worker([queue], connection=rconn, name=worker_name)
        
        worker_status["status"] = "running"
        worker_status["last_activity"] = time.time()
        
        print(f"🚀 Worker '{worker_name}' started on queue '{QUEUE_NAME}'")
        print(f"📡 Connected to Redis: {REDIS_URL[:50]}...")
        
        # Run worker with exception handling
        while True:
            try:
                # Work with timeout to allow status updates
                job = worker.work(burst=False, with_scheduler=True)
                if job:
                    worker_status["jobs_processed"] += 1
                    worker_status["last_activity"] = time.time()
                    print(f"✅ Processed job {worker_status['jobs_processed']}")
                
            except Exception as e:
                print(f"❌ Worker error: {e}")
                worker_status["status"] = "error"
                worker_status["error"] = str(e)
                time.sleep(5)  # Wait before retrying
                
    except Exception as e:
        print(f"❌ Failed to start worker: {e}")
        worker_status["status"] = "error"
        worker_status["error"] = str(e)

@app.route('/health')
def health():
    """Health check endpoint for Cloud Run."""
    return jsonify({
        "status": "ok",
        "worker": worker_status,
        "queue": QUEUE_NAME,
        "redis_url": REDIS_URL[:50] + "..." if REDIS_URL else None,
    })

@app.route('/')
def root():
    """Root endpoint."""
    return jsonify({
        "service": "TubeAI Worker",
        "status": worker_status["status"],
        "jobs_processed": worker_status["jobs_processed"]
    })

if __name__ == "__main__":
    # Start the worker in a background thread
    worker_thread = threading.Thread(target=run_worker, daemon=True)
    worker_thread.start()
    
    print(f"🌐 Starting HTTP server on port {PORT}")
    print(f"🔧 Worker status available at /health")
    
    # Start Flask app
    app.run(host="0.0.0.0", port=PORT, debug=False)
