"""
Asset Storage
File storage utilities for assets.
"""
import os
import hashlib
from typing import Optional
from datetime import datetime
from pathlib import Path


# Base storage path
STORAGE_BASE = "storage/assets"


def get_storage_path(
    user_id: str,
    asset_type: str,
    asset_id: str,
    extension: str
) -> str:
    """Generate storage path for asset"""
    now = datetime.utcnow()
    year = now.strftime("%Y")
    month = now.strftime("%m")
    
    path = f"{STORAGE_BASE}/{user_id}/{asset_type}/{year}/{month}/{asset_id}.{extension}"
    return path


def ensure_storage_dir(path: str) -> None:
    """Ensure storage directory exists"""
    dir_path = os.path.dirname(path)
    os.makedirs(dir_path, exist_ok=True)


def calculate_checksum(file_path: str) -> str:
    """Calculate SHA-256 checksum of file"""
    sha256 = hashlib.sha256()
    
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    
    return sha256.hexdigest()


def calculate_checksum_from_bytes(data: bytes) -> str:
    """Calculate SHA-256 checksum from bytes"""
    return hashlib.sha256(data).hexdigest()


def save_file(data: bytes, path: str) -> int:
    """Save file to storage, return file size"""
    ensure_storage_dir(path)
    
    with open(path, 'wb') as f:
        f.write(data)
    
    return len(data)


def read_file(path: str) -> Optional[bytes]:
    """Read file from storage"""
    if not os.path.exists(path):
        return None
    
    with open(path, 'rb') as f:
        return f.read()


def delete_file(path: str) -> bool:
    """Delete file from storage"""
    try:
        if os.path.exists(path):
            os.remove(path)
            return True
    except Exception:
        pass
    return False


def file_exists(path: str) -> bool:
    """Check if file exists"""
    return os.path.exists(path)


def get_file_size(path: str) -> int:
    """Get file size in bytes"""
    if os.path.exists(path):
        return os.path.getsize(path)
    return 0


def copy_file(src: str, dst: str) -> bool:
    """Copy file to new location"""
    try:
        ensure_storage_dir(dst)
        import shutil
        shutil.copy2(src, dst)
        return True
    except Exception:
        return False


def get_version_path(
    user_id: str,
    asset_id: str,
    version_number: int,
    extension: str
) -> str:
    """Generate storage path for asset version"""
    return f"{STORAGE_BASE}/{user_id}/versions/{asset_id}/v{version_number}.{extension}"


def get_thumbnail_path(
    user_id: str,
    asset_id: str,
    size: str = "150"
) -> str:
    """Generate storage path for thumbnail"""
    return f"{STORAGE_BASE}/{user_id}/thumbnails/{asset_id}_{size}.jpg"
