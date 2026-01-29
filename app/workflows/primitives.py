"""
Workflow Primitives
Defines core data structures for DAG-based workflows.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Callable, Any, Optional, Set
from enum import Enum
from datetime import datetime

from app.core.logging import get_logger

logger = get_logger(__name__)


class TaskStatus(str, Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class Task:
    """
    Workflow task node.
    """
    id: str
    name: str
    execute_fn: Callable
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Runtime state
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "dependencies": self.dependencies,
            "metadata": self.metadata,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self._calculate_duration()
        }
    
    def _calculate_duration(self) -> Optional[float]:
        """Calculate task duration"""
        if not self.started_at:
            return None
        
        end_time = self.completed_at or datetime.utcnow()
        duration = (end_time - self.started_at).total_seconds()
        return round(duration, 2)


@dataclass
class DAG:
    """
    Directed Acyclic Graph representing workflow.
    """
    id: str
    name: str
    tasks: Dict[str, Task] = field(default_factory=dict)
    
    def add_task(self, task: Task):
        """Add task to DAG"""
        if task.id in self.tasks:
            raise ValueError(f"Task {task.id} already exists in DAG")
        
        self.tasks[task.id] = task
        logger.debug(f"Added task {task.id} to DAG {self.id}")
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID"""
        return self.tasks.get(task_id)
    
    def get_task_dependencies(self, task_id: str) -> List[Task]:
        """Get task dependencies"""
        task = self.get_task(task_id)
        if not task:
            return []
        
        return [
            self.tasks[dep_id]
            for dep_id in task.dependencies
            if dep_id in self.tasks
        ]
    
    def get_dependent_tasks(self, task_id: str) -> List[Task]:
        """Get tasks that depend on this task"""
        return [
            task for task in self.tasks.values()
            if task_id in task.dependencies
        ]
    
    def validate(self) -> bool:
        """
        Validate DAG structure.
        
        Returns:
            True if valid, raises ValueError otherwise
        """
        # Check all dependencies exist
        for task in self.tasks.values():
            for dep in task.dependencies:
                if dep not in self.tasks:
                    raise ValueError(f"Task {task.id} depends on non-existent task {dep}")
        
        # Check for cycles
        if self._has_cycle():
            raise ValueError(f"DAG {self.id} contains cycles")
        
        logger.info(f"DAG {self.id} validated successfully")
        return True
    
    def _has_cycle(self) -> bool:
        """Check if DAG has cycles using DFS"""
        visited = set()
        rec_stack = set()
        
        def dfs(task_id: str) -> bool:
            visited.add(task_id)
            rec_stack.add(task_id)
            
            task = self.tasks[task_id]
            for dep_id in task.dependencies:
                if dep_id not in visited:
                    if dfs(dep_id):
                        return True
                elif dep_id in rec_stack:
                    return True
            
            rec_stack.remove(task_id)
            return False
        
        for task_id in self.tasks:
            if task_id not in visited:
                if dfs(task_id):
                    return True
        
        return False
    
    def get_execution_order(self) -> List[List[str]]:
        """
        Get execution order using topological sort.
        Returns list of levels, where tasks in same level can run in parallel.
        
        Returns:
            List of lists of task IDs (levels)
        """
        # Calculate in-degree for each task
        in_degree = {task_id: 0 for task_id in self.tasks}
        
        for task in self.tasks.values():
            for dep in task.dependencies:
                in_degree[task.id] += 1
        
        # Find all tasks with in-degree 0 (no dependencies)
        levels = []
        remaining = set(self.tasks.keys())
        
        while remaining:
            # Find tasks with all dependencies satisfied
            current_level = [
                task_id for task_id in remaining
                if all(
                    dep_id not in remaining
                    for dep_id in self.tasks[task_id].dependencies
                )
            ]
            
            if not current_level:
                raise ValueError(f"DAG {self.id} has unresolvable dependencies")
            
            levels.append(current_level)
            remaining -= set(current_level)
        
        return levels
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "task_count": len(self.tasks),
            "tasks": {
                task_id: task.to_dict()
                for task_id, task in self.tasks.items()
            }
        }


class ExecutionStatus(str, Enum):
    """DAG execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Execution:
    """
    DAG execution context.
    """
    id: str
    dag: DAG
    status: ExecutionStatus = ExecutionStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    results: Dict[str, Any] = field(default_factory=dict)
    errors: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "dag_id": self.dag.id,
            "status": self.status.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self._calculate_duration(),
            "results": self.results,
            "errors": self.errors,
            "task_statuses": {
                task_id: task.status.value
                for task_id, task in self.dag.tasks.items()
            }
        }
    
    def _calculate_duration(self) -> Optional[float]:
        """Calculate execution duration"""
        if not self.started_at:
            return None
        
        end_time = self.completed_at or datetime.utcnow()
        duration = (end_time - self.started_at).total_seconds()
        return round(duration, 2)
