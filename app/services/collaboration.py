"""
Collaboration & Team Features.
Enable team collaboration with comments, mentions, and permissions.
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from enum import Enum
import uuid
import re
import logging

logger = logging.getLogger(__name__)


class TeamPermission(str, Enum):
    """Team member permissions."""
    OWNER = "owner"  # Full control
    ADMIN = "admin"  # Manage team + all editor permissions
    EDITOR = "editor"  # Create, edit, delete videos
    VIEWER = "viewer"  # View only


class Comment:
    """Video comment for collaboration."""
    
    def __init__(
        self,
        id: str,
        video_id: str,
        user_id: str,
        content: str,
        timestamp: Optional[float] = None,  # Video timestamp in seconds
        parent_id: Optional[str] = None  # For threaded replies
    ):
        self.id = id
        self.video_id = video_id
        self.user_id = user_id
        self.content = content
        self.timestamp = timestamp
        self.parent_id = parent_id
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.resolved = False
        self.resolved_by: Optional[str] = None
        self.resolved_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "video_id": self.video_id,
            "user_id": self.user_id,
            "content": self.content,
            "timestamp": self.timestamp,
            "parent_id": self.parent_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "resolved": self.resolved,
            "resolved_by": self.resolved_by,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None
        }


class TeamMember:
    """Team member model."""
    
    def __init__(
        self,
        id: str,
        workspace_id: str,
        user_id: str,
        email: str,
        permission: TeamPermission
    ):
        self.id = id
        self.workspace_id = workspace_id
        self.user_id = user_id
        self.email = email
        self.permission = permission
        self.joined_at = datetime.utcnow()
        self.last_active: Optional[datetime] = None


class CollaborationService:
    """Manage team collaboration."""
    
    def __init__(self, db_session, email_service):
        self.db = db_session
        self.email_service = email_service
        self.comments: Dict[str, Comment] = {}
        self.team_members: Dict[str, TeamMember] = {}
    
    # Team Management
    
    def invite_team_member(
        self,
        workspace_id: str,
        inviter_id: str,
        email: str,
        permission: str
    ) -> Dict:
        """
        Invite team member to workspace.
        
        Args:
            workspace_id: Workspace ID
            inviter_id: User sending invitation
            email: Member email
            permission: Access level
            
        Returns:
            Invitation details
        """
        # Validate permission
        try:
            perm = TeamPermission(permission)
        except ValueError:
            raise ValueError(f"Invalid permission: {permission}")
        
        # Check inviter has permission to invite
        if not self._can_manage_team(inviter_id, workspace_id):
            raise PermissionError("Not authorized to invite members")
        
        # Create invitation
        invitation_id = str(uuid.uuid4())
        token = self._generate_invitation_token()
        
        invitation = {
            "id": invitation_id,
            "workspace_id": workspace_id,
            "email": email,
            "permission": perm.value,
            "token": token,
            "invited_by": inviter_id,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(days=7)).isoformat()
        }
        
        # Save invitation
        self._save_invitation(invitation)
        
        # Send invitation email
        self.email_service.send_team_invitation(
            to_email=email,
            workspace_name="Video Creator Workspace",
            inviter_name="Team Admin",
            invitation_link=f"https://app.ytvideocreator.com/invite/{token}",
            permission=perm.value
        )
        
        logger.info(f"Sent invitation to {email} for workspace {workspace_id}")
        
        return {
            "invitation_id": invitation_id,
            "email": email,
            "permission": perm.value,
            "status": "pending",
            "expires_in_days": 7
        }
    
    def accept_invitation(self, token: str, user_id: str) -> Dict:
        """Accept team invitation."""
        invitation = self._get_invitation_by_token(token)
        
        if not invitation:
            raise ValueError("Invalid invitation token")
        
        if invitation["status"] != "pending":
            raise ValueError("Invitation already used")
        
        # Check expiration
        expires_at = datetime.fromisoformat(invitation["expires_at"])
        if datetime.utcnow() > expires_at:
            raise ValueError("Invitation expired")
        
        # Add user to team
        member_id = str(uuid.uuid4())
        
        member = TeamMember(
            id=member_id,
            workspace_id=invitation["workspace_id"],
            user_id=user_id,
            email=invitation["email"],
            permission=TeamPermission(invitation["permission"])
        )
        
        self.team_members[member_id] = member
        self._save_team_member(member)
        
        # Mark invitation as accepted
        invitation["status"] = "accepted"
        self._save_invitation(invitation)
        
        logger.info(f"User {user_id} joined workspace {invitation['workspace_id']}")
        
        return {
            "success": True,
            "workspace_id": invitation["workspace_id"],
            "permission": invitation["permission"]
        }
    
    def get_team_members(self, workspace_id: str) -> List[Dict]:
        """Get all team members for workspace."""
        members = [
            m for m in self.team_members.values()
            if m.workspace_id == workspace_id
        ]
        
        return [
            {
                "id": m.id,
                "user_id": m.user_id,
                "email": m.email,
                "permission": m.permission.value,
                "joined_at": m.joined_at.isoformat(),
                "last_active": m.last_active.isoformat() if m.last_active else None
            }
            for m in members
        ]
    
    # Comments & Collaboration
    
    def add_comment(
        self,
        video_id: str,
        user_id: str,
        content: str,
        timestamp: Optional[float] = None,
        parent_id: Optional[str] = None
    ) -> Dict:
        """
        Add comment to video.
        
        Args:
            video_id: Video ID
            user_id: Commenter ID
            content: Comment text
            timestamp: Video timestamp in seconds
            parent_id: Parent comment (for replies)
            
        Returns:
            Comment details
        """
        comment_id = str(uuid.uuid4())
        
        comment = Comment(
            id=comment_id,
            video_id=video_id,
            user_id=user_id,
            content=content,
            timestamp=timestamp,
            parent_id=parent_id
        )
        
        self.comments[comment_id] = comment
        self._save_comment(comment)
        
        # Extract and notify mentioned users
        mentioned_users = self._extract_mentions(content)
        for mentioned_user_id in mentioned_users:
            self._notify_mention(mentioned_user_id, comment)
        
        logger.info(f"Added comment {comment_id} on video {video_id}")
        
        return comment.to_dict()
    
    def _extract_mentions(self, content: str) -> List[str]:
        """Extract @mentions from comment."""
        # Find all @username patterns
        pattern = r'@(\w+)'
        usernames = re.findall(pattern, content)
        
        # Convert usernames to user IDs
        # Placeholder - would query database
        return []
    
    def _notify_mention(self, user_id: str, comment: Comment):
        """Send notification about mention."""
        logger.info(f"Notifying user {user_id} about mention in comment {comment.id}")
        # Send in-app notification and email
    
    def get_video_comments(
        self,
        video_id: str,
        include_resolved: bool = False
    ) -> List[Dict]:
        """
        Get all comments for a video.
        
        Args:
            video_id: Video ID
            include_resolved: Include resolved comments
            
        Returns:
            Threaded comment structure
        """
        # Get comments for video
        comments = [
            c for c in self.comments.values()
            if c.video_id == video_id
        ]
        
        if not include_resolved:
            comments = [c for c in comments if not c.resolved]
        
        # Build threaded structure
        return self._build_comment_threads(comments)
    
    def _build_comment_threads(self, comments: List[Comment]) -> List[Dict]:
        """Build threaded comment structure."""
        # Separate root comments and replies
        root_comments = [c for c in comments if c.parent_id is None]
        replies_by_parent = {}
        
        for comment in comments:
            if comment.parent_id:
                if comment.parent_id not in replies_by_parent:
                    replies_by_parent[comment.parent_id] = []
                replies_by_parent[comment.parent_id].append(comment)
        
        # Build threads
        def build_thread(comment: Comment) -> Dict:
            thread = comment.to_dict()
            thread["replies"] = [
                build_thread(reply)
                for reply in replies_by_parent.get(comment.id, [])
            ]
            return thread
        
        return [build_thread(c) for c in root_comments]
    
    def resolve_comment(
        self,
        comment_id: str,
        user_id: str
    ) -> Dict:
        """Mark comment as resolved."""
        comment = self.comments.get(comment_id)
        
        if not comment:
            raise ValueError("Comment not found")
        
        comment.resolved = True
        comment.resolved_by = user_id
        comment.resolved_at = datetime.utcnow()
        
        self._save_comment(comment)
        
        logger.info(f"Comment {comment_id} resolved by {user_id}")
        
        return comment.to_dict()
    
    def unresolve_comment(self, comment_id: str) -> Dict:
        """Reopen resolved comment."""
        comment = self.comments.get(comment_id)
        
        if not comment:
            raise ValueError("Comment not found")
        
        comment.resolved = False
        comment.resolved_by = None
        comment.resolved_at = None
        
        self._save_comment(comment)
        
        return comment.to_dict()
    
    # Helper methods
    
    def _can_manage_team(self, user_id: str, workspace_id: str) -> bool:
        """Check if user can manage team."""
        # Check if user is owner or admin
        member = self._get_member(user_id, workspace_id)
        return member and member.permission in [TeamPermission.OWNER, TeamPermission.ADMIN]
    
    def _get_member(self, user_id: str, workspace_id: str) -> Optional[TeamMember]:
        """Get team member."""
        for member in self.team_members.values():
            if member.user_id == user_id and member.workspace_id == workspace_id:
                return member
        return None
    
    def _generate_invitation_token(self) -> str:
        """Generate secure invitation token."""
        import secrets
        return secrets.token_urlsafe(32)
    
    def _save_invitation(self, invitation: Dict):
        """Save invitation to database."""
        # Placeholder
        pass
    
    def _get_invitation_by_token(self, token: str) -> Optional[Dict]:
        """Get invitation by token."""
        # Placeholder
        return None
    
    def _save_team_member(self, member: TeamMember):
        """Save team member to database."""
        # Placeholder
        pass
    
    def _save_comment(self, comment: Comment):
        """Save comment to database."""
        # Placeholder
        pass
