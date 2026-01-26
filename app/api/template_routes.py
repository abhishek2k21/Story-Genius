"""
Template API Routes
CRUD, versioning, instantiation, and statistics endpoints.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

from app.templates.models import Template, TemplateConfig, ElementType
from app.templates.service import TemplateService, TemplateValidationError
from app.templates.instantiation import TemplateInstantiator, InstantiationError
from app.batch.service import BatchService

router = APIRouter(prefix="/v1/templates", tags=["templates"])

# Initialize services
template_service = TemplateService()
instantiator = TemplateInstantiator()
batch_service = BatchService()


# ==================== Request/Response Models ====================

class CreateTemplateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    platform: str = Field(default="youtube_shorts")
    duration: int = Field(default=30, ge=5, le=180)
    voice: str = Field(default="en-US-GuyNeural")
    genre: str = Field(default="educational")
    language: str = Field(default="en")
    audience: str = Field(default="general")
    tags: Optional[List[str]] = None


class UpdateTemplateRequest(BaseModel):
    platform: Optional[str] = None
    duration: Optional[int] = Field(default=None, ge=5, le=180)
    voice: Optional[str] = None
    genre: Optional[str] = None
    change_description: Optional[str] = None


class InstantiateBatchRequest(BaseModel):
    batch_name: str = Field(..., min_length=1)
    content_items: List[str] = Field(..., min_items=1, max_items=100)
    overrides: Optional[Dict[str, Any]] = None


class InstantiateProjectRequest(BaseModel):
    project_name: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    overrides: Optional[Dict[str, Any]] = None


# ==================== CRUD Endpoints ====================

@router.post("/")
async def create_template(request: CreateTemplateRequest):
    """Create a new template manually"""
    try:
        # Build config from request
        from app.templates.models import TemplateElement, ConstraintBounds
        
        config = TemplateConfig(
            platform=TemplateElement(
                name="platform",
                element_type=ElementType.FIXED,
                value=request.platform
            ),
            duration=TemplateElement(
                name="duration",
                element_type=ElementType.CONSTRAINED,
                value=request.duration,
                bounds=ConstraintBounds(min_value=5, max_value=180)
            ),
            voice=TemplateElement(
                name="voice",
                element_type=ElementType.FIXED,
                value=request.voice
            ),
            genre=TemplateElement(
                name="genre",
                element_type=ElementType.FIXED,
                value=request.genre
            ),
            language=TemplateElement(
                name="language",
                element_type=ElementType.FIXED,
                value=request.language
            ),
            audience=TemplateElement(
                name="audience",
                element_type=ElementType.FIXED,
                value=request.audience
            )
        )
        
        template = template_service.create_template(
            name=request.name,
            config=config,
            description=request.description,
            tags=request.tags
        )
        
        return {
            "id": template.id,
            "name": template.name,
            "version": template.current_version,
            "message": "Template created successfully"
        }
    except TemplateValidationError as e:
        raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")


@router.get("/")
async def list_templates(
    include_public: bool = True,
    tags: Optional[str] = None
):
    """List all available templates"""
    tag_list = tags.split(",") if tags else None
    templates = template_service.list_templates(
        include_public=include_public,
        tags=tag_list
    )
    
    return {
        "templates": [
            {
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "version": t.current_version,
                "usage_count": t.usage_count,
                "success_rate": f"{t.success_rate * 100:.1f}%",
                "tags": t.tags,
                "created_at": t.created_at.isoformat()
            }
            for t in templates
        ]
    }


@router.get("/{template_id}")
async def get_template(template_id: str):
    """Get full template details"""
    template = template_service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return template.to_dict()


@router.put("/{template_id}")
async def update_template(template_id: str, request: UpdateTemplateRequest):
    """Update template creating new version"""
    template = template_service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    try:
        # Get current config and apply updates
        current_config = template.get_current_config()
        
        if request.platform:
            current_config.platform.value = request.platform
        if request.duration:
            current_config.duration.value = request.duration
        if request.voice:
            current_config.voice.value = request.voice
        if request.genre:
            current_config.genre.value = request.genre
        
        updated = template_service.update_template(
            template_id,
            current_config,
            request.change_description
        )
        
        return {
            "id": updated.id,
            "version": updated.current_version,
            "message": "Template updated to new version"
        }
    except TemplateValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{template_id}")
async def delete_template(template_id: str, force: bool = False):
    """Delete template"""
    try:
        result = template_service.delete_template(template_id, force=force)
        if not result:
            raise HTTPException(status_code=404, detail="Template not found")
        return {"message": "Template deleted", "template_id": template_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== Version Endpoints ====================

@router.get("/{template_id}/versions")
async def get_version_history(template_id: str):
    """Get version history for template"""
    try:
        versions = template_service.get_version_history(template_id)
        return {"template_id": template_id, "versions": versions}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{template_id}/versions/{version}")
async def get_specific_version(template_id: str, version: int):
    """Get specific version configuration"""
    template_version = template_service.get_specific_version(template_id, version)
    if not template_version:
        raise HTTPException(status_code=404, detail="Version not found")
    
    return template_version.to_dict()


# ==================== Create From Source ====================

@router.post("/from-batch/{batch_id}")
async def create_from_batch(batch_id: str, name: str, description: Optional[str] = None):
    """Create template from successful batch"""
    batch = batch_service.get_batch(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    try:
        template = template_service.create_from_batch(
            batch=batch,
            name=name,
            description=description
        )
        
        return {
            "id": template.id,
            "name": template.name,
            "source_batch": batch_id,
            "message": "Template created from batch"
        }
    except TemplateValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== Instantiation Endpoints ====================

@router.post("/{template_id}/instantiate/batch")
async def instantiate_batch(template_id: str, request: InstantiateBatchRequest):
    """Create batch from template"""
    try:
        batch = instantiator.instantiate_batch(
            template_id=template_id,
            batch_name=request.batch_name,
            content_items=request.content_items,
            overrides=request.overrides
        )
        
        return {
            "batch_id": batch.id,
            "batch_name": batch.name,
            "template_id": template_id,
            "items_count": len(request.content_items),
            "message": "Batch created from template"
        }
    except InstantiationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{template_id}/instantiate/project")
async def instantiate_project(template_id: str, request: InstantiateProjectRequest):
    """Create project from template"""
    try:
        project = instantiator.instantiate_project(
            template_id=template_id,
            project_name=request.project_name,
            content=request.content,
            overrides=request.overrides
        )
        
        return {
            "project": project,
            "message": "Project created from template"
        }
    except InstantiationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{template_id}/preview")
async def preview_instantiation(template_id: str, params: Dict[str, Any]):
    """Preview instantiation without committing"""
    try:
        preview = instantiator.preview_instantiation(template_id, params)
        return preview
    except InstantiationError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== Stats Endpoints ====================

@router.get("/{template_id}/stats")
async def get_template_stats(template_id: str):
    """Get usage statistics for template"""
    try:
        stats = template_service.get_usage_stats(template_id)
        return stats
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
