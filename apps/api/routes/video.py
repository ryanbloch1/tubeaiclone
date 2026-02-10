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
        print(f"[VIDEO] [FFMPEG] Input images list:")
        for idx, img_data in enumerate(sorted_images):
            print(f"[VIDEO] [FFMPEG]   [{idx}] Scene {img_data.get('scene_number', '?')}: {img_data.get('image_path', '?')} (duration: {img_data.get('duration', 0):.2f}s)")
        
        image_files = []
        for i, img_data in enumerate(sorted_images):
            img_path = img_data['image_path']
            scene_num = img_data.get('scene_number', i + 1)
            
            # Verify source image exists
            if not os.path.exists(img_path):
                print(f"[VIDEO] [FFMPEG] ❌ ERROR: Source image not found: {img_path}")
                return False
            
            # Copy image to temp directory with unique naming (include scene number and index)
            ext = Path(img_path).suffix or '.png'
            temp_img_path = os.path.join(temp_dir, f'img_scene_{scene_num:03d}_seq_{i:04d}{ext}')
            
            # Copy image file
            import shutil
            shutil.copy2(img_path, temp_img_path)
            
            # Verify copy succeeded
            if not os.path.exists(temp_img_path):
                print(f"[VIDEO] [FFMPEG] ❌ ERROR: Failed to copy image to: {temp_img_path}")
                return False
            
            # Calculate file hash to verify it's unique
            import hashlib
            with open(temp_img_path, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()[:8]
            
            # Verify this is a different image than previous one
            if i > 0 and image_files:
                prev_hash = image_files[-1].get('hash', '')
                if prev_hash == file_hash:
                    print(f"[VIDEO] [FFMPEG] ⚠️  WARNING: Segment {i+1} (Scene {scene_num}) has same hash as previous segment (Scene {image_files[-1].get('scene_number', '?')}) - may be duplicate image!")
            
            image_files.append({
                'path': temp_img_path,
                'scene_number': scene_num,
                'duration': img_data.get('duration', audio_duration / len(sorted_images)),
                'start_time': img_data.get('start_time', i * (audio_duration / len(sorted_images))),
                'hash': file_hash  # Store hash for comparison
            })
            print(f"[VIDEO] [FFMPEG]   ✓ Prepared segment {i+1}/{len(sorted_images)}: Scene {scene_num} -> {temp_img_path} (hash: {file_hash[:8]}, duration: {img_data.get('duration', 0):.2f}s)")
        
        # Create individual video segments with fades
        print(f"[VIDEO] [FFMPEG] Creating video segments with fade transitions...")
        video_segments = []
        for i, img_info in enumerate(image_files):
            segment_path = os.path.join(temp_dir, f'segment_{i:04d}.mp4')
            video_segments.append(segment_path)
            
            duration = img_info['duration']
            fade_out = max(0, duration - fade_duration)
            
            print(f"[VIDEO] [FFMPEG]   Creating segment {i+1}/{len(image_files)}: {duration:.2f}s duration, fade out at {fade_out:.2f}s")
            
            # Create video segment with fade (browser-compatible settings)
            cmd_segment = [
                'ffmpeg', '-y',
                '-loop', '1',
                '-i', img_info['path'],
                '-vf', f'scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,fade=t=in:st=0:d={fade_duration},fade=t=out:st={fade_out}:d={fade_duration}',
                '-t', str(duration),
                '-r', '30',  # 30 fps
                '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p',
                '-preset', 'medium',
                '-profile:v', 'baseline',  # Use baseline profile for maximum browser compatibility
                '-level', '3.0',
                segment_path
            ]
            
            # Verify source image exists
            if not os.path.exists(img_info['path']):
                print(f"[VIDEO] [FFMPEG] ❌ ERROR: Source image file not found: {img_info['path']}")
                return False
            
            print(f"[VIDEO] [FFMPEG]   Using image: {img_info['path']} (Scene {img_info.get('scene_number', '?')})")
            
            result = subprocess.run(cmd_segment, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                print(f"[VIDEO] [FFMPEG] ❌ Segment {i+1} creation error:")
                print(f"[VIDEO] [FFMPEG] stderr: {result.stderr[:500]}")
                return False
            
            # Verify segment was created
            if not os.path.exists(segment_path):
                print(f"[VIDEO] [FFMPEG] ❌ Segment file was not created: {segment_path}")
                return False
            
            segment_size = os.path.getsize(segment_path)
            print(f"[VIDEO] [FFMPEG]   ✓ Segment {i+1} created: {segment_path} ({segment_size} bytes)")
        
        # Concatenate all segments
        print(f"[VIDEO] [FFMPEG] Concatenating video segments...")
        concat_list_file = os.path.join(temp_dir, 'filelist.txt')
        with open(concat_list_file, 'w') as f:
            for segment in video_segments:
                f.write(f"file '{segment}'\n")
        
        # Concatenate video segments (re-encode for browser compatibility)
        cmd_concat = [
            'ffmpeg', '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', concat_list_file,
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            '-preset', 'medium',
            '-crf', '23',
            os.path.join(temp_dir, 'video_no_audio.mp4')
        ]
        
        result = subprocess.run(cmd_concat, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            print(f"[VIDEO] [FFMPEG] ❌ Concat error: {result.stderr}")
            return False
        print(f"[VIDEO] [FFMPEG] ✓ Segments concatenated and re-encoded")
        
        # Combine video with audio (re-encode for browser compatibility)
        print(f"[VIDEO] [FFMPEG] Combining video with audio track...")
        cmd_final = [
            'ffmpeg', '-y',
            '-i', os.path.join(temp_dir, 'video_no_audio.mp4'),
            '-i', audio_path,
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            '-preset', 'medium',
            '-crf', '23',
            '-profile:v', 'baseline',  # Use baseline profile for maximum browser compatibility
            '-level', '3.0',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-ar', '44100',  # Standard audio sample rate
            '-strict', '-2',  # Allow experimental codecs (if needed)
            '-movflags', '+faststart',  # CRITICAL: Move moov box to beginning for web playback
            '-map', '0:v:0',  # Map first video stream
            '-map', '1:a:0',  # Map first audio stream
            '-shortest',
            '-f', 'mp4',  # Explicitly specify MP4 format
            output_path
        ]
        
        result = subprocess.run(cmd_final, capture_output=True, text=True, timeout=180)
        
        if result.returncode != 0:
            print(f"[VIDEO] [FFMPEG] ❌ Final combination error:")
            print(f"[VIDEO] [FFMPEG] stderr: {result.stderr[:1000]}")
            # Cleanup on error
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
            return False
        
        if not os.path.exists(output_path):
            print(f"[VIDEO] [FFMPEG] ❌ Output file not found")
            # Cleanup on error
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
            return False
        
        # Post-process: ensure faststart is actually applied using qt-faststart (more reliable)
        print(f"[VIDEO] [FFMPEG] Post-processing: Applying faststart for seeking support...")
        temp_output = output_path + '.tmp'
        
        # Try using qt-faststart first (faster and more reliable)
        qt_faststart_result = subprocess.run(
            ['qt-faststart', output_path, temp_output],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if qt_faststart_result.returncode == 0 and os.path.exists(temp_output):
            # Replace original with faststart version
            import shutil
            shutil.move(temp_output, output_path)
            print(f"[VIDEO] [FFMPEG] ✅ Faststart applied successfully using qt-faststart")
        else:
            # Fallback to FFmpeg faststart
            print(f"[VIDEO] [FFMPEG] qt-faststart not available, trying FFmpeg faststart...")
            cmd_faststart = [
                'ffmpeg', '-y',
                '-i', output_path,
                '-c', 'copy',  # Copy streams without re-encoding
                '-movflags', '+faststart',  # Ensure moov box is at start
                '-f', 'mp4',
                temp_output
            ]
            
            faststart_result = subprocess.run(cmd_faststart, capture_output=True, text=True, timeout=60)
            if faststart_result.returncode == 0 and os.path.exists(temp_output):
                # Replace original with faststart version
                import shutil
                shutil.move(temp_output, output_path)
                print(f"[VIDEO] [FFMPEG] ✅ Faststart applied successfully using FFmpeg")
            else:
                print(f"[VIDEO] [FFMPEG] ⚠️  Faststart post-processing failed")
                if faststart_result.returncode != 0:
                    print(f"[VIDEO] [FFMPEG] FFmpeg faststart error: {faststart_result.stderr[:200]}")
                if os.path.exists(temp_output):
                    os.remove(temp_output)
        
        # Cleanup temp directory
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        # Validate video file with ffprobe - CRITICAL CHECK
        file_size = os.path.getsize(output_path) / (1024 * 1024)
        print(f"[VIDEO] [FFMPEG] Video file created: {output_path} ({file_size:.2f} MB)")
        
        # Verify video file is valid and can be read by ffprobe
        cmd_probe = [
            'ffprobe', '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=codec_name,codec_type,width,height,profile,level',
            '-show_entries', 'format=format_name,format_long_name',
            '-of', 'json',
            output_path
        ]
        
        probe_result = subprocess.run(cmd_probe, capture_output=True, text=True, timeout=30)
        if probe_result.returncode != 0:
            print(f"[VIDEO] [FFMPEG] ❌ Video validation FAILED!")
            print(f"[VIDEO] [FFMPEG] ffprobe error: {probe_result.stderr}")
            print(f"[VIDEO] [FFMPEG] This video may not be playable in browsers")
            # Don't fail completely, but this is a warning
        else:
            print(f"[VIDEO] [FFMPEG] ✅ Video validated by ffprobe - should be playable")
            try:
                import json
                probe_data = json.loads(probe_result.stdout)
                if probe_data.get('streams'):
                    stream = probe_data['streams'][0]
                    print(f"[VIDEO] [FFMPEG] Codec: {stream.get('codec_name')}, Profile: {stream.get('profile')}, Resolution: {stream.get('width')}x{stream.get('height')}")
            except:
                pass
        
        print(f"[VIDEO] [FFMPEG] ✅ Video compilation complete! Output: {output_path} ({file_size:.2f} MB)")
        return True
        
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
        
        # Fetch images - join with scenes to get scene_number
        images_result = (
            supabase.table('images')
            .select('id, scene_id, image_data, scenes!inner(scene_number)')
            .in_('scene_id', scene_ids)
            .order('scenes(scene_number)', desc=False)
            .execute()
        )
        
        print(f"[VIDEO] ✓ Found {len(images_result.data)} images")
        
        # Debug: Print all images and their scene numbers
        print(f"[VIDEO] Images with scene mapping:")
        print(f"[VIDEO] Raw images_result.data structure (first image):")
        if images_result.data and len(images_result.data) > 0:
            import json
            print(f"[VIDEO]   First image keys: {list(images_result.data[0].keys())}")
            print(f"[VIDEO]   First image scenes value: {images_result.data[0].get('scenes')}")
            print(f"[VIDEO]   First image scenes type: {type(images_result.data[0].get('scenes'))}")
        
        for idx, img in enumerate(images_result.data):
            # Try multiple ways to extract scene_number from join
            scene_num = None
            scenes_data = img.get('scenes')
            
            # Handle different Supabase join result formats
            if isinstance(scenes_data, dict):
                scene_num = scenes_data.get('scene_number')
            elif isinstance(scenes_data, list) and len(scenes_data) > 0:
                scene_num = scenes_data[0].get('scene_number')
            
            scene_id = img.get('scene_id')
            mapped_scene = scene_map.get(scene_id, 'NOT FOUND') if scene_id else 'NO_SCENE_ID'
            
            # Use mapped_scene if join didn't work
            if scene_num is None and mapped_scene != 'NOT FOUND':
                scene_num = mapped_scene
            
            # Calculate image data hash for uniqueness check
            img_data = img.get('image_data', '') or img.get('image_data_url', '')
            img_hash = 'NO_DATA'
            if img_data:
                import hashlib
                img_bytes_sample = img_data[:1000] if len(img_data) > 1000 else img_data
                img_hash = hashlib.md5(img_bytes_sample.encode() if isinstance(img_bytes_sample, str) else img_bytes_sample).hexdigest()[:8]
            
            print(f"[VIDEO]   [{idx+1}] Image {img.get('id')[:8]}... scene_id={scene_id}, scene_number={scene_num}, hash={img_hash}")
        
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
                # Get scene_number from scenes join or scene_map
                scene_number = None
                scenes_data = img.get('scenes')
                
                # Handle different Supabase join result formats
                if isinstance(scenes_data, dict):
                    scene_number = scenes_data.get('scene_number')
                elif isinstance(scenes_data, list) and len(scenes_data) > 0:
                    scene_number = scenes_data[0].get('scene_number')
                
                # Fallback to scene_id mapping if join didn't work
                if scene_number is None:
                    scene_id = img.get('scene_id')
                    if scene_id:
                        scene_number = scene_map.get(scene_id)
                    
                    if scene_number is None:
                        # Last resort: use index + 1 (but log warning)
                        print(f"[VIDEO] ⚠️  Warning: Image {i+1} has no scene_number, using index {i+1}")
                        scene_number = i + 1
                
                # Ensure scene_number is an integer
                try:
                    scene_number = int(scene_number) if scene_number is not None else (i + 1)
                except (ValueError, TypeError):
                    print(f"[VIDEO] ⚠️  Warning: Invalid scene_number '{scene_number}' for image {i+1}, using index {i+1}")
                    scene_number = i + 1
                
                print(f"[VIDEO]   [{i+1}] Mapping image (scene_id: {img.get('scene_id')}) -> Scene {scene_number}")
                
                image_data = img.get('image_data', '') or img.get('image_data_url', '')
                
                if not image_data:
                    print(f"[VIDEO] ⚠️  Warning: Image {i+1} has no image data, skipping")
                    continue
                
                if image_data.startswith('data:image'):
                    header, data = image_data.split(',', 1)
                    img_bytes = base64.b64decode(data)
                    img_ext = 'png' if 'png' in header else 'jpg'
                else:
                    img_bytes = base64.b64decode(image_data)
                    img_ext = 'png'
                
                # Calculate hash of image data before saving to verify uniqueness
                import hashlib
                img_hash = hashlib.md5(img_bytes).hexdigest()[:8]
                
                # Use unique filename with both scene number and index to avoid overwrites
                img_path = os.path.join(temp_dir, f'img_scene_{scene_number:03d}_idx_{i:03d}.{img_ext}')
                with open(img_path, 'wb') as f:
                    f.write(img_bytes)
                
                # Check if this is the same image as previous one
                if images_with_scenes:
                    prev_path = images_with_scenes[-1]['image_path']
                    with open(prev_path, 'rb') as f:
                        prev_hash = hashlib.md5(f.read()).hexdigest()[:8]
                    if prev_hash == img_hash:
                        print(f"[VIDEO] ⚠️  WARNING: Image {i+1} (Scene {scene_number}) has SAME HASH as previous image (Scene {images_with_scenes[-1]['scene_number']}) - DUPLICATE IMAGE!")
                
                # Get timing for this scene
                timing = scene_timing_map.get(scene_number, {})
                images_with_scenes.append({
                    'scene_number': scene_number,
                    'image_path': img_path,
                    'start_time': timing.get('start_time', 0),
                    'duration': timing.get('duration', audio_duration / len(images_result.data)),
                    'hash': img_hash  # Store hash for debugging
                })
                print(f"[VIDEO]   Processed image {i+1}/{len(images_result.data)}: Scene {scene_number}, saved to {img_path} (hash: {img_hash}), duration: {timing.get('duration', 0):.2f}s")
            
            # Sort images by scene number to ensure correct order
            images_with_scenes.sort(key=lambda x: x['scene_number'])
            
            # Debug: Print final image list and verify alignment
            print(f"[VIDEO] ===== VIDEO COMPILATION SUMMARY =====")
            print(f"[VIDEO] Scene timings parsed from script (voiceover segments):")
            for timing in scene_timings:
                print(f"[VIDEO]   Scene {timing['scene_number']}: {timing['start_time']:.2f}s - {timing['end_time']:.2f}s (duration: {timing['duration']:.2f}s)")
            print(f"[VIDEO] Images BEFORE remapping (from database):")
            for img in images_with_scenes:
                print(f"[VIDEO]   Image stored with scene_number {img['scene_number']}: {img['image_path']} (hash: {img.get('hash', 'N/A')[:8]})")
            
            # IMPORTANT: Use images as-is by scene_number - NO remapping!
            # Images are already sorted by scene_number and should match scene timings
            # The remapping was causing images to be used in wrong order
            print(f"[VIDEO] Using images directly by scene_number (no remapping)...")
            
            # Sort images by scene_number to ensure correct order
            images_with_scenes.sort(key=lambda x: x.get('scene_number', 0))
            
            # Create a map of scene_number -> image for quick lookup
            images_by_scene = {}
            for img in images_with_scenes:
                scene_num = img.get('scene_number')
                if scene_num:
                    # If multiple images for same scene, use first one
                    if scene_num not in images_by_scene:
                        images_by_scene[scene_num] = img
            
            # Match images to scene timings by exact scene_number match
            matched_images = []
            for timing in scene_timings:
                expected_scene_num = timing['scene_number']
                
                if expected_scene_num in images_by_scene:
                    # Use the image that matches this scene_number exactly
                    img = images_by_scene[expected_scene_num]
                    matched_images.append({
                        'scene_number': expected_scene_num,
                        'image_path': img['image_path'],
                        'start_time': timing['start_time'],
                        'duration': timing['duration'],
                        'hash': img.get('hash', '')
                    })
                    print(f"[VIDEO]   ✓ Scene {expected_scene_num}: Using image with matching scene_number (hash: {img.get('hash', 'N/A')[:8]})")
                else:
                    # No matching image for this scene
                    print(f"[VIDEO]   ⚠️  Scene {expected_scene_num}: No image with matching scene_number found")
                    # Try to use next available image in order
                    # But only if we have images available
                    available_scene_nums = sorted([s for s in images_by_scene.keys() if s not in [m['scene_number'] for m in matched_images]])
                    if available_scene_nums:
                        # Use next available image
                        next_scene = available_scene_nums[0]
                        img = images_by_scene[next_scene]
                        print(f"[VIDEO]   ⚠️  Scene {expected_scene_num}: Using image from Scene {next_scene} as fallback (hash: {img.get('hash', 'N/A')[:8]})")
                        matched_images.append({
                            'scene_number': expected_scene_num,  # Map to expected scene
                            'image_path': img['image_path'],
                            'start_time': timing['start_time'],
                            'duration': timing['duration'],
                            'hash': img.get('hash', '')
                        })
                    elif matched_images:
                        # Repeat last image
                        last_img = matched_images[-1]
                        print(f"[VIDEO]   ⚠️  Scene {expected_scene_num}: Repeating last image from Scene {last_img['scene_number']}")
                        matched_images.append({
                            'scene_number': expected_scene_num,
                            'image_path': last_img['image_path'],
                            'start_time': timing['start_time'],
                            'duration': timing['duration'],
                            'hash': last_img.get('hash', '')
                        })
            
            # Replace with matched images
            if matched_images:
                images_with_scenes = matched_images
                print(f"[VIDEO] ✓ Successfully matched {len(matched_images)} images to {len(scene_timings)} scene timings")
            else:
                print(f"[VIDEO] ❌ ERROR: No images were matched! Original images list had {len(images_with_scenes)} images.")
            
            print(f"[VIDEO] Images AFTER remapping (final order matching script):")
            for img in images_with_scenes:
                print(f"[VIDEO]   Scene {img['scene_number']}: {img['image_path']} -> shows at {img['start_time']:.2f}s - {img['start_time'] + img['duration']:.2f}s (hash: {img.get('hash', 'N/A')[:8]})")
            
            # Verify alignment: each scene timing should have exactly one image
            scene_numbers_in_timings = {t['scene_number'] for t in scene_timings}
            scene_numbers_in_images = {img['scene_number'] for img in images_with_scenes}
            
            missing_scenes = scene_numbers_in_timings - scene_numbers_in_images
            extra_scenes = scene_numbers_in_images - scene_numbers_in_timings
            
            if missing_scenes:
                print(f"[VIDEO] ⚠️  WARNING: Scene timings exist for scenes {sorted(missing_scenes)} but NO IMAGES FOUND - these scenes will be blank!")
            if extra_scenes:
                print(f"[VIDEO] ⚠️  WARNING: Images exist for scenes {sorted(extra_scenes)} but NO SCENE TIMINGS - these images will be skipped!")
            
            # Check for duplicate scene numbers (multiple images for same scene)
            scene_counts = {}
            for img in images_with_scenes:
                scene_num = img['scene_number']
                scene_counts[scene_num] = scene_counts.get(scene_num, 0) + 1
            
            duplicates = {scene: count for scene, count in scene_counts.items() if count > 1}
            if duplicates:
                print(f"[VIDEO] ⚠️  WARNING: Multiple images for same scenes: {duplicates} - only first image will be used per scene!")
            
            # Verify image order matches scene order
            image_scene_numbers = [img['scene_number'] for img in images_with_scenes]
            timing_scene_numbers = [t['scene_number'] for t in scene_timings]
            if image_scene_numbers != timing_scene_numbers:
                print(f"[VIDEO] ⚠️  WARNING: Image scene order {image_scene_numbers} does NOT match timing scene order {timing_scene_numbers}!")
            else:
                print(f"[VIDEO] ✓ Image scene order matches timing scene order: {image_scene_numbers}")
            
            print(f"[VIDEO] =====================================")
            
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
            
            # Validate video file size
            if len(video_bytes) < 100:
                raise HTTPException(status_code=500, detail="Video file is too small or corrupted")
            
            # Check for MP4 file signature (MP4 files should have 'ftyp' at offset 4)
            # Format: [4-byte size][4-byte type='ftyp'][...]
            if len(video_bytes) < 8:
                raise HTTPException(status_code=500, detail="Video file header is corrupted")
            
            box_size = int.from_bytes(video_bytes[0:4], byteorder='big')
            box_type = video_bytes[4:8]
            
            print(f"[VIDEO] First box size: {box_size}, type: {box_type}")
            
            # MP4 files should start with 'ftyp' box
            has_valid_header = (
                box_type == b'ftyp' or
                (len(video_bytes) > 20 and b'ftyp' in video_bytes[4:20])
            )
            
            if not has_valid_header:
                print(f"[VIDEO] ❌ ERROR: Video file does not have valid MP4 header")
                print(f"[VIDEO] First 32 bytes (hex): {video_bytes[:32].hex()}")
                print(f"[VIDEO] First 32 bytes (ascii): {video_bytes[:32]}")
                raise HTTPException(status_code=500, detail="Video file does not have valid MP4 format. File may be corrupted.")
            else:
                print(f"[VIDEO] ✅ Video file has valid MP4 header (ftyp box found)")
            
            # Verify file ends properly (should have some data, not truncated)
            if len(video_bytes) < box_size:
                print(f"[VIDEO] ⚠️  Warning: Video file may be truncated (size: {len(video_bytes)}, expected at least: {box_size})")
            
            # Verify video can be decoded/read before encoding to base64
            # Quick sanity check: try to read first and last few bytes
            if video_bytes[0:4] == b'\x00\x00\x00\x00' and len(video_bytes) > 1000:
                print(f"[VIDEO] ⚠️  Warning: Video file starts with null bytes")
            
            # Encode to base64
            print(f"[VIDEO] Encoding video to base64...")
            video_base64 = base64.b64encode(video_bytes).decode('utf-8')
            
            # Verify base64 encoding
            if len(video_base64) == 0:
                raise HTTPException(status_code=500, detail="Video base64 encoding failed")
            
            # Verify we can decode it back (sanity check)
            try:
                decoded_test = base64.b64decode(video_base64[:100])
                if len(decoded_test) != 75:  # 100 chars base64 = ~75 bytes
                    raise HTTPException(status_code=500, detail="Base64 encoding verification failed")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Base64 encoding corrupted: {str(e)}")
            
            # Store video file on disk instead of database (too large for DB)
            print(f"[VIDEO] Storing video file on disk...")
            video_id = str(uuid.uuid4())
            
            # Create videos directory if it doesn't exist
            videos_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'videos')
            os.makedirs(videos_dir, exist_ok=True)
            
            # Save video file
            video_filename = f"{video_id}.mp4"
            video_filepath = os.path.join(videos_dir, video_filename)
            with open(video_filepath, 'wb') as f:
                f.write(video_bytes)
            print(f"[VIDEO] ✓ Video saved to disk: {video_filepath} ({video_size_mb:.2f} MB)")
            
            # Store video metadata in database (without the actual video data)
            print(f"[VIDEO] Saving video metadata to database...")
            try:
                insert_result = supabase.table('videos').insert({
                    'id': video_id,
                    'project_id': req.project_id,
                    'script_id': script_id,
                    'voiceover_id': voiceover_id,
                    'video_data': None,  # Don't store video data in DB
                    'video_url': f"/api/video/file/{video_id}",  # URL to download video
                    'status': 'completed'
                }).execute()
                
                # Check for errors
                if hasattr(insert_result, 'error') and insert_result.error:
                    error_detail = str(insert_result.error) if not isinstance(insert_result.error, bytes) else "Insert error"
                    raise Exception(f"Supabase insert error: {error_detail}")
                
                print(f"[VIDEO] ✓ Video metadata saved to database (ID: {video_id})")
            except HTTPException:
                # Re-raise HTTP exceptions as-is
                raise
            except Exception as db_error:
                # Extract error message safely, ensuring it's JSON serializable
                error_msg = "Database error occurred"
                try:
                    if isinstance(db_error, Exception):
                        error_msg = str(db_error)
                        # Remove any bytes-like objects from the error message
                        if isinstance(error_msg, bytes):
                            error_msg = error_msg.decode('utf-8', errors='ignore')
                    elif isinstance(db_error, bytes):
                        error_msg = db_error.decode('utf-8', errors='ignore')
                    else:
                        error_msg = str(db_error)
                    
                    # Ensure error message is JSON serializable
                    import json
                    json.dumps({'error': error_msg})
                except (TypeError, UnicodeDecodeError, ValueError):
                    error_msg = "Database error occurred (non-serializable error message)"
                except Exception:
                    error_msg = "Database error occurred"
                
                print(f"[VIDEO] ❌ Database save error: {error_msg}")
                raise HTTPException(status_code=500, detail=f"Failed to save video to database: {error_msg}")
            
            # Update project status
            try:
                supabase.table('projects').update({'status': 'video'}).eq('id', req.project_id).execute()
                print(f"[VIDEO] ✓ Project status updated to 'video'")
            except Exception as e:
                print(f"[VIDEO] ⚠️  Failed to update project status: {e}")
            
            print(f"[VIDEO] ✅ Compilation complete!")
            # Don't return video_data_url here - it's huge and causes serialization issues
            # Frontend can fetch it separately using GET /api/video/project/{project_id}
            return {
                'success': True,
                'video_id': video_id,
                'video_url': f"/api/video/file/{video_id}"
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


@router.get("/file/{video_id}")
async def get_video_file(
    video_id: str,
    user_id: str = Depends(verify_token)
):
    """Serve video file from disk."""
    try:
        supabase = get_supabase()
        
        # Verify video exists and user has access
        video_result = (
            supabase.table('videos')
            .select('project_id')
            .eq('id', video_id)
            .single()
            .execute()
        )
        
        if not video_result.data:
            raise HTTPException(status_code=404, detail="Video not found")
        
        # Verify project ownership
        project_result = supabase.table('projects').select('id').eq('id', video_result.data['project_id']).eq('user_id', user_id).execute()
        if not project_result.data:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Read video file from disk (same path calculation as in compile endpoint)
        videos_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'videos')
        video_filepath = os.path.join(videos_dir, f"{video_id}.mp4")
        
        print(f"[VIDEO] Looking for video file at: {video_filepath}")
        print(f"[VIDEO] Videos directory: {videos_dir}")
        print(f"[VIDEO] Directory exists: {os.path.exists(videos_dir)}")
        
        if not os.path.exists(video_filepath):
            # List files in directory for debugging
            if os.path.exists(videos_dir):
                files = os.listdir(videos_dir)
                print(f"[VIDEO] Files in videos directory: {files[:10]}")
            raise HTTPException(status_code=404, detail=f"Video file not found on server: {video_filepath}")
        
        from fastapi.responses import FileResponse
        return FileResponse(
            video_filepath,
            media_type="video/mp4",
            filename=f"video-{video_id}.mp4"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        print(f"[VIDEO] Failed to serve video file: {error_msg}")
        raise HTTPException(status_code=500, detail=f"Failed to serve video: {error_msg}")


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
        
        # If video exists, set the video URL (new format uses file serving)
        if video:
            if video.get('video_url'):
                # New format: video stored on disk, URL points to file endpoint
                video['video_data_url'] = video['video_url']
            else:
                # Old format: try to get video_data from database (for backwards compatibility)
                video_data_result = (
                    supabase.table('videos')
                    .select('video_data')
                    .eq('id', video['id'])
                    .single()
                    .execute()
                )
                
                if video_data_result.data and video_data_result.data.get('video_data'):
                    video_data = video_data_result.data['video_data']
                    print(f"[VIDEO] Retrieved video_data type: {type(video_data)}")
                    
                    # Handle both formats: base64 text (new) or bytes (old)
                    if isinstance(video_data, bytes):
                        video_base64 = base64.b64encode(video_data).decode('utf-8')
                        video['video_data_url'] = f"data:video/mp4;base64,{video_base64}"
                    elif isinstance(video_data, str):
                        if video_data.startswith('data:video'):
                            video['video_data_url'] = video_data
                        else:
                            video['video_data_url'] = f"data:video/mp4;base64,{video_data}"
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
