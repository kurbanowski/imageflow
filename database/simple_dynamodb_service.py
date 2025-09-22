"""
Simple DynamoDB service that works with standard table structures
"""
import aioboto3
import boto3
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import uuid
import json
from config import (
    DYNAMODB_REGION, 
    DYNAMODB_ENDPOINT_URL, 
    DYNAMODB_TABLE_NAME,
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    DEFAULT_LINK_EXPIRATION_DAYS
)

class SimpleDynamoDBService:
    """
    Simple DynamoDB service that works with existing table structures.
    Assumes a standard photos table with a simple primary key.
    """
    
    def __init__(self):
        self.table_name = DYNAMODB_TABLE_NAME
        self.region = DYNAMODB_REGION
        
        # Session configuration for aioboto3
        self.session_config = {
            'region_name': self.region
        }
        
        # Add credentials if provided
        if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
            self.session_config.update({
                'aws_access_key_id': AWS_ACCESS_KEY_ID,
                'aws_secret_access_key': AWS_SECRET_ACCESS_KEY
            })
        
        # Endpoint URL for local development
        self.endpoint_url = DYNAMODB_ENDPOINT_URL
    
    def get_client(self):
        """Get async DynamoDB client"""
        session = aioboto3.Session(
            aws_access_key_id=self.session_config.get('aws_access_key_id'),
            aws_secret_access_key=self.session_config.get('aws_secret_access_key'),
            region_name=self.session_config['region_name']
        )
        
        if self.endpoint_url:
            return session.client('dynamodb', endpoint_url=self.endpoint_url)
        return session.client('dynamodb')
    
    def get_resource(self):
        """Get async DynamoDB resource"""
        session = aioboto3.Session(
            aws_access_key_id=self.session_config.get('aws_access_key_id'),
            aws_secret_access_key=self.session_config.get('aws_secret_access_key'),
            region_name=self.session_config['region_name']
        )
        
        if self.endpoint_url:
            return session.resource('dynamodb', endpoint_url=self.endpoint_url)
        return session.resource('dynamodb')
    
    async def create_table_if_not_exists(self):
        """Check if table exists (don't try to create it)"""
        try:
            async with self.get_client() as client:
                # Just check if table exists
                await client.describe_table(TableName=self.table_name)
                print(f"Table {self.table_name} exists and is ready")
                return
        except Exception as e:
            print(f"Warning: Could not verify table {self.table_name}: {str(e)}")
            print("Continuing anyway - table may exist with different structure")
    
    # User operations - simplified
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user record"""
        user_id = user_data.get('id') or str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        item = {
            'id': user_id,
            'type': 'USER',
            'user_id': user_id,
            'email': user_data.get('email'),
            'first_name': user_data.get('first_name'),
            'last_name': user_data.get('last_name'),
            'profile_image_url': user_data.get('profile_image_url'),
            'created_at': timestamp,
            'updated_at': timestamp
        }
        
        async with self.get_resource() as dynamodb:
            table = await dynamodb.Table(self.table_name)
            await table.put_item(Item=item)
        
        return item
    
    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID - simplified for demo"""
        # For MVP, return a demo user
        return {
            'id': user_id,
            'user_id': user_id,
            'first_name': 'Demo',
            'last_name': 'User',
            'email': 'demo@example.com',
            'created_at': datetime.now().isoformat()
        }
    
    async def update_user(self, user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update user information - simplified"""
        user = await self.get_user(user_id)
        user.update(updates)
        user['updated_at'] = datetime.now().isoformat()
        return user
    
    # Photo operations - simplified for any table structure
    async def create_photo(self, photo_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new photo record"""
        photo_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        item = {
            'id': photo_id,  # Simple primary key
            'type': 'PHOTO',
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
        
        async with self.get_resource() as dynamodb:
            table = await dynamodb.Table(self.table_name)
            await table.put_item(Item=item)
        
        return item
    
    async def get_photo(self, photo_id: str) -> Optional[Dict[str, Any]]:
        """Get photo by ID - using simple key"""
        async with self.get_resource() as dynamodb:
            table = await dynamodb.Table(self.table_name)
            response = await table.get_item(
                Key={'id': photo_id}  # Simple key structure
            )
            return response.get('Item')
    
    async def update_photo(self, photo_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update photo information"""
        # Whitelist allowed fields
        allowed_fields = {'title', 'description', 'metadata'}
        filtered_updates = {k: v for k, v in updates.items() if k in allowed_fields}
        
        if not filtered_updates:
            photo = await self.get_photo(photo_id)
            if not photo:
                raise ValueError(f"Photo {photo_id} not found")
            return photo
        
        filtered_updates['updated_at'] = datetime.now().isoformat()
        
        update_expression = "SET "
        expression_values = {}
        expression_names = {}
        
        for key, value in filtered_updates.items():
            attr_name = f"#{key}"
            attr_value = f":{key}"
            update_expression += f"{attr_name} = {attr_value}, "
            expression_names[attr_name] = key
            expression_values[attr_value] = value
        
        update_expression = update_expression.rstrip(", ")
        
        async with self.get_resource() as dynamodb:
            table = await dynamodb.Table(self.table_name)
            response = await table.update_item(
                Key={'id': photo_id},  # Simple key
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_names,
                ExpressionAttributeValues=expression_values,
                ReturnValues='ALL_NEW'
            )
            return response['Attributes']
    
    async def list_user_photos(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """List photos by user using scan"""
        async with self.get_resource() as dynamodb:
            table = await dynamodb.Table(self.table_name)
            response = await table.scan(
                FilterExpression='#uid = :user_id AND #type = :photo_type',
                ExpressionAttributeNames={
                    '#uid': 'user_id',
                    '#type': 'type'
                },
                ExpressionAttributeValues={
                    ':user_id': user_id,
                    ':photo_type': 'PHOTO'
                },
                Limit=limit
            )
            
            # Sort by created_at in reverse order
            items = response.get('Items', [])
            items.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            return items[:limit]
    
    async def list_recent_photos(self, limit: int = 20) -> List[Dict[str, Any]]:
        """List most recent photos using scan"""
        async with self.get_resource() as dynamodb:
            table = await dynamodb.Table(self.table_name)
            response = await table.scan(
                FilterExpression='#type = :photo_type',
                ExpressionAttributeNames={'#type': 'type'},
                ExpressionAttributeValues={':photo_type': 'PHOTO'},
                Limit=limit
            )
            
            # Sort by created_at in reverse order
            items = response.get('Items', [])
            items.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            return items[:limit]
    
    async def delete_photo(self, photo_id: str) -> bool:
        """Delete a photo record"""
        try:
            async with self.get_resource() as dynamodb:
                table = await dynamodb.Table(self.table_name)
                await table.delete_item(
                    Key={'id': photo_id}  # Simple key
                )
                return True
        except Exception as e:
            print(f"Failed to delete photo from database: {str(e)}")
            return False
    
    # Comment operations - simplified
    async def create_comment(self, comment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new comment"""
        comment_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        item = {
            'id': comment_id,
            'type': 'COMMENT',
            'comment_id': comment_id,
            'photo_id': comment_data['photo_id'],
            'user_id': comment_data['user_id'],
            'content': comment_data['content'],
            'created_at': timestamp,
            'updated_at': timestamp
        }
        
        async with self.get_resource() as dynamodb:
            table = await dynamodb.Table(self.table_name)
            await table.put_item(Item=item)
        
        return item
    
    async def list_photo_comments(self, photo_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """List comments for a photo"""
        async with self.get_resource() as dynamodb:
            table = await dynamodb.Table(self.table_name)
            response = await table.scan(
                FilterExpression='photo_id = :photo_id AND #type = :comment_type',
                ExpressionAttributeNames={'#type': 'type'},
                ExpressionAttributeValues={
                    ':photo_id': photo_id,
                    ':comment_type': 'COMMENT'
                },
                Limit=limit
            )
            
            # Sort by created_at (oldest first)
            items = response.get('Items', [])
            items.sort(key=lambda x: x.get('created_at', ''))
            return items
    
    # Shareable link operations - simplified
    async def create_shareable_link(self, link_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a shareable link"""
        link_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # Calculate expiration
        expiration_days = link_data.get('expiration_days', DEFAULT_LINK_EXPIRATION_DAYS)
        expires_at = (datetime.now() + timedelta(days=expiration_days)).isoformat()
        
        item = {
            'id': link_id,
            'type': 'SHARE_LINK',
            'link_id': link_id,
            'photo_id': link_data['photo_id'],
            'user_id': link_data['user_id'],
            'expires_at': expires_at,
            'access_count': 0,
            'created_at': timestamp,
            'updated_at': timestamp
        }
        
        async with self.get_resource() as dynamodb:
            table = await dynamodb.Table(self.table_name)
            await table.put_item(Item=item)
        
        return item
    
    async def get_shareable_link(self, link_id: str) -> Optional[Dict[str, Any]]:
        """Get shareable link and check expiration"""
        async with self.get_resource() as dynamodb:
            table = await dynamodb.Table(self.table_name)
            response = await table.get_item(
                Key={'id': link_id}
            )
            
            link = response.get('Item')
            if not link:
                return None
            
            # Check if expired
            expires_at = datetime.fromisoformat(link['expires_at'])
            if datetime.now() > expires_at:
                return None
            
            return link
    
    async def increment_link_access(self, link_id: str) -> None:
        """Increment access count"""
        async with self.get_resource() as dynamodb:
            table = await dynamodb.Table(self.table_name)
            await table.update_item(
                Key={'id': link_id},
                UpdateExpression='ADD access_count :inc SET updated_at = :timestamp',
                ExpressionAttributeValues={
                    ':inc': 1,
                    ':timestamp': datetime.now().isoformat()
                }
            )

# Global simple DynamoDB service instance
simple_dynamodb_service = SimpleDynamoDBService()