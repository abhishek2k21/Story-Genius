"""
VTT Export
WebVTT subtitle format generator with styling support.
"""
from typing import Dict, List, Optional
from app.captions.models import Caption, CaptionCue, StylePreset


def format_vtt_timestamp(seconds: float) -> str:
    """Format seconds to VTT timestamp: HH:MM:SS.mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"


def format_cue_settings(
    align: str = None,
    position: str = None,
    line: str = None,
    size: str = None
) -> str:
    """Format VTT cue settings"""
    settings = []
    
    if align:
        settings.append(f"align:{align}")
    if position:
        settings.append(f"position:{position}")
    if line:
        settings.append(f"line:{line}")
    if size:
        settings.append(f"size:{size}")
    
    return ' '.join(settings)


def apply_styling(text: str, style: StylePreset = None, speaker: str = None) -> str:
    """Apply VTT styling tags to text"""
    styled = text
    
    if speaker:
        styled = f"<v {speaker}>{styled}</v>"
    
    return styled


def export_vtt(
    caption: Caption,
    include_styling: bool = False,
    include_positioning: bool = False,
    include_speaker: bool = False,
    style: StylePreset = None
) -> str:
    """Export caption to VTT format"""
    lines = ["WEBVTT"]
    
    # Add metadata
    lines.append(f"Kind: {caption.caption_type.value}")
    lines.append(f"Language: {caption.language_code}")
    lines.append("")
    
    for cue in caption.cues:
        # Timestamp line
        ts_line = f"{format_vtt_timestamp(cue.start_time)} --> {format_vtt_timestamp(cue.end_time)}"
        
        # Add positioning settings
        if include_positioning and cue.position:
            settings = format_cue_settings(
                align=cue.position.get("align"),
                position=cue.position.get("position"),
                line=cue.position.get("line")
            )
            if settings:
                ts_line += f" {settings}"
        
        lines.append(ts_line)
        
        # Text with styling
        text = cue.text
        
        if include_styling:
            if cue.is_sound_description:
                text = f"<i>[{text}]</i>"
            elif style:
                text = apply_styling(text, style)
        
        if include_speaker and cue.speaker_id:
            text = f"<v {cue.speaker_id}>{text}</v>"
        
        lines.append(text)
        lines.append("")
    
    return '\n'.join(lines)


def parse_vtt_timestamp(timestamp: str) -> float:
    """Parse VTT timestamp to seconds"""
    parts = timestamp.replace('.', ':').split(':')
    
    if len(parts) == 4:
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = int(parts[2])
        millis = int(parts[3])
    elif len(parts) == 3:
        hours = 0
        minutes = int(parts[0])
        seconds = int(parts[1])
        millis = int(parts[2])
    else:
        return 0.0
    
    return hours * 3600 + minutes * 60 + seconds + millis / 1000


def validate_vtt(content: str) -> List[str]:
    """Validate VTT content"""
    issues = []
    lines = content.strip().split('\n')
    
    if not lines:
        issues.append("Empty VTT file")
        return issues
    
    # Check header
    if not lines[0].startswith("WEBVTT"):
        issues.append("Missing WEBVTT header")
    
    # Find first cue
    i = 1
    while i < len(lines) and not ' --> ' in lines[i]:
        i += 1
    
    prev_end = 0.0
    cue_count = 0
    
    while i < len(lines):
        if ' --> ' in lines[i]:
            cue_count += 1
            
            # Parse timestamp
            ts_parts = lines[i].split(' --> ')
            try:
                start = parse_vtt_timestamp(ts_parts[0])
                # End might have settings after it
                end_part = ts_parts[1].split()[0]
                end = parse_vtt_timestamp(end_part)
                
                if start >= end:
                    issues.append(f"Cue {cue_count}: Start time >= end time")
                
                if start < prev_end:
                    issues.append(f"Cue {cue_count}: Overlaps with previous cue")
                
                prev_end = end
            except (IndexError, ValueError):
                issues.append(f"Unable to parse timestamp at line {i+1}")
            
            # Check for text
            i += 1
            if i >= len(lines) or not lines[i].strip():
                issues.append(f"Cue {cue_count}: Missing text content")
        
        i += 1
    
    return issues


def generate_vtt_styles(presets: List[StylePreset]) -> str:
    """Generate VTT style block"""
    if not presets:
        return ""
    
    styles = ["STYLE"]
    
    for preset in presets:
        style_rule = f"""::cue(.{preset.preset_id}) {{
  color: {preset.font_color};
  background-color: {preset.background_color};
  font-family: {preset.font_family};
  text-align: {preset.text_align};
}}"""
        styles.append(style_rule)
    
    return '\n'.join(styles)
