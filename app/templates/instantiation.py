"""
Template Instantiation
Creates projects and batches from templates with parameter validation.
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

from app.templates.models import Template, TemplateConfig, ElementType
from app.templates.service import TemplateService, TemplateValidationError
from app.batch.models import Batch, BatchConfig, BatchItem, BatchStatus
from app.batch.service import BatchService
from app.core.logging import get_logger

logger = get_logger(__name__)


class InstantiationError(Exception):
    """Raised when template instantiation fails"""
    pass


class TemplateInstantiator:
    """Handles template instantiation into projects and batches"""
    
    def __init__(self):
        self.template_service = TemplateService()
        self.batch_service = BatchService()
    
    def instantiate_batch(
        self,
        template_id: str,
        batch_name: str,
        content_items: List[str],
        overrides: Optional[Dict] = None,
        user_id: Optional[str] = None
    ) -> Batch:
        """
        Create a new batch from a template
        
        Args:
            template_id: Template to instantiate
            batch_name: Name for the new batch
            content_items: List of content/topics for each batch item
            overrides: Optional parameter overrides for constrained elements
            user_id: Owner of the new batch
        
        Returns:
            Created Batch
        """
        template = self.template_service.get_template(template_id)
        if not template:
            raise InstantiationError(f"Template {template_id} not found")
        
        # Build params from content
        params = {"content": content_items[0] if content_items else ""}
        if overrides:
            params.update(overrides)
        
        # Validate parameters
        validation = self.template_service.validate_instantiation_params(
            template, params
        )
        
        if not validation["valid"]:
            raise InstantiationError(
                f"Invalid parameters: {', '.join(validation['errors'])}"
            )
        
        # Build batch config from template
        config = template.get_current_config()
        batch_config = self._build_batch_config(config, overrides)
        
        # Create batch
        batch = self.batch_service.create_batch(
            name=batch_name,
            config=batch_config.to_dict(),
            description=f"Created from template: {template.name}",
            user_id=user_id
        )
        
        # Add content items
        self.batch_service.add_items(batch.id, content_items)
        
        # Record template usage
        self.template_service.record_usage(template_id, success=True)
        
        logger.info(
            f"Instantiated batch {batch.id} from template {template_id} "
            f"with {len(content_items)} items"
        )
        
        return batch
    
    def instantiate_project(
        self,
        template_id: str,
        project_name: str,
        content: str,
        overrides: Optional[Dict] = None,
        user_id: Optional[str] = None
    ) -> Dict:
        """
        Create a single project configuration from a template
        
        Args:
            template_id: Template to instantiate
            project_name: Name for the project
            content: The content/topic for this project
            overrides: Optional parameter overrides
            user_id: Owner of the project
        
        Returns:
            Project configuration dictionary
        """
        template = self.template_service.get_template(template_id)
        if not template:
            raise InstantiationError(f"Template {template_id} not found")
        
        # Validate parameters
        params = {"content": content}
        if overrides:
            params.update(overrides)
        
        validation = self.template_service.validate_instantiation_params(
            template, params
        )
        
        if not validation["valid"]:
            raise InstantiationError(
                f"Invalid parameters: {', '.join(validation['errors'])}"
            )
        
        # Build project config
        config = template.get_current_config()
        project_config = self._build_project_config(config, content, overrides)
        
        # Record usage
        self.template_service.record_usage(template_id, success=True)
        
        project = {
            "id": str(uuid.uuid4()),
            "name": project_name,
            "template_id": template_id,
            "template_version": template.current_version,
            "config": project_config,
            "user_id": user_id,
            "created_at": datetime.now().isoformat()
        }
        
        logger.info(f"Instantiated project from template {template_id}")
        
        return project
    
    def _build_batch_config(
        self,
        template_config: TemplateConfig,
        overrides: Optional[Dict] = None
    ) -> BatchConfig:
        """Build BatchConfig from template config"""
        overrides = overrides or {}
        
        def get_value(elem, override_key):
            if override_key in overrides:
                return overrides[override_key]
            return elem.value
        
        return BatchConfig(
            platform=get_value(template_config.platform, "platform"),
            duration=get_value(template_config.duration, "duration"),
            voice=get_value(template_config.voice, "voice"),
            genre=get_value(template_config.genre, "genre"),
            language=get_value(template_config.language, "language"),
            audience=get_value(template_config.audience, "audience"),
            style_profile=get_value(template_config.style_profile, "style_profile")
        )
    
    def _build_project_config(
        self,
        template_config: TemplateConfig,
        content: str,
        overrides: Optional[Dict] = None
    ) -> Dict:
        """Build project configuration dictionary"""
        overrides = overrides or {}
        
        def get_value(elem, override_key):
            if override_key in overrides:
                return overrides[override_key]
            return elem.value
        
        return {
            "platform": get_value(template_config.platform, "platform"),
            "duration": get_value(template_config.duration, "duration"),
            "voice": get_value(template_config.voice, "voice"),
            "genre": get_value(template_config.genre, "genre"),
            "language": get_value(template_config.language, "language"),
            "audience": get_value(template_config.audience, "audience"),
            "style_profile": get_value(template_config.style_profile, "style_profile"),
            "content": content
        }
    
    def preview_instantiation(
        self,
        template_id: str,
        params: Dict
    ) -> Dict:
        """Preview what instantiation would produce without committing"""
        template = self.template_service.get_template(template_id)
        if not template:
            raise InstantiationError(f"Template {template_id} not found")
        
        # Validate
        validation = self.template_service.validate_instantiation_params(
            template, params
        )
        
        # Build preview config
        config = template.get_current_config()
        preview_config = self._build_project_config(
            config,
            params.get("content", ""),
            params
        )
        
        return {
            "template_id": template_id,
            "template_name": template.name,
            "template_version": template.current_version,
            "validation": validation,
            "preview_config": preview_config,
            "fixed_elements": [
                {"name": e.name, "value": e.value}
                for e in config.get_fixed_elements()
            ],
            "variable_elements": [
                {"name": e.name, "provided": e.name in params}
                for e in config.get_variable_elements()
            ]
        }
