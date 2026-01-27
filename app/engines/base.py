"""
Standard Engine Interface
Defines base classes for all engines with consistent input/output structures.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid


class EngineStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class EngineInput:
    """Standard input structure for all engines"""
    job_id: str
    engine_id: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    upstream_artifacts: Dict[str, str] = field(default_factory=dict)  # ref -> path
    quality_requirements: Dict[str, float] = field(default_factory=dict)
    timeout_seconds: int = 300
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "job_id": self.job_id,
            "engine_id": self.engine_id,
            "parameters": self.parameters,
            "upstream_artifacts": self.upstream_artifacts,
            "quality_requirements": self.quality_requirements,
            "timeout_seconds": self.timeout_seconds,
            "metadata": self.metadata
        }


@dataclass
class EngineOutput:
    """Standard output structure for all engines"""
    job_id: str
    engine_id: str
    status: EngineStatus = EngineStatus.COMPLETED
    primary_artifact: Optional[str] = None
    secondary_artifacts: Dict[str, str] = field(default_factory=dict)
    quality_scores: Dict[str, float] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    duration_ms: float = 0
    
    def to_dict(self) -> Dict:
        return {
            "job_id": self.job_id,
            "engine_id": self.engine_id,
            "status": self.status.value,
            "primary_artifact": self.primary_artifact,
            "secondary_artifacts": self.secondary_artifacts,
            "quality_scores": self.quality_scores,
            "metrics": self.metrics,
            "metadata": self.metadata,
            "error_message": self.error_message,
            "duration_ms": self.duration_ms
        }


class BaseEngine(ABC):
    """Base class for all engines - defines standard interface"""
    
    def __init__(self, engine_id: str, engine_type: str, version: str = "1.0.0"):
        self.engine_id = engine_id
        self.engine_type = engine_type
        self.version = version
        self.status = EngineStatus.IDLE
        self._cancelled = False
    
    @abstractmethod
    def validate_input(self, input_data: EngineInput) -> Dict:
        """Validate input before execution. Returns {valid: bool, errors: []}"""
        pass
    
    @abstractmethod
    async def execute(self, input_data: EngineInput) -> EngineOutput:
        """Execute the engine. Main processing logic."""
        pass
    
    @abstractmethod
    def validate_output(self, output: EngineOutput) -> Dict:
        """Validate output after execution. Returns {valid: bool, errors: []}"""
        pass
    
    def cancel(self):
        """Request cancellation"""
        self._cancelled = True
        self.status = EngineStatus.CANCELLED
    
    def cleanup(self):
        """Clean up resources after execution"""
        self._cancelled = False
        self.status = EngineStatus.IDLE
    
    def get_capabilities(self) -> Dict:
        """Return engine capabilities"""
        return {
            "engine_id": self.engine_id,
            "engine_type": self.engine_type,
            "version": self.version,
            "status": self.status.value
        }
    
    def report_progress(self, progress: float, message: str = ""):
        """Report execution progress (0-100)"""
        # Override for custom progress reporting
        pass


@dataclass
class EngineDefinition:
    """Definition for engine registration"""
    engine_id: str
    engine_type: str
    version: str
    capabilities: List[str]
    required_inputs: List[str]
    optional_inputs: List[str]
    output_types: List[str]
    resource_requirements: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "engine_id": self.engine_id,
            "engine_type": self.engine_type,
            "version": self.version,
            "capabilities": self.capabilities,
            "required_inputs": self.required_inputs,
            "optional_inputs": self.optional_inputs,
            "output_types": self.output_types,
            "resource_requirements": self.resource_requirements
        }
