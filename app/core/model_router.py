"""
Week 17 Day 4 - Model Router
Internal model selection, not user-facing.
User doesn't need to understand models - we pick the best one for the task.
"""
from typing import Literal, Optional
from enum import Enum
from dataclasses import dataclass

from app.core.contract import GenerationContract, QualityMode
from app.core.logging import get_logger

logger = get_logger(__name__)


class TaskType(str, Enum):
    """Types of tasks for model selection."""
    REASONING = "reasoning"       # Path 1, analysis, scoring
    SCRIPTING = "scripting"       # Script generation
    SYNTHESIS = "synthesis"       # Idea refinement
    TRANSLATION = "translation"   # Native language generation
    VIDEO = "video"               # Veo video generation
    AUDIO = "audio"               # TTS


@dataclass
class ModelConfig:
    """Configuration for a specific model."""
    model_id: str
    provider: str
    strengths: list
    speed: str  # fast, medium, slow
    cost: str   # low, medium, high


# Model registry
MODEL_REGISTRY = {
    # Gemini models
    "gemini-2.0-flash": ModelConfig(
        model_id="gemini-2.0-flash-001",
        provider="vertex",
        strengths=["fast", "scripting", "general"],
        speed="fast",
        cost="low"
    ),
    "gemini-2.0-pro": ModelConfig(
        model_id="gemini-2.0-pro-001",
        provider="vertex",
        strengths=["reasoning", "synthesis", "quality"],
        speed="medium",
        cost="medium"
    ),
    "gemini-1.5-pro": ModelConfig(
        model_id="gemini-1.5-pro",
        provider="vertex",
        strengths=["reasoning", "long_context", "analysis"],
        speed="slow",
        cost="high"
    ),
    # Video models
    "veo-2": ModelConfig(
        model_id="veo-002",
        provider="vertex",
        strengths=["video", "animation"],
        speed="slow",
        cost="high"
    ),
}


class ModelRouter:
    """
    Routes tasks to the best model.
    User doesn't choose - we optimize internally.
    """
    
    def __init__(self):
        self.registry = MODEL_REGISTRY
        logger.info("ModelRouter initialized")
    
    def select_model(
        self,
        task: TaskType,
        quality_mode: QualityMode = QualityMode.BALANCED,
        language: str = "en"
    ) -> ModelConfig:
        """
        Select the best model for the task.
        
        Args:
            task: Type of task to perform
            quality_mode: Quality vs speed tradeoff
            language: Target language
            
        Returns:
            Best ModelConfig for this task
        """
        # Reasoning tasks → strongest model
        if task == TaskType.REASONING:
            if quality_mode == QualityMode.PREMIUM:
                model = self.registry["gemini-1.5-pro"]
            elif quality_mode == QualityMode.FAST:
                model = self.registry["gemini-2.0-flash"]
            else:
                model = self.registry["gemini-2.0-pro"]
            
        # Scripting → fast + fluent
        elif task == TaskType.SCRIPTING:
            if quality_mode == QualityMode.PREMIUM:
                model = self.registry["gemini-2.0-pro"]
            else:
                model = self.registry["gemini-2.0-flash"]
        
        # Synthesis → balanced
        elif task == TaskType.SYNTHESIS:
            if quality_mode == QualityMode.FAST:
                model = self.registry["gemini-2.0-flash"]
            else:
                model = self.registry["gemini-2.0-pro"]
        
        # Translation/native language → model with good language support
        elif task == TaskType.TRANSLATION:
            # For non-English, use models with better multilingual
            if language != "en":
                model = self.registry["gemini-2.0-pro"]
            else:
                model = self.registry["gemini-2.0-flash"]
        
        # Video → Veo
        elif task == TaskType.VIDEO:
            model = self.registry["veo-2"]
        
        # Default
        else:
            model = self.registry["gemini-2.0-flash"]
        
        logger.debug(f"Selected {model.model_id} for {task.value} (quality={quality_mode.value})")
        return model
    
    def select_for_contract(self, contract: GenerationContract, task: TaskType) -> ModelConfig:
        """
        Select model based on contract settings.
        
        Args:
            contract: The generation contract
            task: Type of task
            
        Returns:
            Best model for this contract and task
        """
        return self.select_model(
            task=task,
            quality_mode=QualityMode(contract.quality_mode),
            language=contract.resolve_language()
        )
    
    def get_model_for_reasoning(self, quality_mode: str = "balanced") -> str:
        """Quick helper: get model for Path 1 reasoning."""
        config = self.select_model(TaskType.REASONING, QualityMode(quality_mode))
        return config.model_id
    
    def get_model_for_scripting(self, quality_mode: str = "balanced") -> str:
        """Quick helper: get model for script generation."""
        config = self.select_model(TaskType.SCRIPTING, QualityMode(quality_mode))
        return config.model_id


# Singleton
_router = None

def get_model_router() -> ModelRouter:
    global _router
    if _router is None:
        _router = ModelRouter()
    return _router


def select_model(task: str, quality_mode: str = "balanced", language: str = "en") -> str:
    """
    Quick function to select model.
    
    Args:
        task: "reasoning", "scripting", "synthesis", "translation", "video"
        quality_mode: "fast", "balanced", "premium"
        language: Language code
        
    Returns:
        Model ID string
    """
    router = get_model_router()
    config = router.select_model(
        TaskType(task),
        QualityMode(quality_mode),
        language
    )
    return config.model_id
