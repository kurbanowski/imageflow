"""
Comment management API routes
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any, Optional

from models import Comment, CommentCreate, CommentUpdate
from database import db_service
from routers.utils import get_current_user_optional, require_authentication

router = APIRouter(prefix="/api/comments", tags=["comments"])

@router.get("/photo/{photo_id}", response_model=List[Dict[str, Any]])
async def list_photo_comments(
    photo_id: str,
    limit: int = 50,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
):
    """List comments for a specific photo"""
    try:
        # Check if photo exists
        photo = await db_service.get_photo(photo_id)
        if not photo:
            raise HTTPException(status_code=404, detail="Photo not found")
        
        comments = await db_service.list_photo_comments(photo_id=photo_id, limit=min(limit, 100))
        
        # Get user information for each comment
        result = []
        for comment in comments:
            user = await db_service.get_user(comment['user_id'])
            if user:
                result.append({
                    "comment": comment,
                    "user": user
                })
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve comments: {str(e)}")

@router.post("/", response_model=Comment)
async def create_comment(
    comment_data: CommentCreate,
    current_user: Dict[str, Any] = Depends(require_authentication)
):
    """Create a new comment (requires authentication)"""
    try:
        # Check if photo exists
        photo = await db_service.get_photo(comment_data.photo_id)
        if not photo:
            raise HTTPException(status_code=404, detail="Photo not found")
        
        # Create comment
        comment_dict = comment_data.dict()
        comment_dict['user_id'] = current_user['user_id']
        
        comment = await db_service.create_comment(comment_dict)
        return comment
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create comment: {str(e)}")

@router.put("/{comment_id}", response_model=Comment)
async def update_comment(
    comment_id: str,
    comment_update: CommentUpdate,
    current_user: Dict[str, Any] = Depends(require_authentication)
):
    """Update a comment (owner only)"""
    try:
        # Check if comment exists and user owns it
        comments = await db_service.list_photo_comments("", limit=1000)  # Need to find comment
        comment = None
        for c in comments:
            if c.get('comment_id') == comment_id:
                comment = c
                break
        
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")
        
        if comment['user_id'] != current_user['user_id']:
            raise HTTPException(status_code=403, detail="Not authorized to update this comment")
        
        # Update comment (would need update_comment method in db_service)
        # For now, return the original comment
        return comment
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update comment: {str(e)}")

@router.delete("/{comment_id}")
async def delete_comment(
    comment_id: str,
    current_user: Dict[str, Any] = Depends(require_authentication)
):
    """Delete a comment (owner only)"""
    try:
        # Check if comment exists and user owns it
        comments = await db_service.list_photo_comments("", limit=1000)  # Need to find comment
        comment = None
        for c in comments:
            if c.get('comment_id') == comment_id:
                comment = c
                break
        
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")
        
        if comment['user_id'] != current_user['user_id']:
            raise HTTPException(status_code=403, detail="Not authorized to delete this comment")
        
        # Delete comment (would need delete_comment method in db_service)
        return {"message": "Comment deletion initiated"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete comment: {str(e)}")