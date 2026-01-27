"""
Caption Service
Main caption management operations.
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import threading

from app.captions.models import (
    Caption, CaptionCue, CaptionType, CaptionStatus, StylePreset,
    SYSTEM_PRESETS, SUPPORTED_LANGUAGES, create_caption_id
)
from app.captions.timing import generate_cues, validate_timing
from app.captions.srt import export_srt, validate_srt
from app.captions.vtt import export_vtt, validate_vtt
from app.captions.accessibility import validate_accessibility, generate_accessibility_report


class CaptionService:
    """Central caption management service"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._captions: Dict[str, Caption] = {}
            cls._instance._styles: Dict[str, StylePreset] = {p.preset_id: p for p in SYSTEM_PRESETS}
            cls._instance._lock = threading.Lock()
        return cls._instance
    
    def generate_captions(
        self,
        project_id: str,
        text: str,
        start_time: float,
        duration: float,
        language_code: str = "en",
        caption_type: CaptionType = CaptionType.SUBTITLE,
        style_preset_id: str = "default"
    ) -> Caption:
        """Generate captions from text"""
        caption_id = create_caption_id()
        
        # Generate cues
        cues = generate_cues(caption_id, text, start_time, duration)
        
        # Validate timing
        timing_issues = validate_timing(cues)
        
        # Calculate accessibility score
        caption = Caption(
            caption_id=caption_id,
            project_id=project_id,
            language_code=language_code,
            caption_type=caption_type,
            cues=cues,
            status=CaptionStatus.READY,
            style_preset_id=style_preset_id
        )
        
        score, _ = validate_accessibility(caption)
        caption.accessibility_score = score
        
        with self._lock:
            self._captions[caption_id] = caption
        
        return caption
    
    def get_caption(self, caption_id: str) -> Optional[Caption]:
        """Get caption by ID"""
        return self._captions.get(caption_id)
    
    def list_captions(self, project_id: str) -> List[Caption]:
        """List captions for project"""
        return [c for c in self._captions.values() if c.project_id == project_id]
    
    def update_cue(
        self,
        caption_id: str,
        cue_id: str,
        text: str = None,
        start_time: float = None,
        end_time: float = None
    ) -> Tuple[Optional[CaptionCue], str]:
        """Update a specific cue"""
        caption = self.get_caption(caption_id)
        if not caption:
            return None, "Caption not found"
        
        for cue in caption.cues:
            if cue.cue_id == cue_id:
                if text is not None:
                    cue.text = text
                if start_time is not None:
                    cue.start_time = start_time
                if end_time is not None:
                    cue.end_time = end_time
                
                caption.updated_at = datetime.utcnow()
                return cue, "Cue updated"
        
        return None, "Cue not found"
    
    def delete_caption(self, caption_id: str) -> bool:
        """Delete caption"""
        if caption_id in self._captions:
            del self._captions[caption_id]
            return True
        return False
    
    def export(
        self,
        caption_id: str,
        format: str = "srt",
        include_styling: bool = False,
        include_positioning: bool = False,
        style_preset_id: str = None
    ) -> Tuple[Optional[str], str]:
        """Export caption to format"""
        caption = self.get_caption(caption_id)
        if not caption:
            return None, "Caption not found"
        
        style = None
        if style_preset_id:
            style = self._styles.get(style_preset_id)
        
        if format == "srt":
            content = export_srt(caption, include_styling)
            issues = validate_srt(content)
        elif format == "vtt":
            content = export_vtt(caption, include_styling, include_positioning, style=style)
            issues = validate_vtt(content)
        else:
            return None, f"Unsupported format: {format}"
        
        if issues:
            return content, f"Exported with warnings: {len(issues)} issues"
        
        return content, "Export successful"
    
    def validate(self, caption_id: str, audio_duration: float = None) -> Optional[Dict]:
        """Validate caption accessibility"""
        caption = self.get_caption(caption_id)
        if not caption:
            return None
        
        return generate_accessibility_report(caption, audio_duration)
    
    def get_styles(self) -> List[StylePreset]:
        """Get all style presets"""
        return list(self._styles.values())
    
    def create_style(
        self,
        name: str,
        font_color: str = "#FFFFFF",
        background_color: str = "#000000",
        background_opacity: float = 0.75,
        text_align: str = "center"
    ) -> StylePreset:
        """Create custom style preset"""
        preset = StylePreset(
            preset_id=f"custom_{len(self._styles)}",
            name=name,
            font_color=font_color,
            background_color=background_color,
            background_opacity=background_opacity,
            text_align=text_align
        )
        
        self._styles[preset.preset_id] = preset
        return preset
    
    def get_languages(self) -> Dict[str, str]:
        """Get supported languages"""
        return SUPPORTED_LANGUAGES
    
    def add_language_version(
        self,
        caption_id: str,
        language_code: str,
        cues: List[Dict]
    ) -> Tuple[Optional[Caption], str]:
        """Add translation for caption"""
        original = self.get_caption(caption_id)
        if not original:
            return None, "Caption not found"
        
        if language_code not in SUPPORTED_LANGUAGES:
            return None, f"Unsupported language: {language_code}"
        
        # Create new caption with translated cues
        new_id = create_caption_id()
        new_cues = []
        
        for i, cue_data in enumerate(cues):
            original_cue = original.cues[i] if i < len(original.cues) else original.cues[-1]
            new_cues.append(CaptionCue(
                cue_id=f"{new_id}_{i}",
                caption_id=new_id,
                cue_index=i + 1,
                start_time=original_cue.start_time,
                end_time=original_cue.end_time,
                text=cue_data.get("text", "")
            ))
        
        translation = Caption(
            caption_id=new_id,
            project_id=original.project_id,
            language_code=language_code,
            caption_type=original.caption_type,
            cues=new_cues,
            status=CaptionStatus.READY,
            is_primary=False,
            is_auto_translated=True
        )
        
        score, _ = validate_accessibility(translation)
        translation.accessibility_score = score
        
        with self._lock:
            self._captions[new_id] = translation
        
        return translation, "Translation added"


caption_service = CaptionService()
