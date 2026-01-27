"""
SRT Export
SubRip subtitle format generator.
"""
from typing import List
from app.captions.models import Caption, CaptionCue


def format_srt_timestamp(seconds: float) -> str:
    """Format seconds to SRT timestamp: HH:MM:SS,mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def format_cue_as_srt(cue: CaptionCue) -> str:
    """Format single cue as SRT"""
    lines = [
        str(cue.cue_index),
        f"{format_srt_timestamp(cue.start_time)} --> {format_srt_timestamp(cue.end_time)}",
        cue.text
    ]
    return '\n'.join(lines)


def export_srt(caption: Caption, include_styling: bool = False) -> str:
    """Export caption to SRT format"""
    if not caption.cues:
        return ""
    
    cue_blocks = []
    
    for cue in caption.cues:
        text = cue.text
        
        # Add basic styling if requested
        if include_styling and cue.is_sound_description:
            text = f"[{text}]"
        
        cue_str = f"{cue.cue_index}\n"
        cue_str += f"{format_srt_timestamp(cue.start_time)} --> {format_srt_timestamp(cue.end_time)}\n"
        cue_str += text
        
        cue_blocks.append(cue_str)
    
    return '\n\n'.join(cue_blocks) + '\n'


def parse_srt_timestamp(timestamp: str) -> float:
    """Parse SRT timestamp to seconds"""
    parts = timestamp.replace(',', ':').split(':')
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = int(parts[2])
    millis = int(parts[3])
    
    return hours * 3600 + minutes * 60 + seconds + millis / 1000


def validate_srt(content: str) -> List[str]:
    """Validate SRT content"""
    issues = []
    lines = content.strip().split('\n')
    
    if not lines:
        issues.append("Empty SRT file")
        return issues
    
    cue_count = 0
    i = 0
    prev_end = 0.0
    
    while i < len(lines):
        # Skip empty lines
        if not lines[i].strip():
            i += 1
            continue
        
        # Expect cue number
        try:
            cue_num = int(lines[i].strip())
            cue_count += 1
            
            if cue_num != cue_count:
                issues.append(f"Cue number mismatch at line {i+1}: expected {cue_count}, got {cue_num}")
        except ValueError:
            issues.append(f"Invalid cue number at line {i+1}")
            i += 1
            continue
        
        i += 1
        
        # Expect timestamp line
        if i >= len(lines):
            issues.append(f"Missing timestamp after cue {cue_count}")
            break
        
        ts_line = lines[i].strip()
        if ' --> ' not in ts_line:
            issues.append(f"Invalid timestamp format at line {i+1}")
        else:
            parts = ts_line.split(' --> ')
            try:
                start = parse_srt_timestamp(parts[0])
                end = parse_srt_timestamp(parts[1].split()[0])
                
                if start >= end:
                    issues.append(f"Cue {cue_count}: Start time >= end time")
                
                if start < prev_end:
                    issues.append(f"Cue {cue_count}: Overlaps with previous cue")
                
                prev_end = end
            except (IndexError, ValueError):
                issues.append(f"Unable to parse timestamp at line {i+1}")
        
        i += 1
        
        # Expect text lines until empty line
        if i >= len(lines) or not lines[i].strip():
            issues.append(f"Cue {cue_count}: Missing text content")
        
        while i < len(lines) and lines[i].strip():
            i += 1
    
    return issues
