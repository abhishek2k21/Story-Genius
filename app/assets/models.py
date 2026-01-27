"""
Asset Models
Data structures for asset management.
"""
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid


class AssetType(str, Enum):
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    FONT = "font"
    LOGO = "logo"


class AssetStatus(str, Enum):
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"
    DELETED = "deleted"


# Asset type configurations
ASSET_CONFIG = {
    AssetType.IMAGE: {
        "extensions": ["jpg", "jpeg", "png", "webp", "gif"],
        "max_size": 10 * 1024 * 1024,  # 10MB
        "mime_types": ["image/jpeg", "image/png", "image/webp", "image/gif"]
    },
    AssetType.AUDIO: {
        "extensions": ["mp3", "wav", "m4a"],
        "max_size": 50 * 1024 * 1024,  # 50MB
        "mime_types": ["audio/mpeg", "audio/wav", "audio/x-m4a"]
    },
    AssetType.VIDEO: {
        "extensions": ["mp4", "mov", "webm"],
        "max_size": 200 * 1024 * 1024,  # 200MB
        "mime_types": ["video/mp4", "video/quicktime", "video/webm"]
    },
    AssetType.FONT: {
        "extensions": ["ttf", "otf", "woff"],
        "max_size": 5 * 1024 * 1024,  # 5MB
        "mime_types": ["font/ttf", "font/otf", "font/woff"]
    },
    AssetType.LOGO: {
        "extensions": ["png", "svg"],
        "max_size": 5 * 1024 * 1024,  # 5MB
        "mime_types": ["image/png", "image/svg+xml"]
    }
}


@dataclass
class Asset:
    """Asset model"""
    asset_id: str
    user_id: str
    name: str
    asset_type: AssetType
    mime_type: str
    file_extension: str
    file_size: int
    storage_path: str
    original_filename: str
    checksum: str
    status: AssetStatus = AssetStatus.PROCESSING
    description: str = ""
    folder_id: Optional[str] = None
    metadata: Dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        return {
            "asset_id": self.asset_id,
            "name": self.name,
            "asset_type": self.asset_type.value,
            "mime_type": self.mime_type,
            "file_extension": self.file_extension,
            "file_size": self.file_size,
            "status": self.status.value,
            "description": self.description,
            "folder_id": self.folder_id,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


@dataclass
class AssetVersion:
    """Asset version for history"""
    version_id: str
    asset_id: str
    version_number: int
    storage_path: str
    file_size: int
    checksum: str
    change_description: str = ""
    metadata: Dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "version_id": self.version_id,
            "version_number": self.version_number,
            "file_size": self.file_size,
            "change_description": self.change_description,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class Folder:
    """Folder for organization"""
    folder_id: str
    user_id: str
    name: str
    parent_folder_id: Optional[str] = None
    description: str = ""
    color: str = "#6366f1"
    asset_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        return {
            "folder_id": self.folder_id,
            "name": self.name,
            "parent_folder_id": self.parent_folder_id,
            "description": self.description,
            "color": self.color,
            "asset_count": self.asset_count,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class Tag:
    """Tag for categorization"""
    tag_id: str
    user_id: str
    name: str
    color: str = "#6366f1"
    usage_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        return {
            "tag_id": self.tag_id,
            "name": self.name,
            "color": self.color,
            "usage_count": self.usage_count
        }


@dataclass
class AssetReference:
    """Track where assets are used"""
    reference_id: str
    asset_id: str
    resource_type: str  # project, template, batch
    resource_id: str
    usage_type: str  # thumbnail, background, audio, etc.
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        return {
            "reference_id": self.reference_id,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "usage_type": self.usage_type,
            "created_at": self.created_at.isoformat()
        }


def create_asset_id() -> str:
    return str(uuid.uuid4())


def create_folder_id() -> str:
    return str(uuid.uuid4())


def create_tag_id() -> str:
    return str(uuid.uuid4())


def get_asset_type_from_extension(ext: str) -> Optional[AssetType]:
    """Determine asset type from file extension"""
    ext = ext.lower().lstrip('.')
    for asset_type, config in ASSET_CONFIG.items():
        if ext in config["extensions"]:
            return asset_type
    return None


def validate_asset_type(asset_type: AssetType, extension: str, size: int) -> tuple:
    """Validate file against asset type config"""
    config = ASSET_CONFIG.get(asset_type)
    if not config:
        return False, "Unknown asset type"
    
    if extension.lower() not in config["extensions"]:
        return False, f"Invalid extension for {asset_type.value}"
    
    if size > config["max_size"]:
        max_mb = config["max_size"] // (1024 * 1024)
        return False, f"File too large. Max {max_mb}MB for {asset_type.value}"
    
    return True, "Valid"
