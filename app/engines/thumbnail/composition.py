"""
Thumbnail Composition
Combine frame and text into final thumbnail.
"""
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import os

from app.engines.thumbnail.presets import ThumbStyle, TextPosition, get_style
from app.engines.thumbnail.analysis import FrameAnalysis, FaceDetection


@dataclass
class ComposedThumbnail:
    """A composed thumbnail with text overlay"""
    thumbnail_id: str
    source_frame_id: str
    source_path: str
    text: str
    text_position: TextPosition
    style: ThumbStyle
    output_path: str
    
    def to_dict(self) -> Dict:
        return {
            "id": self.thumbnail_id,
            "source_frame": self.source_frame_id,
            "text": self.text,
            "position": self.text_position.value,
            "style": self.style.name,
            "output": self.output_path
        }


def find_best_text_position(
    analysis: FrameAnalysis,
    width: int,
    height: int
) -> TextPosition:
    """Find optimal text position avoiding faces and busy areas"""
    faces = analysis.face_positions
    
    if not faces:
        # No faces, use bottom center (standard)
        return TextPosition.BOTTOM_CENTER
    
    # Check where faces are
    face = faces[0]
    face_center_x = face.x + face.width // 2
    face_center_y = face.y + face.height // 2
    
    # If face is in center, place text at bottom
    if face_center_x > width * 0.33 and face_center_x < width * 0.66:
        if face_center_y < height * 0.5:
            return TextPosition.BOTTOM_CENTER
        else:
            return TextPosition.TOP_CENTER
    
    # Face on left, text on right
    if face_center_x < width * 0.5:
        return TextPosition.RIGHT_THIRD
    
    # Face on right, text on left
    return TextPosition.LEFT_THIRD


def get_text_coordinates(
    position: TextPosition,
    width: int,
    height: int,
    text_height: int = 100
) -> Tuple[int, int]:
    """Get x, y coordinates for text position"""
    padding = 40
    
    if position == TextPosition.TOP_CENTER:
        return (width // 2, padding + text_height // 2)
    
    elif position == TextPosition.BOTTOM_CENTER:
        return (width // 2, height - padding - text_height // 2)
    
    elif position == TextPosition.LEFT_THIRD:
        return (width // 4, height // 2)
    
    elif position == TextPosition.RIGHT_THIRD:
        return (width * 3 // 4, height // 2)
    
    elif position == TextPosition.CENTER:
        return (width // 2, height // 2)
    
    return (width // 2, height - 100)


def compose_thumbnail(
    frame_path: str,
    frame_id: str,
    text: str,
    position: TextPosition,
    style: ThumbStyle,
    output_path: str,
    analysis: FrameAnalysis = None
) -> ComposedThumbnail:
    """Compose thumbnail with text overlay"""
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageFilter
        
        # Open frame
        img = Image.open(frame_path).convert('RGBA')
        width, height = img.size
        
        # Create text layer
        txt_layer = Image.new('RGBA', img.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(txt_layer)
        
        # Get font
        try:
            font = ImageFont.truetype("arial.ttf", style.font_size)
        except:
            font = ImageFont.load_default()
        
        # Get text position
        x, y = get_text_coordinates(position, width, height, style.font_size)
        
        # Get text bounding box
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Adjust position for centering
        x = x - text_width // 2
        y = y - text_height // 2
        
        # Draw background if specified
        if style.background_color and not style.background_color.startswith("gradient"):
            bg_padding = style.background_padding
            draw.rectangle(
                [x - bg_padding, y - bg_padding,
                 x + text_width + bg_padding, y + text_height + bg_padding],
                fill=style.background_color
            )
        
        # Draw shadow
        if style.shadow:
            shadow_offset = style.shadow_offset
            draw.text(
                (x + shadow_offset[0], y + shadow_offset[1]),
                text,
                font=font,
                fill=style.shadow_color
            )
        
        # Draw stroke/outline
        if style.stroke_width > 0:
            for dx in range(-style.stroke_width, style.stroke_width + 1):
                for dy in range(-style.stroke_width, style.stroke_width + 1):
                    if dx != 0 or dy != 0:
                        draw.text((x + dx, y + dy), text, font=font, fill=style.stroke_color)
        
        # Draw main text
        draw.text((x, y), text, font=font, fill=style.text_color)
        
        # Composite
        img = Image.alpha_composite(img, txt_layer)
        
        # Apply adjustments
        img = _apply_adjustments(img, analysis)
        
        # Save
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        img.convert('RGB').save(output_path, quality=95)
        
    except ImportError:
        # Create placeholder for testing
        _create_placeholder_thumbnail(output_path)
    
    return ComposedThumbnail(
        thumbnail_id=f"thumb_{frame_id}",
        source_frame_id=frame_id,
        source_path=frame_path,
        text=text,
        text_position=position,
        style=style,
        output_path=output_path
    )


def _apply_adjustments(img, analysis: Optional[FrameAnalysis]) -> "Image":
    """Apply brightness/contrast adjustments based on analysis"""
    try:
        from PIL import ImageEnhance
        
        if analysis:
            # Boost brightness if low
            if analysis.brightness < 50:
                enhancer = ImageEnhance.Brightness(img)
                img = enhancer.enhance(1.15)
            
            # Boost contrast if low
            if analysis.contrast < 50:
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(1.1)
            
            # Boost saturation/vibrancy if low
            if analysis.vibrancy < 50:
                enhancer = ImageEnhance.Color(img)
                img = enhancer.enhance(1.15)
        
        return img
    except:
        return img


def _create_placeholder_thumbnail(output_path: str):
    """Create placeholder thumbnail for testing"""
    try:
        from PIL import Image
        img = Image.new('RGB', (1280, 720), color=(100, 100, 150))
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        img.save(output_path)
    except:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            f.write("placeholder")
