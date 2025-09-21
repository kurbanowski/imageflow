"""
Utility functions for routers
"""
from typing import Dict, Any, Optional
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from middleware.auth import auth_middleware

security = HTTPBearer(auto_error=False)

# Create dependency functions that can be reused across routers
async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[Dict[str, Any]]:
    """Get current user if authenticated, None otherwise"""
    return await auth_middleware.get_current_user(credentials)

async def require_authentication(
    user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
) -> Dict[str, Any]:
    """Require user to be authenticated"""
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user