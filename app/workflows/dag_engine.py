"""
DAG Workflow Engine
Executes workflows defined as Directed Acyclic Graphs with parallel task execution.
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from app.workflows.primitives import (
    DAG,
    Task,
    Execution,
    TaskStatus,
    ExecutionStatus
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class DAGEngine:
    """
    DAG execution engine with parallel task execution.
    """
    
    def __init__(self, max_workers: int = 10):
        self.max_workers = max_workers
        logger.info(f"DAGEngine initialized (max_workers={max_workers})")
    
    def execute_dag(self, dag: DAG, execution_id: Optional[str] = None) -> Execution:
        """
        Execute DAG workflow.
        
        Args:
            dag: DAG to execute
            execution_id: Optional execution ID
        
        Returns:
            Execution result
        """
        import uuid
        
        # Validate DAG
        dag.validate()
        
        # Create execution context
        exec_id = execution_id or str(uuid.uuid4())
        execution = Execution(
            id=exec_id,
            dag=dag,
            status=ExecutionStatus.RUNNING,
            started_at=datetime.utcnow()
        )
        
        logger.info(f"Starting DAG execution: {dag.id} (execution_id={exec_id})")
        
        try:
            # Get execution order (topological sort)
            levels = dag.get_execution_order()
            
            logger.info(
                f"Execution plan: {len(levels)} levels, "
                f"{len(dag.tasks)} total tasks"
            )
            
            # Execute each level
            for level_idx, level_tasks in enumerate(levels):
                logger.info(
                    f"Executing level {level_idx + 1}/{len(levels)}: "
                    f"{len(level_tasks)} parallel tasks"
                )
                
                # Execute tasks in parallel
                self._execute_level(dag, level_tasks, execution)
                
                # Check for failures
                failed_tasks = [
                    task_id for task_id in level_tasks
                    if dag.get_task(task_id).status == TaskStatus.FAILED
                ]
                
                if failed_tasks:
                    logger.error(
                        f"Level {level_idx + 1} failed: {len(failed_tasks)} tasks failed"
                    )
                    execution.status = ExecutionStatus.FAILED
                    break
            
            # Mark as completed if no failures
            if execution.status == ExecutionStatus.RUNNING:
                execution.status = ExecutionStatus.COMPLETED
                logger.info(f"DAG execution completed successfully: {exec_id}")
            
        except Exception as e:
            logger.error(f"DAG execution failed: {e}", exc_info=True)
            execution.status = ExecutionStatus.FAILED
            execution.errors["_execution"] = str(e)
        
        finally:
            execution.completed_at = datetime.utcnow()
        
        return execution
    
    def _execute_level(
        self,
        dag: DAG,
        task_ids: List[str],
        execution: Execution
    ):
        """Execute tasks in parallel"""
        
        if len(task_ids) == 1:
            # Single task, execute directly
            task = dag.get_task(task_ids[0])
            self._execute_task(task, execution)
        else:
            # Multiple tasks, execute in parallel
            with ThreadPoolExecutor(max_workers=min(len(task_ids), self.max_workers)) as executor:
                futures = {
                    executor.submit(self._execute_task, dag.get_task(task_id), execution): task_id
                    for task_id in task_ids
                }
                
                for future in as_completed(futures):
                    task_id = futures[future]
                    try:
                        future.result()
                    except Exception as e:
                        logger.error(f"Task {task_id} execution failed: {e}")
    
    def _execute_task(self, task: Task, execution: Execution):
        """Execute single task"""
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.utcnow()
        
        logger.info(f"Executing task: {task.id} ({task.name})")
        
        try:
            # Get dependency results
            dep_results = {
                dep_id: execution.results.get(dep_id)
                for dep_id in task.dependencies
            }
            
            # Execute task function
            result = task.execute_fn(**dep_results) if dep_results else task.execute_fn()
            
            # Store result
            task.result = result
            task.status = TaskStatus.COMPLETED
            execution.results[task.id] = result
            
            logger.info(f"Task completed: {task.id} (duration={task._calculate_duration()}s)")
            
        except Exception as e:
            logger.error(f"Task failed: {task.id} - {e}", exc_info=True)
            task.status = TaskStatus.FAILED
            task.error = str(e)
            execution.errors[task.id] = str(e)
        
        finally:
            task.completed_at = datetime.utcnow()


# Global instance
dag_engine = DAGEngine()
