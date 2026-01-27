"""
Text Overlay Timing Engine
Handles word-level timestamps and phrase grouping for synchronized text display.
"""
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum


@dataclass
class WordTimestamp:
    """Timestamp for a single word"""
    word: str
    start_time: float  # seconds
    end_time: float
    duration: float = 0
    confidence: float = 1.0
    is_segment_start: bool = False
    is_emphasis: bool = False
    
    def __post_init__(self):
        self.duration = self.end_time - self.start_time
    
    def to_dict(self) -> Dict:
        return {
            "word": self.word,
            "start": round(self.start_time, 3),
            "end": round(self.end_time, 3),
            "duration": round(self.duration, 3),
            "is_emphasis": self.is_emphasis
        }


@dataclass
class Phrase:
    """Group of words for display"""
    phrase_id: int
    text: str
    words: List[WordTimestamp] = field(default_factory=list)
    start_time: float = 0
    end_time: float = 0
    segment_id: Optional[str] = None
    
    @property
    def word_count(self) -> int:
        return len(self.words)
    
    @property
    def duration(self) -> float:
        return self.end_time - self.start_time
    
    def to_dict(self) -> Dict:
        return {
            "id": self.phrase_id,
            "text": self.text,
            "start": round(self.start_time, 3),
            "end": round(self.end_time, 3),
            "duration": round(self.duration, 3),
            "word_count": self.word_count,
            "segment": self.segment_id
        }


# Timing configuration
MIN_DISPLAY_TIME = 0.8  # seconds
MAX_DISPLAY_TIME = 4.0  # seconds
WORDS_PER_SECOND = 3.5  # average reading speed
TRANSITION_BUFFER = 0.1  # gap between phrases
EARLY_APPEARANCE = 0.1  # show text slightly before audio
MAX_WORDS_PER_PHRASE = 7
PUNCTUATION_BREAKS = {'.', '!', '?', ',', ';', ':'}


def extract_word_timestamps(
    text: str,
    total_duration: float,
    segment_boundaries: List[int] = None
) -> List[WordTimestamp]:
    """
    Generate word-level timestamps from text and duration.
    For actual TTS, this would come from the audio engine.
    """
    words = text.split()
    if not words:
        return []
    
    segment_starts = set(segment_boundaries or [])
    
    # Calculate time per word
    time_per_word = total_duration / len(words)
    
    timestamps = []
    current_time = 0
    
    for i, word in enumerate(words):
        # Check for emphasis (caps or ends with !)
        is_emphasis = word.isupper() or word.endswith('!')
        
        # Check segment boundary
        is_segment_start = i in segment_starts
        
        word_duration = time_per_word
        
        # Pause after punctuation
        has_punctuation = any(p in word for p in PUNCTUATION_BREAKS)
        if has_punctuation:
            word_duration *= 1.3
        
        timestamps.append(WordTimestamp(
            word=word,
            start_time=current_time,
            end_time=current_time + word_duration,
            is_segment_start=is_segment_start,
            is_emphasis=is_emphasis
        ))
        
        current_time += word_duration
    
    return timestamps


def group_into_phrases(
    timestamps: List[WordTimestamp],
    max_words: int = MAX_WORDS_PER_PHRASE
) -> List[Phrase]:
    """Group words into displayable phrases"""
    if not timestamps:
        return []
    
    phrases = []
    current_words = []
    phrase_id = 0
    current_segment = None
    
    for ts in timestamps:
        # Start new phrase on segment boundary or max words
        should_break = (
            len(current_words) >= max_words or
            ts.is_segment_start or
            (current_words and any(p in current_words[-1].word for p in '.!?'))
        )
        
        if should_break and current_words:
            phrases.append(_create_phrase(phrase_id, current_words, current_segment))
            phrase_id += 1
            current_words = []
        
        if ts.is_segment_start:
            current_segment = f"segment_{phrase_id}"
        
        current_words.append(ts)
    
    # Final phrase
    if current_words:
        phrases.append(_create_phrase(phrase_id, current_words, current_segment))
    
    return phrases


def _create_phrase(phrase_id: int, words: List[WordTimestamp], segment_id: str = None) -> Phrase:
    """Create a phrase from word list"""
    text = ' '.join(w.word for w in words)
    return Phrase(
        phrase_id=phrase_id,
        text=text,
        words=words,
        start_time=words[0].start_time,
        end_time=words[-1].end_time,
        segment_id=segment_id
    )


@dataclass
class DisplayTiming:
    """Calculated display timing for a phrase"""
    phrase_id: int
    text: str
    display_start: float
    display_end: float
    audio_start: float
    audio_end: float
    position: str = "lower_third"
    transition_in: str = "fade_in"
    transition_out: str = "fade_out"
    
    @property
    def display_duration(self) -> float:
        return self.display_end - self.display_start
    
    def to_dict(self) -> Dict:
        return {
            "phrase_id": self.phrase_id,
            "text": self.text,
            "display_start": round(self.display_start, 3),
            "display_end": round(self.display_end, 3),
            "display_duration": round(self.display_duration, 3),
            "audio_start": round(self.audio_start, 3),
            "audio_end": round(self.audio_end, 3),
            "position": self.position,
            "transition_in": self.transition_in,
            "transition_out": self.transition_out
        }


def calculate_display_timing(
    phrases: List[Phrase],
    position: str = "lower_third"
) -> List[DisplayTiming]:
    """Calculate display timing from phrases with conflict resolution"""
    timings = []
    
    for phrase in phrases:
        # Start slightly before audio
        display_start = max(0, phrase.start_time - EARLY_APPEARANCE)
        
        # Calculate minimum display time based on word count
        min_time = max(MIN_DISPLAY_TIME, phrase.word_count / WORDS_PER_SECOND)
        
        # Calculate display end
        display_end = max(
            phrase.end_time + TRANSITION_BUFFER,
            display_start + min_time
        )
        
        # Cap at max display time
        if display_end - display_start > MAX_DISPLAY_TIME:
            display_end = display_start + MAX_DISPLAY_TIME
        
        timings.append(DisplayTiming(
            phrase_id=phrase.phrase_id,
            text=phrase.text,
            display_start=display_start,
            display_end=display_end,
            audio_start=phrase.start_time,
            audio_end=phrase.end_time,
            position=position
        ))
    
    # Resolve overlaps
    timings = _resolve_overlaps(timings)
    
    return timings


def _resolve_overlaps(timings: List[DisplayTiming]) -> List[DisplayTiming]:
    """Resolve overlapping display windows"""
    if len(timings) <= 1:
        return timings
    
    for i in range(len(timings) - 1):
        current = timings[i]
        next_timing = timings[i + 1]
        
        # If overlap, adjust current end
        if current.display_end > next_timing.display_start:
            current.display_end = next_timing.display_start - TRANSITION_BUFFER
            
            # Ensure minimum display time
            if current.display_end - current.display_start < MIN_DISPLAY_TIME:
                current.display_end = current.display_start + MIN_DISPLAY_TIME
    
    return timings


def generate_timeline(
    text: str,
    duration: float,
    position: str = "lower_third"
) -> Dict:
    """Generate complete text overlay timeline"""
    # Extract timestamps
    timestamps = extract_word_timestamps(text, duration)
    
    # Group into phrases
    phrases = group_into_phrases(timestamps)
    
    # Calculate display timing
    timings = calculate_display_timing(phrases, position)
    
    return {
        "total_duration": duration,
        "phrase_count": len(phrases),
        "phrases": [p.to_dict() for p in phrases],
        "timings": [t.to_dict() for t in timings]
    }
