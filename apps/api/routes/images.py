from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import base64
import uuid
import re
import os
import json
import asyncio

from auth.verify import verify_token
from db.client import get_supabase

router = APIRouter()


class ImageGenerateRequest(BaseModel):
    project_id: str
    script_id: Optional[str] = None
    prompt: Optional[str] = None
    num_images: int = 4
    style_name: Optional[str] = None

class ImageRegenerateRequest(BaseModel):
    image_id: str
    prompt: Optional[str] = None


def _parse_scenes_from_script(script_text: str) -> List[dict]:
    """Parse script into scenes and extract visual descriptions."""
    scenes = []
    lines = script_text.split('\n')
    current_scene = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Match "Scene X" pattern
        scene_match = re.match(r'^Scene\s+(\d+)', line, re.IGNORECASE)
        if scene_match:
            if current_scene:
                scenes.append(current_scene)
            scene_num = int(scene_match.group(1))
            current_scene = {
                'scene_number': scene_num,
                'text': line,
                'visuals': None,
                'content': [],
                'narration': None
            }
        elif current_scene:
            # Look for "**Visuals:**" or "Visuals:" line
            visuals_match = re.match(r'\*\*?Visuals?\*\*?:\s*(.+)', line, re.IGNORECASE)
            if visuals_match:
                # Extract visual description (remove the label)
                visuals_text = visuals_match.group(1).strip()
                current_scene['visuals'] = visuals_text
            # Look for "**Content/Narration:**" or "Content/Narration:" line
            elif re.match(r'\*\*?Content[/\\]Narration\*\*?:\s*(.+)', line, re.IGNORECASE):
                narration_match = re.match(r'\*\*?Content[/\\]Narration\*\*?:\s*(.+)', line, re.IGNORECASE)
                if narration_match:
                    narration_text = narration_match.group(1).strip()
                    current_scene['narration'] = narration_text
            elif current_scene['visuals'] is None:
                # Accumulate content until we find visuals
                current_scene['content'].append(line)
                current_scene['text'] += '\n' + line
    
    if current_scene:
        scenes.append(current_scene)
    
    return scenes


def _clean_text(text: str) -> str:
    """Remove markdown formatting and clean up text."""
    if not text:
        return ""
    # Remove markdown bold markers
    text = re.sub(r'\*\*([^*]+)\*\*:', r'\1:', text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    # Remove other markdown
    text = re.sub(r'^\*\s*', '', text, flags=re.MULTILINE)
    # Clean up whitespace
    text = ' '.join(text.split())
    return text.strip()

STYLE_PROMPT_MAP = {
    'Photorealistic': 'Photorealistic cinematic lighting, ultra-detailed, DSLR quality',
    'Comic Book': 'Bold comic book illustration, ink outlines, vibrant cel-shading',
    'Studio Ghibli': 'Studio Ghibli inspired animation, painterly backgrounds, whimsical atmosphere',
    'Cyberpunk Neon': 'Cyberpunk neon aesthetic, glowing city lights, high contrast futuristic styling',
    'Watercolor Storybook': 'Soft watercolor storybook illustration, gentle hues, textured paper feel',
}


def _apply_style_to_prompt(style_name: Optional[str], prompt: str) -> str:
    style_key = (style_name or 'Photorealistic').strip() or 'Photorealistic'
    descriptor = STYLE_PROMPT_MAP.get(style_key, style_key)
    return f"{descriptor}. {prompt}"


def _generate_image_prompt_for_scene(scene: dict, use_ai: bool = False) -> str:
    """Generate an image generation prompt for a scene."""
    # If visuals are explicitly provided, use them
    if scene.get('visuals'):
        visuals = scene['visuals']
        # Clean up markdown formatting
        visuals = _clean_text(visuals)
        # Enhance with AI if requested and API key available
        if use_ai:
            try:
                from google import generativeai as genai
                api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
                if api_key and api_key not in ['your_api_key_here', 'YOUR_KEY_HERE']:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-2.0-flash-exp')
                    prompt = f"""Convert this video scene description into a detailed, cinematic image generation prompt. 
Focus on composition, lighting, mood, and visual details. Make it suitable for AI image generation.

Scene description: {visuals}

Return only the enhanced prompt, nothing else."""
                    response = model.generate_content(prompt)
                    return response.text.strip()
            except Exception as e:
                print(f"AI prompt generation failed, using raw visuals: {e}")
        return visuals
    
    # Fallback: use narration if available, otherwise content
    if scene.get('narration'):
        narration = _clean_text(scene['narration'])
        return narration if narration else f"Scene {scene['scene_number']}"
    
    if scene.get('content'):
        # Extract narration from content if it contains "Content/Narration"
        content_text = ' '.join(scene['content'])
        narration_match = re.search(r'\*\*?Content[/\\]Narration\*\*?:\s*(.+?)(?:\*\*Visuals?\*\*?:|$)', content_text, re.IGNORECASE | re.DOTALL)
        if narration_match:
            narration = _clean_text(narration_match.group(1))
            return narration if narration else f"Scene {scene['scene_number']}"
        
        # Otherwise use first part of content
        content_preview = ' '.join(scene['content'][:2])[:100]
        content_preview = _clean_text(content_preview)
        return f"Scene {scene['scene_number']}: {content_preview}"
    
    return f"Scene {scene['scene_number']}"


def _svg_data_url(text: str, width: int = 1024, height: int = 576) -> str:
    # Lightweight placeholder: SVG with text, no external deps
    safe_text = (text or "").replace("<", "&lt;").replace(">", "&gt;")[:120]
    svg = f"""
<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}'>
  <defs>
    <linearGradient id='g' x1='0' y1='0' x2='1' y2='1'>
      <stop offset='0%' stop-color='#0ea5e9'/>
      <stop offset='100%' stop-color='#22c55e'/>
    </linearGradient>
  </defs>
  <rect width='100%' height='100%' fill='url(#g)'/>
  <text x='50%' y='50%' dominant-baseline='middle' text-anchor='middle'
        font-family='Arial, Helvetica, sans-serif' font-size='36' fill='white'
        style='paint-order: stroke; stroke: rgba(0,0,0,0.35); stroke-width: 3px;'>
    {safe_text or 'Generated Image'}
  </text>
  <text x='50%' y='{height - 22}' dominant-baseline='middle' text-anchor='middle'
        font-family='Arial, Helvetica, sans-serif' font-size='16' fill='rgba(255,255,255,0.9)'>
    TubeAI Placeholder
  </text>
  </svg>
""".strip()
    encoded = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
    return f"data:image/svg+xml;base64,{encoded}"


@router.post("/generate")
async def generate_images(req: ImageGenerateRequest, user_id: str = Depends(verify_token)):
    try:
        supabase = get_supabase()

        # Verify project ownership
        project_result = supabase.table('projects').select('id, style').eq('id', req.project_id).eq('user_id', user_id).execute()
        if not project_result.data:
            raise HTTPException(status_code=403, detail="Project not found or access denied")
        
        project_style = project_result.data[0].get('style') if project_result.data else None
        style_source = req.style_name or project_style or 'Photorealistic'
        style_name = style_source.strip() if isinstance(style_source, str) else 'Photorealistic'

        # If script_id not provided, pick the latest script for the project
        script_id = req.script_id
        script_text = None
        if not script_id:
            script_res = (
                supabase.table('scripts')
                .select('id, created_at')
                .eq('project_id', req.project_id)
                .order('created_at', desc=True)
                .limit(1)
                .execute()
            )
            if not script_res.data:
                raise HTTPException(status_code=400, detail="No script found for this project")
            script_id = script_res.data[0]['id']

        # Fetch the script content
        script_data = (
            supabase.table('scripts')
            .select('raw_script, edited_script')
            .eq('id', script_id)
            .single()
            .execute()
        )
        
        if script_data.data:
            # Use edited_script if available, otherwise raw_script
            script_text = script_data.data.get('edited_script') or script_data.data.get('raw_script')
        
        if not script_text:
            raise HTTPException(status_code=400, detail="Script content not found")

        # Parse script into scenes
        print(f"Parsing script (length: {len(script_text)}) into scenes...")
        parsed_scenes = _parse_scenes_from_script(script_text)
        print(f"Parsed {len(parsed_scenes)} scenes from script")
        
        if not parsed_scenes:
            # Fallback: if no scenes found, create scenes based on num_images
            print(f"No scenes parsed from script, using fallback with {req.num_images} images")
            num = max(1, min(12, int(req.num_images) if req.num_images else 8))
            parsed_scenes = [{'scene_number': i+1, 'visuals': req.prompt or f"Scene {i+1}", 'text': f"Scene {i+1}", 'content': []} for i in range(num)]
        
        # Create scenes in database and collect scene_ids
        scene_id_map = {}  # Maps scene_number -> scene_id
        use_ai_enhancement = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        
        for scene_data in parsed_scenes:
            scene_num = scene_data.get('scene_number')
            scene_desc = scene_data.get('text', f"Scene {scene_num}")
            
            # Check if scene already exists
            existing_scene = (
                supabase.table('scenes')
                .select('id')
                .eq('script_id', script_id)
                .eq('scene_number', scene_num)
                .limit(1)
                .execute()
            )
            
            if existing_scene.data and len(existing_scene.data) > 0:
                scene_id_map[scene_num] = existing_scene.data[0]['id']
            else:
                # Create new scene
                new_scene = (
                    supabase.table('scenes')
                    .insert({
                        'script_id': script_id,
                        'scene_number': scene_num,
                        'description': scene_desc
                    })
                    .execute()
                )
                if new_scene.data:
                    scene_id_map[scene_num] = new_scene.data[0]['id']
                else:
                    print(f"Failed to create scene {scene_num}")
                    continue
        
        if not scene_id_map:
            raise HTTPException(status_code=400, detail="No scenes created")
        
        # Generate images for each scene and yield them as they're created
        async def generate_and_stream():
            transformed_images = []
            
            for scene_data in parsed_scenes:
                scene_num = scene_data.get('scene_number')
                if scene_num not in scene_id_map:
                    continue
                    
                scene_id = scene_id_map[scene_num]
                
                # Generate prompt for this scene (for image generation)
                image_prompt = _generate_image_prompt_for_scene(
                    scene_data, 
                    use_ai=bool(use_ai_enhancement and use_ai_enhancement not in ['your_api_key_here', 'YOUR_KEY_HERE'])
                )
                styled_prompt = _apply_style_to_prompt(style_name, image_prompt)
                
                # Extract clean narration text for display
                display_text = None
                if scene_data.get('narration'):
                    display_text = _clean_text(scene_data['narration'])
                elif scene_data.get('content'):
                    # Try to extract narration from content
                    content_text = ' '.join(scene_data['content'])
                    narration_match = re.search(r'\*\*?Content[/\\]Narration\*\*?:\s*(.+?)(?:\*\*Visuals?\*\*?:|$)', content_text, re.IGNORECASE | re.DOTALL)
                    if narration_match:
                        display_text = _clean_text(narration_match.group(1))
                    else:
                        # Fallback: use first part of content, cleaned
                        display_text = _clean_text(' '.join(scene_data['content'][:2])[:150])
                
                img_id = str(uuid.uuid4())
                
                # Generate image using Stable Diffusion (same approach as main.py)
                data_url = None
                try:
                    from PIL import Image
                    import io
                    
                    # Use the same SD model as main.py
                    sd_model = os.getenv("IMAGE_SD_MODEL", "stabilityai/stable-diffusion-2-1-base")
                    
                    try:
                        # Import SD components (same as main.py)
                        from diffusers import StableDiffusionPipeline
                        import torch
                        
                        print(f"Generating image for scene {scene_num} with prompt: {styled_prompt[:50]}...")
                        
                        # Use a module-level cache (similar to main.py's global cache)
                        global _sd_pipeline_cache, _sd_model_cache
                        if '_sd_pipeline_cache' not in globals():
                            _sd_pipeline_cache = None
                            _sd_model_cache = None
                        
                        # Get or create pipeline (same logic as main.py)
                        if _sd_pipeline_cache is None or _sd_model_cache != sd_model:
                            # Auto-detect device (same as main.py)
                            if torch.cuda.is_available():
                                device = "cuda"
                                dtype = torch.float16
                            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                                device = "mps"
                                dtype = torch.float32
                            else:
                                device = "cpu"
                                dtype = torch.float32
                            
                            print(f"Loading SD pipeline: {sd_model} on {device}")
                            _sd_pipeline_cache = StableDiffusionPipeline.from_pretrained(sd_model, torch_dtype=dtype)
                            _sd_pipeline_cache = _sd_pipeline_cache.to(device)
                            _sd_model_cache = sd_model
                            print("SD pipeline loaded successfully")
                        
                        pipe = _sd_pipeline_cache
                        
                        # Generate image (same parameters as /images/sd/generate endpoint)
                        image: Image.Image = pipe(
                            styled_prompt,
                            num_inference_steps=30,
                            guidance_scale=7.5,
                            height=512,
                            width=512,
                        ).images[0]
                        
                        # Convert to base64 (same as main.py)
                        buf = io.BytesIO()
                        image.save(buf, format="PNG")
                        buf.seek(0)
                        b64 = base64.b64encode(buf.read()).decode("utf-8")
                        data_url = f"data:image/png;base64,{b64}"
                        print(f"Successfully generated image for scene {scene_num}")
                        
                    except ImportError as ie:
                        print(f"SD dependencies not installed: {ie}")
                        print(f"  Install with: pip install diffusers torch")
                        data_url = None
                    except Exception as e:
                        print(f"SD generation error for scene {scene_num}: {str(e)}")
                        import traceback
                        traceback.print_exc()
                        data_url = None
                            
                except Exception as e:
                    print(f"Failed to generate image for scene {scene_num}: {str(e)}")
                    data_url = None
                
                # Use placeholder if real generation failed (this runs regardless of exceptions)
                if not data_url:
                    data_url = _svg_data_url(styled_prompt)
                
                # Save image to database immediately (this always runs, outside try/except)
                image_row = {
                    'id': img_id,
                    'scene_id': scene_id,
                    'prompt_text': styled_prompt,  # Store image generation prompt with style
                    'image_data': data_url,
                    'status': 'completed'
                }
                
                insert_res = supabase.table('images').insert(image_row).execute()
                if insert_res.data:
                    inserted_img = insert_res.data[0]
                    # Get scene_number
                    scene_num_found = None
                    for num, sid in scene_id_map.items():
                        if sid == inserted_img.get('scene_id'):
                            scene_num_found = num
                            break
                    
                    transformed_img = {
                        'id': inserted_img['id'],
                        'scene_id': inserted_img.get('scene_id'),
                        'image_data_url': inserted_img.get('image_data'),
                        'prompt': display_text or image_prompt,  # Use clean narration for display, fallback to prompt
                        'styled_prompt': styled_prompt,
                        'scene_number': scene_num_found,
                        'status': inserted_img.get('status'),
                        'created_at': inserted_img.get('created_at')
                    }
                    transformed_images.append(transformed_img)
                    
                    # Yield this image immediately
                    yield f"data: {json.dumps({'type': 'image', 'image': transformed_img})}\n\n"
                    await asyncio.sleep(0.1)  # Small delay to ensure frontend processes
            
            # Update project status to 'images'
            try:
                supabase.table('projects').update({'status': 'images'}).eq('id', req.project_id).execute()
            except Exception:
                pass
            
            # Send completion message
            yield f"data: {json.dumps({'type': 'complete', 'count': len(transformed_images), 'images': transformed_images})}\n\n"
        
        return StreamingResponse(
            generate_and_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Image generation error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Image generation failed: {str(e)}")


@router.post("/regenerate")
async def regenerate_image(req: ImageRegenerateRequest, user_id: str = Depends(verify_token)):
    """Regenerate a single image by ID."""
    try:
        supabase = get_supabase()
        
        # Get the existing image with scene info
        image_result = supabase.table('images').select('*, scenes(scene_number, script_id)').eq('id', req.image_id).execute()
        
        if not image_result.data or not image_result.data[0]:
            raise HTTPException(status_code=404, detail="Image not found")
        
        image_data = image_result.data[0]
        scene_id = image_data.get('scene_id')
        
        # Get scene info
        scene_number = None
        script_id = None
        if image_data.get('scenes') and isinstance(image_data['scenes'], list) and len(image_data['scenes']) > 0:
            scene_info = image_data['scenes'][0]
            scene_number = scene_info.get('scene_number')
            script_id = scene_info.get('script_id')
        elif isinstance(image_data.get('scenes'), dict):
            scene_info = image_data['scenes']
            scene_number = scene_info.get('scene_number')
            script_id = scene_info.get('script_id')
        
        # Verify ownership via script -> project
        if script_id:
            script_result = supabase.table('scripts').select('project_id').eq('id', script_id).execute()
            if script_result.data:
                project_id = script_result.data[0].get('project_id')
                project_result = supabase.table('projects').select('user_id').eq('id', project_id).execute()
                if project_result.data and project_result.data[0].get('user_id') != user_id:
                    raise HTTPException(status_code=403, detail="Access denied")
        
        prompt_text = req.prompt or image_data.get('prompt_text', '')
        
        if not prompt_text:
            raise HTTPException(status_code=400, detail="No prompt available for regeneration")
        
        # Generate new image using Stable Diffusion (same logic as generate endpoint)
        data_url = None
        try:
            from PIL import Image
            import io
            
            sd_model = os.getenv("IMAGE_SD_MODEL", "stabilityai/stable-diffusion-2-1-base")
            
            try:
                from diffusers import StableDiffusionPipeline
                import torch
                
                print(f"Regenerating image {req.image_id} with prompt: {prompt_text[:50]}...")
                
                global _sd_pipeline_cache, _sd_model_cache
                if '_sd_pipeline_cache' not in globals():
                    _sd_pipeline_cache = None
                    _sd_model_cache = None
                
                if _sd_pipeline_cache is None or _sd_model_cache != sd_model:
                    if torch.cuda.is_available():
                        device = "cuda"
                        dtype = torch.float16
                    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                        device = "mps"
                        dtype = torch.float32
                    else:
                        device = "cpu"
                        dtype = torch.float32
                    
                    print(f"Loading SD pipeline: {sd_model} on {device}")
                    _sd_pipeline_cache = StableDiffusionPipeline.from_pretrained(sd_model, torch_dtype=dtype)
                    _sd_pipeline_cache = _sd_pipeline_cache.to(device)
                    _sd_model_cache = sd_model
                    print("SD pipeline loaded successfully")
                
                pipe = _sd_pipeline_cache
                
                image: Image.Image = pipe(
                    prompt_text,
                    num_inference_steps=30,
                    guidance_scale=7.5,
                    height=512,
                    width=512,
                ).images[0]
                
                buf = io.BytesIO()
                image.save(buf, format="PNG")
                buf.seek(0)
                b64 = base64.b64encode(buf.read()).decode("utf-8")
                data_url = f"data:image/png;base64,{b64}"
                print(f"Successfully regenerated image {req.image_id}")
                
            except ImportError:
                print(f"SD dependencies not installed, using placeholder")
                data_url = None
            except Exception as e:
                print(f"SD generation error: {str(e)}")
                import traceback
                traceback.print_exc()
                data_url = None
                
        except Exception as e:
            print(f"Failed to regenerate image: {str(e)}")
            data_url = None
        
        if not data_url:
            data_url = _svg_data_url(prompt_text)
        
        # Update the image in database (don't update prompt_text - preserve original base prompt)
        update_result = supabase.table('images').update({
            'image_data': data_url,
            # Don't update prompt_text - keep original base prompt
            'status': 'completed'
        }).eq('id', req.image_id).execute()
        
        if not update_result.data:
            raise HTTPException(status_code=500, detail="Failed to update image")
        
        updated_image = update_result.data[0]
        
        # Get the original prompt_text (before any user edits)
        original_prompt = image_data.get('prompt_text', '')
        
        return {
            'success': True,
            'image': {
                'id': updated_image['id'],
                'scene_id': updated_image.get('scene_id'),
                'image_data_url': updated_image.get('image_data'),
                'prompt': updated_image.get('prompt_text', ''),
                'styled_prompt': original_prompt,  # Return original base prompt, not the combined one
                'scene_number': scene_number,
                'status': updated_image.get('status'),
                'created_at': updated_image.get('created_at')
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Image regeneration error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Image regeneration failed: {str(e)}")


@router.get("/project/{project_id}")
async def list_images_for_project(project_id: str, user_id: str = Depends(verify_token)):
    try:
        supabase = get_supabase()

        # Verify project ownership
        project_result = supabase.table('projects').select('id').eq('id', project_id).eq('user_id', user_id).execute()
        if not project_result.data:
            raise HTTPException(status_code=403, detail="Project not found or access denied")

        # Fetch latest script then its images (small, ordered set)
        latest_script = (
            supabase.table('scripts')
            .select('id, created_at')
            .eq('project_id', project_id)
            .order('created_at', desc=True)
            .limit(1)
            .execute()
        )
        if not latest_script.data:
            return { 'success': True, 'images': [] }

        script_id = latest_script.data[0]['id']
        
        # Get images via scenes - ORDER BY scene_number to match video compilation order
        images_res = (
            supabase.table('images')
            .select('*, scenes!inner(scene_number, script_id)')
            .eq('scenes.script_id', script_id)
            .order('scenes(scene_number)', desc=False)  # Order by scene_number, not created_at
            .limit(24)
            .execute()
        )
        
        # Transform to match frontend expectations
        images = []
        if images_res.data:
            for img in images_res.data:
                # Convert image_data to image_data_url format for frontend
                image_data_url = img.get('image_data') or img.get('image_url')
                images.append({
                    'id': img['id'],
                    'scene_id': img['scene_id'],
                    'image_data_url': image_data_url,
                    'prompt': img.get('prompt_text', ''),  # This will be the narration for display
                    'styled_prompt': img.get('prompt_text', ''),  # Store original base prompt
                    'scene_number': img.get('scenes', {}).get('scene_number') if isinstance(img.get('scenes'), dict) else None,
                    'status': img.get('status'),
                    'created_at': img.get('created_at')
                })
        
        return { 'success': True, 'images': images }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch images: {str(e)}")



