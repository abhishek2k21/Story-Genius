"""
Permission Definitions and Checks
Granular permission system.
"""
from typing import List, Dict, Set
from enum import Enum


class Permission(str, Enum):
    # Project permissions
    PROJECTS_READ = "projects:read"
    PROJECTS_WRITE = "projects:write"
    PROJECTS_DELETE = "projects:delete"
    
    # Job permissions
    JOBS_READ = "jobs:read"
    JOBS_WRITE = "jobs:write"
    
    # Batch permissions
    BATCHES_READ = "batches:read"
    BATCHES_WRITE = "batches:write"
    
    # Template permissions
    TEMPLATES_READ = "templates:read"
    TEMPLATES_WRITE = "templates:write"
    
    # Asset permissions
    ASSETS_READ = "assets:read"
    ASSETS_WRITE = "assets:write"
    
    # Admin permissions
    ADMIN_USERS = "admin:users"
    ADMIN_SYSTEM = "admin:system"


# Permission groups
PERMISSION_GROUPS: Dict[str, Set[str]] = {
    "readonly": {
        Permission.PROJECTS_READ.value,
        Permission.JOBS_READ.value,
        Permission.BATCHES_READ.value,
        Permission.TEMPLATES_READ.value,
        Permission.ASSETS_READ.value
    },
    "standard": {
        Permission.PROJECTS_READ.value,
        Permission.PROJECTS_WRITE.value,
        Permission.JOBS_READ.value,
        Permission.JOBS_WRITE.value,
        Permission.BATCHES_READ.value,
        Permission.BATCHES_WRITE.value,
        Permission.TEMPLATES_READ.value,
        Permission.TEMPLATES_WRITE.value,
        Permission.ASSETS_READ.value,
        Permission.ASSETS_WRITE.value
    },
    "full": {
        Permission.PROJECTS_READ.value,
        Permission.PROJECTS_WRITE.value,
        Permission.PROJECTS_DELETE.value,
        Permission.JOBS_READ.value,
        Permission.JOBS_WRITE.value,
        Permission.BATCHES_READ.value,
        Permission.BATCHES_WRITE.value,
        Permission.TEMPLATES_READ.value,
        Permission.TEMPLATES_WRITE.value,
        Permission.ASSETS_READ.value,
        Permission.ASSETS_WRITE.value
    },
    "admin": set(p.value for p in Permission)
}


# Role default permissions
ROLE_PERMISSIONS: Dict[str, Set[str]] = {
    "creator": PERMISSION_GROUPS["standard"],
    "admin": PERMISSION_GROUPS["admin"]
}


# Endpoint to permission mapping
ENDPOINT_PERMISSIONS: Dict[str, str] = {
    # Projects
    "GET:/v1/projects": Permission.PROJECTS_READ.value,
    "POST:/v1/projects": Permission.PROJECTS_WRITE.value,
    "DELETE:/v1/projects": Permission.PROJECTS_DELETE.value,
    
    # Jobs
    "GET:/v1/jobs": Permission.JOBS_READ.value,
    "POST:/v1/jobs": Permission.JOBS_WRITE.value,
    
    # Batches
    "GET:/v1/batches": Permission.BATCHES_READ.value,
    "POST:/v1/batches": Permission.BATCHES_WRITE.value,
    
    # Templates
    "GET:/v1/templates": Permission.TEMPLATES_READ.value,
    "POST:/v1/templates": Permission.TEMPLATES_WRITE.value,
    
    # Admin
    "GET:/v1/admin": Permission.ADMIN_USERS.value,
    "POST:/v1/admin": Permission.ADMIN_USERS.value
}


def get_role_permissions(role: str) -> Set[str]:
    """Get permissions for role"""
    return ROLE_PERMISSIONS.get(role, PERMISSION_GROUPS["readonly"])


def get_group_permissions(group: str) -> Set[str]:
    """Get permissions for group"""
    return PERMISSION_GROUPS.get(group, set())


def check_permission(
    user_permissions: Set[str],
    required: str
) -> bool:
    """Check if user has required permission"""
    # Admin has all
    if Permission.ADMIN_SYSTEM.value in user_permissions:
        return True
    
    return required in user_permissions


def get_endpoint_permission(method: str, path: str) -> str:
    """Get required permission for endpoint"""
    # Normalize path
    base_path = '/'.join(path.split('/')[:3])
    key = f"{method}:{base_path}"
    
    return ENDPOINT_PERMISSIONS.get(key, "")


def expand_permissions(permissions: List[str]) -> Set[str]:
    """Expand permission groups to individual permissions"""
    result = set()
    
    for p in permissions:
        if p in PERMISSION_GROUPS:
            result.update(PERMISSION_GROUPS[p])
        else:
            result.add(p)
    
    return result
