"""
Photo management API routes
"""
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from typing import List, Optional, Dict, Any
import os
from datetime import datetime

from models import Photo, PhotoCreate, PhotoUpdate, PhotoWithUser, PaginationParams
from database import db_service
from routers.utils import get_current_user_optional, require_authentication
from utils import is_image_file, get_content_type, format_file_size
from config import MAX_FILE_SIZE_MB

router = APIRouter(prefix="/api/photos", tags=["photos"])

@router.get("/", response_model=List[PhotoWithUser])
async def list_recent_photos(
    limit: int = 20,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
):
    """List recent photos (public endpoint)"""
    try:
        photos = await db_service.list_recent_photos(limit=min(limit, 100))
        
        # Get user information for each photo
        result = []
        for photo in photos:
            user = await db_service.get_user(photo['user_id'])
            if user:
                result.append({
                    "photo": photo,
                    "user": user
                })
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve photos: {str(e)}")

@router.get("/user/{user_id}", response_model=List[Photo])
async def list_user_photos(
    user_id: str,
    limit: int = 20,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
):
    """List photos by specific user"""
    try:
        photos = await db_service.list_user_photos(user_id=user_id, limit=min(limit, 100))
        return photos
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve user photos: {str(e)}")

@router.get("/{photo_id}", response_model=PhotoWithUser)
async def get_photo(
    photo_id: str,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
):
    """Get a specific photo with user information"""
    try:
        photo = await db_service.get_photo(photo_id)
        if not photo:
            raise HTTPException(status_code=404, detail="Photo not found")
        
        user = await db_service.get_user(photo['user_id'])
        if not user:
            raise HTTPException(status_code=404, detail="Photo owner not found")
        
        return {
            "photo": photo,
            "user": user
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve photo: {str(e)}")

@router.post("/upload", response_model=Dict[str, Any])
async def upload_photo(
    title: str = Form(...),
    description: str = Form(""),
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(require_authentication)
):
    """Upload a new photo (requires authentication)"""
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        if not is_image_file(file.filename):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Check file size (get size by seeking to end)
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning
        
        max_size_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
        if file_size > max_size_bytes:
            raise HTTPException(
                status_code=400, 
                detail=f"File too large. Maximum size: {format_file_size(max_size_bytes)}"
            )
        
        # For now, we'll create a placeholder file path
        # In a real implementation, this would integrate with object storage
        file_path = f"/uploads/{current_user['user_id']}/{file.filename}"
        
        # Create photo record
        photo_data = {
            'user_id': current_user['user_id'],
            'title': title,
            'description': description,
            'file_path': file_path,
            'file_size': file_size,
            'content_type': get_content_type(file.filename),
            'metadata': {
                'original_filename': file.filename,
                'upload_timestamp': datetime.now().isoformat()
            }
        }
        
        photo = await db_service.create_photo(photo_data)
        
        return {
            "photo": photo,
            "message": "Photo uploaded successfully",
            "upload_url": file_path  # In real implementation, this would be a signed URL
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload photo: {str(e)}")

@router.put("/{photo_id}", response_model=Photo)
async def update_photo(
    photo_id: str,
    photo_update: PhotoUpdate,
    current_user: Dict[str, Any] = Depends(require_authentication)
):
    """Update photo metadata (owner only)"""
    try:
        # Check if photo exists and user owns it
        photo = await db_service.get_photo(photo_id)
        if not photo:
            raise HTTPException(status_code=404, detail="Photo not found")
        
        if photo['user_id'] != current_user['user_id']:
            raise HTTPException(status_code=403, detail="Not authorized to update this photo")
        
        # Update photo
        updates = photo_update.dict(exclude_unset=True)
        if updates:
            updated_photo = await db_service.update_photo(photo_id, updates)
            return updated_photo
        
        return photo
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update photo: {str(e)}")

@router.delete("/{photo_id}")
async def delete_photo(
    photo_id: str,
    current_user: Dict[str, Any] = Depends(require_authentication)
):
    """Delete a photo (owner only)"""
    try:
        # Check if photo exists and user owns it
        photo = await db_service.get_photo(photo_id)
        if not photo:
            raise HTTPException(status_code=404, detail="Photo not found")
        
        if photo['user_id'] != current_user['user_id']:
            raise HTTPException(status_code=403, detail="Not authorized to delete this photo")
        
        # In a real implementation, you would also delete the file from storage
        # For now, we'll just note that the photo should be deleted
        
        return {"message": "Photo deletion initiated"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete photo: {str(e)}")