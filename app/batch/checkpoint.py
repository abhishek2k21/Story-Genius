"""
Checkpoint System for Resumable Batch Processing
Allows batches to be paused and resumed from the last checkpoint.
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime
import json

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class Checkpoint:
    """Checkpoint data structure"""
    batch_id: str
    checkpoint_id: str
    current_item_index: int
    completed_items: List[str]
    failed_items: List[Dict[str, Any]]
    batch_metadata: Dict[str, Any]
    timestamp: datetime
    
    def to_dict(self) -> dict:
        return {
            "batch_id": self.batch_id,
            "checkpoint_id": self.checkpoint_id,
            "current_item_index": self.current_item_index,
            "completed_items": self.completed_items,
            "failed_items": self.failed_items,
            "batch_metadata": self.batch_metadata,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Checkpoint':
        return cls(
            batch_id=data["batch_id"],
            checkpoint_id=data["checkpoint_id"],
            current_item_index=data["current_item_index"],
            completed_items=data["completed_items"],
            failed_items=data["failed_items"],
            batch_metadata=data["batch_metadata"],
            timestamp=datetime.fromisoformat(data["timestamp"])
        )


class CheckpointManager:
    """
    Manages checkpoints for resumable batch processing.
    """
    
    def __init__(self):
        # In-memory storage (in production, use database)
        self._checkpoints: Dict[str, Checkpoint] = {}
        logger.info("CheckpointManager initialized")
    
    def save_checkpoint(
        self,
        batch_id: str,
        current_index: int,
        completed_items: List[str],
        failed_items: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Checkpoint:
        """
        Save batch checkpoint.
        
        Args:
            batch_id: Batch ID
            current_index: Current item index
            completed_items: List of completed item IDs
            failed_items: List of failed items with errors
            metadata: Optional metadata
        
        Returns:
            Created checkpoint
        """
        import uuid
        
        checkpoint = Checkpoint(
            batch_id=batch_id,
            checkpoint_id=str(uuid.uuid4()),
            current_item_index=current_index,
            completed_items=completed_items,
            failed_items=failed_items,
            batch_metadata=metadata or {},
            timestamp=datetime.utcnow()
        )
        
        self._checkpoints[batch_id] = checkpoint
        
        logger.info(
            f"Checkpoint saved for batch {batch_id}: "
            f"index={current_index}, completed={len(completed_items)}"
        )
        
        return checkpoint
    
    def load_checkpoint(self, batch_id: str) -> Optional[Checkpoint]:
        """
        Load checkpoint for batch.
        
        Args:
            batch_id: Batch ID
        
        Returns:
            Checkpoint if exists, None otherwise
        """
        checkpoint = self._checkpoints.get(batch_id)
        
        if checkpoint:
            logger.info(f"Checkpoint loaded for batch {batch_id}")
        else:
            logger.debug(f"No checkpoint found for batch {batch_id}")
        
        return checkpoint
    
    def has_checkpoint(self, batch_id: str) -> bool:
        """Check if checkpoint exists"""
        return batch_id in self._checkpoints
    
    def delete_checkpoint(self, batch_id: str) -> bool:
        """
        Delete checkpoint (after successful completion).
        
        Args:
            batch_id: Batch ID
        
        Returns:
            True if deleted, False if not found
        """
        if batch_id in self._checkpoints:
            del self._checkpoints[batch_id]
            logger.info(f"Checkpoint deleted for batch {batch_id}")
            return True
        return False
    
    def resume_from_checkpoint(
        self,
        batch_id: str,
        all_items: List[Any],
        process_fn: callable
    ) -> Dict[str, Any]:
        """
        Resume batch processing from checkpoint.
        
        Args:
            batch_id: Batch ID
            all_items: All batch items
            process_fn: Function to process each item
        
        Returns:
            Processing result
        """
        checkpoint = self.load_checkpoint(batch_id)
        
        if not checkpoint:
            logger.warning(f"No checkpoint for batch {batch_id}, starting from beginning")
            start_index = 0
            completed = []
            failed = []
        else:
            start_index = checkpoint.current_item_index
            completed = checkpoint.completed_items.copy()
            failed = checkpoint.failed_items.copy()
            
            logger.info(
                f"Resuming batch {batch_id} from index {start_index} "
                f"({len(completed)} already completed)"
            )
        
        # Process remaining items
        for i in range(start_index, len(all_items)):
            item = all_items[i]
            
            try:
                # Process item
                result = process_fn(item)
                completed.append(str(item))
                
                # Save checkpoint every 10 items
                if (i + 1) % 10 == 0:
                    self.save_checkpoint(
                        batch_id=batch_id,
                        current_index=i + 1,
                        completed_items=completed,
                        failed_items=failed
                    )
                
            except Exception as e:
                logger.error(f"Item {i} failed: {e}")
                failed.append({
                    "item": str(item),
                    "index": i,
                    "error": str(e)
                })
                
                # Save checkpoint after failure
                self.save_checkpoint(
                    batch_id=batch_id,
                    current_index=i + 1,
                    completed_items=completed,
                    failed_items=failed
                )
        
        # Delete checkpoint after completion
        self.delete_checkpoint(batch_id)
        
        return {
            "batch_id": batch_id,
            "total_items": len(all_items),
            "completed": len(completed),
            "failed": len(failed),
            "resumed_from_index": start_index
        }


class PauseResumeController:
    """
    Controls pause/resume functionality for batches.
    """
    
    def __init__(self, checkpoint_manager: CheckpointManager):
        self.checkpoint_manager = checkpoint_manager
        self._paused_batches: set = set()
    
    def pause_batch(self, batch_id: str):
        """
        Pause batch processing.
        
        Args:
            batch_id: Batch ID to pause
        """
        self._paused_batches.add(batch_id)
        logger.info(f"Batch {batch_id} paused")
    
    def resume_batch(self, batch_id: str):
        """
        Resume batch processing.
        
        Args:
            batch_id: Batch ID to resume
        """
        if batch_id in self._paused_batches:
            self._paused_batches.remove(batch_id)
            logger.info(f"Batch {batch_id} resumed")
    
    def is_paused(self, batch_id: str) -> bool:
        """Check if batch is paused"""
        return batch_id in self._paused_batches
    
    def should_continue(self, batch_id: str) -> bool:
        """
        Check if batch should continue processing.
        
        Args:
            batch_id: Batch ID
        
        Returns:
            True if should continue, False if paused
        """
        return not self.is_paused(batch_id)


# Global instances
checkpoint_manager = CheckpointManager()
pause_resume_controller = PauseResumeController(checkpoint_manager)
