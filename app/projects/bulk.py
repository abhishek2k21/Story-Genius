"""
Bulk Operations
Efficient bulk project management.
"""
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import uuid


MAX_BULK_SIZE = 100


@dataclass
class BulkResult:
    """Result of bulk operation"""
    operation_id: str
    operation: str
    total_count: int
    success_count: int
    failure_count: int
    failures: List[Dict] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "operation_id": self.operation_id,
            "operation": self.operation,
            "total_count": self.total_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "failures": self.failures
        }


class ProjectBulkService:
    """Bulk project operations"""
    
    def validate_bulk_size(self, project_ids: List[str]) -> tuple:
        """Validate bulk operation size"""
        if len(project_ids) > MAX_BULK_SIZE:
            return False, f"Maximum {MAX_BULK_SIZE} projects per operation"
        if len(project_ids) == 0:
            return False, "No projects specified"
        return True, "Valid"
    
    def bulk_move(
        self,
        project_ids: List[str],
        folder_id: str,
        move_fn
    ) -> BulkResult:
        """Move multiple projects to folder"""
        valid, msg = self.validate_bulk_size(project_ids)
        if not valid:
            return BulkResult(
                operation_id=str(uuid.uuid4()),
                operation="move",
                total_count=0,
                success_count=0,
                failure_count=1,
                failures=[{"error": msg}]
            )
        
        success = 0
        failures = []
        
        for pid in project_ids:
            try:
                if move_fn(pid, folder_id):
                    success += 1
                else:
                    failures.append({"project_id": pid, "error": "Move failed"})
            except Exception as e:
                failures.append({"project_id": pid, "error": str(e)})
        
        return BulkResult(
            operation_id=str(uuid.uuid4()),
            operation="move",
            total_count=len(project_ids),
            success_count=success,
            failure_count=len(failures),
            failures=failures
        )
    
    def bulk_tag(
        self,
        project_ids: List[str],
        tag_ids: List[str],
        tag_fn
    ) -> BulkResult:
        """Add tags to multiple projects"""
        valid, msg = self.validate_bulk_size(project_ids)
        if not valid:
            return BulkResult(
                operation_id=str(uuid.uuid4()),
                operation="tag",
                total_count=0,
                success_count=0,
                failure_count=1,
                failures=[{"error": msg}]
            )
        
        success = 0
        failures = []
        
        for pid in project_ids:
            try:
                result, _ = tag_fn(pid, tag_ids)
                if result:
                    success += 1
                else:
                    failures.append({"project_id": pid, "error": "Tag failed"})
            except Exception as e:
                failures.append({"project_id": pid, "error": str(e)})
        
        return BulkResult(
            operation_id=str(uuid.uuid4()),
            operation="tag",
            total_count=len(project_ids),
            success_count=success,
            failure_count=len(failures),
            failures=failures
        )
    
    def bulk_archive(
        self,
        project_ids: List[str],
        archive_fn
    ) -> BulkResult:
        """Archive multiple projects"""
        valid, msg = self.validate_bulk_size(project_ids)
        if not valid:
            return BulkResult(
                operation_id=str(uuid.uuid4()),
                operation="archive",
                total_count=0,
                success_count=0,
                failure_count=1,
                failures=[{"error": msg}]
            )
        
        success = 0
        failures = []
        
        for pid in project_ids:
            try:
                if archive_fn(pid):
                    success += 1
                else:
                    failures.append({"project_id": pid, "error": "Archive failed"})
            except Exception as e:
                failures.append({"project_id": pid, "error": str(e)})
        
        return BulkResult(
            operation_id=str(uuid.uuid4()),
            operation="archive",
            total_count=len(project_ids),
            success_count=success,
            failure_count=len(failures),
            failures=failures
        )
    
    def bulk_delete(
        self,
        project_ids: List[str],
        delete_fn
    ) -> BulkResult:
        """Delete multiple projects"""
        valid, msg = self.validate_bulk_size(project_ids)
        if not valid:
            return BulkResult(
                operation_id=str(uuid.uuid4()),
                operation="delete",
                total_count=0,
                success_count=0,
                failure_count=1,
                failures=[{"error": msg}]
            )
        
        success = 0
        failures = []
        
        for pid in project_ids:
            try:
                if delete_fn(pid):
                    success += 1
                else:
                    failures.append({"project_id": pid, "error": "Delete failed"})
            except Exception as e:
                failures.append({"project_id": pid, "error": str(e)})
        
        return BulkResult(
            operation_id=str(uuid.uuid4()),
            operation="delete",
            total_count=len(project_ids),
            success_count=success,
            failure_count=len(failures),
            failures=failures
        )
    
    def bulk_duplicate(
        self,
        project_ids: List[str],
        duplicate_fn
    ) -> BulkResult:
        """Duplicate multiple projects"""
        valid, msg = self.validate_bulk_size(project_ids)
        if not valid:
            return BulkResult(
                operation_id=str(uuid.uuid4()),
                operation="duplicate",
                total_count=0,
                success_count=0,
                failure_count=1,
                failures=[{"error": msg}]
            )
        
        success = 0
        failures = []
        created = []
        
        for pid in project_ids:
            try:
                new_id = duplicate_fn(pid)
                if new_id:
                    success += 1
                    created.append(new_id)
                else:
                    failures.append({"project_id": pid, "error": "Duplicate failed"})
            except Exception as e:
                failures.append({"project_id": pid, "error": str(e)})
        
        result = BulkResult(
            operation_id=str(uuid.uuid4()),
            operation="duplicate",
            total_count=len(project_ids),
            success_count=success,
            failure_count=len(failures),
            failures=failures
        )
        result.created_ids = created
        return result


project_bulk_service = ProjectBulkService()
