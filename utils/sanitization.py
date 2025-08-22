"""Sanitization module: rewrites sensitive or explicit content to be YouTube-safe."""

import re

def sanitize_script(script):
    """
    Sanitize a script for YouTube safety and voiceover optimization.
    Args:
        script (str): The script to sanitize.
    Returns:
        str: Sanitized script.
    """
    if not script:
        return script
    
    # Convert to string if needed
    script = str(script)
    
    # Remove markdown formatting
    script = re.sub(r'\*\*(.*?)\*\*', r'\1', script)  # Bold
    script = re.sub(r'\*(.*?)\*', r'\1', script)      # Italic
    script = re.sub(r'`(.*?)`', r'\1', script)        # Code
    script = re.sub(r'#+\s*', '', script)             # Headers
    script = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', script)  # Links
    
    # Remove extra whitespace and normalize
    script = re.sub(r'\n\s*\n', '\n\n', script)  # Multiple newlines to double newlines
    script = re.sub(r' +', ' ', script)          # Multiple spaces to single space
    script = re.sub(r'\t+', ' ', script)         # Tabs to spaces
    
    # Clean up common AI generation artifacts
    script = re.sub(r'^Here\'s a.*?script.*?:\s*', '', script, flags=re.IGNORECASE)
    script = re.sub(r'^Script.*?:\s*', '', script, flags=re.IGNORECASE)
    script = re.sub(r'^Title.*?:\s*', '', script, flags=re.IGNORECASE)
    
    # Remove numbered lists and bullet points
    script = re.sub(r'^\d+\.\s*', '', script, flags=re.MULTILINE)
    script = re.sub(r'^[-*•]\s*', '', script, flags=re.MULTILINE)
    
    # Remove scene directions and stage directions (for voiceover-only content)
    script = remove_scene_directions(script)
    
    # Clean up common profanity and sensitive content (YouTube-safe alternatives)
    profanity_replacements = {
        r'\bdamn\b': 'darn',
        r'\bhell\b': 'heck',
        r'\bass\b': 'bottom',
        r'\bshit\b': 'stuff',
        r'\bfuck\b': 'fudge',
        r'\bbitch\b': 'person',
        r'\bwhore\b': 'person',
        r'\bslut\b': 'person',
        r'\bcrap\b': 'stuff',
        r'\bpiss\b': 'pee',
        r'\bwank\b': 'self-pleasure',
        r'\bcock\b': 'rooster',
        r'\bdick\b': 'person',
        r'\bpussy\b': 'cat',
        r'\btits\b': 'chest',
        r'\bboobs\b': 'chest',
    }
    
    for pattern, replacement in profanity_replacements.items():
        script = re.sub(pattern, replacement, script, flags=re.IGNORECASE)
    
    # Remove excessive punctuation
    script = re.sub(r'!{2,}', '!', script)
    script = re.sub(r'\?{2,}', '?', script)
    script = re.sub(r'\.{3,}', '...', script)
    
    # Clean up quotes and formatting - using simple string replacements
    script = script.replace('"', '"').replace('"', '"').replace('"', '"')
    script = script.replace("'", "'").replace("'", "'")
    script = script.replace("'''", "'")
    
    # Remove any remaining markdown or formatting artifacts
    script = re.sub(r'```.*?```', '', script, flags=re.DOTALL)
    script = re.sub(r'`.*?`', '', script)
    
    # Ensure proper sentence structure
    script = re.sub(r'\s+([.!?])', r'\1', script)
    script = re.sub(r'([.!?])\s*([A-Z])', r'\1 \2', script)
    
    # Remove any leading/trailing whitespace
    script = script.strip()
    
    # Ensure the script ends with proper punctuation
    if script and script[-1] not in '.!?':
        script += '.'
    
    return script

def remove_scene_directions(script):
    """
    Remove scene directions, stage directions, and other non-spoken content.
    This is essential for voiceover generation - only spoken dialogue should remain.
    
    Args:
        script (str): Script that may contain scene directions
        
    Returns:
        str: Script with only spoken content
    """
    if not script:
        return script
    
    # Remove scene headers (e.g., "Scene 1 (0:00-0:30): Description")
    script = re.sub(r'^Scene\s+\d+\s*\([^)]+\):\s*[^\n]*\n?', '', script, flags=re.MULTILINE | re.IGNORECASE)
    
    # Remove stage directions in parentheses
    script = re.sub(r'\([^)]*\)', '', script)
    
    # Remove square bracketed directions
    script = re.sub(r'\[[^\]]*\]', '', script)
    
    # Remove "Narrator:" labels and similar
    script = re.sub(r'^(Narrator|Host|Speaker):\s*', '', script, flags=re.MULTILINE | re.IGNORECASE)
    
    # Remove lines that are clearly directions (start with action words)
    direction_patterns = [
        r'^(Show|Cut to|Display|Open on|Focus on|Zoom in|Pan to|Fade|Transition).*$',
        r'^(Video|Audio|Music|Sound).*$',
        r'^(Note|Remember|Important).*$'
    ]
    for pattern in direction_patterns:
        script = re.sub(pattern, '', script, flags=re.MULTILINE | re.IGNORECASE)
    
    # Remove lines with only timestamps or technical info
    script = re.sub(r'^\d+:\d+[-–]\d+:\d+.*$', '', script, flags=re.MULTILINE)
    script = re.sub(r'^Length:.*$', '', script, flags=re.MULTILINE)
    script = re.sub(r'^Style:.*$', '', script, flags=re.MULTILINE)
    
    # Remove pipe characters (often used as separators in scripts)
    script = re.sub(r'\s*\|\s*', ' ', script)
    
    # Remove lines that are just formatting or metadata
    script = re.sub(r'^[-=]+$', '', script, flags=re.MULTILINE)
    
    # Clean up multiple newlines and spaces
    script = re.sub(r'\n\s*\n\s*\n+', '\n\n', script)  # Multiple newlines to double
    script = re.sub(r'\n\s*\n', '\n', script)          # Double newlines to single
    script = re.sub(r' +', ' ', script)                 # Multiple spaces to single
    
    # Remove empty lines and trim
    lines = [line.strip() for line in script.split('\n') if line.strip()]
    script = ' '.join(lines)
    
    return script.strip()

def split_script_into_segments(script, max_segment_length=200):
    """
    Split a script into smaller segments for better voiceover processing.
    Args:
        script (str): The script to split.
        max_segment_length (int): Maximum characters per segment.
    Returns:
        list: List of script segments.
    """
    if not script:
        return []
    
    # Split by sentences first
    sentences = re.split(r'(?<=[.!?])\s+', script)
    segments = []
    current_segment = ""
    
    for sentence in sentences:
        if len(current_segment) + len(sentence) <= max_segment_length:
            current_segment += sentence + " "
        else:
            if current_segment:
                segments.append(current_segment.strip())
            current_segment = sentence + " "
    
    # Add the last segment
    if current_segment:
        segments.append(current_segment.strip())
    
    return segments

def add_voiceover_instructions(script):
    """
    Add voiceover-friendly formatting and instructions.
    Args:
        script (str): The script to format.
    Returns:
        str: Script with voiceover instructions.
    """
    if not script:
        return script
    
    # Add pauses for natural speech
    script = re.sub(r'([.!?])\s+([A-Z])', r'\1 [PAUSE] \2', script)
    
    # Add emphasis markers for important words
    script = re.sub(r'\b(amazing|incredible|unbelievable|fantastic|awesome)\b', r'[EMPHASIS]\1[/EMPHASIS]', script, flags=re.IGNORECASE)
    
    return script
