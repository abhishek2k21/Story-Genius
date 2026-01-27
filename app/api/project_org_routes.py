"""
Project Organization API Routes
Folders, tags, search, archive, favorites, and bulk operations.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List

from app.projects.folders import project_folder_service
from app.projects.tags import project_tag_service
from app.projects.search import project_search_service, SearchCriteria
from app.projects.archive import project_archive_service
from app.projects.bulk import project_bulk_service
from app.api.auth_routes import get_current_user
from app.auth.models import AuthContext

router = APIRouter(prefix="/v1/projects", tags=["project-organization"])


# ==================== Request Models ====================

class CreateFolderRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    parent_folder_id: Optional[str] = None
    description: str = ""
    color: str = "#6366f1"
    icon: str = "folder"


class UpdateFolderRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None


class CreateTagRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=30)
    color: str = "#6366f1"
    description: str = ""


class TagsRequest(BaseModel):
    tag_ids: List[str]


class SearchRequest(BaseModel):
    query: Optional[str] = None
    folder_id: Optional[str] = None
    tags: Optional[List[str]] = None
    tag_match: str = "any"
    status: Optional[str] = None
    is_favorite: Optional[bool] = None
    is_archived: Optional[bool] = None
    platform: Optional[str] = None
    sort: str = "created_desc"
    page: int = 1
    page_size: int = 20


class BulkMoveRequest(BaseModel):
    project_ids: List[str]
    folder_id: str


class BulkTagRequest(BaseModel):
    project_ids: List[str]
    tag_ids: List[str]


class BulkIdsRequest(BaseModel):
    project_ids: List[str]


class SaveSearchRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    criteria: dict
    is_default: bool = False


# ==================== Folder Endpoints ====================

@router.get("/folders")
async def list_folders(
    parent_id: Optional[str] = None,
    auth: AuthContext = Depends(get_current_user)
):
    """List project folders"""
    folders = project_folder_service.list_folders(auth.user.user_id, parent_id)
    return {
        "count": len(folders),
        "folders": [f.to_dict() for f in folders]
    }


@router.get("/folders/all")
async def get_all_folders(auth: AuthContext = Depends(get_current_user)):
    """Get all folders for user"""
    folders = project_folder_service.get_all_folders(auth.user.user_id)
    return {
        "count": len(folders),
        "folders": [f.to_dict() for f in folders]
    }


@router.post("/folders")
async def create_folder(
    request: CreateFolderRequest,
    auth: AuthContext = Depends(get_current_user)
):
    """Create project folder"""
    folder, msg = project_folder_service.create_folder(
        user_id=auth.user.user_id,
        name=request.name,
        parent_folder_id=request.parent_folder_id,
        description=request.description,
        color=request.color,
        icon=request.icon
    )
    
    if not folder:
        raise HTTPException(status_code=400, detail=msg)
    
    return {"message": msg, "folder": folder.to_dict()}


@router.get("/folders/{folder_id}")
async def get_folder(folder_id: str, auth: AuthContext = Depends(get_current_user)):
    """Get folder details"""
    folder = project_folder_service.get_folder(folder_id, auth.user.user_id)
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    return folder.to_dict()


@router.put("/folders/{folder_id}")
async def update_folder(
    folder_id: str,
    request: UpdateFolderRequest,
    auth: AuthContext = Depends(get_current_user)
):
    """Update folder"""
    folder, msg = project_folder_service.update_folder(
        folder_id=folder_id,
        user_id=auth.user.user_id,
        name=request.name,
        description=request.description,
        color=request.color,
        icon=request.icon
    )
    
    if not folder:
        raise HTTPException(status_code=404, detail=msg)
    
    return {"message": msg, "folder": folder.to_dict()}


@router.delete("/folders/{folder_id}")
async def delete_folder(
    folder_id: str,
    force: bool = False,
    auth: AuthContext = Depends(get_current_user)
):
    """Delete folder"""
    success, msg = project_folder_service.delete_folder(folder_id, auth.user.user_id, force)
    
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    
    return {"message": msg}


# ==================== Tag Endpoints ====================

@router.get("/tags")
async def list_tags(auth: AuthContext = Depends(get_current_user)):
    """List project tags"""
    tags = project_tag_service.list_tags(auth.user.user_id)
    return {
        "count": len(tags),
        "tags": [t.to_dict() for t in tags]
    }


@router.post("/tags")
async def create_tag(
    request: CreateTagRequest,
    auth: AuthContext = Depends(get_current_user)
):
    """Create project tag"""
    tag, msg = project_tag_service.create_tag(
        user_id=auth.user.user_id,
        name=request.name,
        color=request.color,
        description=request.description
    )
    
    if not tag:
        raise HTTPException(status_code=400, detail=msg)
    
    return {"message": msg, "tag": tag.to_dict()}


@router.put("/tags/{tag_id}")
async def update_tag(
    tag_id: str,
    request: CreateTagRequest,
    auth: AuthContext = Depends(get_current_user)
):
    """Update tag"""
    tag, msg = project_tag_service.update_tag(
        tag_id=tag_id,
        user_id=auth.user.user_id,
        name=request.name,
        color=request.color,
        description=request.description
    )
    
    if not tag:
        raise HTTPException(status_code=404, detail=msg)
    
    return {"message": msg, "tag": tag.to_dict()}


@router.delete("/tags/{tag_id}")
async def delete_tag(tag_id: str, auth: AuthContext = Depends(get_current_user)):
    """Delete tag"""
    success, msg = project_tag_service.delete_tag(tag_id, auth.user.user_id)
    
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    
    return {"message": msg}


@router.post("/tags/{source_id}/merge/{target_id}")
async def merge_tags(
    source_id: str,
    target_id: str,
    auth: AuthContext = Depends(get_current_user)
):
    """Merge source tag into target"""
    success, msg = project_tag_service.merge_tags(source_id, target_id, auth.user.user_id)
    
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    
    return {"message": msg}


# ==================== Search Endpoints ====================

@router.post("/search")
async def search_projects(
    request: SearchRequest,
    auth: AuthContext = Depends(get_current_user)
):
    """Search projects"""
    criteria = SearchCriteria(
        query=request.query or "",
        folder_id=request.folder_id,
        tags=request.tags or [],
        tag_match=request.tag_match,
        status=request.status,
        is_favorite=request.is_favorite,
        is_archived=request.is_archived,
        platform=request.platform,
        sort=request.sort,
        page=request.page,
        page_size=request.page_size
    )
    
    # For demo, return empty results
    result = project_search_service.search([], criteria, project_tag_service)
    return result.to_dict()


@router.get("/recent")
async def get_recent_projects(
    limit: int = 10,
    auth: AuthContext = Depends(get_current_user)
):
    """Get recent projects"""
    recent_ids = project_archive_service.get_recent(auth.user.user_id, limit)
    return {"count": len(recent_ids), "project_ids": recent_ids}


@router.get("/favorites")
async def get_favorite_projects(auth: AuthContext = Depends(get_current_user)):
    """Get favorite projects"""
    favorites = project_archive_service.get_favorites()
    return {"count": len(favorites), "project_ids": list(favorites)}


# ==================== Archive/Favorite Endpoints ====================

@router.post("/{project_id}/favorite")
async def mark_favorite(project_id: str, auth: AuthContext = Depends(get_current_user)):
    """Mark project as favorite"""
    project_archive_service.add_favorite(project_id)
    return {"message": "Marked as favorite", "project_id": project_id}


@router.post("/{project_id}/unfavorite")
async def unmark_favorite(project_id: str, auth: AuthContext = Depends(get_current_user)):
    """Remove from favorites"""
    project_archive_service.remove_favorite(project_id)
    return {"message": "Removed from favorites", "project_id": project_id}


@router.post("/{project_id}/archive")
async def archive_project(project_id: str, auth: AuthContext = Depends(get_current_user)):
    """Archive project"""
    project_archive_service.archive_project(project_id)
    return {"message": "Project archived", "project_id": project_id}


@router.post("/{project_id}/unarchive")
async def unarchive_project(project_id: str, auth: AuthContext = Depends(get_current_user)):
    """Unarchive project"""
    project_archive_service.unarchive_project(project_id)
    return {"message": "Project unarchived", "project_id": project_id}


@router.post("/{project_id}/tags")
async def add_tags_to_project(
    project_id: str,
    request: TagsRequest,
    auth: AuthContext = Depends(get_current_user)
):
    """Add tags to project"""
    success, msg = project_tag_service.add_tags_to_project(project_id, request.tag_ids)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"message": "Tags added"}


@router.delete("/{project_id}/tags")
async def remove_tags_from_project(
    project_id: str,
    request: TagsRequest,
    auth: AuthContext = Depends(get_current_user)
):
    """Remove tags from project"""
    project_tag_service.remove_tags_from_project(project_id, request.tag_ids)
    return {"message": "Tags removed"}


# ==================== Bulk Operations ====================

@router.post("/bulk/move")
async def bulk_move(
    request: BulkMoveRequest,
    auth: AuthContext = Depends(get_current_user)
):
    """Move multiple projects to folder"""
    result = project_bulk_service.bulk_move(
        request.project_ids,
        request.folder_id,
        lambda pid, fid: True  # Placeholder
    )
    return result.to_dict()


@router.post("/bulk/tag")
async def bulk_tag(
    request: BulkTagRequest,
    auth: AuthContext = Depends(get_current_user)
):
    """Add tags to multiple projects"""
    result = project_bulk_service.bulk_tag(
        request.project_ids,
        request.tag_ids,
        project_tag_service.add_tags_to_project
    )
    return result.to_dict()


@router.post("/bulk/archive")
async def bulk_archive(
    request: BulkIdsRequest,
    auth: AuthContext = Depends(get_current_user)
):
    """Archive multiple projects"""
    result = project_bulk_service.bulk_archive(
        request.project_ids,
        project_archive_service.archive_project
    )
    return result.to_dict()


@router.post("/bulk/delete")
async def bulk_delete(
    request: BulkIdsRequest,
    auth: AuthContext = Depends(get_current_user)
):
    """Delete multiple projects"""
    result = project_bulk_service.bulk_delete(
        request.project_ids,
        lambda pid: True  # Placeholder
    )
    return result.to_dict()


# ==================== Saved Searches ====================

@router.get("/searches")
async def list_saved_searches(auth: AuthContext = Depends(get_current_user)):
    """List saved searches"""
    searches = project_search_service.list_saved_searches(auth.user.user_id)
    return {
        "count": len(searches),
        "searches": [s.to_dict() for s in searches]
    }


@router.post("/searches")
async def save_search(
    request: SaveSearchRequest,
    auth: AuthContext = Depends(get_current_user)
):
    """Save a search"""
    search = project_search_service.save_search(
        user_id=auth.user.user_id,
        name=request.name,
        criteria=request.criteria,
        is_default=request.is_default
    )
    return {"message": "Search saved", "search": search.to_dict()}


@router.delete("/searches/{search_id}")
async def delete_saved_search(
    search_id: str,
    auth: AuthContext = Depends(get_current_user)
):
    """Delete saved search"""
    if project_search_service.delete_saved_search(search_id, auth.user.user_id):
        return {"message": "Search deleted"}
    raise HTTPException(status_code=404, detail="Search not found")
