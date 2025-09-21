from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import uuid

class EntityType(str, Enum):
    USER = "USER"
    PHOTO = "PHOTO"
    COMMENT = "COMMENT"
    SHARE_LINK = "SHARE_LINK"

# User Models
class UserBase(BaseModel):
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    profile_image_url: Optional[str] = None

class UserCreate(UserBase):
    id: Optional[str] = None

class UserUpdate(UserBase):
    pass

class User(UserBase):
    user_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Photo Models
class PhotoBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    
    @validator('title')
    def title_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip()

class PhotoCreate(PhotoBase):
    user_id: str
    file_path: str
    file_size: Optional[int] = 0
    content_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}

class PhotoUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    metadata: Optional[Dict[str, Any]] = None

class Photo(PhotoBase):
    photo_id: str
    user_id: str
    file_path: str
    file_size: int
    content_type: str
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Comment Models
class CommentBase(BaseModel):
    content: str = Field(..., min_length=1, max_length=500)
    
    @validator('content')
    def content_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Comment cannot be empty')
        return v.strip()

class CommentCreate(CommentBase):
    photo_id: str
    user_id: str

class CommentUpdate(BaseModel):
    content: Optional[str] = Field(None, min_length=1, max_length=500)

class Comment(CommentBase):
    comment_id: str
    photo_id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Shareable Link Models
class ShareableLinkBase(BaseModel):
    expiration_days: Optional[int] = Field(30, ge=1, le=365)

class ShareableLinkCreate(ShareableLinkBase):
    photo_id: str
    user_id: str

class ShareableLink(ShareableLinkBase):
    link_id: str
    photo_id: str
    user_id: str
    expires_at: datetime
    access_count: int
    created_at: datetime
    updated_at: datetime
    
    @property
    def is_expired(self) -> bool:
        return datetime.now() > self.expires_at
    
    @property
    def share_url(self) -> str:
        return f"/share/{self.link_id}"
    
    class Config:
        from_attributes = True

# Response Models
class PhotoWithUser(BaseModel):
    photo: Photo
    user: User

class PhotoWithComments(BaseModel):
    photo: Photo
    user: User
    comments: List[Comment]
    comment_users: Dict[str, User]  # Map comment user_ids to User objects

class ShareableLinkResponse(BaseModel):
    link: ShareableLink
    photo: Photo
    user: User

# Utility Models
class PaginationParams(BaseModel):
    limit: int = Field(20, ge=1, le=100)
    last_evaluated_key: Optional[str] = None

class UploadResponse(BaseModel):
    photo_id: str
    upload_url: str
    message: str

class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None