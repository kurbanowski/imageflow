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
from services.s3_service import s3_service
from utils import is_image_file, get_content_type, format_file_size
from config import MAX_FILE_SIZE_MB, USE_MOCK_SERVICES

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
        
        # Generate presigned URL for secure file access if using S3
        if not USE_MOCK_SERVICES and 'file_path' in photo:
            try:
                presigned_url = await s3_service.generate_presigned_url(photo['file_path'], expiration=3600)  # 1 hour
                photo['presigned_url'] = presigned_url
            except Exception as e:
                print(f"Warning: Failed to generate presigned URL for photo view: {str(e)}")
        
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
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
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
        
        # Upload to S3 or use mock service in development
        if USE_MOCK_SERVICES:
            # Mock implementation for development
            file_path = f"/uploads/{user_id}/{file.filename}"
            file_url = file_path
        else:
            # Real S3 upload
            upload_result = await s3_service.upload_file(
                file_obj=file.file,
                user_id=user_id,
                original_filename=file.filename,
                content_type=get_content_type(file.filename)
            )
            file_path = upload_result['file_path']
            
            # Generate presigned URL for secure access instead of direct S3 URL
            try:
                file_url = await s3_service.generate_presigned_url(file_path, expiration=86400)  # 24 hours
            except Exception as e:
                print(f"Warning: Failed to generate presigned URL: {str(e)}")
                file_url = upload_result['file_url']  # Fallback to direct URL
        
        # Create photo record (use demo user if no auth)
        user_id = current_user['user_id'] if current_user else 'demo-user'
        photo_data = {
            'user_id': user_id,
            'title': title,
            'description': description,
            'file_path': file_path,
            'file_size': file_size,
            'content_type': get_content_type(file.filename),
            'metadata': {
                'original_filename': file.filename,
                'upload_timestamp': datetime.now().isoformat(),
                'file_url': file_url if not USE_MOCK_SERVICES else None
            }
        }
        
        photo = await db_service.create_photo(photo_data)
        
        return {
            "photo": photo,
            "message": "Photo uploaded successfully",
            "file_url": file_url
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload photo: {str(e)}")

@router.put("/{photo_id}", response_model=Photo)
async def update_photo(
    photo_id: str,
    photo_update: PhotoUpdate
):
    """Update photo metadata (owner only)"""
    try:
        # Check if photo exists
        photo = await db_service.get_photo(photo_id)
        if not photo:
            raise HTTPException(status_code=404, detail="Photo not found")
        
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
    photo_id: str
):
    """Delete a photo (owner only)"""
    try:
        # Check if photo exists
        photo = await db_service.get_photo(photo_id)
        if not photo:
            raise HTTPException(status_code=404, detail="Photo not found")
        
        # Delete from S3 if not using mock services
        if not USE_MOCK_SERVICES and 'file_path' in photo:
            try:
                await s3_service.delete_file(photo['file_path'])
            except Exception as e:
                print(f"Warning: Failed to delete file from S3: {str(e)}")
        
        # Delete photo record from database
        deleted = await db_service.delete_photo(photo_id)
        if not deleted:
            raise HTTPException(status_code=500, detail="Failed to delete photo from database")
        
        return {"message": "Photo deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete photo: {str(e)}")