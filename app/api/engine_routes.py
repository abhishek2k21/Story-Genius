"""
Engine API Routes
Endpoints for engines, hooks, and scripts.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List

from app.engines.base import EngineInput
from app.engines.registry import EngineRegistry
from app.engines.hook_engine import hook_engine, HookStyle
from app.engines.script_engine import script_engine, ContentCategory, StructureTemplate
from app.engines.hook_templates import list_all_templates, get_template

router = APIRouter(prefix="/v1", tags=["engines"])


# ==================== Engine Endpoints ====================

@router.get("/engines")
async def list_engines():
    """List all registered engines"""
    return {"engines": EngineRegistry.list_all()}


@router.get("/engines/{engine_id}")
async def get_engine(engine_id: str):
    """Get engine details"""
    engine = EngineRegistry.get_engine(engine_id)
    if not engine:
        raise HTTPException(status_code=404, detail="Engine not found")
    
    definition = EngineRegistry.get_definition(engine_id)
    return {
        "engine": engine.get_capabilities(),
        "definition": definition.to_dict() if definition else None
    }


@router.get("/engines/{engine_id}/health")
async def engine_health(engine_id: str):
    """Get engine health status"""
    return EngineRegistry.get_health(engine_id)


@router.get("/engines/{engine_id}/metrics")
async def engine_metrics(engine_id: str):
    """Get engine performance metrics"""
    return EngineRegistry.get_metrics(engine_id)


# ==================== Hook Endpoints ====================

class GenerateHooksRequest(BaseModel):
    topic: str = Field(..., min_length=1)
    style: str = Field(default="curiosity")
    count: int = Field(default=5, ge=1, le=10)


@router.post("/hooks/generate")
async def generate_hooks(request: GenerateHooksRequest):
    """Generate hooks for a topic"""
    try:
        input_data = EngineInput(
            job_id="api_request",
            engine_id="hook_engine_v1",
            parameters={
                "topic": request.topic,
                "style": request.style,
                "count": request.count
            }
        )
        
        output = await hook_engine.execute(input_data)
        
        EngineRegistry.record_execution(
            "hook_engine_v1",
            success=True,
            duration_ms=output.duration_ms
        )
        
        return {
            "best_hook": output.primary_artifact,
            "hooks": output.metadata.get("hooks", []),
            "topic": request.topic,
            "style": request.style
        }
    except Exception as e:
        EngineRegistry.record_execution("hook_engine_v1", success=False, duration_ms=0)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hooks/templates")
async def list_hook_templates():
    """List all hook templates"""
    return {"templates": list_all_templates()}


@router.get("/hooks/templates/{template_id}")
async def get_hook_template(template_id: str):
    """Get specific hook template"""
    template = get_template(template_id)
    return template.to_dict()


@router.get("/hooks/styles")
async def list_hook_styles():
    """List available hook styles"""
    return {"styles": [s.value for s in HookStyle]}


class ScoreHookRequest(BaseModel):
    hook_text: str
    template_id: Optional[str] = None


@router.post("/hooks/score")
async def score_hook(request: ScoreHookRequest):
    """Score a hook's effectiveness"""
    template = get_template(request.template_id or "curiosity_gap")
    score = hook_engine._score_hook(request.hook_text, template)
    
    return {
        "hook": request.hook_text,
        "score": score.to_dict(),
        "total": round(score.total, 2)
    }


# ==================== Script Endpoints ====================

class GenerateScriptRequest(BaseModel):
    topic: str = Field(..., min_length=1)
    category: str = Field(default="fact")
    structure: str = Field(default="hook_body_cta")
    target_duration: int = Field(default=30, ge=5, le=180)
    hook_style: str = Field(default="curiosity")


@router.post("/scripts/generate")
async def generate_script(request: GenerateScriptRequest):
    """Generate a segmented script"""
    try:
        input_data = EngineInput(
            job_id="api_request",
            engine_id="script_engine_v1",
            parameters={
                "topic": request.topic,
                "category": request.category,
                "structure": request.structure,
                "target_duration": request.target_duration,
                "hook_style": request.hook_style
            }
        )
        
        output = await script_engine.execute(input_data)
        
        EngineRegistry.record_execution(
            "script_engine_v1",
            success=True,
            duration_ms=output.duration_ms
        )
        
        return {
            "script": output.metadata.get("script", {}),
            "full_text": output.primary_artifact,
            "quality": output.quality_scores
        }
    except Exception as e:
        EngineRegistry.record_execution("script_engine_v1", success=False, duration_ms=0)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scripts/structures")
async def list_structures():
    """List available script structures"""
    return {
        "structures": [
            {"id": s.value, "name": s.name.replace("_", " ").title()}
            for s in StructureTemplate
        ]
    }


@router.get("/scripts/categories")
async def list_categories():
    """List content categories"""
    return {"categories": [c.value for c in ContentCategory]}
