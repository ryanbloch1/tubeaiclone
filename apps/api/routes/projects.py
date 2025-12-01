"""
Project management endpoints (create/update, photo status) for images-first flow.
"""

import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from auth.verify import verify_token_async
from db.client import get_supabase


router = APIRouter(prefix="/api/projects", tags=["projects"])


class ProjectSaveRequest(BaseModel):
    """Create or update a project from property details without generating a script."""

    project_id: Optional[str] = Field(
        None, description="Existing project ID to update; omit to create a new project"
    )
    title: Optional[str] = Field(None, description="Project title, defaults to topic/address")
    topic: Optional[str] = Field(None, description="Video topic/title")
    style_name: Optional[str] = Field(None, description="Style/tone for the script")
    mode: Optional[str] = Field("script", description="Generation mode")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=1.0)
    word_count: Optional[int] = Field(500, ge=50, le=5000)
    image_count: Optional[int] = Field(10, ge=1, le=20)
    video_length: Optional[str] = Field("1:00")
    selection: Optional[str] = None
    extra_context: Optional[str] = None
    # Real estate fields
    video_type: Optional[str] = Field(None)
    property_address: Optional[str] = Field(None)
    property_type: Optional[str] = Field(None)
    property_price: Optional[float] = Field(None)
    bedrooms: Optional[int] = Field(None)
    bathrooms: Optional[float] = Field(None)
    square_feet: Optional[int] = Field(None)
    mls_number: Optional[str] = Field(None)
    property_features: Optional[list[str]] = Field(None)


class ProjectSaveResponse(BaseModel):
    success: bool
    project_id: str


class ProjectPhotosStatusResponse(BaseModel):
    success: bool
    project_id: str
    uploaded_count: int
    analysed_count: int
    min_required: int


@router.post("/save", response_model=ProjectSaveResponse)
async def save_project(
    request: ProjectSaveRequest,
    user_id: str = Depends(verify_token_async),
):
    """
    Create or update a project from property details only (no script generation).
    """
    supabase = get_supabase()

    title = (request.title or request.topic or request.property_address or "Untitled Project").strip()
    topic = (request.topic or request.property_address or title).strip()

    data = {
        "user_id": user_id,
        "title": title,
        "topic": topic,
        "style": request.style_name,
        "mode": request.mode or "script",
        "temperature": request.temperature,
        "word_count": request.word_count,
        "image_count": request.image_count,
        "video_length": request.video_length,
        "selection": request.selection,
        "extra_context": request.extra_context,
        # Real estate fields
        "video_type": request.video_type or "listing",
        "property_address": request.property_address,
        "property_type": request.property_type,
        "property_price": request.property_price,
        "bedrooms": request.bedrooms,
        "bathrooms": request.bathrooms,
        "square_feet": request.square_feet,
        "mls_number": request.mls_number,
        "property_features": (
            request.property_features if request.property_features is None else request.property_features
        ),
    }

    try:
        if request.project_id:
            # Update existing project (owned by user)
            result = (
                supabase.table("projects")
                .update(data)
                .eq("id", request.project_id)
                .eq("user_id", user_id)
                .execute()
            )
            if not result.data:
                raise HTTPException(status_code=404, detail="Project not found or access denied")
            project_id = result.data[0]["id"]
        else:
            # Create new project
            result = supabase.table("projects").insert(data).execute()
            if not result.data:
                raise HTTPException(status_code=500, detail="Failed to create project")
            project_id = result.data[0]["id"]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save project: {e}") from e

    return ProjectSaveResponse(success=True, project_id=project_id)


@router.get("/{project_id}/photos-status", response_model=ProjectPhotosStatusResponse)
async def project_photos_status(
    project_id: str,
    user_id: str = Depends(verify_token_async),
):
    """
    Return how many uploaded photos a project has and how many are analysed.
    Used to gate script generation on the frontend.
    """
    supabase = get_supabase()

    # Verify user owns the project
    try:
        project_res = (
            supabase.table("projects")
            .select("id, user_id")
            .eq("id", project_id)
            .eq("user_id", user_id)
            .single()
            .execute()
        )
        if not project_res.data:
            raise HTTPException(status_code=404, detail="Project not found or access denied")
    except Exception as e:
        # .single() raises if no results found
        raise HTTPException(status_code=404, detail="Project not found or access denied") from e

    try:
        images_res = (
            supabase.table("images")
            .select("id, source_type, photo_analysis")
            .eq("project_id", project_id)
            .eq("source_type", "uploaded")
            .execute()
        )
    except Exception as e:
        print(f"[PHOTOS_STATUS] Error loading photos: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to load project photos: {e}") from e

    uploaded_count = 0
    analysed_count = 0
    if images_res.data:
        for img in images_res.data:
            uploaded_count += 1
            if img.get("photo_analysis"):
                analysed_count += 1

    min_required = int(os.getenv("MIN_ANALYSED_PHOTOS", "5"))

    return ProjectPhotosStatusResponse(
        success=True,
        project_id=project_id,
        uploaded_count=uploaded_count,
        analysed_count=analysed_count,
        min_required=min_required,
    )


