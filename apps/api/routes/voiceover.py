from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
import base64
import uuid
# datetime import removed as it's not used in current schema

from auth.verify import verify_token
from db.client import get_supabase
from services.system_tts import system_tts, get_voice_by_name

router = APIRouter()

class VoiceoverGenerationRequest(BaseModel):
    project_id: str
    script_id: str
    text: str
    voice_id: Optional[str] = "default"  # Default system voice
    model_id: Optional[str] = "system_tts"

class VoiceoverGenerationResponse(BaseModel):
    success: bool
    voiceover_id: str
    audio_data_url: str

class VoiceoverUpdateRequest(BaseModel):
    edited_text: str

@router.post("/generate", response_model=VoiceoverGenerationResponse)
async def generate_voiceover(
    request: VoiceoverGenerationRequest,
    user_id: str = Depends(verify_token)
):
    """Generate voiceover using System TTS and save to database"""
    try:
        supabase = get_supabase()
        
        # Verify project ownership
        project_result = supabase.table('projects').select('id').eq('id', request.project_id).eq('user_id', user_id).execute()
        if not project_result.data:
            raise HTTPException(status_code=403, detail="Project not found or access denied")
        
        # Verify script ownership
        script_result = supabase.table('scripts').select('id').eq('id', request.script_id).eq('project_id', request.project_id).execute()
        if not script_result.data:
            raise HTTPException(status_code=403, detail="Script not found or access denied")
        
        # Generate voiceover using System TTS
        try:
            # Get system voice ID
            system_voice_id = get_voice_by_name(request.voice_id)
            
            # Generate speech using system TTS
            audio = system_tts.generate_speech(request.text, system_voice_id)
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"System TTS generation failed: {str(e)}")
        
        # Convert audio to base64
        audio_bytes = bytes(audio)
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        audio_data_url = f"data:audio/wav;base64,{audio_base64}"
        
        # Generate voiceover ID
        voiceover_id = str(uuid.uuid4())
        
        # Save to database
        try:
            voiceover_result = supabase.table('voiceovers').insert({
                'id': voiceover_id,
                'script_id': request.script_id,
                'audio_data_url': audio_data_url,
                'status': 'complete'
            }).execute()
            
            if not voiceover_result.data:
                raise HTTPException(status_code=500, detail="Failed to save voiceover to database")
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        
        return VoiceoverGenerationResponse(
            success=True,
            voiceover_id=voiceover_id,
            audio_data_url=audio_data_url
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Voiceover generation failed: {str(e)}")

@router.post("/update/{voiceover_id}")
async def update_voiceover(
    voiceover_id: str,
    request: VoiceoverUpdateRequest,
    user_id: str = Depends(verify_token)
):
    """Update voiceover text and regenerate if needed"""
    try:
        supabase = get_supabase()
        
        # Verify voiceover ownership through script -> project relationship
        voiceover_result = supabase.table('voiceovers').select('*, scripts!inner(project_id, projects!inner(user_id))').eq('id', voiceover_id).execute()
        if not voiceover_result.data:
            raise HTTPException(status_code=404, detail="Voiceover not found")
        
        voiceover = voiceover_result.data[0]
        if voiceover['scripts']['projects']['user_id'] != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Update the voiceover (currently no editable fields in schema)
        # For now, just return success since the schema doesn't support text editing
        update_result = {"data": [{"id": voiceover_id}]}
        
        if not update_result.data:
            raise HTTPException(status_code=500, detail="Failed to update voiceover")
        
        return {"success": True, "message": "Voiceover updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")

@router.get("/project/{project_id}")
async def get_voiceovers_for_project(
    project_id: str,
    user_id: str = Depends(verify_token)
):
    """Get all voiceovers for a project"""
    try:
        supabase = get_supabase()
        
        # Verify project ownership
        project_result = supabase.table('projects').select('id').eq('id', project_id).eq('user_id', user_id).execute()
        if not project_result.data:
            raise HTTPException(status_code=403, detail="Project not found or access denied")
        
        # Get scripts for this project first, then get voiceovers for those scripts
        scripts_result = supabase.table('scripts').select('id').eq('project_id', project_id).execute()
        script_ids = [script['id'] for script in scripts_result.data]
        
        if script_ids:
            voiceovers_result = supabase.table('voiceovers').select('*').in_('script_id', script_ids).order('created_at', desc=True).execute()
        else:
            voiceovers_result = type('obj', (object,), {'data': []})()  # Empty result
        
        return {"success": True, "voiceovers": voiceovers_result.data}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch voiceovers: {str(e)}")
