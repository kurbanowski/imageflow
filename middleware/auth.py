"""
Authentication middleware for FastAPI with Replit Auth integration
"""
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
import jwt
import os
from datetime import datetime

security = HTTPBearer(auto_error=False)

class AuthMiddleware:
    """Authentication middleware using Replit Auth tokens"""
    
    def __init__(self):
        self.issuer_url = os.environ.get('ISSUER_URL', "https://replit.com/oidc")
        
    async def get_current_user(
        self, 
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
    ) -> Optional[Dict[str, Any]]:
        """Get current user from JWT token"""
        if not credentials:
            return None
            
        try:
            # Decode and verify JWT token
            token = credentials.credentials
            
            # For development, we'll use unverified tokens but validate structure
            # In production, implement proper JWKS verification with issuer
            try:
                payload = jwt.decode(token, options={"verify_signature": False})
                
                # Validate required claims
                required_claims = ['sub', 'iss', 'aud', 'exp']
                for claim in required_claims:
                    if claim not in payload:
                        raise HTTPException(status_code=401, detail=f"Missing required claim: {claim}")
                
                # Validate issuer
                if payload.get('iss') != self.issuer_url:
                    raise HTTPException(status_code=401, detail="Invalid token issuer")
                    
            except jwt.ExpiredSignatureError:
                raise HTTPException(status_code=401, detail="Token expired")
            except jwt.InvalidTokenError as e:
                raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
            
            # Check token expiration
            if 'exp' in payload:
                exp_timestamp = payload['exp']
                if datetime.utcnow().timestamp() > exp_timestamp:
                    raise HTTPException(status_code=401, detail="Token expired")
            
            return {
                'user_id': payload.get('sub'),
                'email': payload.get('email'),
                'first_name': payload.get('first_name'),
                'last_name': payload.get('last_name'),
                'profile_image_url': payload.get('profile_image_url')
            }
            
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Authentication error: {str(e)}")
    
    async def require_auth(
        self, 
        user: Optional[Dict[str, Any]] = Depends(lambda self=None: auth_middleware.get_current_user())
    ) -> Dict[str, Any]:
        """Require authentication - raises 401 if not authenticated"""
        if not user:
            raise HTTPException(status_code=401, detail="Authentication required")
        return user

# Global middleware instance
auth_middleware = AuthMiddleware()