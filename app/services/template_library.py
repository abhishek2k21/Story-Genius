"""
Video Template Library System.
Curated templates to accelerate video creation.
"""
from typing import List, Dict, Optional
from enum import Enum
from datetime import datetime
import uuid


class TemplateCategory(str, Enum):
    """Template categories."""
    SOCIAL_MEDIA = "social_media"
    MARKETING = "marketing"
    EDUCATION = "education"
    ENTERTAINMENT = "entertainment"
    BUSINESS = "business"


class VideoTemplate:
    """Video template model."""
    
    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        category: TemplateCategory,
        thumbnail_url: str,
        preview_url: Optional[str] = None,
        duration_seconds: int = 60,
        is_pro_only: bool = False,
        tags: Optional[List[str]] = None
    ):
        self.id = id
        self.name = name
        self.description = description
        self.category = category
        self.thumbnail_url = thumbnail_url
        self.preview_url = preview_url
        self.duration_seconds = duration_seconds
        self.is_pro_only = is_pro_only
        self.tags = tags or []
        self.created_at = datetime.now()
        self.usage_count = 0
        
        # Template configuration
        self.config = {
            "scenes": [],
            "transitions": ["fade", "slide"],
            "music": None,
            "fonts": ["Roboto", "Open Sans"],
            "colors": ["#FF6B6B", "#4ECDC4", "#45B7D1"],
            "customizable_fields": []
        }
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "thumbnail_url": self.thumbnail_url,
            "preview_url": self.preview_url,
            "duration": self.duration_seconds,
            "is_pro_only": self.is_pro_only,
            "tags": self.tags,
            "usage_count": self.usage_count,
            "created_at": self.created_at.isoformat()
        }


class TemplateLibrary:
    """Manage template library."""
    
    def __init__(self):
        self.templates: Dict[str, VideoTemplate] = {}
        self._seed_starter_templates()
    
    def _seed_starter_templates(self):
        """Create starter template collection."""
        
        # 1. Instagram Reel - Product Showcase (Free)
        self.add_template(VideoTemplate(
            id="tpl_instagram_product",
            name="Instagram Reel - Product Showcase",
            description="Modern, dynamic template perfect for product launches and feature highlights",
            category=TemplateCategory.SOCIAL_MEDIA,
            thumbnail_url="/templates/instagram_product.jpg",
            preview_url="/templates/previews/instagram_product.mp4",
            duration_seconds=30,
            is_pro_only=False,
            tags=["instagram", "product", "reel", "modern"]
        ))
        
        # 2. TikTok Tutorial (Free)
        self.add_template(VideoTemplate(
            id="tpl_tiktok_tutorial",
            name="TikTok - Tutorial Quick Tips",
            description="Clean, educational style for how-to content and quick tips",
            category=TemplateCategory.EDUCATION,
            thumbnail_url="/templates/tiktok_tutorial.jpg",
            preview_url="/templates/previews/tiktok_tutorial.mp4",
            duration_seconds=60,
            is_pro_only=False,
            tags=["tiktok", "tutorial", "education", "tips"]
        ))
        
        # 3. YouTube Short - Quote Animation (Free)
        self.add_template(VideoTemplate(
            id="tpl_youtube_quote",
            name="YouTube Short - Quote Animation",
            description="Minimal, elegant template for inspirational quotes and announcements",
            category=TemplateCategory.SOCIAL_MEDIA,
            thumbnail_url="/templates/youtube_quote.jpg",
            preview_url="/templates/previews/youtube_quote.mp4",
            duration_seconds=15,
            is_pro_only=False,
            tags=["youtube", "short", "quote", "minimal"]
        ))
        
        # 4. Product Demo (Pro)
        self.add_template(VideoTemplate(
            id="tpl_product_demo",
            name="Product Demo in 60 Seconds",
            description="Professional template for product demos and explainer videos",
            category=TemplateCategory.MARKETING,
            thumbnail_url="/templates/product_demo.jpg",
            preview_url="/templates/previews/product_demo.mp4",
            duration_seconds=60,
            is_pro_only=True,
            tags=["product", "demo", "professional", "marketing"]
        ))
        
        # 5. Brand Story (Pro)
        self.add_template(VideoTemplate(
            id="tpl_brand_story",
            name="Brand Story Template",
            description="Cinematic template for brand storytelling and company narratives",
            category=TemplateCategory.MARKETING,
            thumbnail_url="/templates/brand_story.jpg",
            preview_url="/templates/previews/brand_story.mp4",
            duration_seconds=90,
            is_pro_only=True,
            tags=["brand", "story", "cinematic", "marketing"]
        ))
        
        # 6. Educational Explainer (Free)
        self.add_template(VideoTemplate(
            id="tpl_edu_explainer",
            name="Educational Explainer",
            description="Clear diagrams and animations for educational content and tutorials",
            category=TemplateCategory.EDUCATION,
            thumbnail_url="/templates/edu_explainer.jpg",
            preview_url="/templates/previews/edu_explainer.mp4",
            duration_seconds=120,
            is_pro_only=False,
            tags=["education", "explainer", "tutorial", "diagrams"]
        ))
        
        # 7. Animated Statistics (Free)
        self.add_template(VideoTemplate(
            id="tpl_animated_stats",
            name="Animated Statistics",
            description="Data visualization template for statistics and reports",
            category=TemplateCategory.BUSINESS,
            thumbnail_url="/templates/animated_stats.jpg",
            preview_url="/templates/previews/animated_stats.mp4",
            duration_seconds=45,
            is_pro_only=False,
            tags=["statistics", "data", "visualization", "business"]
        ))
    
    def add_template(self, template: VideoTemplate):
        """Add template to library."""
        self.templates[template.id] = template
    
    def get_template(self, template_id: str) -> Optional[VideoTemplate]:
        """Get specific template."""
        return self.templates.get(template_id)
    
    def get_templates(
        self,
        category: Optional[str] = None,
        user_tier: str = "free",
        tags: Optional[List[str]] = None,
        sort_by: str = "popular"
    ) -> List[Dict]:
        """
        Get templates with filtering and sorting.
        
        Args:
            category: Filter by category
            user_tier: User subscription tier
            tags: Filter by tags
            sort_by: Sort order ('popular', 'recent', 'duration')
            
        Returns:
            List of templates
        """
        templates = list(self.templates.values())
        
        # Filter by category
        if category:
            templates = [
                t for t in templates
                if t.category.value == category
            ]
        
        # Filter by user tier
        if user_tier == "free":
            templates = [t for t in templates if not t.is_pro_only]
        
        # Filter by tags
        if tags:
            templates = [
                t for t in templates
                if any(tag in t.tags for tag in tags)
            ]
        
        # Sort
        if sort_by == "popular":
            templates.sort(key=lambda x: x.usage_count, reverse=True)
        elif sort_by == "recent":
            templates.sort(key=lambda x: x.created_at, reverse=True)
        elif sort_by == "duration":
            templates.sort(key=lambda x: x.duration_seconds)
        
        return [t.to_dict() for t in templates]
    
    def get_categories(self) -> List[Dict]:
        """Get all categories with template counts."""
        categories = {}
        
        for template in self.templates.values():
            cat = template.category.value
            if cat not in categories:
                categories[cat] = {
                    "name": cat,
                    "display_name": cat.replace("_", " ").title(),
                    "count": 0,
                    "free_count": 0,
                    "pro_count": 0
                }
            
            categories[cat]["count"] += 1
            if template.is_pro_only:
                categories[cat]["pro_count"] += 1
            else:
                categories[cat]["free_count"] += 1
        
        return list(categories.values())
    
    def use_template(
        self,
        template_id: str,
        user_id: str,
        customizations: Dict
    ) -> Dict:
        """
        Create video from template with user customizations.
        
        Args:
            template_id: Template ID
            user_id: User ID
            customizations: User customizations
            
        Returns:
            Video creation job details
        """
        template = self.templates.get(template_id)
        if not template:
            raise ValueError("Template not found")
        
        # Increment usage count
        template.usage_count += 1
        
        # Clone template config
        video_config = template.config.copy()
        
        # Apply user customizations
        video_config.update(customizations)
        
        # Create video job
        job_id = str(uuid.uuid4())
        
        # In production, this would create actual video job
        return {
            "job_id": job_id,
            "status": "queued",
            "template_id": template_id,
            "template_name": template.name,
            "estimated_completion_seconds": template.duration_seconds * 2
        }
    
    def get_popular_templates(self, limit: int = 5) -> List[Dict]:
        """Get most popular templates."""
        templates = list(self.templates.values())
        templates.sort(key=lambda x: x.usage_count, reverse=True)
        return [t.to_dict() for t in templates[:limit]]


# Global instance
template_library = TemplateLibrary()


# FastAPI endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.services.template_library import template_library

router = APIRouter(prefix="/templates", tags=["templates"])

@router.get("/")
async def list_templates(
    category: Optional[str] = None,
    tags: Optional[str] = None,
    sort_by: str = "popular",
    current_user: User = Depends(get_current_user)
):
    '''Get all templates.'''
    tag_list = tags.split(",") if tags else None
    
    return template_library.get_templates(
        category=category,
        user_tier=current_user.subscription_tier,
        tags=tag_list,
        sort_by=sort_by
    )

@router.get("/categories")
async def get_categories():
    '''Get template categories.'''
    return template_library.get_categories()

@router.get("/{template_id}")
async def get_template(template_id: str):
    '''Get specific template.'''
    template = template_library.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template.to_dict()

class UseTemplateRequest(BaseModel):
    customizations: Dict

@router.post("/{template_id}/use")
async def use_template(
    template_id: str,
    data: UseTemplateRequest,
    current_user: User = Depends(get_current_user)
):
    '''Create video from template.'''
    return template_library.use_template(
        template_id=template_id,
        user_id=current_user.id,
        customizations=data.customizations
    )

@router.get("/popular")
async def get_popular_templates(limit: int = 5):
    '''Get popular templates.'''
    return template_library.get_popular_templates(limit=limit)
"""
