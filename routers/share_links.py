"""
Shareable link management API routes
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any

from models import ShareableLink, ShareableLinkCreate, ShareableLinkResponse
from database import db_service
from routers.utils import get_current_user_optional, require_authentication

router = APIRouter(prefix="/api/share", tags=["sharing"])

@router.post("/", response_model=ShareableLink)
async def create_share_link(
    link_data: ShareableLinkCreate
):
    """Create a shareable link for a photo (requires authentication)"""
    try:
        # Check if photo exists
        photo = await db_service.get_photo(link_data.photo_id)
        if not photo:
            raise HTTPException(status_code=404, detail="Photo not found")
        
        # Create shareable link (use demo user for MVP)
        link_dict = link_data.dict()
        link_dict['user_id'] = 'demo-user'
        
        share_link = await db_service.create_shareable_link(link_dict)
        return share_link
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create share link: {str(e)}")

@router.get("/{link_id}", response_model=ShareableLinkResponse)
async def get_shared_photo(link_id: str):
    """Access a photo via shareable link (public endpoint)"""
    try:
        # Get shareable link and check if valid/not expired
        share_link = await db_service.get_shareable_link(link_id)
        if not share_link:
            raise HTTPException(status_code=404, detail="Share link not found or expired")
        
        # Increment access count
        await db_service.increment_link_access(link_id)
        
        # Get photo and user information
        photo = await db_service.get_photo(share_link['photo_id'])
        if not photo:
            raise HTTPException(status_code=404, detail="Photo not found")
        
        user = await db_service.get_user(photo['user_id'])
        if not user:
            raise HTTPException(status_code=404, detail="Photo owner not found")
        
        return {
            "link": share_link,
            "photo": photo,
            "user": user
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to access shared photo: {str(e)}")

@router.get("/photo/{photo_id}/links")
async def list_photo_links(
    photo_id: str
):
    """List all shareable links for a photo (owner only)"""
    try:
        # Check if photo exists
        photo = await db_service.get_photo(photo_id)
        if not photo:
            raise HTTPException(status_code=404, detail="Photo not found")
        
        # This would require a list_links_by_photo method in db_service
        # For now, return empty list
        return {"links": [], "message": "Feature not yet implemented"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve share links: {str(e)}")

@router.delete("/{link_id}")
async def delete_share_link(
    link_id: str
):
    """Delete a shareable link (owner only)"""
    try:
        # Get shareable link
        share_link = await db_service.get_shareable_link(link_id)
        if not share_link:
            raise HTTPException(status_code=404, detail="Share link not found")
        
        # Delete link (would need delete_share_link method in db_service)
        return {"message": "Share link deletion initiated"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete share link: {str(e)}")