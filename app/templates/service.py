"""
Template Service
Manages template lifecycle, validation, and storage.
"""
from typing import Dict, List, Optional
from datetime import datetime
import json
import os

from app.templates.models import (
    Template, TemplateVersion, TemplateConfig,
    TemplateElement, ElementType, ConstraintBounds
)
from app.batch.models import Batch
from app.core.video_formats import Platform, get_format
from app.core.logging import get_logger

logger = get_logger(__name__)

# In-memory storage (replace with database in production)
_templates: Dict[str, Template] = {}


class TemplateValidationError(Exception):
    """Raised when template validation fails"""
    pass


class TemplateService:
    """Service for managing templates"""
    
    def __init__(self):
        self.storage_path = ".story_assets/templates"
        os.makedirs(self.storage_path, exist_ok=True)
    
    # ==================== CRUD Operations ====================
    
    def create_template(
        self,
        name: str,
        config: Optional[TemplateConfig] = None,
        description: Optional[str] = None,
        user_id: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Template:
        """Create new template manually"""
        template = Template(
            name=name,
            description=description,
            user_id=user_id,
            source_type="manual",
            tags=tags or []
        )
        
        if config:
            template.versions = [TemplateVersion(version=1, config=config)]
        
        # Validate before saving
        self._validate_template(template)
        
        _templates[template.id] = template
        self._save_template(template)
        
        logger.info(f"Created template {template.id}: {name}")
        return template
    
    def create_from_batch(
        self,
        batch: Batch,
        name: str,
        description: Optional[str] = None
    ) -> Template:
        """Create template from successful batch configuration"""
        # Extract config from batch
        config = TemplateConfig.from_batch_config(batch.config.to_dict())
        
        template = Template(
            name=name,
            description=description or f"Created from batch: {batch.name}",
            source_type="batch",
            source_id=batch.id,
            user_id=batch.user_id
        )
        
        template.versions = [TemplateVersion(
            version=1,
            config=config,
            change_description="Initial version from batch"
        )]
        
        self._validate_template(template)
        
        _templates[template.id] = template
        self._save_template(template)
        
        logger.info(f"Created template {template.id} from batch {batch.id}")
        return template
    
    def get_template(self, template_id: str) -> Optional[Template]:
        """Get template by ID"""
        if template_id in _templates:
            return _templates[template_id]
        return self._load_template(template_id)
    
    def list_templates(
        self,
        user_id: Optional[str] = None,
        include_public: bool = True,
        tags: Optional[List[str]] = None
    ) -> List[Template]:
        """List templates with optional filters"""
        templates = list(_templates.values())
        
        # Filter by user
        if user_id:
            templates = [
                t for t in templates
                if t.user_id == user_id or (include_public and t.is_public)
            ]
        
        # Filter by tags
        if tags:
            templates = [
                t for t in templates
                if any(tag in t.tags for tag in tags)
            ]
        
        # Only active templates
        templates = [t for t in templates if t.active]
        
        return sorted(templates, key=lambda t: t.updated_at, reverse=True)
    
    def update_template(
        self,
        template_id: str,
        config: TemplateConfig,
        change_description: str = None
    ) -> Template:
        """Update template creating new version"""
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        # Create new version
        template.create_new_version(config, change_description)
        
        # Validate
        self._validate_template(template)
        
        self._save_template(template)
        
        logger.info(f"Updated template {template_id} to version {template.current_version}")
        return template
    
    def delete_template(self, template_id: str, force: bool = False) -> bool:
        """Delete template"""
        template = self.get_template(template_id)
        if not template:
            return False
        
        if template.usage_count > 0 and not force:
            raise ValueError(
                f"Template has {template.usage_count} usages. Use force=True to delete."
            )
        
        # Soft delete by marking inactive
        template.active = False
        self._save_template(template)
        
        if template_id in _templates:
            del _templates[template_id]
        
        logger.info(f"Deleted template {template_id}")
        return True
    
    # ==================== Version Operations ====================
    
    def get_version_history(self, template_id: str) -> List[Dict]:
        """Get all versions for a template"""
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        return [
            {
                "version": v.version,
                "change_description": v.change_description,
                "created_at": v.created_at.isoformat(),
                "is_current": v.version == template.current_version
            }
            for v in template.versions
        ]
    
    def get_specific_version(
        self,
        template_id: str,
        version: int
    ) -> Optional[TemplateVersion]:
        """Get specific version of a template"""
        template = self.get_template(template_id)
        if not template:
            return None
        return template.get_version(version)
    
    # ==================== Validation ====================
    
    def _validate_template(self, template: Template):
        """Validate template configuration"""
        config = template.get_current_config()
        
        # Must have at least one fixed element
        fixed = config.get_fixed_elements()
        if not fixed:
            raise TemplateValidationError("Template must have at least one fixed element")
        
        # Must have content as variable
        variable = config.get_variable_elements()
        has_content = any(e.name == "content" for e in variable)
        if not has_content:
            raise TemplateValidationError("Template must have 'content' as variable element")
        
        # Validate platform reference
        platform_elem = config.platform
        if platform_elem.value:
            try:
                platform = Platform(platform_elem.value)
                fmt = get_format(platform)
            except ValueError:
                raise TemplateValidationError(f"Invalid platform: {platform_elem.value}")
            
            # Validate duration against platform
            duration_elem = config.duration
            if duration_elem.value and duration_elem.value > fmt.max_duration:
                raise TemplateValidationError(
                    f"Duration {duration_elem.value}s exceeds {platform_elem.value} max of {fmt.max_duration}s"
                )
        
        # Validate constrained elements have bounds
        constrained = config.get_constrained_elements()
        for elem in constrained:
            if not elem.bounds:
                raise TemplateValidationError(
                    f"Constrained element '{elem.name}' must have bounds defined"
                )
        
        logger.debug(f"Template {template.id} validation passed")
    
    def validate_instantiation_params(
        self,
        template: Template,
        params: Dict
    ) -> Dict:
        """Validate parameters for instantiation"""
        config = template.get_current_config()
        errors = []
        warnings = []
        
        # Check required variable elements
        for elem in config.get_variable_elements():
            if elem.required and elem.name not in params:
                errors.append(f"Missing required parameter: {elem.name}")
        
        # Check constrained elements are within bounds
        for elem in config.get_constrained_elements():
            if elem.name in params:
                value = params[elem.name]
                bounds = elem.bounds
                
                if bounds.min_value is not None and value < bounds.min_value:
                    errors.append(
                        f"{elem.name} value {value} below minimum {bounds.min_value}"
                    )
                if bounds.max_value is not None and value > bounds.max_value:
                    errors.append(
                        f"{elem.name} value {value} above maximum {bounds.max_value}"
                    )
                if bounds.allowed_values and value not in bounds.allowed_values:
                    errors.append(
                        f"{elem.name} value '{value}' not in allowed values"
                    )
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    # ==================== Usage Tracking ====================
    
    def record_usage(self, template_id: str, success: bool = True):
        """Record template usage for statistics"""
        template = self.get_template(template_id)
        if template:
            template.increment_usage(success)
            self._save_template(template)
    
    def get_usage_stats(self, template_id: str) -> Dict:
        """Get usage statistics for template"""
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        return {
            "template_id": template_id,
            "usage_count": template.usage_count,
            "success_count": template.success_count,
            "success_rate": f"{template.success_rate * 100:.1f}%",
            "created_at": template.created_at.isoformat(),
            "last_used": template.updated_at.isoformat()
        }
    
    # ==================== Storage ====================
    
    def _save_template(self, template: Template):
        """Save template to disk"""
        path = os.path.join(self.storage_path, f"{template.id}.json")
        with open(path, 'w') as f:
            json.dump(template.to_dict(), f, indent=2)
    
    def _load_template(self, template_id: str) -> Optional[Template]:
        """Load template from disk"""
        path = os.path.join(self.storage_path, f"{template_id}.json")
        if not os.path.exists(path):
            return None
        
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            template = Template.from_dict(data)
            _templates[template.id] = template
            return template
        except Exception as e:
            logger.error(f"Error loading template {template_id}: {e}")
            return None
