"""
Mock DynamoDB service for development when AWS credentials are not available
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import uuid
from utils import generate_uuid, calculate_expiration_date

class MockDynamoDBService:
    """
    Mock DynamoDB service that stores data in memory for development
    """
    
    def __init__(self):
        self.data = {}
        self.initialized = True
    
    async def create_table_if_not_exists(self):
        """Mock table creation"""
        print("Mock DynamoDB service initialized")
        return True
    
    # User operations
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user"""
        user_id = user_data.get('id') or generate_uuid()
        timestamp = datetime.now().isoformat()
        
        item = {
            'entity_type': 'USER',
            'user_id': user_id,
            'email': user_data.get('email'),
            'first_name': user_data.get('first_name'),
            'last_name': user_data.get('last_name'),
            'profile_image_url': user_data.get('profile_image_url'),
            'created_at': timestamp,
            'updated_at': timestamp
        }
        
        self.data[f"USER#{user_id}"] = item
        return item
    
    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        return self.data.get(f"USER#{user_id}")
    
    async def update_user(self, user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update user information"""
        user_key = f"USER#{user_id}"
        if user_key in self.data:
            self.data[user_key].update(updates)
            self.data[user_key]['updated_at'] = datetime.now().isoformat()
            return self.data[user_key]
        raise KeyError(f"User {user_id} not found")
    
    # Photo operations
    async def create_photo(self, photo_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new photo record"""
        photo_id = generate_uuid()
        timestamp = datetime.now().isoformat()
        
        item = {
            'entity_type': 'PHOTO',
            'photo_id': photo_id,
            'user_id': photo_data['user_id'],
            'title': photo_data.get('title', ''),
            'description': photo_data.get('description', ''),
            'file_path': photo_data['file_path'],
            'file_size': photo_data.get('file_size', 0),
            'content_type': photo_data.get('content_type', ''),
            'metadata': photo_data.get('metadata', {}),
            'created_at': timestamp,
            'updated_at': timestamp
        }
        
        self.data[f"PHOTO#{photo_id}"] = item
        return item
    
    async def get_photo(self, photo_id: str) -> Optional[Dict[str, Any]]:
        """Get photo by ID"""
        return self.data.get(f"PHOTO#{photo_id}")
    
    async def update_photo(self, photo_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update photo information"""
        photo_key = f"PHOTO#{photo_id}"
        if photo_key in self.data:
            self.data[photo_key].update(updates)
            self.data[photo_key]['updated_at'] = datetime.now().isoformat()
            return self.data[photo_key]
        raise KeyError(f"Photo {photo_id} not found")
    
    async def list_user_photos(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """List photos by user"""
        photos = []
        for key, item in self.data.items():
            if (key.startswith("PHOTO#") and 
                item.get('user_id') == user_id):
                photos.append(item)
        
        # Sort by created_at descending
        photos.sort(key=lambda x: x['created_at'], reverse=True)
        return photos[:limit]
    
    async def list_recent_photos(self, limit: int = 20) -> List[Dict[str, Any]]:
        """List most recent photos across all users"""
        photos = []
        for key, item in self.data.items():
            if key.startswith("PHOTO#"):
                photos.append(item)
        
        # Sort by created_at descending
        photos.sort(key=lambda x: x['created_at'], reverse=True)
        return photos[:limit]
    
    # Comment operations
    async def create_comment(self, comment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new comment on a photo"""
        comment_id = generate_uuid()
        timestamp = datetime.now().isoformat()
        
        item = {
            'entity_type': 'COMMENT',
            'comment_id': comment_id,
            'photo_id': comment_data['photo_id'],
            'user_id': comment_data['user_id'],
            'content': comment_data['content'],
            'created_at': timestamp,
            'updated_at': timestamp
        }
        
        self.data[f"COMMENT#{comment_id}"] = item
        return item
    
    async def list_photo_comments(self, photo_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """List comments for a photo"""
        comments = []
        for key, item in self.data.items():
            if (key.startswith("COMMENT#") and 
                item.get('photo_id') == photo_id):
                comments.append(item)
        
        # Sort by created_at ascending
        comments.sort(key=lambda x: x['created_at'])
        return comments[:limit]
    
    # Shareable link operations
    async def create_shareable_link(self, link_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a shareable link for a photo"""
        link_id = generate_uuid()
        timestamp = datetime.now().isoformat()
        
        # Calculate expiration date
        expiration_days = link_data.get('expiration_days', 30)
        expires_at = calculate_expiration_date(expiration_days).isoformat()
        
        item = {
            'entity_type': 'SHARE_LINK',
            'link_id': link_id,
            'photo_id': link_data['photo_id'],
            'user_id': link_data['user_id'],
            'expires_at': expires_at,
            'access_count': 0,
            'created_at': timestamp,
            'updated_at': timestamp
        }
        
        self.data[f"SHARE_LINK#{link_id}"] = item
        return item
    
    async def get_shareable_link(self, link_id: str) -> Optional[Dict[str, Any]]:
        """Get shareable link by ID and check if it's still valid"""
        link = self.data.get(f"SHARE_LINK#{link_id}")
        if not link:
            return None
        
        # Check if link has expired
        expires_at = datetime.fromisoformat(link['expires_at'])
        if datetime.now() > expires_at:
            return None
        
        return link
    
    async def increment_link_access(self, link_id: str) -> None:
        """Increment access count for a shareable link"""
        link_key = f"SHARE_LINK#{link_id}"
        if link_key in self.data:
            self.data[link_key]['access_count'] += 1
            self.data[link_key]['updated_at'] = datetime.now().isoformat()

# Mock instance for development
mock_dynamodb_service = MockDynamoDBService()