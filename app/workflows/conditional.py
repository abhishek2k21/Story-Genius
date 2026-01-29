"""
Conditional Workflow Logic
Implements branching and conditional task execution.
"""
from typing import Callable, Any, Optional, List
from dataclasses import dataclass

from app.workflows.primitives import Task, DAG
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class Condition:
    """
    Conditional predicate for branching.
    """
    name: str
    predicate: Callable[[Any], bool]
    description: str
    
    def evaluate(self, context: Any) -> bool:
        """Evaluate condition"""
        result = self.predicate(context)
        logger.debug(f"Condition '{self.name}' evaluated to: {result}")
        return result


class ConditionalTask(Task):
    """
    Task with conditional execution.
    """
    
    def __init__(
        self,
        id: str,
        name: str,
        condition: Condition,
        execute_fn: Callable,
        dependencies: List[str] = None,
        metadata: dict = None
    ):
        super().__init__(
            id=id,
            name=name,
            execute_fn=execute_fn,
            dependencies=dependencies or [],
            metadata=metadata or {}
        )
        self.condition = condition
    
    def should_execute(self, context: Any) -> bool:
        """Check if task should execute based on condition"""
        return self.condition.evaluate(context)


class BranchTask:
    """
    Branching task that routes to different tasks based on condition.
    """
    
    def __init__(
        self,
        id: str,
        name: str,
        condition: Condition,
        true_task: Task,
        false_task: Task
    ):
        self.id = id
        self.name = name
        self.condition = condition
        self.true_task = true_task
        self.false_task = false_task
    
    def select_task(self, context: Any) -> Task:
        """Select which task to execute based on condition"""
        if self.condition.evaluate(context):
            logger.info(f"Branch '{self.name}': condition TRUE, executing {self.true_task.id}")
            return self.true_task
        else:
            logger.info(f"Branch '{self.name}': condition FALSE, executing {self.false_task.id}")
            return self.false_task


# Common condition builders

def quality_threshold_condition(threshold: float) -> Condition:
    """
    Condition: quality score > threshold
    
    Args:
        threshold: Quality score threshold (0-100)
    
    Returns:
        Condition
    """
    return Condition(
        name=f"quality_>{threshold}",
        predicate=lambda ctx: ctx.get("quality_score", 0) > threshold,
        description=f"Quality score must be greater than {threshold}"
    )


def token_limit_condition(limit: int) -> Condition:
    """
    Condition: token count < limit
    
    Args:
        limit: Token count limit
    
    Returns:
        Condition
    """
    return Condition(
        name=f"tokens<{limit}",
        predicate=lambda ctx: ctx.get("token_count", 0) < limit,
        description=f"Token count must be less than {limit}"
    )


def error_rate_condition(threshold: float) -> Condition:
    """
    Condition: error rate < threshold
    
    Args:
        threshold: Error rate threshold (0-1)
    
    Returns:
        Condition
    """
    return Condition(
        name=f"error_rate<{threshold}",
        predicate=lambda ctx: ctx.get("error_rate", 0) < threshold,
        description=f"Error rate must be less than {threshold}"
    )


# Workflow builders with conditions

def create_quality_workflow(dag: DAG, quality_threshold: float = 80.0):
    """
    Create workflow with quality-based branching.
    
    Quality > 80: auto-publish
    Quality 70-80: manual review
    Quality < 70: regenerate
    """
    # Quality check task
    def check_quality():
        # Mock quality check
        quality_score = 85.0  # In production: actual quality check
        return {"quality_score": quality_score}
    
    quality_task = Task(
        id="check_quality",
        name="Quality Check",
        execute_fn=check_quality
    )
    dag.add_task(quality_task)
    
    # Publish task (quality > 80)
    def publish():
        logger.info("Auto-publishing high-quality content")
        return {"status": "published"}
    
    publish_task = Task(
        id="publish",
        name="Auto-Publish",
        execute_fn=publish,
        dependencies=["check_quality"]
    )
    
    # Manual review task (quality 70-80)
    def manual_review():
        logger.info("Queuing for manual review")
        return {"status": "queued_for_review"}
    
    review_task = Task(
        id="manual_review",
        name="Manual Review",
        execute_fn=manual_review,
        dependencies=["check_quality"]
    )
    
    # Regenerate task (quality < 70)
    def regenerate():
        logger.info("Quality too low, regenerating")
        return {"status": "regenerating"}
    
    regen_task = Task(
        id="regenerate",
        name="Regenerate",
        execute_fn=regenerate,
        dependencies=["check_quality"]
    )
    
    # Add conditional tasks
    # NOTE: In full implementation, DAGEngine would evaluate conditions dynamically
    # For now, adding all tasks and documenting the logic
    
    dag.add_task(publish_task)
    dag.add_task(review_task)
    dag.add_task(regen_task)
    
    return dag
