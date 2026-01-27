"""
Asset Library API Routes
Upload, organize, and manage assets.
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from pydantic import BaseModel, Field
from typing import Optional, List

from app.assets.service import asset_service
from app.assets.folders import folder_service
from app.assets.tags import tag_service
from app.assets.versions import version_service
from app.api.auth_routes import get_current_user
from app.auth.models import AuthContext

router = APIRouter(prefix="/v1/assets", tags=["assets"])


# ==================== Request Models ====================

class UpdateAssetRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    folder_id: Optional[str] = None


class CreateFolderRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    parent_folder_id: Optional[str] = None
    description: str = ""
    color: str = "#6366f1"


class CreateTagRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    color: str = "#6366f1"


class AddTagsRequest(BaseModel):
    tag_ids: List[str]


class SearchRequest(BaseModel):
    query: Optional[str] = None
    asset_type: Optional[str] = None
    tags: Optional[List[str]] = None
    folder_id: Optional[str] = None


# ==================== Asset Endpoints ====================

@router.post("/upload")
async def upload_asset(
    file: UploadFile = File(...),
    name: Optional[str] = None,
    description: str = "",
    folder_id: Optional[str] = None,
    auth: AuthContext = Depends(get_current_user)
):
    """Upload new asset"""
    data = await file.read()
    
    asset, msg = asset_service.upload_asset(
        user_id=auth.user.user_id,
        filename=file.filename,
        data=data,
        name=name,
        description=description,
        folder_id=folder_id
    )
    
    if not asset:
        raise HTTPException(status_code=400, detail=msg)
    
    return {"message": msg, "asset": asset.to_dict()}


@router.get("")
async def list_assets(
    asset_type: Optional[str] = None,
    folder_id: Optional[str] = None,
    auth: AuthContext = Depends(get_current_user)
):
    """List user's assets"""
    assets = asset_service.list_assets(
        user_id=auth.user.user_id,
        asset_type=asset_type,
        folder_id=folder_id
    )
    return {
        "count": len(assets),
        "assets": [a.to_dict() for a in assets]
    }


@router.get("/stats")
async def get_asset_stats(auth: AuthContext = Depends(get_current_user)):
    """Get asset statistics"""
    return asset_service.get_stats(auth.user.user_id)


@router.post("/search")
async def search_assets(
    request: SearchRequest,
    auth: AuthContext = Depends(get_current_user)
):
    """Search assets"""
    assets = asset_service.search_assets(
        user_id=auth.user.user_id,
        query=request.query,
        asset_type=request.asset_type,
        tags=request.tags,
        folder_id=request.folder_id
    )
    return {
        "count": len(assets),
        "assets": [a.to_dict() for a in assets]
    }


@router.get("/{asset_id}")
async def get_asset(asset_id: str, auth: AuthContext = Depends(get_current_user)):
    """Get asset details"""
    asset = asset_service.get_asset(asset_id, auth.user.user_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    tags = tag_service.get_asset_tags(asset_id)
    versions_count = version_service.get_version_count(asset_id)
    refs = asset_service.get_references(asset_id)
    
    result = asset.to_dict()
    result["tags"] = [t.to_dict() for t in tags]
    result["versions_count"] = versions_count
    result["references_count"] = len(refs)
    
    return result


@router.put("/{asset_id}")
async def update_asset(
    asset_id: str,
    request: UpdateAssetRequest,
    auth: AuthContext = Depends(get_current_user)
):
    """Update asset metadata"""
    asset, msg = asset_service.update_asset(
        asset_id=asset_id,
        user_id=auth.user.user_id,
        name=request.name,
        description=request.description,
        folder_id=request.folder_id
    )
    
    if not asset:
        raise HTTPException(status_code=404, detail=msg)
    
    return {"message": msg, "asset": asset.to_dict()}


@router.delete("/{asset_id}")
async def delete_asset(
    asset_id: str,
    force: bool = False,
    auth: AuthContext = Depends(get_current_user)
):
    """Delete asset"""
    success, msg = asset_service.delete_asset(asset_id, auth.user.user_id, force)
    
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    
    return {"message": msg}


# ==================== Version Endpoints ====================

@router.get("/{asset_id}/versions")
async def list_versions(asset_id: str, auth: AuthContext = Depends(get_current_user)):
    """List asset versions"""
    asset = asset_service.get_asset(asset_id, auth.user.user_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    versions = version_service.get_versions(asset_id)
    return {
        "count": len(versions),
        "versions": [v.to_dict() for v in versions]
    }


@router.get("/{asset_id}/references")
async def list_references(asset_id: str, auth: AuthContext = Depends(get_current_user)):
    """List asset references"""
    asset = asset_service.get_asset(asset_id, auth.user.user_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    refs = asset_service.get_references(asset_id)
    return {
        "count": len(refs),
        "references": [r.to_dict() for r in refs]
    }


# ==================== Folder Endpoints ====================

@router.get("/folders/list")
async def list_folders(
    parent_id: Optional[str] = None,
    auth: AuthContext = Depends(get_current_user)
):
    """List folders"""
    folders = folder_service.list_folders(auth.user.user_id, parent_id)
    return {
        "count": len(folders),
        "folders": [f.to_dict() for f in folders]
    }


@router.post("/folders")
async def create_folder(
    request: CreateFolderRequest,
    auth: AuthContext = Depends(get_current_user)
):
    """Create folder"""
    folder, msg = folder_service.create_folder(
        user_id=auth.user.user_id,
        name=request.name,
        parent_folder_id=request.parent_folder_id,
        description=request.description,
        color=request.color
    )
    
    if not folder:
        raise HTTPException(status_code=400, detail=msg)
    
    return {"message": msg, "folder": folder.to_dict()}


@router.delete("/folders/{folder_id}")
async def delete_folder(
    folder_id: str,
    force: bool = False,
    auth: AuthContext = Depends(get_current_user)
):
    """Delete folder"""
    success, msg = folder_service.delete_folder(folder_id, auth.user.user_id, force)
    
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    
    return {"message": msg}


# ==================== Tag Endpoints ====================

@router.get("/tags/list")
async def list_tags(auth: AuthContext = Depends(get_current_user)):
    """List tags"""
    tags = tag_service.list_tags(auth.user.user_id)
    return {
        "count": len(tags),
        "tags": [t.to_dict() for t in tags]
    }


@router.post("/tags")
async def create_tag(
    request: CreateTagRequest,
    auth: AuthContext = Depends(get_current_user)
):
    """Create tag"""
    tag, msg = tag_service.create_tag(
        user_id=auth.user.user_id,
        name=request.name,
        color=request.color
    )
    
    if not tag:
        raise HTTPException(status_code=400, detail=msg)
    
    return {"message": msg, "tag": tag.to_dict()}


@router.delete("/tags/{tag_id}")
async def delete_tag(tag_id: str, auth: AuthContext = Depends(get_current_user)):
    """Delete tag"""
    success, msg = tag_service.delete_tag(tag_id, auth.user.user_id)
    
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    
    return {"message": msg}


@router.post("/{asset_id}/tags")
async def add_tags_to_asset(
    asset_id: str,
    request: AddTagsRequest,
    auth: AuthContext = Depends(get_current_user)
):
    """Add tags to asset"""
    asset = asset_service.get_asset(asset_id, auth.user.user_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    tag_service.add_tags_to_asset(asset_id, request.tag_ids)
    return {"message": "Tags added"}


@router.delete("/{asset_id}/tags")
async def remove_tags_from_asset(
    asset_id: str,
    request: AddTagsRequest,
    auth: AuthContext = Depends(get_current_user)
):
    """Remove tags from asset"""
    asset = asset_service.get_asset(asset_id, auth.user.user_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    tag_service.remove_tags_from_asset(asset_id, request.tag_ids)
    return {"message": "Tags removed"}
