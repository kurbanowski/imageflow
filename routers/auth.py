"""
Authentication API routes
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, Optional

from models import User, UserCreate, UserUpdate
from database import db_service
from routers.utils import get_current_user_optional, require_authentication

router = APIRouter(prefix="/api/auth", tags=["authentication"])

@router.get("/me", response_model=User)
async def get_current_user_profile(
    current_user: Dict[str, Any] = Depends(require_authentication)
):
    """Get current user profile"""
    try:
        user = await db_service.get_user(current_user['user_id'])
        if not user:
            # Create user if doesn't exist (first login)
            user_data = {
                'id': current_user['user_id'],
                'email': current_user.get('email'),
                'first_name': current_user.get('first_name'),
                'last_name': current_user.get('last_name'),
                'profile_image_url': current_user.get('profile_image_url')
            }
            user = await db_service.create_user(user_data)
        
        return user
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve user profile: {str(e)}")

@router.put("/me", response_model=User)
async def update_user_profile(
    user_update: UserUpdate,
    current_user: Dict[str, Any] = Depends(require_authentication)
):
    """Update current user profile"""
    try:
        updates = user_update.dict(exclude_unset=True)
        if updates:
            updated_user = await db_service.update_user(current_user['user_id'], updates)
            return updated_user
        
        # If no updates, return current user
        user = await db_service.get_user(current_user['user_id'])
        return user
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update user profile: {str(e)}")

@router.get("/status")
async def auth_status(
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
):
    """Check authentication status"""
    if current_user:
        return {
            "authenticated": True,
            "user_id": current_user['user_id'],
            "email": current_user.get('email')
        }
    return {"authenticated": False}

@router.post("/login")
async def login():
    """Login endpoint - redirects to Replit Auth"""
    return {
        "message": "Please use Replit Auth login",
        "login_url": "/auth/replit_auth/login"
    }

@router.post("/logout")
async def logout():
    """Logout endpoint - redirects to Replit Auth logout"""
    return {
        "message": "Please use Replit Auth logout",
        "logout_url": "/auth/replit_auth/logout"
    }