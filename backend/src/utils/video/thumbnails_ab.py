"""
Thumbnail Variants
A/B testing thumbnail generation.
"""
import hashlib
import random
from pathlib import Path
from typing import Optional

from src.core.logging import get_logger
from src.core.settings import settings
from src.domains.video_generation.styles import get_style
from src.utils.video.thumbnail import generate_thumbnail, ThumbnailConfig

logger = get_logger(__name__)


class ThumbnailVariant:
    """A thumbnail variant for A/B testing."""

    def __init__(
        self,
        variant_id: str,
        path: str,
        config: dict,
    ):
        self.variant_id = variant_id
        self.path = path
        self.config = config


def generate_ab_thumbnails(
    video_path: str,
    story_id: str,
    title: str,
    style_id: Optional[str] = None,
    num_variants: int = 3,
) -> list[ThumbnailVariant]:
    """
    Generate multiple thumbnail variants for A/B testing.

    Strategies:
    - Different frame positions
    - With/without text overlay
    - Different color treatments
    """
    output_dir = settings.media_dir / "thumbnails" / story_id
    output_dir.mkdir(parents=True, exist_ok=True)

    variants = []
    style = get_style(style_id) if style_id else None

    # Variant configurations
    configs = [
        {
            "name": "hero",
            "position": 0.3,  # 30% into video
            "add_text": True,
            "text_style": "bold",
        },
        {
            "name": "action",
            "position": 0.5,  # Middle of video
            "add_text": True,
            "text_style": "dynamic",
        },
        {
            "name": "clean",
            "position": 0.2,
            "add_text": False,
            "enhance": True,
        },
        {
            "name": "dramatic",
            "position": 0.7,
            "add_text": True,
            "text_style": "cinematic",
            "vignette": True,
        },
        {
            "name": "teaser",
            "position": 0.1,  # Early frame
            "add_text": True,
            "text_style": "minimal",
        },
    ]

    # Select variants to generate
    selected_configs = random.sample(configs, min(num_variants, len(configs)))

    for config in selected_configs:
        variant_id = f"{story_id}_{config['name']}"
        output_path = output_dir / f"thumb_{config['name']}.jpg"

        try:
            # Generate base thumbnail
            thumb_config = ThumbnailConfig(
                width=1280,
                height=720,
                position_ratio=config["position"],
            )

            thumb_path = generate_thumbnail(video_path, str(output_path), thumb_config)

            # Apply text overlay if configured
            if config.get("add_text") and thumb_path:
                thumb_path = _add_thumbnail_text(
                    thumb_path,
                    title,
                    config.get("text_style", "bold"),
                )

            if thumb_path:
                variants.append(ThumbnailVariant(
                    variant_id=variant_id,
                    path=thumb_path,
                    config=config,
                ))

        except Exception as e:
            logger.warning(f"Failed to generate variant {config['name']}: {e}")

    return variants


def _add_thumbnail_text(
    image_path: str,
    text: str,
    style: str = "bold",
) -> str:
    """Add text overlay to thumbnail."""
    try:
        from PIL import Image, ImageDraw, ImageFont

        img = Image.open(image_path)
        draw = ImageDraw.Draw(img)

        # Font settings based on style
        font_size = 60 if style == "bold" else 48
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()

        # Text positioning
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        x = (img.width - text_width) // 2
        y = img.height - text_height - 40  # Bottom with padding

        # Draw shadow
        draw.text((x + 2, y + 2), text, font=font, fill="black")
        # Draw text
        draw.text((x, y), text, font=font, fill="white")

        img.save(image_path)
        return image_path

    except Exception as e:
        logger.warning(f"Failed to add text to thumbnail: {e}")
        return image_path


def select_best_thumbnail(
    variants: list[ThumbnailVariant],
    selection_strategy: str = "first",
) -> Optional[ThumbnailVariant]:
    """
    Select the best thumbnail variant.

    Strategies:
    - first: Use first variant
    - random: Random selection
    - hero: Prefer "hero" variant
    """
    if not variants:
        return None

    if selection_strategy == "random":
        return random.choice(variants)

    if selection_strategy == "hero":
        for v in variants:
            if "hero" in v.variant_id:
                return v

    return variants[0]
