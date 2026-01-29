"""
Video Template Library
Reusable templates for video generation.
"""
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from app.core.logging import get_logger

logger = get_logger(__name__)


class TemplateVisibility(Enum):
    """Template visibility levels"""
    PERSONAL = "personal"  # Only creator
    TEAM = "team"  # Shared within team
    PUBLIC = "public"  # Community marketplace


@dataclass
class VideoTemplate:
    """Video template data"""
    template_id: str
    creator_id: str
    name: str
    description: str
    visibility: TemplateVisibility
    parameters: Dict  # Video generation parameters
    created_at: datetime = field(default_factory=datetime.utcnow)
    team_id: Optional[str] = None
    use_count: int = 0
    tags: List[str] = field(default_factory=list)


class TemplateManager:
    """
    Video template library management.
    
    Features:
    - Personal templates
    - Team templates
    - Public marketplace
    - Template sharing
    - Template application
    """
    
    def __init__(self):
        self._templates: Dict[str, VideoTemplate] = {}
        self._creator_templates: Dict[str, List[str]] = {}  # creator_id -> template_ids
        self._team_templates: Dict[str, List[str]] = {}  # team_id -> template_ids
        self._public_templates: List[str] = []  # public template_ids
        logger.info("TemplateManager initialized")
        
        # Create default templates
        self._create_default_templates()
    
    def create_template(
        self,
        template_id: str,
        creator_id: str,
        name: str,
        description: str,
        parameters: Dict,
        visibility: TemplateVisibility = TemplateVisibility.PERSONAL,
        team_id: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> VideoTemplate:
        """
        Create a new template.
        
        Args:
            template_id: Unique template ID
            creator_id: Creator user ID
            name: Template name
            description: Template description
            parameters: Video generation parameters
            visibility: Visibility level
            team_id: Optional team ID for team templates
            tags: Optional tags
        
        Returns:
            Created template
        """
        template = VideoTemplate(
            template_id=template_id,
            creator_id=creator_id,
            name=name,
            description=description,
            visibility=visibility,
            parameters=parameters,
            team_id=team_id,
            tags=tags or []
        )
        
        self._templates[template_id] = template
        
        # Index by creator
        if creator_id not in self._creator_templates:
            self._creator_templates[creator_id] = []
        self._creator_templates[creator_id].append(template_id)
        
        # Index by team
        if visibility == TemplateVisibility.TEAM and team_id:
            if team_id not in self._team_templates:
                self._team_templates[team_id] = []
            self._team_templates[team_id].append(template_id)
        
        # Index public
        if visibility == TemplateVisibility.PUBLIC:
            self._public_templates.append(template_id)
        
        logger.info(
            f"Created template: {template_id} ({visibility.value}) by {creator_id}"
        )
        
        return template
    
    def get_template(self, template_id: str) -> Optional[VideoTemplate]:
        """Get template by ID"""
        return self._templates.get(template_id)
    
    def get_user_templates(
        self,
        user_id: str,
        include_team: bool = True
    ) -> List[VideoTemplate]:
        """
        Get templates accessible by user.
        
        Args:
            user_id: User ID
            include_team: Include team templates
        
        Returns:
            List of templates
        """
        templates = []
        
        # Personal templates
        template_ids = self._creator_templates.get(user_id, [])
        templates.extend([
            self._templates[tid] for tid in template_ids
            if tid in self._templates
        ])
        
        # Team templates (would need team_manager integration)
        # For now, just return personal
        
        return templates
    
    def get_public_templates(
        self,
        tag: Optional[str] = None,
        limit: int = 50
    ) -> List[VideoTemplate]:
        """
        Get public templates from marketplace.
        
        Args:
            tag: Optional tag filter
            limit: Number of templates to return
        
        Returns:
            List of public templates
        """
        templates = [
            self._templates[tid] for tid in self._public_templates
            if tid in self._templates
        ]
        
        # Filter by tag
        if tag:
            templates = [t for t in templates if tag in t.tags]
        
        # Sort by use count (most popular first)
        templates.sort(key=lambda t: t.use_count, reverse=True)
        
        return templates[:limit]
    
    def apply_template(
        self,
        template_id: str,
        user_id: str
    ) -> Dict:
        """
        Apply template (get parameters for video generation).
        
        Args:
            template_id: Template ID
            user_id: User applying template
        
        Returns:
            Template parameters
        """
        if template_id not in self._templates:
            raise ValueError(f"Template not found: {template_id}")
        
        template = self._templates[template_id]
        
        # Increment use count
        template.use_count += 1
        
        logger.info(f"Applied template {template_id} by {user_id}")
        
        return template.parameters.copy()
    
    def share_template(
        self,
        template_id: str,
        target_visibility: TemplateVisibility,
        team_id: Optional[str] = None
    ):
        """
        Share template (change visibility).
        
        Args:
            template_id: Template ID
            target_visibility: New visibility level
            team_id: Required for team visibility
        """
        if template_id not in self._templates:
            raise ValueError(f"Template not found: {template_id}")
        
        template = self._templates[template_id]
        old_visibility = template.visibility
        
        # Update visibility
        template.visibility = target_visibility
        template.team_id = team_id
        
        # Update indices
        if old_visibility == TemplateVisibility.PUBLIC:
            self._public_templates.remove(template_id)
        
        if target_visibility == TemplateVisibility.PUBLIC:
            self._public_templates.append(template_id)
        elif target_visibility == TemplateVisibility.TEAM and team_id:
            if team_id not in self._team_templates:
                self._team_templates[team_id] = []
            self._team_templates[team_id].append(template_id)
        
        logger.info(
            f"Shared template {template_id}: {old_visibility.value} → {target_visibility.value}"
        )
    
    def delete_template(self, template_id: str, user_id: str):
        """
        Delete template.
        
        Args:
            template_id: Template ID
            user_id: User deleting template
        """
        if template_id not in self._templates:
            return
        
        template = self._templates[template_id]
        
        # Only creator can delete
        if template.creator_id != user_id:
            raise PermissionError("Only creator can delete template")
        
        # Remove from indices
        creator_id = template.creator_id
        if creator_id in self._creator_templates:
            self._creator_templates[creator_id] = [
                tid for tid in self._creator_templates[creator_id]
                if tid != template_id
            ]
        
        if template.visibility == TemplateVisibility.PUBLIC:
            self._public_templates = [
                tid for tid in self._public_templates
                if tid != template_id
            ]
        
        if template.team_id and template.team_id in self._team_templates:
            self._team_templates[template.team_id] = [
                tid for tid in self._team_templates[template.team_id]
                if tid != template_id
            ]
        
        # Delete template
        del self._templates[template_id]
        
        logger.info(f"Deleted template {template_id}")
    
    def _create_default_templates(self):
        """Create default public templates"""
        defaults = [
            {
                "id": "template_comedy_short",
                "name": "Comedy Short",
                "description": "Fast-paced comedic video template",
                "params": {
                    "hook_quality": 85,
                    "pacing": "fast",
                    "tone": "humorous",
                    "duration": 60,
                    "genre": "comedy",
                    "has_music": True,
                    "has_effects": True
                },
                "tags": ["comedy", "short", "viral"]
            },
            {
                "id": "template_educational",
                "name": "Educational Tutorial",
                "description": "Clear educational content template",
                "params": {
                    "hook_quality": 75,
                    "pacing": "medium",
                    "tone": "educational",
                    "duration": 180,
                    "genre": "educational",
                    "has_music": False,
                    "has_effects": False
                },
                "tags": ["educational", "tutorial", "informative"]
            },
            {
                "id": "template_vlog",
                "name": "Vlog Style",
                "description": "Personal vlog template",
                "params": {
                    "hook_quality": 70,
                    "pacing": "medium",
                    "tone": "casual",
                    "duration": 120,
                    "genre": "vlog",
                    "has_music": True,
                    "has_effects": False
                },
                "tags": ["vlog", "personal", "lifestyle"]
            },
            {
                "id": "template_dramatic",
                "name": "Dramatic Story",
                "description": "Slow-paced dramatic narrative",
                "params": {
                    "hook_quality": 90,
                    "pacing": "slow",
                    "tone": "dramatic",
                    "duration": 150,
                    "genre": "drama",
                    "has_music": True,
                    "has_effects": True
                },
                "tags": ["drama", "story", "emotional"]
            },
            {
                "id": "template_product_review",
                "name": "Product Review",
                "description": "Honest product review format",
                "params": {
                    "hook_quality": 80,
                    "pacing": "medium",
                    "tone": "honest",
                    "duration": 90,
                    "genre": "review",
                    "has_music": False,
                    "has_effects": False
                },
                "tags": ["review", "product", "honest"]
            }
        ]
        
        for default in defaults:
            self.create_template(
                template_id=default["id"],
                creator_id="system",
                name=default["name"],
                description=default["description"],
                parameters=default["params"],
                visibility=TemplateVisibility.PUBLIC,
                tags=default["tags"]
            )
        
        logger.info(f"Created {len(defaults)} default templates")


# Global instance
template_manager = TemplateManager()
