"""
Commenting and Feedback System
Real-time commenting with threading and mentions.
"""
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from app.core.logging import get_logger

logger = get_logger(__name__)


class CommentStatus(Enum):
    """Comment status"""
    OPEN = "open"
    RESOLVED = "resolved"


@dataclass
class Comment:
    """Comment data"""
    comment_id: str
    user_id: str
    target_id: str  # video_id or project_id
    target_type: str  # "video" or "project"
    content: str
    timestamp: Optional[float] = None  # For video comments (seconds)
    status: CommentStatus = CommentStatus.OPEN
    created_at: datetime = field(default_factory=datetime.utcnow)
    parent_id: Optional[str] = None  # For threaded replies
    mentions: List[str] = field(default_factory=list)  # @mentioned user_ids


class CommentingSystem:
    """
    Real-time commenting and feedback system.
    
    Features:
    - Video comments (timestamp-based)
    - Project comments
    - Comment threading (replies)
    - @mentions with notifications
    - Resolve/unresolve comments
    """
    
    def __init__(self):
        self._comments: Dict[str, Comment] = {}
        self._target_comments: Dict[str, List[str]] = {}  # target_id -> comment_ids
        self._user_mentions: Dict[str, List[str]] = {}  # user_id -> comment_ids
        logger.info("CommentingSystem initialized")
    
    def add_comment(
        self,
        comment_id: str,
        user_id: str,
        target_id: str,
        target_type: str,
        content: str,
        timestamp: Optional[float] = None,
        parent_id: Optional[str] = None
    ) -> Comment:
        """
        Add a comment.
        
        Args:
            comment_id: Unique comment ID
            user_id: Commenter user ID
            target_id: Target video/project ID
            target_type: "video" or "project"
            content: Comment text
            timestamp: Optional video timestamp (seconds)
            parent_id: Optional parent comment for threading
        
        Returns:
            Created comment
        """
        # Extract mentions (@username)
        mentions = self._extract_mentions(content)
        
        comment = Comment(
            comment_id=comment_id,
            user_id=user_id,
            target_id=target_id,
            target_type=target_type,
            content=content,
            timestamp=timestamp,
            parent_id=parent_id,
            mentions=mentions
        )
        
        self._comments[comment_id] = comment
        
        # Index by target
        if target_id not in self._target_comments:
            self._target_comments[target_id] = []
        self._target_comments[target_id].append(comment_id)
        
        # Index mentions
        for mentioned_user in mentions:
            if mentioned_user not in self._user_mentions:
                self._user_mentions[mentioned_user] = []
            self._user_mentions[mentioned_user].append(comment_id)
        
        logger.info(
            f"Added comment: {comment_id} on {target_type} {target_id} "
            f"(timestamp: {timestamp}, mentions: {len(mentions)})"
        )
        
        return comment
    
    def get_comments(
        self,
        target_id: str,
        include_resolved: bool = False
    ) -> List[Comment]:
        """
        Get all comments for a target.
        
        Args:
            target_id: Target video/project ID
            include_resolved: Include resolved comments
        
        Returns:
            List of comments
        """
        comment_ids = self._target_comments.get(target_id, [])
        comments = [self._comments[cid] for cid in comment_ids if cid in self._comments]
        
        # Filter by status
        if not include_resolved:
            comments = [c for c in comments if c.status == CommentStatus.OPEN]
        
        # Sort by timestamp (video comments) or created_at
        comments.sort(key=lambda c: c.timestamp if c.timestamp else 0)
        
        return comments
    
    def get_comment_thread(self, comment_id: str) -> List[Comment]:
        """
        Get comment and all its replies.
        
        Args:
            comment_id: Root comment ID
        
        Returns:
            List of comments (root + replies)
        """
        if comment_id not in self._comments:
            return []
        
        thread = [self._comments[comment_id]]
        
        # Find all replies
        for cid, comment in self._comments.items():
            if comment.parent_id == comment_id:
                thread.append(comment)
        
        # Sort by created_at
        thread.sort(key=lambda c: c.created_at)
        
        return thread
    
    def reply_to_comment(
        self,
        reply_id: str,
        parent_id: str,
        user_id: str,
        content: str
    ) -> Comment:
        """
        Reply to a comment.
        
        Args:
            reply_id: Unique reply ID
            parent_id: Parent comment ID
            user_id: Replier user ID
            content: Reply text
        
        Returns:
            Created reply
        """
        if parent_id not in self._comments:
            raise ValueError(f"Parent comment not found: {parent_id}")
        
        parent = self._comments[parent_id]
        
        # Create reply with same target as parent
        reply = self.add_comment(
            comment_id=reply_id,
            user_id=user_id,
            target_id=parent.target_id,
            target_type=parent.target_type,
            content=content,
            timestamp=parent.timestamp,  # Inherit timestamp
            parent_id=parent_id
        )
        
        logger.info(f"Added reply {reply_id} to comment {parent_id}")
        
        return reply
    
    def resolve_comment(self, comment_id: str, user_id: str):
        """
        Mark comment as resolved.
        
        Args:
            comment_id: Comment ID
            user_id: User resolving the comment
        """
        if comment_id not in self._comments:
            raise ValueError(f"Comment not found: {comment_id}")
        
        comment = self._comments[comment_id]
        comment.status = CommentStatus.RESOLVED
        
        logger.info(f"Resolved comment {comment_id} by {user_id}")
    
    def unresolve_comment(self, comment_id: str, user_id: str):
        """
        Mark comment as unresolved.
        
        Args:
            comment_id: Comment ID
            user_id: User unresolving the comment
        """
        if comment_id not in self._comments:
            raise ValueError(f"Comment not found: {comment_id}")
        
        comment = self._comments[comment_id]
        comment.status = CommentStatus.OPEN
        
        logger.info(f"Unresolved comment {comment_id} by {user_id}")
    
    def delete_comment(self, comment_id: str, user_id: str):
        """
        Delete a comment.
        
        Args:
            comment_id: Comment ID
            user_id: User deleting the comment
        """
        if comment_id not in self._comments:
            return
        
        comment = self._comments[comment_id]
        
        # Only allow creator to delete
        if comment.user_id != user_id:
            raise PermissionError("Only comment creator can delete")
        
        # Remove from indices
        target_id = comment.target_id
        if target_id in self._target_comments:
            self._target_comments[target_id] = [
                cid for cid in self._target_comments[target_id]
                if cid != comment_id
            ]
        
        for mentioned_user in comment.mentions:
            if mentioned_user in self._user_mentions:
                self._user_mentions[mentioned_user] = [
                    cid for cid in self._user_mentions[mentioned_user]
                    if cid != comment_id
                ]
        
        # Delete comment
        del self._comments[comment_id]
        
        logger.info(f"Deleted comment {comment_id}")
    
    def get_user_mentions(self, user_id: str) -> List[Comment]:
        """
        Get all comments mentioning a user.
        
        Args:
            user_id: User ID
        
        Returns:
            List of comments
        """
        comment_ids = self._user_mentions.get(user_id, [])
        comments = [self._comments[cid] for cid in comment_ids if cid in self._comments]
        
        # Sort by created_at (descending)
        comments.sort(key=lambda c: c.created_at, reverse=True)
        
        return comments
    
    def _extract_mentions(self, content: str) -> List[str]:
        """Extract @mentions from comment content"""
        import re
        
        # Find all @username patterns
        pattern = r'@(\w+)'
        matches = re.findall(pattern, content)
        
        return list(set(matches))  # Deduplicate


# Global instance
commenting_system = CommentingSystem()
