import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path
import mimetypes

def generate_uuid() -> str:
    """Generate a new UUID string"""
    return str(uuid.uuid4())

def generate_link_id() -> str:
    """Generate a secure link ID"""
    return str(uuid.uuid4()).replace('-', '')

def get_file_extension(filename: str) -> str:
    """Get file extension from filename"""
    return Path(filename).suffix.lower()

def get_content_type(filename: str) -> str:
    """Get MIME type from filename"""
    content_type, _ = mimetypes.guess_type(filename)
    return content_type or 'application/octet-stream'

def is_image_file(filename: str) -> bool:
    """Check if file is an image based on extension"""
    from config import ALLOWED_IMAGE_EXTENSIONS
    return get_file_extension(filename) in ALLOWED_IMAGE_EXTENSIONS

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size = float(size_bytes)
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"

def calculate_expiration_date(days: int = 30) -> datetime:
    """Calculate expiration date from now"""
    return datetime.now() + timedelta(days=days)

def is_expired(expiration_date: datetime) -> bool:
    """Check if a date has passed"""
    return datetime.now() > expiration_date

def serialize_datetime(dt: datetime) -> str:
    """Serialize datetime to ISO format"""
    return dt.isoformat()

def deserialize_datetime(dt_str: str) -> datetime:
    """Deserialize datetime from ISO format"""
    return datetime.fromisoformat(dt_str)

def create_response_metadata(
    total_count: Optional[int] = None,
    page_size: Optional[int] = None,
    has_more: Optional[bool] = None
) -> Dict[str, Any]:
    """Create standard response metadata"""
    metadata: Dict[str, Any] = {
        'timestamp': datetime.now().isoformat()
    }
    
    if total_count is not None:
        metadata['total_count'] = total_count
    if page_size is not None:
        metadata['page_size'] = page_size
    if has_more is not None:
        metadata['has_more'] = has_more
    
    return metadata

def hash_string(input_string: str) -> str:
    """Create SHA256 hash of a string"""
    return hashlib.sha256(input_string.encode()).hexdigest()

def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate string to max length with suffix"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix