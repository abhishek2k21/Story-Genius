"""
Thumbnail Export
Multi-platform export with size optimization.
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import os


class Platform(str, Enum):
    YOUTUBE = "youtube"
    YOUTUBE_SHORTS = "youtube_shorts"
    INSTAGRAM_REELS = "instagram_reels"
    INSTAGRAM_FEED = "instagram_feed"
    TIKTOK = "tiktok"


@dataclass
class PlatformSpec:
    """Platform thumbnail specification"""
    platform: Platform
    width: int
    height: int
    aspect_ratio: str
    max_file_size: int  # bytes, 0 = no limit
    format: str = "jpeg"
    
    def to_dict(self) -> Dict:
        return {
            "platform": self.platform.value,
            "resolution": f"{self.width}x{self.height}",
            "aspect_ratio": self.aspect_ratio,
            "max_size_kb": self.max_file_size // 1024 if self.max_file_size else None,
            "format": self.format
        }


# Platform specifications
PLATFORM_SPECS: Dict[Platform, PlatformSpec] = {
    Platform.YOUTUBE: PlatformSpec(
        platform=Platform.YOUTUBE,
        width=1280,
        height=720,
        aspect_ratio="16:9",
        max_file_size=2 * 1024 * 1024
    ),
    Platform.YOUTUBE_SHORTS: PlatformSpec(
        platform=Platform.YOUTUBE_SHORTS,
        width=1080,
        height=1920,
        aspect_ratio="9:16",
        max_file_size=2 * 1024 * 1024
    ),
    Platform.INSTAGRAM_REELS: PlatformSpec(
        platform=Platform.INSTAGRAM_REELS,
        width=1080,
        height=1920,
        aspect_ratio="9:16",
        max_file_size=0
    ),
    Platform.INSTAGRAM_FEED: PlatformSpec(
        platform=Platform.INSTAGRAM_FEED,
        width=1080,
        height=1080,
        aspect_ratio="1:1",
        max_file_size=0
    ),
    Platform.TIKTOK: PlatformSpec(
        platform=Platform.TIKTOK,
        width=1080,
        height=1920,
        aspect_ratio="9:16",
        max_file_size=0
    )
}


def get_platform_spec(platform: str) -> PlatformSpec:
    """Get spec for platform"""
    try:
        p = Platform(platform)
        return PLATFORM_SPECS.get(p, PLATFORM_SPECS[Platform.YOUTUBE])
    except ValueError:
        return PLATFORM_SPECS[Platform.YOUTUBE]


def list_platforms() -> Dict:
    """List all platform specifications"""
    return {"platforms": [s.to_dict() for s in PLATFORM_SPECS.values()]}


@dataclass
class ThumbnailExport:
    """Exported thumbnail for a platform"""
    export_id: str
    thumbnail_id: str
    platform: Platform
    file_path: str
    width: int
    height: int
    file_size: int
    format: str
    
    def to_dict(self) -> Dict:
        return {
            "id": self.export_id,
            "thumbnail": self.thumbnail_id,
            "platform": self.platform.value,
            "path": self.file_path,
            "resolution": f"{self.width}x{self.height}",
            "size_kb": self.file_size // 1024,
            "format": self.format
        }


def export_for_platform(
    source_path: str,
    thumbnail_id: str,
    platform: str,
    output_dir: str
) -> ThumbnailExport:
    """Export thumbnail for specific platform"""
    spec = get_platform_spec(platform)
    
    output_filename = f"{thumbnail_id}_{platform}.{spec.format}"
    output_path = os.path.join(output_dir, output_filename)
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        from PIL import Image
        
        img = Image.open(source_path)
        
        # Smart crop to aspect ratio
        img = _smart_crop(img, spec.width, spec.height)
        
        # Resize to target
        img = img.resize((spec.width, spec.height), Image.LANCZOS)
        
        # Save with optimization
        quality = 95
        img.convert('RGB').save(output_path, spec.format.upper(), quality=quality)
        
        # Check file size and reduce quality if needed
        if spec.max_file_size > 0:
            while os.path.getsize(output_path) > spec.max_file_size and quality > 60:
                quality -= 5
                img.convert('RGB').save(output_path, spec.format.upper(), quality=quality)
        
        file_size = os.path.getsize(output_path)
        
    except ImportError:
        # Create placeholder
        _create_placeholder_export(output_path, spec)
        file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
    
    return ThumbnailExport(
        export_id=f"export_{thumbnail_id}_{platform}",
        thumbnail_id=thumbnail_id,
        platform=spec.platform,
        file_path=output_path,
        width=spec.width,
        height=spec.height,
        file_size=file_size,
        format=spec.format
    )


def export_for_all_platforms(
    source_path: str,
    thumbnail_id: str,
    output_dir: str,
    platforms: List[str] = None
) -> List[ThumbnailExport]:
    """Export thumbnail for multiple platforms"""
    if platforms is None:
        platforms = [p.value for p in Platform]
    
    exports = []
    for platform in platforms:
        export = export_for_platform(source_path, thumbnail_id, platform, output_dir)
        exports.append(export)
    
    return exports


def _smart_crop(img, target_width: int, target_height: int):
    """Crop image to target aspect ratio preserving center"""
    src_width, src_height = img.size
    target_ratio = target_width / target_height
    src_ratio = src_width / src_height
    
    if abs(src_ratio - target_ratio) < 0.01:
        # Already correct ratio
        return img
    
    if src_ratio > target_ratio:
        # Source is wider, crop sides
        new_width = int(src_height * target_ratio)
        left = (src_width - new_width) // 2
        return img.crop((left, 0, left + new_width, src_height))
    else:
        # Source is taller, crop top/bottom
        new_height = int(src_width / target_ratio)
        top = (src_height - new_height) // 2
        return img.crop((0, top, src_width, top + new_height))


def _create_placeholder_export(output_path: str, spec: PlatformSpec):
    """Create placeholder export for testing"""
    try:
        from PIL import Image
        img = Image.new('RGB', (spec.width, spec.height), color=(100, 150, 200))
        img.save(output_path)
    except:
        with open(output_path, 'w') as f:
            f.write("placeholder")
