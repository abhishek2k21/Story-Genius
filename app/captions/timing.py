"""
Caption Timing
Timing extraction and cue generation.
"""
from typing import List
from app.captions.models import WordTiming, CaptionCue, create_cue_id


# Cue generation rules
MAX_CHARS_PER_LINE = 42
MAX_LINES_PER_CUE = 2
MAX_CUE_DURATION = 7.0  # seconds
MIN_CUE_DURATION = 1.0  # seconds
MIN_GAP_BETWEEN_CUES = 0.1  # seconds


def extract_word_timings(text: str, start_time: float, duration: float) -> List[WordTiming]:
    """Extract word-level timing from text and duration"""
    words = text.split()
    if not words:
        return []
    
    # Distribute time evenly across words
    word_duration = duration / len(words)
    
    timings = []
    current_time = start_time
    
    for word in words:
        timings.append(WordTiming(
            word=word,
            start_time=current_time,
            end_time=current_time + word_duration,
            confidence=1.0
        ))
        current_time += word_duration
    
    return timings


def generate_cues(
    caption_id: str,
    text: str,
    start_time: float,
    duration: float,
    max_chars: int = MAX_CHARS_PER_LINE,
    max_lines: int = MAX_LINES_PER_CUE
) -> List[CaptionCue]:
    """Generate caption cues from text with proper timing"""
    words = text.split()
    if not words:
        return []
    
    # Calculate timing per word
    word_duration = duration / len(words)
    
    cues = []
    current_words = []
    current_chars = 0
    current_lines = 1
    cue_start = start_time
    cue_index = 1
    word_index = 0
    
    for i, word in enumerate(words):
        word_len = len(word)
        
        # Check if adding this word exceeds line limit
        if current_chars + word_len + 1 > max_chars:
            if current_lines < max_lines:
                # Start new line
                current_lines += 1
                current_chars = word_len
            else:
                # Create cue and start new one
                if current_words:
                    cue_end = start_time + (i * word_duration)
                    cues.append(CaptionCue(
                        cue_id=create_cue_id(),
                        caption_id=caption_id,
                        cue_index=cue_index,
                        start_time=cue_start,
                        end_time=cue_end,
                        text=' '.join(current_words)
                    ))
                    cue_index += 1
                    cue_start = cue_end + MIN_GAP_BETWEEN_CUES
                
                current_words = [word]
                current_chars = word_len
                current_lines = 1
                continue
        else:
            current_chars += word_len + 1
        
        current_words.append(word)
    
    # Add final cue
    if current_words:
        cues.append(CaptionCue(
            cue_id=create_cue_id(),
            caption_id=caption_id,
            cue_index=cue_index,
            start_time=cue_start,
            end_time=start_time + duration,
            text=' '.join(current_words)
        ))
    
    # Split cues that are too long
    cues = split_long_cues(cues, MAX_CUE_DURATION)
    
    return cues


def split_long_cues(cues: List[CaptionCue], max_duration: float) -> List[CaptionCue]:
    """Split cues that exceed maximum duration"""
    result = []
    index = 1
    
    for cue in cues:
        if cue.duration <= max_duration:
            cue.cue_index = index
            result.append(cue)
            index += 1
        else:
            # Split into smaller cues
            words = cue.text.split()
            num_splits = int(cue.duration / max_duration) + 1
            words_per_split = len(words) // num_splits
            
            split_duration = cue.duration / num_splits
            current_start = cue.start_time
            
            for i in range(num_splits):
                start_idx = i * words_per_split
                end_idx = start_idx + words_per_split if i < num_splits - 1 else len(words)
                
                split_text = ' '.join(words[start_idx:end_idx])
                if split_text:
                    result.append(CaptionCue(
                        cue_id=create_cue_id(),
                        caption_id=cue.caption_id,
                        cue_index=index,
                        start_time=current_start,
                        end_time=current_start + split_duration,
                        text=split_text
                    ))
                    index += 1
                    current_start += split_duration
    
    return result


def validate_timing(cues: List[CaptionCue]) -> List[str]:
    """Validate cue timing"""
    issues = []
    
    for i, cue in enumerate(cues):
        # Check minimum duration
        if cue.duration < MIN_CUE_DURATION:
            issues.append(f"Cue {i+1}: Duration {cue.duration:.2f}s is too short")
        
        # Check maximum duration
        if cue.duration > MAX_CUE_DURATION:
            issues.append(f"Cue {i+1}: Duration {cue.duration:.2f}s exceeds maximum")
        
        # Check overlap with next cue
        if i < len(cues) - 1:
            gap = cues[i+1].start_time - cue.end_time
            if gap < 0:
                issues.append(f"Cue {i+1}-{i+2}: Cues overlap by {-gap:.3f}s")
    
    return issues


def calculate_reading_speed(cues: List[CaptionCue]) -> float:
    """Calculate words per minute reading speed"""
    if not cues:
        return 0.0
    
    total_words = sum(len(c.text.split()) for c in cues)
    total_duration = sum(c.duration for c in cues)
    
    if total_duration == 0:
        return 0.0
    
    return (total_words / total_duration) * 60
