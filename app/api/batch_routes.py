"""
Batch Generation API Routes
CRUD, processing control, and query endpoints for batch operations.
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

from app.batch.models import BatchStatus
from app.batch.service import BatchService, BatchValidationError

router = APIRouter(prefix="/v1/batch", tags=["batch"])

# Initialize service
batch_service = BatchService()


# ==================== Request/Response Models ====================

class BatchConfigRequest(BaseModel):
    platform: str = Field(default="youtube_shorts")
    duration: int = Field(default=30, ge=5, le=180)
    voice: str = Field(default="en-US-GuyNeural")
    genre: str = Field(default="educational")
    language: str = Field(default="en")
    audience: str = Field(default="general")


class CreateBatchRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    config: Optional[BatchConfigRequest] = None


class AddItemsRequest(BaseModel):
    contents: List[str] = Field(..., min_items=1, max_items=100)


class BatchResponse(BaseModel):
    id: str
    name: str
    status: str
    total_items: int
    completed_items: int
    failed_items: int


# ==================== CRUD Endpoints ====================

@router.post("/", response_model=BatchResponse)
async def create_batch(request: CreateBatchRequest):
    """Create a new batch in draft state"""
    config = request.config.dict() if request.config else None
    
    batch = batch_service.create_batch(
        name=request.name,
        description=request.description,
        config=config
    )
    
    return BatchResponse(
        id=batch.id,
        name=batch.name,
        status=batch.status.value,
        total_items=batch.total_items,
        completed_items=batch.completed_items,
        failed_items=batch.failed_items
    )


@router.get("/{batch_id}")
async def get_batch(batch_id: str):
    """Get batch details including all items"""
    batch = batch_service.get_batch(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    return batch.to_dict()


@router.get("/")
async def list_batches(status: Optional[str] = None):
    """List all batches with optional status filter"""
    status_filter = BatchStatus(status) if status else None
    batches = batch_service.list_batches(status=status_filter)
    
    return {
        "batches": [
            {
                "id": b.id,
                "name": b.name,
                "status": b.status.value,
                "total_items": b.total_items,
                "completed_items": b.completed_items,
                "failed_items": b.failed_items,
                "created_at": b.created_at.isoformat()
            }
            for b in batches
        ]
    }


@router.delete("/{batch_id}")
async def delete_batch(batch_id: str):
    """Delete a batch (only if draft, complete, or cancelled)"""
    try:
        result = batch_service.delete_batch(batch_id)
        if not result:
            raise HTTPException(status_code=404, detail="Batch not found")
        return {"message": "Batch deleted", "batch_id": batch_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== Item Management ====================

@router.post("/{batch_id}/items")
async def add_items(batch_id: str, request: AddItemsRequest):
    """Add items to a draft batch"""
    try:
        items = batch_service.add_items(batch_id, request.contents)
        return {
            "message": f"Added {len(items)} items",
            "items": [i.to_dict() for i in items]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{batch_id}/items/{item_id}")
async def remove_item(batch_id: str, item_id: str):
    """Remove item from draft batch"""
    try:
        result = batch_service.remove_item(batch_id, item_id)
        if not result:
            raise HTTPException(status_code=404, detail="Item not found")
        return {"message": "Item removed", "item_id": item_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== Lifecycle Control ====================

@router.post("/{batch_id}/lock")
async def lock_batch(batch_id: str):
    """Lock batch configuration (validates before locking)"""
    try:
        batch = batch_service.lock_batch(batch_id)
        return {
            "message": "Batch locked and validated",
            "batch_id": batch.id,
            "status": batch.status.value,
            "locked_at": batch.locked_at.isoformat()
        }
    except BatchValidationError as e:
        raise HTTPException(status_code=400, detail=f"Validation failed: {str(e)}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{batch_id}/unlock")
async def unlock_batch(batch_id: str):
    """Unlock batch to allow modifications"""
    try:
        batch = batch_service.unlock_batch(batch_id)
        return {
            "message": "Batch unlocked",
            "batch_id": batch.id,
            "status": batch.status.value
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== Processing Control ====================

@router.post("/{batch_id}/start")
async def start_processing(batch_id: str, background_tasks: BackgroundTasks):
    """Start processing a locked batch"""
    batch = batch_service.get_batch(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    if batch.status not in [BatchStatus.LOCKED, BatchStatus.PARTIAL]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot start batch in {batch.status.value} state"
        )
    
    # Start processing in background
    background_tasks.add_task(run_batch_processing, batch_id)
    
    return {
        "message": "Batch processing started",
        "batch_id": batch_id,
        "status": "processing",
        "total_items": batch.total_items
    }


@router.post("/{batch_id}/retry")
async def retry_failed(batch_id: str, background_tasks: BackgroundTasks):
    """Retry only failed items in a batch"""
    batch = batch_service.get_batch(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    if batch.status not in [BatchStatus.PARTIAL, BatchStatus.FAILED]:
        raise HTTPException(
            status_code=400,
            detail=f"No failed items to retry in {batch.status.value} batch"
        )
    
    failed_count = len(batch.get_failed_items())
    
    # Start retry in background
    background_tasks.add_task(run_batch_retry, batch_id)
    
    return {
        "message": f"Retrying {failed_count} failed items",
        "batch_id": batch_id,
        "items_to_retry": failed_count
    }


# ==================== Query Endpoints ====================

@router.get("/{batch_id}/progress")
async def get_progress(batch_id: str):
    """Get batch processing progress"""
    batch = batch_service.get_batch(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    return {
        "batch_id": batch_id,
        "status": batch.status.value,
        "progress": {
            "total": batch.total_items,
            "completed": batch.completed_items,
            "failed": batch.failed_items,
            "pending": batch.total_items - batch.completed_items - batch.failed_items,
            "percent_complete": round(
                (batch.completed_items / batch.total_items * 100) if batch.total_items > 0 else 0,
                1
            )
        }
    }


@router.get("/{batch_id}/failed")
async def get_failed_items(batch_id: str):
    """Get failed items with error messages"""
    batch = batch_service.get_batch(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    failed = batch.get_failed_items()
    return {
        "batch_id": batch_id,
        "failed_count": len(failed),
        "items": [i.to_dict() for i in failed]
    }


@router.get("/{batch_id}/outputs")
async def get_outputs(batch_id: str):
    """Get successful outputs"""
    batch = batch_service.get_batch(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    complete = batch.get_complete_items()
    return {
        "batch_id": batch_id,
        "output_count": len(complete),
        "items": [
            {
                "order": i.order,
                "content": i.content[:50] + "..." if len(i.content) > 50 else i.content,
                "output_path": i.output_path
            }
            for i in sorted(complete, key=lambda x: x.order)
        ]
    }


# ==================== Background Tasks ====================

async def run_batch_processing(batch_id: str):
    """Background task for batch processing"""
    import asyncio
    await batch_service.start_processing(batch_id)


async def run_batch_retry(batch_id: str):
    """Background task for retrying failed items"""
    import asyncio
    await batch_service.retry_failed(batch_id)
