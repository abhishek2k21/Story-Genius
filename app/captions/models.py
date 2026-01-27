"""
Caption Models
Data structures for captions and cues.
"""
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid


class CaptionType(str, Enum):
    SUBTITLE = "subtitle"
    CLOSED_CAPTION = "closed_caption"


class CaptionStatus(str, Enum):
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class TranslationStatus(str, Enum):
    PENDING = "pending"
    COMPLETE = "complete"
    REVIEWED = "reviewed"


# Supported languages
SUPPORTED_LANGUAGES = {
    "en": "English",
    "es": "Spanish",
    "pt": "Portuguese",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "nl": "Dutch",
    "pl": "Polish",
    "ru": "Russian",
    "ja": "Japanese",
    "ko": "Korean",
    "zh": "Chinese",
    "ar": "Arabic",
    "hi": "Hindi"
}


@dataclass
class WordTiming:
    """Word-level timing"""
    word: str
    start_time: float
    end_time: float
    confidence: float = 1.0
    
    def to_dict(self) -> Dict:
        return {
            "word": self.word,
            "start_time": round(self.start_time, 3),
            "end_time": round(self.end_time, 3),
            "confidence": self.confidence
        }


@dataclass
class CaptionCue:
    """Single caption cue"""
    cue_id: str
    caption_id: str
    cue_index: int
    start_time: float
    end_time: float
    text: str
    words: List[WordTiming] = field(default_factory=list)
    speaker_id: str = ""
    style_id: str = ""
    position: Dict = field(default_factory=dict)
    is_sound_description: bool = False
    
    def to_dict(self) -> Dict:
        return {
            "cue_id": self.cue_id,
            "cue_index": self.cue_index,
            "start_time": round(self.start_time, 3),
            "end_time": round(self.end_time, 3),
            "duration": round(self.end_time - self.start_time, 3),
            "text": self.text,
            "speaker_id": self.speaker_id,
            "is_sound_description": self.is_sound_description
        }
    
    @property
    def duration(self) -> float:
        return self.end_time - self.start_time


@dataclass
class Caption:
    """Caption track for a project"""
    caption_id: str
    project_id: str
    language_code: str
    caption_type: CaptionType
    cues: List[CaptionCue] = field(default_factory=list)
    status: CaptionStatus = CaptionStatus.PROCESSING
    is_primary: bool = True
    is_auto_translated: bool = False
    translation_status: TranslationStatus = TranslationStatus.PENDING
    style_preset_id: str = ""
    accessibility_score: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def cue_count(self) -> int:
        return len(self.cues)
    
    @property
    def total_duration(self) -> float:
        if not self.cues:
            return 0.0
        return self.cues[-1].end_time - self.cues[0].start_time
    
    @property
    def word_count(self) -> int:
        return sum(len(c.text.split()) for c in self.cues)
    
    def to_dict(self) -> Dict:
        return {
            "caption_id": self.caption_id,
            "project_id": self.project_id,
            "language_code": self.language_code,
            "language_name": SUPPORTED_LANGUAGES.get(self.language_code, "Unknown"),
            "caption_type": self.caption_type.value,
            "status": self.status.value,
            "cue_count": self.cue_count,
            "total_duration": round(self.total_duration, 2),
            "word_count": self.word_count,
            "is_primary": self.is_primary,
            "accessibility_score": self.accessibility_score,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class StylePreset:
    """Caption style preset"""
    preset_id: str
    name: str
    font_family: str = "Arial"
    font_size: str = "100%"
    font_color: str = "#FFFFFF"
    background_color: str = "#000000"
    background_opacity: float = 0.75
    text_align: str = "center"
    position: str = "bottom"
    is_system: bool = False
    
    def to_dict(self) -> Dict:
        return {
            "preset_id": self.preset_id,
            "name": self.name,
            "font_family": self.font_family,
            "font_size": self.font_size,
            "font_color": self.font_color,
            "background_color": self.background_color,
            "background_opacity": self.background_opacity,
            "text_align": self.text_align,
            "position": self.position,
            "is_system": self.is_system
        }


# System style presets
SYSTEM_PRESETS = [
    StylePreset(
        preset_id="default",
        name="Default",
        font_color="#FFFFFF",
        background_color="#000000",
        background_opacity=0.75,
        is_system=True
    ),
    StylePreset(
        preset_id="high_contrast",
        name="High Contrast",
        font_color="#FFFF00",
        background_color="#000000",
        background_opacity=1.0,
        is_system=True
    ),
    StylePreset(
        preset_id="minimal",
        name="Minimal",
        font_color="#FFFFFF",
        background_color="#000000",
        background_opacity=0.0,
        is_system=True
    ),
    StylePreset(
        preset_id="boxed",
        name="Boxed",
        font_color="#FFFFFF",
        background_color="#000000",
        background_opacity=1.0,
        is_system=True
    )
]


def create_caption_id() -> str:
    return str(uuid.uuid4())


def create_cue_id() -> str:
    return str(uuid.uuid4())
