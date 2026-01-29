"""
Team Management with Role-Based Access Control
Multi-user collaboration with permissions.
"""
from typing import Dict, List, Set, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict

from app.core.logging import get_logger

logger = get_logger(__name__)


class TeamRole(Enum):
    """Team member roles"""
    OWNER = "owner"
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


class Permission(Enum):
    """Permissions"""
    CREATE_VIDEO = "create_video"
    EDIT_VIDEO = "edit_video"
    DELETE_VIDEO = "delete_video"
    PUBLISH_VIDEO = "publish_video"
    MANAGE_TEAM = "manage_team"
    MANAGE_BILLING = "manage_billing"
    VIEW_ANALYTICS = "view_analytics"
    COMMENT = "comment"


# Role permissions mapping
ROLE_PERMISSIONS = {
    TeamRole.OWNER: {
        Permission.CREATE_VIDEO,
        Permission.EDIT_VIDEO,
        Permission.DELETE_VIDEO,
        Permission.PUBLISH_VIDEO,
        Permission.MANAGE_TEAM,
        Permission.MANAGE_BILLING,
        Permission.VIEW_ANALYTICS,
        Permission.COMMENT
    },
    TeamRole.ADMIN: {
        Permission.CREATE_VIDEO,
        Permission.EDIT_VIDEO,
        Permission.DELETE_VIDEO,
        Permission.PUBLISH_VIDEO,
        Permission.MANAGE_TEAM,
        Permission.VIEW_ANALYTICS,
        Permission.COMMENT
    },
    TeamRole.EDITOR: {
        Permission.CREATE_VIDEO,
        Permission.EDIT_VIDEO,
        Permission.PUBLISH_VIDEO,
        Permission.VIEW_ANALYTICS,
        Permission.COMMENT
    },
    TeamRole.VIEWER: {
        Permission.VIEW_ANALYTICS,
        Permission.COMMENT
    }
}


@dataclass
class TeamMember:
    """Team member data"""
    user_id: str
    role: TeamRole
    joined_at: datetime = field(default_factory=datetime.utcnow)
    invited_by: Optional[str] = None


@dataclass
class Team:
    """Team data"""
    team_id: str
    name: str
    owner_id: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    members: Dict[str, TeamMember] = field(default_factory=dict)


@dataclass
class ActivityLog:
    """Team activity log entry"""
    team_id: str
    user_id: str
    action: str
    target: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


class TeamManager:
    """
    Team management with role-based access control.
    
    Features:
    - Team creation and management
    - Role-based permissions
    - Member invitations
    - Activity logging
    """
    
    def __init__(self):
        self._teams: Dict[str, Team] = {}
        self._user_teams: Dict[str, Set[str]] = defaultdict(set)  # user_id -> team_ids
        self._pending_invites: Dict[str, Dict] = {}  # invite_id -> invite_data
        self._activity_log: List[ActivityLog] = []
        logger.info("TeamManager initialized")
    
    def create_team(
        self,
        team_id: str,
        name: str,
        owner_id: str
    ) -> Team:
        """
        Create a new team.
        
        Args:
            team_id: Unique team ID
            name: Team name
            owner_id: User ID of owner
        
        Returns:
            Created team
        """
        team = Team(
            team_id=team_id,
            name=name,
            owner_id=owner_id
        )
        
        # Add owner as member
        team.members[owner_id] = TeamMember(
            user_id=owner_id,
            role=TeamRole.OWNER
        )
        
        self._teams[team_id] = team
        self._user_teams[owner_id].add(team_id)
        
        # Log activity
        self._log_activity(team_id, owner_id, "team_created")
        
        logger.info(f"Created team: {team_id} (owner: {owner_id})")
        
        return team
    
    def add_member(
        self,
        team_id: str,
        user_id: str,
        role: TeamRole,
        invited_by: str
    ):
        """
        Add member to team.
        
        Args:
            team_id: Team ID
            user_id: User ID to add
            role: Role to assign
            invited_by: User ID of inviter
        """
        if team_id not in self._teams:
            raise ValueError(f"Team not found: {team_id}")
        
        team = self._teams[team_id]
        
        # Check if inviter has permission
        if not self.check_permission(invited_by, team_id, Permission.MANAGE_TEAM):
            raise PermissionError("Inviter does not have permission to manage team")
        
        # Add member
        team.members[user_id] = TeamMember(
            user_id=user_id,
            role=role,
            invited_by=invited_by
        )
        
        self._user_teams[user_id].add(team_id)
        
        # Log activity
        self._log_activity(team_id, invited_by, "member_added", user_id)
        
        logger.info(f"Added member {user_id} to team {team_id} as {role.value}")
    
    def remove_member(
        self,
        team_id: str,
        user_id: str,
        removed_by: str
    ):
        """
        Remove member from team.
        
        Args:
            team_id: Team ID
            user_id: User ID to remove
            removed_by: User ID of remover
        """
        if team_id not in self._teams:
            raise ValueError(f"Team not found: {team_id}")
        
        team = self._teams[team_id]
        
        # Cannot remove owner
        if user_id == team.owner_id:
            raise ValueError("Cannot remove team owner")
        
        # Check permission
        if not self.check_permission(removed_by, team_id, Permission.MANAGE_TEAM):
            raise PermissionError("User does not have permission to manage team")
        
        # Remove member
        if user_id in team.members:
            del team.members[user_id]
            self._user_teams[user_id].discard(team_id)
            
            # Log activity
            self._log_activity(team_id, removed_by, "member_removed", user_id)
            
            logger.info(f"Removed member {user_id} from team {team_id}")
    
    def update_member_role(
        self,
        team_id: str,
        user_id: str,
        new_role: TeamRole,
        updated_by: str
    ):
        """
        Update member's role.
        
        Args:
            team_id: Team ID
            user_id: User ID
            new_role: New role
            updated_by: User ID of updater
        """
        if team_id not in self._teams:
            raise ValueError(f"Team not found: {team_id}")
        
        team = self._teams[team_id]
        
        # Cannot change owner's role
        if user_id == team.owner_id:
            raise ValueError("Cannot change owner's role")
        
        # Check permission
        if not self.check_permission(updated_by, team_id, Permission.MANAGE_TEAM):
            raise PermissionError("User does not have permission to manage team")
        
        # Update role
        if user_id in team.members:
            old_role = team.members[user_id].role
            team.members[user_id].role = new_role
            
            # Log activity
            self._log_activity(
                team_id,
                updated_by,
                "role_updated",
                f"{user_id} ({old_role.value} → {new_role.value})"
            )
            
            logger.info(f"Updated {user_id} role to {new_role.value} in team {team_id}")
    
    def check_permission(
        self,
        user_id: str,
        team_id: str,
        permission: Permission
    ) -> bool:
        """
        Check if user has permission in team.
        
        Args:
            user_id: User ID
            team_id: Team ID
            permission: Permission to check
        
        Returns:
            True if user has permission
        """
        if team_id not in self._teams:
            return False
        
        team = self._teams[team_id]
        
        if user_id not in team.members:
            return False
        
        member = team.members[user_id]
        role_permissions = ROLE_PERMISSIONS.get(member.role, set())
        
        return permission in role_permissions
    
    def get_team(self, team_id: str) -> Optional[Team]:
        """Get team by ID"""
        return self._teams.get(team_id)
    
    def get_user_teams(self, user_id: str) -> List[Team]:
        """Get all teams user belongs to"""
        team_ids = self._user_teams.get(user_id, set())
        return [self._teams[tid] for tid in team_ids if tid in self._teams]
    
    def get_team_members(self, team_id: str) -> List[TeamMember]:
        """Get all members of a team"""
        if team_id not in self._teams:
            return []
        
        return list(self._teams[team_id].members.values())
    
    def get_activity_log(
        self,
        team_id: str,
        limit: int = 50
    ) -> List[ActivityLog]:
        """
        Get activity log for team.
        
        Args:
            team_id: Team ID
            limit: Number of entries to return
        
        Returns:
            Activity log entries
        """
        logs = [
            log for log in self._activity_log
            if log.team_id == team_id
        ]
        
        # Sort by timestamp (descending)
        logs.sort(key=lambda x: x.timestamp, reverse=True)
        
        return logs[:limit]
    
    def _log_activity(
        self,
        team_id: str,
        user_id: str,
        action: str,
        target: Optional[str] = None
    ):
        """Log team activity"""
        log = ActivityLog(
            team_id=team_id,
            user_id=user_id,
            action=action,
            target=target
        )
        
        self._activity_log.append(log)


# Global instance
team_manager = TeamManager()
