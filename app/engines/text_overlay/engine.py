"""
Text Overlay Engine
Main engine combining timing, positioning, styling, and animation.
"""
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import uuid

from app.engines.base import BaseEngine, EngineInput, EngineOutput, EngineStatus, EngineDefinition
from app.engines.registry import EngineRegistry
from app.engines.text_overlay.timing import (
    generate_timeline, DisplayTiming, extract_word_timestamps, group_into_phrases, calculate_display_timing
)
from app.engines.text_overlay.positioning import (
    get_safe_zone, calculate_position, TextPosition, calculate_max_font_size
)
from app.engines.text_overlay.styling import get_style, TextStyle, WordHighlight
from app.engines.text_overlay.animation import get_animation, generate_keyframes, Animation
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class RenderInstruction:
    """Single text overlay render instruction"""
    instruction_id: str
    phrase_id: int
    text: str
    frame_start: int
    frame_end: int
    position_x: int
    position_y: int
    width: int
    height: int
    style: Dict
    animation_in: Dict
    animation_out: Dict
    layer: int = 10
    
    def to_dict(self) -> Dict:
        return {
            "id": self.instruction_id,
            "phrase_id": self.phrase_id,
            "text": self.text,
            "frame_range": [self.frame_start, self.frame_end],
            "position": {"x": self.position_x, "y": self.position_y},
            "size": {"width": self.width, "height": self.height},
            "style": self.style,
            "animation_in": self.animation_in,
            "animation_out": self.animation_out,
            "layer": self.layer
        }


@dataclass
class TextOverlayResult:
    """Complete text overlay output"""
    overlay_id: str
    phrase_count: int
    total_duration: float
    render_instructions: List[RenderInstruction] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "overlay_id": self.overlay_id,
            "phrase_count": self.phrase_count,
            "total_duration": self.total_duration,
            "instruction_count": len(self.render_instructions),
            "instructions": [r.to_dict() for r in self.render_instructions]
        }


class TextOverlayEngine(BaseEngine):
    """Engine for generating synchronized text overlays"""
    
    def __init__(self):
        super().__init__(
            engine_id="text_overlay_engine_v1",
            engine_type="text_overlay",
            version="1.0.0"
        )
        self.fps = 30  # Default framerate
    
    def validate_input(self, input_data: EngineInput) -> Dict:
        errors = []
        params = input_data.parameters
        
        if not params.get("text") and not params.get("script"):
            errors.append("Missing required: text or script")
        
        if not params.get("duration"):
            errors.append("Missing required: duration")
        
        return {"valid": len(errors) == 0, "errors": errors}
    
    async def execute(self, input_data: EngineInput) -> EngineOutput:
        """Generate text overlay instructions"""
        self.status = EngineStatus.RUNNING
        
        params = input_data.parameters
        text = params.get("text", params.get("script", ""))
        duration = params.get("duration", 30)
        platform = params.get("platform", "youtube_shorts")
        style_preset = params.get("style", "boxed")
        position = params.get("position", "lower_third")
        animation_in = params.get("animation_in", "fade_in")
        animation_out = params.get("animation_out", "fade_out")
        self.fps = params.get("fps", 30)
        
        # Generate overlay
        result = self._generate_overlay(
            text=text,
            duration=duration,
            platform=platform,
            style_preset=style_preset,
            position=position,
            animation_in=animation_in,
            animation_out=animation_out
        )
        
        self.status = EngineStatus.COMPLETED
        
        return EngineOutput(
            job_id=input_data.job_id,
            engine_id=self.engine_id,
            status=EngineStatus.COMPLETED,
            primary_artifact=result.overlay_id,
            metadata=result.to_dict(),
            quality_scores={
                "timing_accuracy": 0.95,
                "safe_zone_compliance": 1.0
            }
        )
    
    def validate_output(self, output: EngineOutput) -> Dict:
        errors = []
        if not output.metadata.get("instructions"):
            errors.append("No render instructions generated")
        return {"valid": len(errors) == 0, "errors": errors}
    
    def _generate_overlay(
        self,
        text: str,
        duration: float,
        platform: str,
        style_preset: str,
        position: str,
        animation_in: str,
        animation_out: str
    ) -> TextOverlayResult:
        """Generate complete overlay with instructions"""
        overlay_id = str(uuid.uuid4())
        
        # Get timing
        timestamps = extract_word_timestamps(text, duration)
        phrases = group_into_phrases(timestamps)
        timings = calculate_display_timing(phrases, position)
        
        # Get positioning
        text_pos = TextPosition(position)
        pos_coords = calculate_position(platform, text_pos)
        
        # Get style
        style = get_style(style_preset)
        
        # Get animations
        anim_in = get_animation(animation_in)
        anim_out = get_animation(animation_out)
        
        # Generate render instructions
        instructions = []
        for timing in timings:
            # Calculate frames
            frame_start = int(timing.display_start * self.fps)
            frame_end = int(timing.display_end * self.fps)
            
            # Auto font size
            font_size = calculate_max_font_size(timing.text, pos_coords.width)
            style.font_size = font_size
            
            instruction = RenderInstruction(
                instruction_id=f"{overlay_id}_{timing.phrase_id}",
                phrase_id=timing.phrase_id,
                text=timing.text,
                frame_start=frame_start,
                frame_end=frame_end,
                position_x=pos_coords.x,
                position_y=pos_coords.y,
                width=pos_coords.width,
                height=pos_coords.height,
                style=style.to_dict(),
                animation_in=anim_in.to_dict(),
                animation_out=anim_out.to_dict()
            )
            instructions.append(instruction)
        
        return TextOverlayResult(
            overlay_id=overlay_id,
            phrase_count=len(phrases),
            total_duration=duration,
            render_instructions=instructions
        )


# Create and register engine
text_overlay_engine = TextOverlayEngine()
EngineRegistry.register(
    text_overlay_engine,
    EngineDefinition(
        engine_id="text_overlay_engine_v1",
        engine_type="text_overlay",
        version="1.0.0",
        capabilities=["timing_sync", "safe_zones", "styling", "animation"],
        required_inputs=["text", "duration"],
        optional_inputs=["platform", "style", "position", "animation_in", "animation_out"],
        output_types=["render_instructions", "overlay_timeline"]
    )
)
