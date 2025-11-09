from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import base64
import uuid
import os
import subprocess
import tempfile
import re
from pathlib import Path

from auth.verify import verify_token
from db.client import get_supabase

router = APIRouter()


class VideoCompileRequest(BaseModel):
    project_id: str


def _check_ffmpeg() -> bool:
    """Check if FFmpeg is available."""
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, 
                              timeout=5)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def _get_audio_duration(audio_path: str) -> float:
    """Get audio duration in seconds using FFprobe."""
    try:
        result = subprocess.run([
            'ffprobe', '-v', 'error', '-show_entries',
            'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1',
            audio_path
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            return float(result.stdout.strip())
        return 0.0
    except Exception as e:
        print(f"Error getting audio duration: {e}")
        return 0.0


def _parse_scene_timings(script_text: str, audio_duration: float) -> List[dict]:
    """Parse script to extract scene boundaries and calculate timings.
    
    Attempts to detect scene transitions by:
    1. Looking for explicit timestamps in script (e.g., "Scene 1 (0:00-0:15)")
    2. Using word count per scene to estimate duration
    3. Falling back to even distribution if no timing info available
    """
    scenes = []
    lines = script_text.split('\n')
    current_scene = None
    scene_content = {}
    
    # Find all scene markers and collect content
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        if not line_stripped:
            continue
            
        # Match "Scene X" pattern with optional timestamps
        match = re.match(r'^Scene\s+(\d+)(?:\s*\(([\d:]+)\s*-\s*([\d:]+)\))?', line_stripped, re.IGNORECASE)
        if match:
            scene_num = int(match.group(1))
            start_time_str = match.group(2) if match.group(2) else None
            end_time_str = match.group(3) if match.group(3) else None
            
            if current_scene:
                scene_content[current_scene['number']] = {
                    'content': current_scene.get('content', ''),
                    'start_time': current_scene.get('start_time'),
                    'end_time': current_scene.get('end_time')
                }
            
            # Parse timestamps if available
            start_time = None
            end_time = None
            if start_time_str and end_time_str:
                try:
                    start_parts = start_time_str.split(':')
                    end_parts = end_time_str.split(':')
                    if len(start_parts) == 2:
                        start_time = int(start_parts[0]) * 60 + int(start_parts[1])
                    if len(end_parts) == 2:
                        end_time = int(end_parts[0]) * 60 + int(end_parts[1])
                except:
                    pass
            
            current_scene = {
                'number': scene_num,
                'start_time': start_time,
                'end_time': end_time,
                'content': ''
            }
        elif current_scene:
            # Accumulate content for current scene
            current_scene['content'] += ' ' + line_stripped
    
    # Add last scene
    if current_scene:
        scene_content[current_scene['number']] = {
            'content': current_scene.get('content', ''),
            'start_time': current_scene.get('start_time'),
            'end_time': current_scene.get('end_time')
        }
    
    if not scene_content:
        return []
    
    # Calculate timings
    sorted_scenes = sorted(scene_content.items())
    
    # If we have explicit timestamps, use them
    has_timestamps = any(s.get('start_time') is not None for s in scene_content.values())
    
    if has_timestamps:
        for scene_num, scene_data in sorted_scenes:
            start = scene_data.get('start_time', 0)
            end = scene_data.get('end_time')
            if end is None:
                # Use next scene's start or audio duration
                next_scene = next((s for n, s in sorted_scenes if n > scene_num), None)
                end = next_scene.get('start_time') if next_scene else audio_duration
            
            scenes.append({
                'scene_number': scene_num,
                'start_time': start,
                'end_time': end,
                'duration': end - start
            })
    else:
        # Use word count to estimate duration (more words = longer duration)
        total_words = sum(len(s.get('content', '').split()) for s in scene_content.values())
        
        if total_words > 0:
            # Distribute audio duration based on word count
            cumulative_time = 0
            for i, (scene_num, scene_data) in enumerate(sorted_scenes):
                word_count = len(scene_data.get('content', '').split())
                scene_duration = (word_count / total_words) * audio_duration
                
                start_time = cumulative_time
                end_time = cumulative_time + scene_duration
                
                scenes.append({
                    'scene_number': scene_num,
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration': scene_duration
                })
                
                cumulative_time = end_time
        else:
            # Fallback: even distribution
            duration_per_scene = audio_duration / len(sorted_scenes)
            for i, (scene_num, scene_data) in enumerate(sorted_scenes):
                start_time = i * duration_per_scene
                end_time = (i + 1) * duration_per_scene if i < len(sorted_scenes) - 1 else audio_duration
                
                scenes.append({
                    'scene_number': scene_num,
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration': end_time - start_time
                })
    
    return scenes


def _compile_video_with_scene_timings(
    audio_path: str,
    images: List[dict],  # List of {scene_number, image_path, start_time, duration}
    output_path: str,
    audio_duration: float
) -> bool:
    """Compile video using FFmpeg with fade transitions and scene-specific timings."""
    print(f"[VIDEO] [FFMPEG] Starting video compilation...")
    print(f"[VIDEO] [FFMPEG] Audio: {audio_path}, Images: {len(images)}, Output: {output_path}")
    try:
        # Create temporary directory for image sequence
        temp_dir = tempfile.mkdtemp()
        
        # Sort images by scene number
        sorted_images = sorted(images, key=lambda x: x.get('scene_number', 0))
        
        if not sorted_images:
            raise ValueError("No images provided")
        
        fade_duration = 0.5  # 0.5 second fade transitions
        
        # Prepare image paths and create copies with proper naming
        print(f"[VIDEO] [FFMPEG] Preparing {len(sorted_images)} image segments...")
        image_files = []
        for i, img_data in enumerate(sorted_images):
            img_path = img_data['image_path']
            # Copy image to temp directory with sequential naming
            ext = Path(img_path).suffix or '.png'
            temp_img_path = os.path.join(temp_dir, f'img_{i:04d}{ext}')
            
            # Copy image file
            import shutil
            shutil.copy2(img_path, temp_img_path)
            image_files.append({
                'path': temp_img_path,
                'duration': img_data.get('duration', audio_duration / len(sorted_images)),
                'start_time': img_data.get('start_time', i * (audio_duration / len(sorted_images)))
            })
            print(f"[VIDEO] [FFMPEG]   Prepared segment {i+1}/{len(sorted_images)}: Scene {img_data.get('scene_number', '?')} ({img_data.get('duration', 0):.2f}s)")
        
        # Create individual video segments with fades
        print(f"[VIDEO] [FFMPEG] Creating video segments with fade transitions...")
        video_segments = []
        for i, img_info in enumerate(image_files):
            segment_path = os.path.join(temp_dir, f'segment_{i:04d}.mp4')
            video_segments.append(segment_path)
            
            duration = img_info['duration']
            fade_out = max(0, duration - fade_duration)
            
            print(f"[VIDEO] [FFMPEG]   Creating segment {i+1}/{len(image_files)}: {duration:.2f}s duration, fade out at {fade_out:.2f}s")
            
            # Create video segment with fade
            cmd_segment = [
                'ffmpeg', '-y',
                '-loop', '1',
                '-i', img_info['path'],
                '-vf', f'scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,fade=t=in:st=0:d={fade_duration},fade=t=out:st={fade_out}:d={fade_duration}',
                '-t', str(duration),
                '-r', '30',  # 30 fps
                '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p',
                segment_path
            ]
            
            result = subprocess.run(cmd_segment, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                print(f"[VIDEO] [FFMPEG] ❌ Segment creation error: {result.stderr}")
                return False
            print(f"[VIDEO] [FFMPEG]   ✓ Segment {i+1} created")
        
        # Concatenate all segments
        print(f"[VIDEO] [FFMPEG] Concatenating video segments...")
        concat_list_file = os.path.join(temp_dir, 'filelist.txt')
        with open(concat_list_file, 'w') as f:
            for segment in video_segments:
                f.write(f"file '{segment}'\n")
        
        # Concatenate video segments
        cmd_concat = [
            'ffmpeg', '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', concat_list_file,
            '-c', 'copy',
            os.path.join(temp_dir, 'video_no_audio.mp4')
        ]
        
        result = subprocess.run(cmd_concat, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            print(f"[VIDEO] [FFMPEG] ❌ Concat error: {result.stderr}")
            return False
        print(f"[VIDEO] [FFMPEG] ✓ Segments concatenated")
        
        # Combine video with audio
        print(f"[VIDEO] [FFMPEG] Combining video with audio track...")
        cmd_final = [
            'ffmpeg', '-y',
            '-i', os.path.join(temp_dir, 'video_no_audio.mp4'),
            '-i', audio_path,
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-shortest',
            output_path
        ]
        
        result = subprocess.run(cmd_final, capture_output=True, text=True, timeout=120)
        
        # Cleanup temp directory
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        if result.returncode != 0:
            print(f"[VIDEO] [FFMPEG] ❌ Final combination error: {result.stderr}")
            return False
        
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path) / (1024 * 1024)
            print(f"[VIDEO] [FFMPEG] ✅ Video compilation complete! Output: {output_path} ({file_size:.2f} MB)")
            return True
        else:
            print(f"[VIDEO] [FFMPEG] ❌ Output file not found")
            return False
        
    except Exception as e:
        print(f"[VIDEO] [FFMPEG] ❌ Video compilation error: {e}")
        import traceback
        traceback.print_exc()
        return False


@router.post("/compile")
async def compile_video(
    req: VideoCompileRequest,
    user_id: str = Depends(verify_token)
):
    """Compile video from script, voiceover, and images."""
    print(f"[VIDEO] Starting compilation for project {req.project_id}")
    try:
        supabase = get_supabase()
        
        # Verify project ownership
        print(f"[VIDEO] Verifying project ownership...")
        project_result = supabase.table('projects').select('id').eq('id', req.project_id).eq('user_id', user_id).execute()
        if not project_result.data:
            raise HTTPException(status_code=403, detail="Project not found or access denied")
        print(f"[VIDEO] ✓ Project ownership verified")
        
        # Check FFmpeg availability
        print(f"[VIDEO] Checking FFmpeg availability...")
        if not _check_ffmpeg():
            raise HTTPException(status_code=503, detail="FFmpeg is not available. Please install FFmpeg.")
        print(f"[VIDEO] ✓ FFmpeg is available")
        
        # Fetch script
        print(f"[VIDEO] Fetching script...")
        script_result = (
            supabase.table('scripts')
            .select('id, raw_script, edited_script')
            .eq('project_id', req.project_id)
            .order('created_at', desc=True)
            .limit(1)
            .execute()
        )
        
        if not script_result.data:
            raise HTTPException(status_code=400, detail="No script found for this project")
        
        script = script_result.data[0]
        script_id = script['id']
        script_text = script.get('edited_script') or script.get('raw_script', '')
        print(f"[VIDEO] ✓ Script found (ID: {script_id}, length: {len(script_text)} chars)")
        
        # Fetch voiceover
        print(f"[VIDEO] Fetching voiceover...")
        voiceover_result = (
            supabase.table('voiceovers')
            .select('id, audio_data_url')
            .eq('script_id', script_id)
            .order('created_at', desc=True)
            .limit(1)
            .execute()
        )
        
        if not voiceover_result.data:
            raise HTTPException(status_code=400, detail="No voiceover found for this project")
        
        voiceover = voiceover_result.data[0]
        voiceover_id = voiceover['id']
        audio_data_url = voiceover.get('audio_data_url', '')
        
        if not audio_data_url:
            raise HTTPException(status_code=400, detail="Voiceover audio data not found")
        print(f"[VIDEO] ✓ Voiceover found (ID: {voiceover_id}, audio length: {len(audio_data_url)} chars)")
        
        # Fetch images
        print(f"[VIDEO] Fetching scenes and images...")
        scenes_result = (
            supabase.table('scenes')
            .select('id, scene_number')
            .eq('script_id', script_id)
            .order('scene_number', desc=False)
            .execute()
        )
        
        if not scenes_result.data:
            raise HTTPException(status_code=400, detail="No scenes found for this project")
        
        scene_ids = [s['id'] for s in scenes_result.data]
        scene_map = {s['id']: s['scene_number'] for s in scenes_result.data}
        print(f"[VIDEO] ✓ Found {len(scene_ids)} scenes")
        
        images_result = (
            supabase.table('images')
            .select('id, scene_id, image_data')
            .in_('scene_id', scene_ids)
            .order('created_at', desc=False)
            .execute()
        )
        
        if not images_result.data:
            raise HTTPException(status_code=400, detail="No images found for this project")
        print(f"[VIDEO] ✓ Found {len(images_result.data)} images")
        
        # Create temporary files
        print(f"[VIDEO] Creating temporary directory...")
        temp_dir = tempfile.mkdtemp()
        print(f"[VIDEO] ✓ Temp directory: {temp_dir}")
        
        try:
            # Save audio to temp file
            print(f"[VIDEO] Processing audio data...")
            audio_data = audio_data_url
            if audio_data.startswith('data:audio'):
                # Extract base64 data
                header, data = audio_data.split(',', 1)
                audio_bytes = base64.b64decode(data)
                audio_ext = 'wav' if 'wav' in header else 'mp3'
            else:
                # Assume it's already base64
                audio_bytes = base64.b64decode(audio_data)
                audio_ext = 'wav'
            
            audio_path = os.path.join(temp_dir, f'audio.{audio_ext}')
            with open(audio_path, 'wb') as f:
                f.write(audio_bytes)
            print(f"[VIDEO] ✓ Audio saved to {audio_path} ({len(audio_bytes)} bytes)")
            
            # Get audio duration
            print(f"[VIDEO] Getting audio duration...")
            audio_duration = _get_audio_duration(audio_path)
            if audio_duration <= 0:
                raise HTTPException(status_code=400, detail="Could not determine audio duration")
            print(f"[VIDEO] ✓ Audio duration: {audio_duration:.2f} seconds")
            
            # Parse scene timings
            print(f"[VIDEO] Parsing scene timings...")
            scene_timings = _parse_scene_timings(script_text, audio_duration)
            print(f"[VIDEO] ✓ Parsed {len(scene_timings)} scene timings")
            for timing in scene_timings:
                print(f"[VIDEO]   Scene {timing['scene_number']}: {timing['start_time']:.2f}s - {timing['end_time']:.2f}s")
            
            # Prepare images with scene numbers and map to timings
            print(f"[VIDEO] Processing images...")
            images_with_scenes = []
            scene_timing_map = {s['scene_number']: s for s in scene_timings}
            
            for i, img in enumerate(images_result.data):
                scene_id = img.get('scene_id')
                scene_number = scene_map.get(scene_id, 0)
                image_data = img.get('image_data', '')
                
                if image_data.startswith('data:image'):
                    header, data = image_data.split(',', 1)
                    img_bytes = base64.b64decode(data)
                    img_ext = 'png' if 'png' in header else 'jpg'
                else:
                    img_bytes = base64.b64decode(image_data)
                    img_ext = 'png'
                
                img_path = os.path.join(temp_dir, f'img_scene_{scene_number}.{img_ext}')
                with open(img_path, 'wb') as f:
                    f.write(img_bytes)
                
                # Get timing for this scene
                timing = scene_timing_map.get(scene_number, {})
                images_with_scenes.append({
                    'scene_number': scene_number,
                    'image_path': img_path,
                    'start_time': timing.get('start_time', 0),
                    'duration': timing.get('duration', audio_duration / len(images_result.data))
                })
                print(f"[VIDEO]   Processed image {i+1}/{len(images_result.data)}: Scene {scene_number} ({len(img_bytes)} bytes)")
            
            # Sort images by scene number
            images_with_scenes.sort(key=lambda x: x['scene_number'])
            
            # Compile video with scene-specific timings
            print(f"[VIDEO] Starting video compilation with FFmpeg...")
            output_path = os.path.join(temp_dir, 'output.mp4')
            success = _compile_video_with_scene_timings(
                audio_path,
                images_with_scenes,
                output_path,
                audio_duration
            )
            
            if not success or not os.path.exists(output_path):
                raise HTTPException(status_code=500, detail="Video compilation failed")
            
            # Read compiled video
            print(f"[VIDEO] Reading compiled video...")
            with open(output_path, 'rb') as f:
                video_bytes = f.read()
            video_size_mb = len(video_bytes) / (1024 * 1024)
            print(f"[VIDEO] ✓ Video compiled successfully ({video_size_mb:.2f} MB)")
            
            video_base64 = base64.b64encode(video_bytes).decode('utf-8')
            video_data_url = f"data:video/mp4;base64,{video_base64}"
            
            # Store video in database
            print(f"[VIDEO] Saving video to database...")
            video_id = str(uuid.uuid4())
            try:
                # Insert video but don't return video_data in response to avoid serialization issues
                video_insert = supabase.table('videos').insert({
                    'id': video_id,
                    'project_id': req.project_id,
                    'script_id': script_id,
                    'voiceover_id': voiceover_id,
                    'video_data': video_bytes,  # Store as binary
                    'status': 'completed'
                }).execute()
                
                # Just check that execute completed without error (don't access .data to avoid bytes serialization)
                print(f"[VIDEO] ✓ Video saved to database (ID: {video_id})")
            except Exception as db_error:
                error_msg = str(db_error)
                # Ensure error message is JSON serializable
                if isinstance(db_error, bytes):
                    error_msg = db_error.decode('utf-8', errors='ignore')
                # Also check if error message contains bytes
                try:
                    # Try to serialize error_msg to JSON to catch any remaining bytes
                    import json
                    json.dumps({'error': error_msg})
                except TypeError:
                    error_msg = "Database error occurred (non-serializable error message)"
                print(f"[VIDEO] ❌ Database save error: {error_msg}")
                raise HTTPException(status_code=500, detail=f"Failed to save video to database: {error_msg}")
            
            # Update project status
            try:
                supabase.table('projects').update({'status': 'video'}).eq('id', req.project_id).execute()
                print(f"[VIDEO] ✓ Project status updated to 'video'")
            except Exception as e:
                print(f"[VIDEO] ⚠️  Failed to update project status: {e}")
            
            print(f"[VIDEO] ✅ Compilation complete!")
            return {
                'success': True,
                'video_id': video_id,
                'video_data_url': video_data_url
            }
            
        finally:
            # Cleanup temp directory
            print(f"[VIDEO] Cleaning up temporary files...")
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
            print(f"[VIDEO] ✓ Cleanup complete")
            
    except HTTPException as e:
        print(f"[VIDEO] ❌ HTTP Exception: {e.status_code} - {e.detail}")
        raise
    except Exception as e:
        error_msg = str(e)
        print(f"[VIDEO] ❌ Video compilation error: {error_msg}")
        import traceback
        traceback.print_exc()
        # Ensure error message is JSON serializable
        if isinstance(e, bytes):
            error_msg = e.decode('utf-8', errors='ignore')
        raise HTTPException(status_code=500, detail=f"Video compilation failed: {error_msg}")


@router.get("/project/{project_id}")
async def get_video_for_project(
    project_id: str,
    user_id: str = Depends(verify_token)
):
    """Get video for a project."""
    try:
        supabase = get_supabase()
        
        # Verify project ownership
        project_result = supabase.table('projects').select('id').eq('id', project_id).eq('user_id', user_id).execute()
        if not project_result.data:
            raise HTTPException(status_code=403, detail="Project not found or access denied")
        
        # Get latest video for project (exclude video_data to avoid serialization issues)
        video_result = (
            supabase.table('videos')
            .select('id, project_id, script_id, voiceover_id, video_url, status, error_message, created_at, updated_at')
            .eq('project_id', project_id)
            .order('created_at', desc=True)
            .limit(1)
            .execute()
        )
        
        video = video_result.data[0] if video_result.data else None
        
        # If video exists and we need the data, fetch it separately and convert to base64
        if video:
            video_data_result = (
                supabase.table('videos')
                .select('video_data')
                .eq('id', video['id'])
                .single()
                .execute()
            )
            
            if video_data_result.data and video_data_result.data.get('video_data'):
                video_bytes = video_data_result.data['video_data']
                if isinstance(video_bytes, bytes):
                    video_base64 = base64.b64encode(video_bytes).decode('utf-8')
                    video['video_data_url'] = f"data:video/mp4;base64,{video_base64}"
                else:
                    video['video_data_url'] = None
            else:
                video['video_data_url'] = None
        
        return {
            'success': True,
            'video': video
        }
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        print(f"[VIDEO] Failed to fetch video: {error_msg}")
        import traceback
        traceback.print_exc()
        # Ensure error message is JSON serializable
        if isinstance(e, bytes):
            error_msg = e.decode('utf-8', errors='ignore')
        raise HTTPException(status_code=500, detail=f"Failed to fetch video: {error_msg}")

