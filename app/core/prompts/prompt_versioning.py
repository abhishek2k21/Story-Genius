"""
Prompt Versioning System
Track prompt versions and enable rollback.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
import json

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class PromptVersion:
    """Prompt version record"""
    id: str
    prompt_id: str
    version: str
    template: str
    created_at: datetime
    author: str
    changes: str = ""
    performance_score: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "prompt_id": self.prompt_id,
            "version": self.version,
            "template": self.template,
            "created_at": self.created_at.isoformat(),
            "author": self.author,
            "changes": self.changes,
            "performance_score": self.performance_score,
            "metadata": self.metadata
        }


class PromptVersionManager:
    """
    Manages prompt versions.
    In production, store in database.
    """
    
    def __init__(self):
        # In-memory storage (replace with database)
        self._versions: Dict[str, List[PromptVersion]] = {}
    
    def create_version(
        self,
        prompt_id: str,
        version: str,
        template: str,
        author: str = "system",
        changes: str = ""
    ) -> PromptVersion:
        """
        Create a new prompt version.
        
        Args:
            prompt_id: Prompt identifier
            version: Version string (e.g., "1.0", "1.1")
            template: Prompt template text
            author: Author of the change
            changes: Description of changes
            
        Returns:
            Created PromptVersion
        """
        import uuid
        
        version_record = PromptVersion(
            id=str(uuid.uuid4()),
            prompt_id=prompt_id,
            version=version,
            template=template,
            created_at=datetime.utcnow(),
            author=author,
            changes=changes
        )
        
        if prompt_id not in self._versions:
            self._versions[prompt_id] = []
        
        self._versions[prompt_id].append(version_record)
        
        logger.info(
            f"Created version {version} for prompt {prompt_id}",
            extra={"prompt_id": prompt_id, "version": version, "author": author}
        )
        
        return version_record
    
    def get_version(
        self,
        prompt_id: str,
        version: str
    ) -> Optional[PromptVersion]:
        """Get specific version of a prompt"""
        if prompt_id not in self._versions:
            return None
        
        for v in self._versions[prompt_id]:
            if v.version == version:
                return v
        
        return None
    
    def get_latest_version(
        self,
        prompt_id: str
    ) -> Optional[PromptVersion]:
        """Get most recent version of a prompt"""
        if prompt_id not in self._versions:
            return None
        
        versions = sorted(
            self._versions[prompt_id],
            key=lambda v: v.created_at,
            reverse=True
        )
        
        return versions[0] if versions else None
    
    def list_versions(
        self,
        prompt_id: str
    ) -> List[PromptVersion]:
        """List all versions of a prompt"""
        if prompt_id not in self._versions:
            return []
        
        return sorted(
            self._versions[prompt_id],
            key=lambda v: v.created_at,
            reverse=True
        )
    
    def rollback(
        self,
        prompt_id: str,
        target_version: str
    ) -> bool:
        """
        Rollback prompt to a previous version.
        Creates new version with old template.
        
        Args:
            prompt_id: Prompt to rollback
            target_version: Version to rollback to
            
        Returns:
            True if successful
        """
        target = self.get_version(prompt_id, target_version)
        if not target:
            logger.error(f"Version {target_version} not found for prompt {prompt_id}")
            return False
        
        # Increment version number
        latest = self.get_latest_version(prompt_id)
        if latest:
            # Parse version (e.g., "1.5" -> 1.6)
            try:
                major, minor = latest.version.split(".")
                new_version = f"{major}.{int(minor) + 1}"
            except:
                new_version = "rollback"
        else:
            new_version = target_version
        
        # Create new version with old template
        self.create_version(
            prompt_id=prompt_id,
            version=new_version,
            template=target.template,
            author="system",
            changes=f"Rollback to version {target_version}"
        )
        
        logger.info(
            f"Rolled back prompt {prompt_id} to version {target_version}",
            extra={"prompt_id": prompt_id, "from_version": latest.version if latest else None, "to_version": target_version}
        )
        
        return True
    
    def update_performance(
        self,
        prompt_id: str,
        version: str,
        score: float
    ):
        """Update performance score for a version"""
        version_record = self.get_version(prompt_id, version)
        if version_record:
            version_record.performance_score = score
            logger.info(
                f"Updated performance score for {prompt_id} v{version}: {score}",
                extra={"prompt_id": prompt_id, "version": version, "score": score}
            )
    
    def compare_versions(
        self,
        prompt_id: str,
        version1: str,
        version2: str
    ) -> Dict:
        """
        Compare two versions of a prompt.
        
        Returns:
            Dictionary with comparison results
        """
        v1 = self.get_version(prompt_id, version1)
        v2 = self.get_version(prompt_id, version2)
        
        if not v1 or not v2:
            return {"error": "One or both versions not found"}
        
        return {
            "prompt_id": prompt_id,
            "version1": {
                "version": v1.version,
                "created_at": v1.created_at.isoformat(),
                "author": v1.author,
                "performance_score": v1.performance_score,
                "template_length": len(v1.template)
            },
            "version2": {
                "version": v2.version,
                "created_at": v2.created_at.isoformat(),
                "author": v2.author,
                "performance_score": v2.performance_score,
                "template_length": len(v2.template)
            },
            "diff": {
                "template_changed": v1.template != v2.template,
                "performance_delta": (v2.performance_score or 0) - (v1.performance_score or 0)
            }
        }


# Global version manager
version_manager = PromptVersionManager()
