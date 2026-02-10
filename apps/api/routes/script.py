"""
Script generation endpoints with Supabase integration
"""

import os
from typing import Optional, Literal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from auth.verify import verify_token_async
from db.client import get_supabase

router = APIRouter(prefix="/api/script", tags=["script"])


class ScriptGenerationRequest(BaseModel):
    """Request model for script generation"""
    project_id: str = Field(..., description="Project ID to associate script with")
    topic: str = Field(..., min_length=1, max_length=500, description="Video topic/title")
    style_name: Optional[str] = Field(None, description="Style/tone for the script")
    mode: Literal['script', 'outline', 'rewrite'] = Field('script', description="Generation mode")
    temperature: float = Field(0.7, ge=0.0, le=1.0, description="AI creativity level")
    word_count: int = Field(500, ge=50, le=5000, description="Target word count")
    image_count: int = Field(10, ge=1, le=20, description="Number of scenes")
    selection: Optional[str] = Field(None, description="Text selection for rewrite mode")
    context_mode: Optional[Literal['default', 'video', 'web']] = Field('default')
    transcript: Optional[str] = Field(None, description="Video transcript for context")
    web_data: Optional[str] = Field(None, description="Web research data for context")
    # Real estate fields
    video_type: Optional[Literal['listing', 'neighborhood_guide', 'market_update']] = Field(None)
    property_address: Optional[str] = Field(None)
    property_type: Optional[str] = Field(None)
    property_price: Optional[float] = Field(None)
    bedrooms: Optional[int] = Field(None)
    bathrooms: Optional[float] = Field(None)
    square_feet: Optional[int] = Field(None)
    mls_number: Optional[str] = Field(None)
    property_features: Optional[list[str]] = Field(None)
    model_provider: Optional[Literal['auto', 'groq', 'gemini', 'openai', 'anthropic']] = Field('auto')
    model_name: Optional[str] = Field(None, description="Provider-specific model name override")


class ScriptGenerationResponse(BaseModel):
    """Response model for script generation"""
    success: bool
    script_id: str
    content: str
    mode: str
    image_count: int


@router.post("/generate", response_model=ScriptGenerationResponse)
async def generate_script(
    request: ScriptGenerationRequest,
    user_id: str = Depends(verify_token_async)
):
    """
    Generate a script using the selected AI provider and save to Supabase.
    
    Flow:
    1. Verify user owns the project
    2. Generate script using selected provider/model
    3. Save to database
    4. Update project status
    5. Return script content and ID
    """
    supabase = get_supabase()
    
    # 1. Verify user owns this project
    try:
        project_result = supabase.table('projects') \
            .select('*') \
            .eq('id', request.project_id) \
            .eq('user_id', user_id) \
            .single() \
            .execute()
        
        if not project_result.data:
            raise HTTPException(status_code=404, detail="Project not found or access denied")
            
        project = project_result.data
        
    except Exception as e:
        if "404" in str(e):
            raise HTTPException(status_code=404, detail="Project not found")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    # 2. Collect analysed photos for this project (images-first flow)
    photos: list[dict] = []
    analysed_count = 0
    uploaded_count = 0
    try:
        # Prefer project-level uploaded photos (no scenes needed yet), ordered by sort_index then created_at
        images_res = (
            supabase.table("images")
            .select("id, source_type, photo_analysis, sort_index, created_at")
            .eq("project_id", request.project_id)
            .eq("source_type", "uploaded")
            .order("sort_index", desc=False)
            .order("created_at", desc=False)
            .execute()
        )
        if images_res.data:
            for img in images_res.data:
                uploaded_count += 1
                pa = img.get("photo_analysis")
                if pa and isinstance(pa, dict):
                    analysed_count += 1
                    photos.append(
                        {
                            "id": img["id"],
                            "scene_type": pa.get("scene_type"),
                            "caption": pa.get("caption"),
                            "features": pa.get("features") or [],
                        }
                    )
    except Exception as e:
        # Photo grounding is best-effort; errors here should not block script generation
        print(f"[SCRIPT] Failed to load project-level photo analysis for grounding: {e}")

    # Enforce a minimum analysed photo count once the user has started uploading photos
    min_analysed_photos = int(os.getenv("MIN_ANALYSED_PHOTOS", "5"))
    if uploaded_count > 0 and analysed_count < min_analysed_photos:
        raise HTTPException(
            status_code=400,
            detail=(
                f"At least {min_analysed_photos} uploaded photos with analysis are required "
                f"before generating a photo-grounded script. Currently analysed: {analysed_count}."
            ),
        )

    # For now, first script uses project-level photos in upload order (one scene per photo).
    # If no photos exist, photos list will be empty and the script falls back to non-photo template.

    # 3. Generate script using selected provider/model (delegated to service)
    try:
        from services.script_generation import generate_script_with_gemini
        
        script_content = await generate_script_with_gemini(
            topic=request.topic,
            style_name=request.style_name,
            mode=request.mode,
            temperature=request.temperature,
            word_count=request.word_count,
            image_count=request.image_count,
            selection=request.selection,
            context_mode=request.context_mode,
            transcript=request.transcript,
            web_data=request.web_data,
            # Real estate fields
            video_type=request.video_type,
            property_address=request.property_address,
            property_type=request.property_type,
            property_price=request.property_price,
            bedrooms=request.bedrooms,
            bathrooms=request.bathrooms,
            square_feet=request.square_feet,
            mls_number=request.mls_number,
            property_features=request.property_features,
            model_provider=request.model_provider,
            model_name=request.model_name,
            photos=photos or None,
        )
        
    except ImportError:
        raise HTTPException(
            status_code=501,
            detail="Script generation service not available"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Script generation failed: {str(e)}"
        )
    
    # 3. Build a scene->photo mapping for later use (one scene per photo in order)
    scene_photo_map = None
    if photos:
        scene_photo_map = [
            {"scene_number": idx + 1, "image_id": p["id"]}
            for idx, p in enumerate(photos)
        ]

    # 4. Save script to database
    try:
        script_result = supabase.table('scripts').insert({
            'project_id': request.project_id,
            'raw_script': script_content,
            'edited_script': script_content,
            'sanitized_script': script_content,
            'scene_photo_map': scene_photo_map
        }).execute()
        
        script_id = script_result.data[0]['id']
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save script: {str(e)}"
        )
    
    # 5. If we have project-level photos but no scenes yet, create scenes and link photos
    if photos:
        try:
            # Create basic scenes in order and link each photo to its scene
            scene_id_map: dict[int, str] = {}
            for idx, p in enumerate(photos):
                scene_number = idx + 1
                # Create scene with a generic description for now
                scene_result = (
                    supabase.table("scenes")
                    .insert(
                        {
                            "script_id": script_id,
                            "scene_number": scene_number,
                            "description": f"Scene {scene_number} - Photo-based scene",
                        }
                    )
                    .execute()
                )
                if scene_result.data:
                    scene_id = scene_result.data[0]["id"]
                    scene_id_map[scene_number] = scene_id
                    # Link all images with this id (project-level photos) to the new scene
                    supabase.table("images").update(
                        {"scene_id": scene_id}
                    ).eq("id", p["id"]).execute()
        except Exception as e:
            # Non-critical; log and continue
            print(f"Warning: Failed to create scenes or link photos: {e}")

    # 6. Update project status and settings
    try:
        supabase.table('projects').update({
            'status': 'script',
            'topic': request.topic,
            'style': request.style_name,
            'mode': request.mode,
            'temperature': request.temperature,
            'word_count': request.word_count,
            'image_count': request.image_count
        }).eq('id', request.project_id).execute()
        
    except Exception as e:
        # Non-critical error, log but don't fail
        print(f"Warning: Failed to update project: {str(e)}")
    
    # 7. Return response
    return {
        "success": True,
        "script_id": script_id,
        "content": script_content,
        "mode": request.mode,
        "image_count": request.image_count
    }


class ScriptUpdateRequest(BaseModel):
    edited_content: str = Field(..., description="Edited script content")

@router.put("/{script_id}", response_model=dict)
async def update_script(
    script_id: str,
    request: ScriptUpdateRequest,
    user_id: str = Depends(verify_token_async)
):
    """
    Update an existing script's edited content.
    """
    supabase = get_supabase()
    
    # Verify user owns this script via project ownership
    try:
        script_result = (
            supabase.table("scripts")
            .select("id, project_id, projects!inner(user_id)")
            .eq("id", script_id)
            .single()
            .execute()
        )
        
        if not script_result.data:
            raise HTTPException(status_code=404, detail="Script not found")

        project = script_result.data.get("projects") or {}
        if project.get("user_id") != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
            
    except Exception as e:
        if "404" in str(e):
            raise HTTPException(status_code=404, detail="Script not found")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    # Update script
    try:
        update_result = supabase.table('scripts').update({
            'edited_script': request.edited_content
        }).eq('id', script_id).execute()
        
        return {
            "success": True,
            "script_id": script_id,
            "message": "Script updated successfully"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update script: {str(e)}"
        )
