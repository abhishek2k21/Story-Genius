"""
Advanced Role-Based Access Control (RBAC).
Granular permissions for enterprise teams.
"""
from typing import List, Dict, Optional, Set
from datetime import datetime
from enum import Enum
import uuid
import logging

logger = logging.getLogger(__name__)


class Permission(str, Enum):
    """Granular permissions."""
    # Video permissions
    VIDEO_VIEW = "video.view"
    VIDEO_CREATE = "video.create"
    VIDEO_EDIT = "video.edit"
    VIDEO_DELETE = "video.delete"
    VIDEO_PUBLISH = "video.publish"
    
    # Template permissions
    TEMPLATE_VIEW = "template.view"
    TEMPLATE_CREATE = "template.create"
    TEMPLATE_EDIT = "template.edit"
    
    # Team permissions
    TEAM_VIEW = "team.view"
    TEAM_MANAGE = "team.manage"
    
    # Billing permissions
    BILLING_VIEW = "billing.view"
    BILLING_MANAGE = "billing.manage"
    
    # Analytics permissions
    ANALYTICS_VIEW = "analytics.view"
    ANALYTICS_EXPORT = "analytics.export"
    
    # Webhook permissions
    WEBHOOK_VIEW = "webhook.view"
    WEBHOOK_MANAGE = "webhook.manage"


class Role:
    """Role model with permissions."""
    
    def __init__(
        self,
        id: str,
        name: str,
        permissions: List[str],
        organization_id: str,
        description: Optional[str] = None
    ):
        self.id = id
        self.name = name
        self.permissions = permissions
        self.organization_id = organization_id
        self.description = description
        self.is_system_role = False
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "role_id": self.id,
            "name": self.name,
            "description": self.description,
            "permissions": self.permissions,
            "permission_count": len(self.permissions),
            "is_system_role": self.is_system_role,
            "created_at": self.created_at.isoformat()
        }


class RBACService:
    """Advanced RBAC management service."""
    
    def __init__(self):
        # Create predefined system roles
        self.system_roles = self._create_system_roles()
        self.custom_roles: Dict[str, Role] = {}
        self.user_roles: Dict[str, Set[str]] = {}  # user_id -> set of role_ids
    
    def _create_system_roles(self) -> Dict[str, Role]:
        """Create predefined system roles."""
        all_permissions = [p.value for p in Permission]
        
        return {
            "owner": Role(
                id="role_owner",
                name="Owner",
                permissions=all_permissions,  # All permissions
                organization_id="system",
                description="Full access to all features and settings"
            ),
            
            "admin": Role(
                id="role_admin",
                name="Admin",
                permissions=[
                    Permission.VIDEO_VIEW.value,
                    Permission.VIDEO_CREATE.value,
                    Permission.VIDEO_EDIT.value,
                    Permission.VIDEO_DELETE.value,
                    Permission.VIDEO_PUBLISH.value,
                    Permission.TEMPLATE_VIEW.value,
                    Permission.TEMPLATE_CREATE.value,
                    Permission.TEMPLATE_EDIT.value,
                    Permission.TEAM_VIEW.value,
                    Permission.TEAM_MANAGE.value,
                    Permission.ANALYTICS_VIEW.value,
                    Permission.ANALYTICS_EXPORT.value,
                    Permission.WEBHOOK_VIEW.value,
                    Permission.WEBHOOK_MANAGE.value
                ],
                organization_id="system",
                description="Manage team, videos, and analytics. Cannot manage billing."
            ),
            
            "editor": Role(
                id="role_editor",
                name="Editor",
                permissions=[
                    Permission.VIDEO_VIEW.value,
                    Permission.VIDEO_CREATE.value,
                    Permission.VIDEO_EDIT.value,
                    Permission.VIDEO_PUBLISH.value,
                    Permission.TEMPLATE_VIEW.value,
                    Permission.ANALYTICS_VIEW.value
                ],
                organization_id="system",
                description="Create and edit videos, view analytics"
            ),
            
            "viewer": Role(
                id="role_viewer",
                name="Viewer",
                permissions=[
                    Permission.VIDEO_VIEW.value,
                    Permission.TEMPLATE_VIEW.value,
                    Permission.ANALYTICS_VIEW.value
                ],
                organization_id="system",
                description="View-only access to videos and analytics"
            )
        }
    
    def create_custom_role(
        self,
        organization_id: str,
        name: str,
        permissions: List[str],
        description: Optional[str] = None
    ) -> Dict:
        """
        Create custom role for organization.
        
        Args:
            organization_id: Organization ID
            name: Role name
            permissions: List of permission strings
            description: Optional description
            
        Returns:
            Created role details
        """
        # Validate permissions
        valid_permissions = [p.value for p in Permission]
        
        for perm in permissions:
            if perm not in valid_permissions:
                raise ValueError(f"Invalid permission: {perm}")
        
        # Create role
        role_id = str(uuid.uuid4())
        
        role = Role(
            id=role_id,
            name=name,
            permissions=permissions,
            organization_id=organization_id,
            description=description
        )
        
        # Save role
        self.custom_roles[role_id] = role
        self._save_role(role)
        
        logger.info(f"Created custom role '{name}' for organization {organization_id}")
        
        return role.to_dict()
    
    def assign_role(
        self,
        user_id: str,
        role_id: str,
        organization_id: str
    ) -> Dict:
        """
        Assign role to user.
        
        Args:
            user_id: User ID
            role_id: Role ID
            organization_id: Organization ID
            
        Returns:
            Assignment details
        """
        # Get role
        role = self._get_role(role_id)
        
        if not role:
            raise ValueError(f"Role not found: {role_id}")
        
        # Verify role belongs to organization or is system role
        if role.organization_id != organization_id and role.organization_id != "system":
            raise ValueError("Role does not belong to this organization")
        
        # Add role to user
        if user_id not in self.user_roles:
            self.user_roles[user_id] = set()
        
        self.user_roles[user_id].add(role_id)
        
        # Save assignment
        self._save_user_role(user_id, role_id, organization_id)
        
        logger.info(f"Assigned role '{role.name}' to user {user_id}")
        
        return {
            "user_id": user_id,
            "role_id": role_id,
            "role_name": role.name,
            "permissions": role.permissions
        }
    
    def remove_role(
        self,
        user_id: str,
        role_id: str
    ) -> bool:
        """Remove role from user."""
        if user_id in self.user_roles:
            self.user_roles[user_id].discard(role_id)
            self._delete_user_role(user_id, role_id)
            
            logger.info(f"Removed role {role_id} from user {user_id}")
            return True
        
        return False
    
    def check_permission(
        self,
        user_id: str,
        permission: str,
        resource_id: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> bool:
        """
        Check if user has specific permission.
        
        Args:
            user_id: User ID
            permission: Permission to check (e.g., "video.edit")
            resource_id: Optional resource ID for resource-specific checks
            organization_id: Optional organization context
            
        Returns:
            True if user has permission
        """
        # Get user's roles
        user_role_ids = self.user_roles.get(user_id, set())
        
        if not user_role_ids:
            logger.debug(f"User {user_id} has no roles")
            return False
        
        # Check each role for permission
        for role_id in user_role_ids:
            role = self._get_role(role_id)
            
            if not role:
                continue
            
            # Check if role has permission
            if permission in role.permissions:
                # If resource-specific check
                if resource_id:
                    # Check resource ownership/access
                    if self._check_resource_access(user_id, resource_id, organization_id):
                        return True
                else:
                    # General permission granted
                    return True
        
        logger.debug(f"User {user_id} does not have permission: {permission}")
        return False
    
    def get_user_permissions(
        self,
        user_id: str,
        organization_id: Optional[str] = None
    ) -> List[str]:
        """
        Get all permissions for user.
        
        Args:
            user_id: User ID
            organization_id: Optional organization filter
            
        Returns:
            List of permission strings
        """
        user_role_ids = self.user_roles.get(user_id, set())
        
        all_permissions = set()
        
        for role_id in user_role_ids:
            role = self._get_role(role_id)
            
            if not role:
                continue
            
            # Filter by organization if specified
            if organization_id and role.organization_id not in [organization_id, "system"]:
                continue
            
            # Add role permissions
            all_permissions.update(role.permissions)
        
        return sorted(list(all_permissions))
    
    def get_user_roles(
        self,
        user_id: str,
        organization_id: Optional[str] = None
    ) -> List[Dict]:
        """Get all roles assigned to user."""
        user_role_ids = self.user_roles.get(user_id, set())
        
        roles = []
        
        for role_id in user_role_ids:
            role = self._get_role(role_id)
            
            if not role:
                continue
            
            # Filter by organization if specified
            if organization_id and role.organization_id not in [organization_id, "system"]:
                continue
            
            roles.append(role.to_dict())
        
        return roles
    
    def list_available_roles(
        self,
        organization_id: str
    ) -> List[Dict]:
        """List all roles available for organization."""
        available_roles = []
        
        # Add system roles
        for role in self.system_roles.values():
            available_roles.append(role.to_dict())
        
        # Add organization custom roles
        for role in self.custom_roles.values():
            if role.organization_id == organization_id:
                available_roles.append(role.to_dict())
        
        return available_roles
    
    def _get_role(self, role_id: str) -> Optional[Role]:
        """Get role by ID."""
        # Check system roles
        if role_id in self.system_roles:
            return self.system_roles[role_id]
        
        # Check custom roles
        if role_id in self.custom_roles:
            return self.custom_roles[role_id]
        
        return None
    
    def _check_resource_access(
        self,
        user_id: str,
        resource_id: str,
        organization_id: Optional[str]
    ) -> bool:
        """Check if user has access to specific resource."""
        # Resource-level access control
        # Check if user is owner or has access via organization
        
        # Placeholder: In production, query database
        return True
    
    def _save_role(self, role: Role):
        """Save role to database."""
        pass
    
    def _save_user_role(self, user_id: str, role_id: str, organization_id: str):
        """Save user-role assignment to database."""
        pass
    
    def _delete_user_role(self, user_id: str, role_id: str):
        """Delete user-role assignment from database."""
        pass


# Permission decorator for FastAPI
"""
from functools import wraps
from fastapi import HTTPException, Depends

def require_permission(permission: str):
    '''Decorator to require specific permission.'''
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get current user from dependency
            current_user = kwargs.get('current_user')
            
            if not current_user:
                raise HTTPException(status_code=401, detail="Not authenticated")
            
            # Check permission
            rbac = RBACService()
            
            if not rbac.check_permission(current_user.id, permission):
                raise HTTPException(
                    status_code=403,
                    detail=f"Missing required permission: {permission}"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


# Usage example
@router.delete("/videos/{video_id}")
@require_permission(Permission.VIDEO_DELETE.value)
async def delete_video(
    video_id: str,
    current_user: User = Depends(get_current_user)
):
    '''Delete video (requires video.delete permission).'''
    return video_service.delete(video_id)
"""
