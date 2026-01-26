"""
Format-Aware Video Processor
Handles video processing with platform-specific formats, aspect ratios, and safe zones.
"""
from typing import Optional, Dict, Tuple
from dataclasses import dataclass
from app.core.video_formats import VideoFormat, Platform, get_format
from app.core.logging import get_logger
import os

logger = get_logger(__name__)


@dataclass
class DurationValidation:
    """Result of duration validation"""
    valid: bool
    duration: float
    warnings: list


class FormatAwareVideoProcessor:
    """Processes videos with platform-specific format requirements"""
    
    def __init__(self, video_format: VideoFormat):
        self.format = video_format
        self.width = video_format.resolution[0]
        self.height = video_format.resolution[1]
        self.safe_zone = video_format.safe_zone
    
    def resize_clip_to_format(self, clip):
        """
        Resize and crop clip to target format with smart cropping
        
        Args:
            clip: MoviePy VideoFileClip
        
        Returns:
            Resized and cropped clip
        """
        clip_aspect = clip.w / clip.h
        target_aspect = self.width / self.height
        
        if clip_aspect > target_aspect:
            # Clip is wider - crop sides
            new_width = int(clip.h * target_aspect)
            x_center = clip.w // 2
            x1 = x_center - new_width // 2
            clip = clip.crop(x1=x1, x2=x1 + new_width)
        else:
            # Clip is taller - crop top/bottom
            new_height = int(clip.w / target_aspect)
            y_center = clip.h // 2
            y1 = y_center - new_height // 2
            clip = clip.crop(y1=y1, y2=y1 + new_height)
        
        # Resize to exact resolution
        return clip.resize((self.width, self.height))
    
    def get_safe_text_position(self, position: str = "bottom") -> Tuple:
        """
        Get text position within safe zone
        
        Args:
            position: "top", "bottom", or "center"
        
        Returns:
            (x, y) position tuple
        """
        if position == "top":
            return ("center", self.safe_zone["top"])
        elif position == "bottom":
            return ("center", self.height - self.safe_zone["bottom"])
        elif position == "center":
            return ("center", "center")
        else:
            return ("center", self.height - self.safe_zone["bottom"])
    
    def validate_duration(self, duration: float) -> DurationValidation:
        """
        Validate video duration against platform limits
        
        Args:
            duration: Video duration in seconds
        
        Returns:
            DurationValidation result
        """
        warnings = []
        valid = True
        
        if duration > self.format.max_duration:
            valid = False
            warnings.append(
                f"Duration {duration:.1f}s exceeds max {self.format.max_duration}s"
            )
        
        min_rec, max_rec = self.format.recommended_duration
        if duration < min_rec:
            warnings.append(
                f"Duration below recommended minimum {min_rec}s"
            )
        elif duration > max_rec:
            warnings.append(
                f"Duration above recommended maximum {max_rec}s"
            )
        
        return DurationValidation(
            valid=valid,
            duration=duration,
            warnings=warnings
        )
    
    def get_format_info(self) -> Dict:
        """Get format information as dictionary"""
        return {
            "platform": self.format.platform.value,
            "aspect_ratio": f"{self.format.aspect_ratio[0]}:{self.format.aspect_ratio[1]}",
            "resolution": f"{self.width}x{self.height}",
            "max_duration": self.format.max_duration,
            "recommended_duration": self.format.recommended_duration,
            "fps": self.format.fps,
            "safe_zone": self.safe_zone
        }


def process_video_for_platform(
    input_path: str,
    output_path: str,
    platform: Platform,
    target_duration: Optional[int] = None
) -> Dict:
    """
    Process video for a specific platform
    
    Args:
        input_path: Path to source video
        output_path: Path for output video
        platform: Target platform
        target_duration: Optional duration limit
    
    Returns:
        Processing result dictionary
    """
    from moviepy.editor import VideoFileClip
    
    video_format = get_format(platform)
    processor = FormatAwareVideoProcessor(video_format)
    
    logger.info(f"Processing video for {platform.value}")
    logger.info(f"Target: {video_format.resolution[0]}x{video_format.resolution[1]}")
    
    # Load original clip
    clip = VideoFileClip(input_path)
    
    # Validate duration
    duration_check = processor.validate_duration(
        target_duration or clip.duration
    )
    
    if duration_check.warnings:
        for warning in duration_check.warnings:
            logger.warning(warning)
    
    # Resize to format
    processed_clip = processor.resize_clip_to_format(clip)
    
    # Trim if needed
    if target_duration and target_duration < processed_clip.duration:
        processed_clip = processed_clip.subclip(0, target_duration)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Export
    processed_clip.write_videofile(
        output_path,
        fps=video_format.fps,
        codec='libx264',
        audio_codec='aac',
        preset='medium',
        threads=4,
        logger=None  # Suppress moviepy logs
    )
    
    # Cleanup
    clip.close()
    processed_clip.close()
    
    logger.info(f"Video processed successfully: {output_path}")
    
    return {
        "success": True,
        "output_path": output_path,
        "format": video_format.platform.value,
        "resolution": f"{video_format.resolution[0]}x{video_format.resolution[1]}",
        "duration_validation": {
            "valid": duration_check.valid,
            "warnings": duration_check.warnings
        }
    }
