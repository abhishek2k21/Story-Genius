"""
Batch Generation Service
Manages batch lifecycle, processing, and consistency enforcement.
"""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional
from datetime import datetime
import json
import os

from app.batch.models import (
    Batch, BatchItem, BatchConfig,
    BatchStatus, BatchItemStatus
)
from app.core.video_formats import Platform, get_format
from app.core.logging import get_logger

logger = get_logger(__name__)

# In-memory storage (replace with database in production)
_batches: Dict[str, Batch] = {}


class BatchValidationError(Exception):
    """Raised when batch validation fails"""
    pass


class BatchService:
    """Service for managing batch generation"""
    
    def __init__(self, max_workers: int = 3):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.storage_path = ".story_assets/batches"
        os.makedirs(self.storage_path, exist_ok=True)
    
    # ==================== CRUD Operations ====================
    
    def create_batch(
        self,
        name: str,
        config: Optional[Dict] = None,
        description: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Batch:
        """Create a new batch in draft state"""
        batch = Batch(
            name=name,
            description=description,
            user_id=user_id,
            config=BatchConfig.from_dict(config or {})
        )
        
        _batches[batch.id] = batch
        self._save_batch(batch)
        
        logger.info(f"Created batch {batch.id}: {name}")
        return batch
    
    def get_batch(self, batch_id: str) -> Optional[Batch]:
        """Get batch by ID"""
        if batch_id in _batches:
            return _batches[batch_id]
        
        # Try loading from disk
        return self._load_batch(batch_id)
    
    def list_batches(
        self,
        user_id: Optional[str] = None,
        status: Optional[BatchStatus] = None
    ) -> List[Batch]:
        """List batches with optional filters"""
        batches = list(_batches.values())
        
        if user_id:
            batches = [b for b in batches if b.user_id == user_id]
        if status:
            batches = [b for b in batches if b.status == status]
        
        return sorted(batches, key=lambda b: b.created_at, reverse=True)
    
    def delete_batch(self, batch_id: str) -> bool:
        """Delete a batch (only if draft or complete)"""
        batch = self.get_batch(batch_id)
        if not batch:
            return False
        
        if batch.status in [BatchStatus.PROCESSING]:
            raise ValueError("Cannot delete batch while processing")
        
        if batch_id in _batches:
            del _batches[batch_id]
        
        # Remove from disk
        path = os.path.join(self.storage_path, f"{batch_id}.json")
        if os.path.exists(path):
            os.remove(path)
        
        logger.info(f"Deleted batch {batch_id}")
        return True
    
    # ==================== Item Management ====================
    
    def add_item(self, batch_id: str, content: str) -> BatchItem:
        """Add item to draft batch"""
        batch = self.get_batch(batch_id)
        if not batch:
            raise ValueError(f"Batch {batch_id} not found")
        
        item = batch.add_item(content)
        self._save_batch(batch)
        
        logger.info(f"Added item {item.id} to batch {batch_id}")
        return item
    
    def add_items(self, batch_id: str, contents: List[str]) -> List[BatchItem]:
        """Add multiple items to draft batch"""
        return [self.add_item(batch_id, content) for content in contents]
    
    def remove_item(self, batch_id: str, item_id: str) -> bool:
        """Remove item from draft batch"""
        batch = self.get_batch(batch_id)
        if not batch:
            raise ValueError(f"Batch {batch_id} not found")
        
        result = batch.remove_item(item_id)
        if result:
            self._save_batch(batch)
        return result
    
    # ==================== Lifecycle Management ====================
    
    def lock_batch(self, batch_id: str) -> Batch:
        """
        Lock batch configuration and validate all items.
        After locking, config cannot change.
        """
        batch = self.get_batch(batch_id)
        if not batch:
            raise ValueError(f"Batch {batch_id} not found")
        
        if batch.status != BatchStatus.DRAFT:
            raise ValueError(f"Cannot lock batch in {batch.status.value} state")
        
        if len(batch.items) == 0:
            raise BatchValidationError("Batch has no items")
        
        # Validate configuration
        self._validate_batch_config(batch)
        
        # Lock the batch
        batch.status = BatchStatus.LOCKED
        batch.locked_at = datetime.now()
        self._save_batch(batch)
        
        logger.info(f"Locked batch {batch_id} with {len(batch.items)} items")
        return batch
    
    def unlock_batch(self, batch_id: str) -> Batch:
        """Unlock batch to allow modifications (only if locked, not processing)"""
        batch = self.get_batch(batch_id)
        if not batch:
            raise ValueError(f"Batch {batch_id} not found")
        
        if batch.status != BatchStatus.LOCKED:
            raise ValueError(f"Cannot unlock batch in {batch.status.value} state")
        
        batch.status = BatchStatus.DRAFT
        batch.locked_at = None
        self._save_batch(batch)
        
        logger.info(f"Unlocked batch {batch_id}")
        return batch
    
    def _validate_batch_config(self, batch: Batch):
        """Validate batch configuration before locking"""
        config = batch.config
        
        # Validate platform
        try:
            platform = Platform(config.platform)
            fmt = get_format(platform)
        except ValueError:
            raise BatchValidationError(f"Invalid platform: {config.platform}")
        
        # Validate duration
        if config.duration > fmt.max_duration:
            raise BatchValidationError(
                f"Duration {config.duration}s exceeds {config.platform} max of {fmt.max_duration}s"
            )
        
        # Validate items have content
        for item in batch.items:
            if not item.content or len(item.content.strip()) == 0:
                raise BatchValidationError(f"Item {item.order + 1} has no content")
        
        logger.info(f"Batch {batch.id} configuration validated")
    
    # ==================== Processing ====================
    
    async def start_processing(self, batch_id: str) -> Batch:
        """Start processing a locked batch"""
        batch = self.get_batch(batch_id)
        if not batch:
            raise ValueError(f"Batch {batch_id} not found")
        
        if batch.status not in [BatchStatus.LOCKED, BatchStatus.PARTIAL]:
            raise ValueError(f"Cannot start batch in {batch.status.value} state")
        
        batch.status = BatchStatus.PROCESSING
        batch.started_at = datetime.now()
        self._save_batch(batch)
        
        logger.info(f"Starting batch {batch_id} processing")
        
        # Get items to process
        items_to_process = batch.get_pending_items()
        if batch.status == BatchStatus.PARTIAL:
            # Also include failed items for retry
            items_to_process.extend(batch.get_failed_items())
        
        # Process items with concurrency limit
        await self._process_items(batch, items_to_process)
        
        return batch
    
    async def _process_items(self, batch: Batch, items: List[BatchItem]):
        """Process batch items with concurrency control"""
        semaphore = asyncio.Semaphore(batch.max_parallel)
        
        async def process_with_semaphore(item: BatchItem):
            async with semaphore:
                await self._process_single_item(batch, item)
        
        # Create tasks for all items
        tasks = [process_with_semaphore(item) for item in items]
        
        # Wait for all to complete (failures are isolated)
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Update batch status
        batch.update_progress()
        self._save_batch(batch)
        
        logger.info(
            f"Batch {batch.id} processing complete: "
            f"{batch.completed_items}/{batch.total_items} success, "
            f"{batch.failed_items} failed"
        )
    
    async def _process_single_item(self, batch: Batch, item: BatchItem):
        """Process a single batch item"""
        logger.info(f"Processing item {item.id} (order: {item.order})")
        
        item.status = BatchItemStatus.PROCESSING
        self._save_batch(batch)
        
        try:
            # Simulate video generation
            # In production, this would call the actual orchestrator
            await self._generate_video_for_item(batch, item)
            
            item.status = BatchItemStatus.COMPLETE
            item.completed_at = datetime.now()
            
            logger.info(f"Item {item.id} completed successfully")
            
        except Exception as e:
            logger.error(f"Item {item.id} failed: {e}")
            item.status = BatchItemStatus.FAILED
            item.error_message = str(e)
            item.retry_count += 1
        
        self._save_batch(batch)
    
    async def _generate_video_for_item(self, batch: Batch, item: BatchItem):
        """Generate video for a single item using batch config"""
        # TODO: Integrate with actual orchestrator
        # For now, simulate generation
        
        import random
        
        # Simulate processing time (1-3 seconds)
        await asyncio.sleep(random.uniform(1, 3))
        
        # Simulate occasional failures (10% chance)
        if random.random() < 0.1:
            raise Exception("Simulated generation failure")
        
        # Create mock output path
        output_path = os.path.join(
            ".story_assets/videos",
            f"batch_{batch.id}",
            f"item_{item.order}_{batch.config.platform}.mp4"
        )
        
        # Create directory (don't actually create video in simulation)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        item.output_path = output_path
    
    # ==================== Retry Operations ====================
    
    async def retry_failed(self, batch_id: str) -> Batch:
        """Retry only failed items in a batch"""
        batch = self.get_batch(batch_id)
        if not batch:
            raise ValueError(f"Batch {batch_id} not found")
        
        if batch.status not in [BatchStatus.PARTIAL, BatchStatus.FAILED]:
            raise ValueError(f"No failed items to retry in {batch.status.value} batch")
        
        failed_items = batch.get_failed_items()
        if not failed_items:
            raise ValueError("No failed items to retry")
        
        # Reset failed items to pending
        for item in failed_items:
            item.status = BatchItemStatus.PENDING
            item.error_message = None
        
        batch.status = BatchStatus.PROCESSING
        self._save_batch(batch)
        
        logger.info(f"Retrying {len(failed_items)} failed items in batch {batch_id}")
        
        await self._process_items(batch, failed_items)
        
        return batch
    
    # ==================== Storage ====================
    
    def _save_batch(self, batch: Batch):
        """Save batch to disk"""
        path = os.path.join(self.storage_path, f"{batch.id}.json")
        with open(path, 'w') as f:
            json.dump(batch.to_dict(), f, indent=2)
    
    def _load_batch(self, batch_id: str) -> Optional[Batch]:
        """Load batch from disk"""
        path = os.path.join(self.storage_path, f"{batch_id}.json")
        if not os.path.exists(path):
            return None
        
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            batch = Batch.from_dict(data)
            _batches[batch.id] = batch
            return batch
        except Exception as e:
            logger.error(f"Error loading batch {batch_id}: {e}")
            return None
    
    def cleanup(self):
        """Cleanup executor"""
        self.executor.shutdown(wait=False)
