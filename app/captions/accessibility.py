"""
Accessibility
Caption accessibility validation and compliance.
"""
from typing import Dict, List, Tuple
from app.captions.models import Caption, CaptionCue
from app.captions.timing import calculate_reading_speed


# Accessibility standards
MIN_CONTRAST_RATIO = 4.5
MIN_READING_TIME_PER_WORD = 0.2  # seconds
MAX_READING_SPEED_WPM = 200
MIN_CUE_DISPLAY_TIME = 1.0  # seconds


def calculate_contrast_ratio(fg_color: str, bg_color: str) -> float:
    """Calculate contrast ratio between two colors"""
    def hex_to_luminance(hex_color: str) -> float:
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16) / 255
        g = int(hex_color[2:4], 16) / 255
        b = int(hex_color[4:6], 16) / 255
        
        def adjust(c):
            return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
        
        r, g, b = adjust(r), adjust(g), adjust(b)
        return 0.2126 * r + 0.7152 * g + 0.0722 * b
    
    L1 = hex_to_luminance(fg_color)
    L2 = hex_to_luminance(bg_color)
    
    lighter = max(L1, L2)
    darker = min(L1, L2)
    
    return (lighter + 0.05) / (darker + 0.05)


def validate_accessibility(caption: Caption) -> Tuple[float, List[str]]:
    """Validate caption accessibility, return score and issues"""
    issues = []
    score = 100.0
    
    if not caption.cues:
        return 0.0, ["No caption cues found"]
    
    # Check reading speed
    reading_speed = calculate_reading_speed(caption.cues)
    if reading_speed > MAX_READING_SPEED_WPM:
        issues.append(f"Reading speed {reading_speed:.0f} WPM exceeds recommended {MAX_READING_SPEED_WPM} WPM")
        score -= 15
    
    # Check individual cues
    short_cues = 0
    long_cues = 0
    
    for cue in caption.cues:
        # Minimum display time
        if cue.duration < MIN_CUE_DISPLAY_TIME:
            short_cues += 1
        
        # Maximum duration
        if cue.duration > 7.0:
            long_cues += 1
        
        # Minimum reading time per word
        words = len(cue.text.split())
        min_time = words * MIN_READING_TIME_PER_WORD
        if cue.duration < min_time:
            issues.append(f"Cue {cue.cue_index}: Insufficient reading time")
            score -= 2
    
    if short_cues > 0:
        issues.append(f"{short_cues} cues have insufficient display time")
        score -= short_cues * 3
    
    if long_cues > 0:
        issues.append(f"{long_cues} cues exceed maximum duration")
        score -= long_cues * 2
    
    # Check coverage
    if caption.total_duration > 0:
        cue_coverage = sum(c.duration for c in caption.cues) / caption.total_duration
        if cue_coverage < 0.5:
            issues.append(f"Caption coverage {cue_coverage*100:.0f}% is low")
            score -= 10
    
    return max(0.0, min(100.0, score)), issues


def check_completeness(caption: Caption, audio_duration: float) -> Dict:
    """Check caption completeness against audio"""
    coverage = (caption.total_duration / audio_duration * 100) if audio_duration > 0 else 0
    
    return {
        "audio_duration": audio_duration,
        "caption_duration": caption.total_duration,
        "coverage_percent": round(coverage, 1),
        "is_complete": coverage >= 90
    }


def suggest_improvements(caption: Caption) -> List[str]:
    """Suggest accessibility improvements"""
    suggestions = []
    
    if not caption.cues:
        return ["Add caption cues"]
    
    # Check for speaker identification
    has_speakers = any(c.speaker_id for c in caption.cues)
    if not has_speakers and len(set(c.speaker_id for c in caption.cues if c.speaker_id)) > 1:
        suggestions.append("Add speaker identification for multiple speakers")
    
    # Check for sound descriptions
    has_descriptions = any(c.is_sound_description for c in caption.cues)
    if not has_descriptions and caption.caption_type.value == "closed_caption":
        suggestions.append("Add sound descriptions for closed captions")
    
    # Check reading speed
    reading_speed = calculate_reading_speed(caption.cues)
    if reading_speed > 180:
        suggestions.append("Consider reducing text or extending cue duration")
    
    return suggestions


def generate_accessibility_report(caption: Caption, audio_duration: float = None) -> Dict:
    """Generate full accessibility report"""
    score, issues = validate_accessibility(caption)
    suggestions = suggest_improvements(caption)
    
    report = {
        "caption_id": caption.caption_id,
        "accessibility_score": round(score, 1),
        "issues": issues,
        "suggestions": suggestions,
        "metrics": {
            "cue_count": caption.cue_count,
            "word_count": caption.word_count,
            "total_duration": round(caption.total_duration, 2),
            "reading_speed_wpm": round(calculate_reading_speed(caption.cues), 1)
        }
    }
    
    if audio_duration:
        report["completeness"] = check_completeness(caption, audio_duration)
    
    return report
