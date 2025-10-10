import base64
import io
import os
import time

try:
    # Load environment variables from a .env file
    from dotenv import find_dotenv, load_dotenv
    load_dotenv(find_dotenv(), override=True)
except ImportError:
    # python-dotenv not installed
    pass
except Exception as e:
    print(f"Error loading .env file: {e}")

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from PIL import Image
from pydantic import BaseModel, Field, validator

# Constants and configuration
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3002",
    "http://localhost:3003",
]

# Global pipeline cache for Stable Diffusion
_sd_pipeline = None
_sd_model_id = None

app = FastAPI(title="TubeAI API", version="0.1.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers for new Supabase-integrated endpoints
try:
    from routes.script import router as script_router
    app.include_router(script_router)
    print("✅ Loaded Supabase-integrated routes")
except ImportError as e:
    print(f"⚠️  Supabase routes not available: {e}")


class ImageRequest(BaseModel):
    """Request model for image generation."""
    prompt: str = Field(..., min_length=1, description="Text prompt for image generation")
    scene_number: int = Field(..., ge=1, description="Scene number for sequencing")
    width: int = Field(512, ge=64, le=1024, description="Image width in pixels")
    height: int = Field(512, ge=64, le=1024, description="Image height in pixels")
    
    @validator('prompt')
    def prompt_not_empty(cls, v):
        """Validate that prompt is not empty."""
        if not v.strip():
            raise ValueError('prompt cannot be empty')
        return v.strip()


class SDImageRequest(BaseModel):
    """Request model for Stable Diffusion image generation."""
    prompt: str = Field(..., min_length=1, description="Text prompt for image generation")
    scene_number: int | None = Field(None, ge=1, description="Scene number for sequencing")
    width: int = Field(512, ge=64, le=1024, description="Image width in pixels")
    height: int = Field(512, ge=64, le=1024, description="Image height in pixels")
    model_id: str | None = Field(
        None, description="Stable Diffusion model ID to override default"
    )
    num_inference_steps: int | None = Field(
        30, ge=1, le=100, description="Number of inference steps"
    )
    guidance_scale: float | None = Field(
        7.5, ge=1.0, le=20.0, description="Guidance scale for generation"
    )
    
    @validator('prompt')
    def prompt_not_empty(cls, v):
        """Validate that prompt is not empty."""
        if not v.strip():
            raise ValueError('prompt cannot be empty')
        return v.strip()


def get_sd_pipeline(model_id: str):
    """
    Get or create a cached Stable Diffusion pipeline.
    
    Args:
        model_id: The model identifier to load
        
    Returns:
        Loaded Stable Diffusion pipeline
    """
    global _sd_pipeline, _sd_model_id
    
    if _sd_pipeline is None or _sd_model_id != model_id:
        # Deferred imports to keep API startup light
        from diffusers import StableDiffusionPipeline
        import torch
        
        # Auto-detect best available device
        if torch.cuda.is_available():
            device = "cuda"
            dtype = torch.float16
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            device = "mps"
            dtype = torch.float32
        else:
            device = "cpu"
            dtype = torch.float32
        
        print(f"Loading SD pipeline: {model_id} on {device}")
        _sd_pipeline = StableDiffusionPipeline.from_pretrained(model_id, torch_dtype=dtype)
        _sd_pipeline = _sd_pipeline.to(device)
        _sd_model_id = model_id
        print("SD pipeline loaded successfully")
    
    return _sd_pipeline


@app.post("/images/generate")
async def create_image(req: ImageRequest):
    """
    Generate an image from a text prompt using free AI services.
    
    Args:
        req: ImageRequest containing prompt and generation parameters
        
    Returns:
        JSON response with image URL and generation details
    """
    try:
        # Deferred import to keep API lightweight at startup
        import tempfile
        from .utils.image_generation import generate_image_free

        # Create temporary file for image output
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False, dir="/tmp")
        output_path = tmp.name
        tmp.close()

        # Generate image using free services
        success = generate_image_free(req.prompt, output_path)

        if not success or not os.path.exists(output_path):
            raise HTTPException(status_code=500, detail="Image generation failed")

        # For now, return a placeholder URL since we need to serve the image
        # In production, you'd upload to cloud storage and return the URL
        timestamp = int(time.time())

        return {
            "success": True,
            "image_url": f"https://picsum.photos/{req.width}/{req.height}?random={req.scene_number}&t={timestamp}",
            "scene_number": req.scene_number,
            "message": "Image generated successfully",
        }

    except HTTPException:
        raise
    except ImportError:
        raise HTTPException(
            status_code=501, 
            detail="Image generation module not available"
        ) from None
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Image generation error: {str(e)}"
        ) from e


@app.post("/images/sd/generate")
async def generate_image_sd(req: SDImageRequest):
    """
    Generate an image using Stable Diffusion.
    
    Args:
        req: SDImageRequest containing prompt and generation parameters
        
    Returns:
        JSON response with base64-encoded image and generation details
    """
    try:
        model_default = os.getenv("IMAGE_SD_MODEL", "stabilityai/stable-diffusion-2-1-base")
        model_id = req.model_id or model_default

        # Get cached pipeline
        pipe = get_sd_pipeline(model_id)

        steps = req.num_inference_steps or 30
        guidance = req.guidance_scale or 7.5

        print(f"Generating image with prompt: {req.prompt[:50]}...")
        image: Image.Image = pipe(
            req.prompt,
            num_inference_steps=steps,
            guidance_scale=guidance,
            height=req.height,
            width=req.width,
        ).images[0]

        # Convert image to base64
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        buf.seek(0)
        b64 = base64.b64encode(buf.read()).decode("utf-8")
        data_url = f"data:image/png;base64,{b64}"

        return JSONResponse(
            {
                "success": True,
                "image_url": data_url,
                "scene_number": req.scene_number or 0,
                "model_id": model_id,
                "dimensions": f"{req.width}x{req.height}"
            }
        )
        
    except HTTPException:
        raise
    except ImportError:
        raise HTTPException(
            status_code=501, 
            detail="Stable Diffusion dependencies not installed"
        ) from None
    except Exception as e:
        print(f"SD generation error: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Stable Diffusion generation error: {str(e)}"
        ) from e


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "TubeAI API",
        "version": "0.1.0"
    }