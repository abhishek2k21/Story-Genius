"""
Engine Registry
Central registry for engine discovery, health tracking, and performance metrics.
"""
from typing import Dict, List, Optional, Type
from datetime import datetime
from app.engines.base import BaseEngine, EngineDefinition, EngineStatus
from app.core.logging import get_logger

logger = get_logger(__name__)

# Global registry storage
_engines: Dict[str, BaseEngine] = {}
_definitions: Dict[str, EngineDefinition] = {}
_metrics: Dict[str, Dict] = {}


class EngineRegistry:
    """Central registry for all engines"""
    
    @classmethod
    def register(cls, engine: BaseEngine, definition: EngineDefinition):
        """Register an engine with its definition"""
        _engines[engine.engine_id] = engine
        _definitions[engine.engine_id] = definition
        _metrics[engine.engine_id] = {
            "executions": 0,
            "successes": 0,
            "failures": 0,
            "total_duration_ms": 0,
            "last_execution": None
        }
        logger.info(f"Registered engine: {engine.engine_id} v{engine.version}")
    
    @classmethod
    def get_engine(cls, engine_id: str) -> Optional[BaseEngine]:
        """Get engine by ID"""
        return _engines.get(engine_id)
    
    @classmethod
    def get_by_type(cls, engine_type: str) -> List[BaseEngine]:
        """Get all engines of a specific type"""
        return [e for e in _engines.values() if e.engine_type == engine_type]
    
    @classmethod
    def list_all(cls) -> List[Dict]:
        """List all registered engines"""
        result = []
        for engine_id, engine in _engines.items():
            definition = _definitions.get(engine_id)
            metrics = _metrics.get(engine_id, {})
            result.append({
                "engine_id": engine_id,
                "type": engine.engine_type,
                "version": engine.version,
                "status": engine.status.value,
                "capabilities": definition.capabilities if definition else [],
                "executions": metrics.get("executions", 0),
                "success_rate": cls._calc_success_rate(engine_id)
            })
        return result
    
    @classmethod
    def get_definition(cls, engine_id: str) -> Optional[EngineDefinition]:
        """Get engine definition"""
        return _definitions.get(engine_id)
    
    @classmethod
    def record_execution(cls, engine_id: str, success: bool, duration_ms: float):
        """Record execution metrics"""
        if engine_id not in _metrics:
            _metrics[engine_id] = {"executions": 0, "successes": 0, "failures": 0, "total_duration_ms": 0}
        
        _metrics[engine_id]["executions"] += 1
        _metrics[engine_id]["total_duration_ms"] += duration_ms
        _metrics[engine_id]["last_execution"] = datetime.now().isoformat()
        
        if success:
            _metrics[engine_id]["successes"] += 1
        else:
            _metrics[engine_id]["failures"] += 1
    
    @classmethod
    def get_metrics(cls, engine_id: str) -> Dict:
        """Get performance metrics for an engine"""
        metrics = _metrics.get(engine_id, {})
        return {
            **metrics,
            "success_rate": cls._calc_success_rate(engine_id),
            "avg_duration_ms": cls._calc_avg_duration(engine_id)
        }
    
    @classmethod
    def get_health(cls, engine_id: str) -> Dict:
        """Get engine health status"""
        engine = _engines.get(engine_id)
        if not engine:
            return {"status": "not_found"}
        
        metrics = _metrics.get(engine_id, {})
        success_rate = cls._calc_success_rate(engine_id)
        
        if success_rate < 0.5 and metrics.get("executions", 0) > 5:
            health = "unhealthy"
        elif success_rate < 0.8:
            health = "degraded"
        else:
            health = "healthy"
        
        return {
            "engine_id": engine_id,
            "status": engine.status.value,
            "health": health,
            "success_rate": f"{success_rate * 100:.1f}%",
            "executions": metrics.get("executions", 0)
        }
    
    @classmethod
    def _calc_success_rate(cls, engine_id: str) -> float:
        metrics = _metrics.get(engine_id, {})
        total = metrics.get("executions", 0)
        if total == 0:
            return 1.0
        return metrics.get("successes", 0) / total
    
    @classmethod
    def _calc_avg_duration(cls, engine_id: str) -> float:
        metrics = _metrics.get(engine_id, {})
        total = metrics.get("executions", 0)
        if total == 0:
            return 0
        return metrics.get("total_duration_ms", 0) / total
