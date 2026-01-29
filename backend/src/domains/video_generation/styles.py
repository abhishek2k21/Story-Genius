"""
Style Presets
Pre-defined visual styles for video generation.
"""
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class StyleCategory(str, Enum):
    """Style categories."""
    ANIMATION = "animation"
    CINEMATIC = "cinematic"
    ARTISTIC = "artistic"
    REALISTIC = "realistic"
    VINTAGE = "vintage"


class StylePreset(BaseModel):
    """A visual style preset."""
    id: str
    name: str
    category: StyleCategory
    prompt_prefix: str
    prompt_suffix: str = ""
    thumbnail_style: Optional[str] = None
    recommended_duration: int = 60  # seconds


# ========================
# Style Library
# ========================

STYLE_PRESETS: dict[str, StylePreset] = {
    # Animation styles
    "pixar": StylePreset(
        id="pixar",
        name="Pixar 3D",
        category=StyleCategory.ANIMATION,
        prompt_prefix="Pixar-style 3D animation, vibrant colors, expressive characters, smooth rendering",
        prompt_suffix="high quality Pixar animation aesthetic",
        thumbnail_style="bright, colorful, 3D animated",
    ),
    "anime": StylePreset(
        id="anime",
        name="Japanese Anime",
        category=StyleCategory.ANIMATION,
        prompt_prefix="Japanese anime style, detailed line art, expressive eyes, dynamic poses",
        prompt_suffix="high quality anime aesthetic",
        thumbnail_style="manga style, vibrant colors",
    ),
    "cartoon": StylePreset(
        id="cartoon",
        name="Classic Cartoon",
        category=StyleCategory.ANIMATION,
        prompt_prefix="Classic cartoon style, bold outlines, exaggerated expressions, playful",
        prompt_suffix="cartoon network style animation",
        thumbnail_style="fun, colorful, cartoon",
    ),
    "disney": StylePreset(
        id="disney",
        name="Disney Classic",
        category=StyleCategory.ANIMATION,
        prompt_prefix="Disney animation style, magical atmosphere, beautiful scenery, enchanting",
        prompt_suffix="Disney fairytale aesthetic",
        thumbnail_style="magical, dreamy, Disney",
    ),

    # Cinematic styles
    "cinematic": StylePreset(
        id="cinematic",
        name="Cinematic",
        category=StyleCategory.CINEMATIC,
        prompt_prefix="Cinematic film style, dramatic lighting, professional cinematography, widescreen",
        prompt_suffix="Hollywood movie quality",
        thumbnail_style="dramatic, professional, film-like",
    ),
    "documentary": StylePreset(
        id="documentary",
        name="Documentary",
        category=StyleCategory.CINEMATIC,
        prompt_prefix="Documentary film style, natural lighting, authentic, informative visuals",
        prompt_suffix="National Geographic quality",
        thumbnail_style="authentic, professional, educational",
    ),
    "noir": StylePreset(
        id="noir",
        name="Film Noir",
        category=StyleCategory.CINEMATIC,
        prompt_prefix="Film noir style, high contrast black and white, dramatic shadows, moody",
        prompt_suffix="classic noir atmosphere",
        thumbnail_style="black and white, dramatic, mysterious",
    ),
    "scifi": StylePreset(
        id="scifi",
        name="Sci-Fi Epic",
        category=StyleCategory.CINEMATIC,
        prompt_prefix="Science fiction film style, futuristic technology, epic scale, stunning visuals",
        prompt_suffix="blockbuster sci-fi quality",
        thumbnail_style="futuristic, epic, high-tech",
    ),

    # Artistic styles
    "watercolor": StylePreset(
        id="watercolor",
        name="Watercolor Art",
        category=StyleCategory.ARTISTIC,
        prompt_prefix="Watercolor painting style, soft edges, flowing colors, artistic brushstrokes",
        prompt_suffix="beautiful watercolor aesthetic",
        thumbnail_style="painted, soft, artistic",
    ),
    "oilpainting": StylePreset(
        id="oilpainting",
        name="Oil Painting",
        category=StyleCategory.ARTISTIC,
        prompt_prefix="Oil painting style, rich textures, classical composition, museum quality",
        prompt_suffix="renaissance masterpiece aesthetic",
        thumbnail_style="classical, textured, rich",
    ),
    "minimalist": StylePreset(
        id="minimalist",
        name="Minimalist",
        category=StyleCategory.ARTISTIC,
        prompt_prefix="Minimalist design, clean lines, simple shapes, elegant negative space",
        prompt_suffix="modern minimalist aesthetic",
        thumbnail_style="clean, simple, elegant",
    ),

    # Realistic styles
    "photorealistic": StylePreset(
        id="photorealistic",
        name="Photorealistic",
        category=StyleCategory.REALISTIC,
        prompt_prefix="Photorealistic rendering, extreme detail, natural lighting, lifelike",
        prompt_suffix="hyperrealistic quality",
        thumbnail_style="realistic, detailed, professional",
    ),
    "nature": StylePreset(
        id="nature",
        name="Nature Documentary",
        category=StyleCategory.REALISTIC,
        prompt_prefix="Nature documentary style, beautiful landscapes, wildlife, pristine environments",
        prompt_suffix="BBC Earth quality",
        thumbnail_style="natural, beautiful, wildlife",
    ),

    # Vintage styles
    "retro80s": StylePreset(
        id="retro80s",
        name="80s Retro",
        category=StyleCategory.VINTAGE,
        prompt_prefix="1980s aesthetic, neon colors, synthwave vibes, retro-futuristic",
        prompt_suffix="80s nostalgia",
        thumbnail_style="neon, retro, synthwave",
    ),
    "vintage": StylePreset(
        id="vintage",
        name="Vintage Film",
        category=StyleCategory.VINTAGE,
        prompt_prefix="Vintage film style, sepia tones, film grain, nostalgic atmosphere",
        prompt_suffix="classic vintage aesthetic",
        thumbnail_style="aged, nostalgic, classic",
    ),
}


def get_style(style_id: str) -> Optional[StylePreset]:
    """Get a style preset by ID."""
    return STYLE_PRESETS.get(style_id.lower())


def list_styles(category: Optional[StyleCategory] = None) -> list[StylePreset]:
    """List all styles, optionally filtered by category."""
    styles = list(STYLE_PRESETS.values())
    if category:
        styles = [s for s in styles if s.category == category]
    return styles


def apply_style_to_prompt(prompt: str, style_id: str) -> str:
    """Apply a style preset to a prompt."""
    style = get_style(style_id)
    if not style:
        return prompt

    return f"{style.prompt_prefix}. {prompt}. {style.prompt_suffix}"


def get_style_categories() -> list[dict]:
    """Get all style categories with their styles."""
    categories = {}
    for style in STYLE_PRESETS.values():
        if style.category not in categories:
            categories[style.category] = []
        categories[style.category].append({
            "id": style.id,
            "name": style.name,
        })

    return [
        {"category": cat.value, "styles": styles}
        for cat, styles in categories.items()
    ]
