"""
Metadata Optimization Engine
Generates click-optimized titles, descriptions, and tags for short-form content.
"""
import json
import sys
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from enum import Enum

# Add StoryGenius to path
STORYGENIUS_PATH = Path(__file__).parent.parent.parent / "StoryGenius"
sys.path.insert(0, str(STORYGENIUS_PATH))

from app.core.logging import get_logger

logger = get_logger(__name__)


class TitleStyle(str, Enum):
    """Title generation styles."""
    CURIOSITY = "curiosity"       # "You won't believe..."
    QUESTION = "question"         # "Why do...?"
    SHOCK = "shock"              # "Scientists are SHOCKED"
    EMOJI_LIGHT = "emoji_light"  # One emoji at end
    EMOJI_HEAVY = "emoji_heavy"  # Multiple emojis


@dataclass
class TitleVariant:
    """A single title variant."""
    text: str
    style: TitleStyle
    score: float = 0.0


@dataclass 
class MetadataResult:
    """Complete metadata package for a video."""
    titles: List[TitleVariant]
    selected_title: str
    description: str
    tags: List[str]
    hashtags: List[str]


class MetadataEngine:
    """
    Generates optimized metadata for short-form content.
    """
    
    def __init__(self):
        self._llm = None
    
    def _get_llm(self):
        """Lazy load LLM."""
        if self._llm is None:
            try:
                from story_genius.llm.vertex_wrapper import VertexLLM
                self._llm = VertexLLM()
            except Exception as e:
                logger.error(f"Failed to initialize LLM: {e}")
                raise
        return self._llm
    
    def generate_titles(
        self,
        hook_text: str,
        topic: str,
        platform: str = "youtube_shorts",
        persona_id: str = None
    ) -> List[TitleVariant]:
        """
        Generate 5 title variants in different styles.
        
        Args:
            hook_text: The video's hook text
            topic: Content topic/theme
            platform: Target platform
            persona_id: Persona for tone matching
            
        Returns:
            List of TitleVariant objects
        """
        logger.info(f"Generating title variants for: {topic}")
        
        llm = self._get_llm()
        
        prompt = f"""
        Create 5 viral title variants for a {platform} video.
        
        Hook: "{hook_text}"
        Topic: {topic}
        {"Persona: " + persona_id if persona_id else ""}
        
        Generate ONE title in each style:
        1. CURIOSITY - Creates information gap ("You won't believe what happened...")
        2. QUESTION - Asks compelling question ("Why do cats...?")
        3. SHOCK - Surprising statement ("This changed EVERYTHING")
        4. EMOJI_LIGHT - One strategic emoji ("The truth about dinosaurs 🦕")
        5. EMOJI_HEAVY - Multiple emojis for energy ("🔥 INSANE discovery 🤯💥")
        
        Rules:
        - Max 60 characters per title
        - Front-load the hook
        - Platform: {platform}
        
        Output ONLY valid JSON array:
        [
            {{"text": "...", "style": "curiosity"}},
            {{"text": "...", "style": "question"}},
            {{"text": "...", "style": "shock"}},
            {{"text": "...", "style": "emoji_light"}},
            {{"text": "...", "style": "emoji_heavy"}}
        ]
        """
        
        try:
            response = llm.generate_content(prompt)
            response = response.replace("```json", "").replace("```", "").strip()
            data = json.loads(response)
            
            titles = []
            for item in data:
                try:
                    style = TitleStyle(item.get("style", "curiosity"))
                except ValueError:
                    style = TitleStyle.CURIOSITY
                
                titles.append(TitleVariant(
                    text=item.get("text", ""),
                    style=style
                ))
            
            logger.info(f"Generated {len(titles)} title variants")
            return titles
            
        except Exception as e:
            logger.error(f"Title generation failed: {e}")
            # Return fallback
            return [TitleVariant(
                text=hook_text[:60],
                style=TitleStyle.CURIOSITY
            )]
    
    def generate_description(
        self,
        hook_text: str,
        topic: str,
        platform: str = "youtube_shorts",
        keywords: List[str] = None
    ) -> str:
        """
        Generate SEO-optimized description with CTA.
        
        Args:
            hook_text: Video hook
            topic: Content topic
            platform: Target platform
            keywords: Optional keywords to include
            
        Returns:
            Optimized description string
        """
        llm = self._get_llm()
        
        keyword_str = ", ".join(keywords) if keywords else topic
        
        prompt = f"""
        Write a short, punchy description for a {platform} video.
        
        Hook: "{hook_text}"
        Topic: {topic}
        Keywords to include: {keyword_str}
        
        Requirements:
        1. Line 1: Restate the hook differently
        2. Line 2: Keyword-rich context (for SEO)
        3. Line 3: Strong CTA
        
        Max 150 characters total.
        
        Output the description text only, no quotes.
        """
        
        try:
            description = llm.generate_content(prompt).strip()
            description = description.strip('"').strip("'")
            logger.info(f"Generated description: {len(description)} chars")
            return description
            
        except Exception as e:
            logger.error(f"Description generation failed: {e}")
            return f"{hook_text}\n\n#shorts #{topic.replace(' ', '')}"
    
    def generate_tags(
        self,
        topic: str,
        platform: str = "youtube_shorts",
        persona_id: str = None,
        count: int = 15
    ) -> List[str]:
        """
        Generate platform-aware keyword tags.
        
        Args:
            topic: Content topic
            platform: Target platform
            persona_id: Persona for tone
            count: Number of tags
            
        Returns:
            List of tag strings
        """
        llm = self._get_llm()
        
        prompt = f"""
        Generate {count} SEO tags for a {platform} video about: {topic}
        
        {"Persona style: " + persona_id if persona_id else ""}
        
        Include:
        - Topic-specific tags
        - Platform tags (#shorts, #viral)
        - Trending adjacent tags
        - Niche tags
        
        Output as JSON array of strings:
        ["tag1", "tag2", ...]
        """
        
        try:
            response = llm.generate_content(prompt)
            response = response.replace("```json", "").replace("```", "").strip()
            tags = json.loads(response)
            
            # Ensure hashtag format
            formatted = []
            for tag in tags[:count]:
                if not tag.startswith("#"):
                    tag = f"#{tag.replace(' ', '')}"
                formatted.append(tag.lower())
            
            return formatted
            
        except Exception as e:
            logger.error(f"Tag generation failed: {e}")
            return [f"#{topic.replace(' ', '')}", "#shorts", "#viral"]
    
    def generate_metadata(
        self,
        hook_text: str,
        topic: str,
        platform: str = "youtube_shorts",
        persona_id: str = None,
        keywords: List[str] = None
    ) -> MetadataResult:
        """
        Generate complete metadata package.
        
        Args:
            hook_text: Video hook
            topic: Content topic
            platform: Target platform
            persona_id: Persona ID
            keywords: Optional keywords
            
        Returns:
            MetadataResult with all metadata
        """
        logger.info(f"Generating complete metadata for: {topic}")
        
        # Generate all components
        titles = self.generate_titles(hook_text, topic, platform, persona_id)
        description = self.generate_description(hook_text, topic, platform, keywords)
        tags = self.generate_tags(topic, platform, persona_id)
        
        # Select best title (prefer curiosity or question styles)
        priority = [TitleStyle.CURIOSITY, TitleStyle.QUESTION, TitleStyle.SHOCK]
        selected = titles[0].text
        
        for style in priority:
            match = next((t for t in titles if t.style == style), None)
            if match:
                selected = match.text
                break
        
        # Extract hashtags from tags
        hashtags = [t for t in tags if t.startswith("#")][:5]
        
        return MetadataResult(
            titles=titles,
            selected_title=selected,
            description=description,
            tags=tags,
            hashtags=hashtags
        )
    
    def format_for_platform(
        self,
        metadata: MetadataResult,
        platform: str
    ) -> Dict:
        """Format metadata for specific platform upload."""
        
        if platform == "youtube_shorts":
            return {
                "title": metadata.selected_title,
                "description": metadata.description + "\n\n" + " ".join(metadata.hashtags),
                "tags": [t.lstrip("#") for t in metadata.tags]
            }
        elif platform == "instagram_reels":
            return {
                "caption": metadata.selected_title + "\n\n" + metadata.description + "\n\n" + " ".join(metadata.hashtags)
            }
        elif platform == "tiktok":
            return {
                "caption": metadata.selected_title + " " + " ".join(metadata.hashtags[:8])
            }
        
        return {"title": metadata.selected_title, "description": metadata.description}
