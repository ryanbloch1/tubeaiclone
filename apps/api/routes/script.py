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
    Generate a script using Gemini AI and save to Supabase.
    
    Flow:
    1. Verify user owns the project
    2. Generate script using Gemini
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
    
    # 2. Generate script using Gemini (delegated to service)
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
            web_data=request.web_data
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
    
    # 3. Save script to database
    try:
        script_result = supabase.table('scripts').insert({
            'project_id': request.project_id,
            'raw_script': script_content,
            'edited_script': script_content,
            'sanitized_script': script_content
        }).execute()
        
        script_id = script_result.data[0]['id']
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save script: {str(e)}"
        )
    
    # 4. Update project status and settings
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
    
    # 5. Return response
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
    
    # Verify user owns this script
    try:
        script_result = supabase.table('scripts') \
            .select('*') \
            .eq('id', script_id) \
            .eq('user_id', user_id) \
            .single() \
            .execute()
        
        if not script_result.data:
            raise HTTPException(status_code=404, detail="Script not found")
            
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

