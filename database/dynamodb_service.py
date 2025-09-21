import aioboto3
import boto3
from boto3.dynamodb.conditions import Key
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

class DynamoDBService:
    """
    DynamoDB service with async operations for the photo sharing application.
    
    Table Design:
    - Single table design using partition key (PK) and sort key (SK)
    - GSI1 for querying by different access patterns
    
    Entity Types:
    - USER#<user_id>
    - PHOTO#<photo_id>  
    - COMMENT#<photo_id>#<comment_id>
    - SHARE_LINK#<link_id>
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
        """Create the main table with proper schema if it doesn't exist"""
        try:
            async with self.get_client() as client:
                # Check if table exists
                try:
                    await client.describe_table(TableName=self.table_name)
                    print(f"Table {self.table_name} already exists")
                    return
                except client.exceptions.ResourceNotFoundException:
                    pass
                
                # Create table
                table_definition = {
                    'TableName': self.table_name,
                    'KeySchema': [
                        {'AttributeName': 'PK', 'KeyType': 'HASH'},  # Partition key
                        {'AttributeName': 'SK', 'KeyType': 'RANGE'}  # Sort key
                    ],
                    'AttributeDefinitions': [
                        {'AttributeName': 'PK', 'AttributeType': 'S'},
                        {'AttributeName': 'SK', 'AttributeType': 'S'},
                        {'AttributeName': 'GSI1PK', 'AttributeType': 'S'},
                        {'AttributeName': 'GSI1SK', 'AttributeType': 'S'},
                        {'AttributeName': 'GSI2PK', 'AttributeType': 'S'},
                        {'AttributeName': 'GSI2SK', 'AttributeType': 'S'}
                    ],
                    'GlobalSecondaryIndexes': [
                        {
                            'IndexName': 'GSI1',
                            'KeySchema': [
                                {'AttributeName': 'GSI1PK', 'KeyType': 'HASH'},
                                {'AttributeName': 'GSI1SK', 'KeyType': 'RANGE'}
                            ],
                            'Projection': {'ProjectionType': 'ALL'}
                        },
                        {
                            'IndexName': 'GSI2',
                            'KeySchema': [
                                {'AttributeName': 'GSI2PK', 'KeyType': 'HASH'},
                                {'AttributeName': 'GSI2SK', 'KeyType': 'RANGE'}
                            ],
                            'Projection': {'ProjectionType': 'ALL'}
                        }
                    ],
                    'BillingMode': 'PAY_PER_REQUEST'
                }
                
                await client.create_table(**table_definition)
                print(f"Created table {self.table_name}")
                
                # Wait for table to be active
                waiter = client.get_waiter('table_exists')
                await waiter.wait(TableName=self.table_name)
                print(f"Table {self.table_name} is now active")
                
                # Enable TTL on the ttl_epoch attribute
                try:
                    await client.update_time_to_live(
                        TableName=self.table_name,
                        TimeToLiveSpecification={
                            'AttributeName': 'ttl_epoch',
                            'Enabled': True
                        }
                    )
                    print(f"TTL enabled on table {self.table_name}")
                except Exception as e:
                    print(f"Warning: Could not enable TTL: {str(e)}")
                    # TTL is not critical for basic functionality
                
        except Exception as e:
            print(f"Error creating table: {str(e)}")
            raise
    
    # User operations
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user"""
        user_id = user_data.get('id') or str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        item = {
            'PK': f"USER#{user_id}",
            'SK': f"USER#{user_id}",
            'GSI1PK': 'USERS',
            'GSI1SK': timestamp,
            'entity_type': 'USER',
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
        """Get user by ID"""
        async with self.get_resource() as dynamodb:
            table = await dynamodb.Table(self.table_name)
            response = await table.get_item(
                Key={'PK': f"USER#{user_id}", 'SK': f"USER#{user_id}"}
            )
            return response.get('Item')
    
    async def update_user(self, user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update user information"""
        updates['updated_at'] = datetime.now().isoformat()
        
        update_expression = "SET "
        expression_values = {}
        
        for key, value in updates.items():
            update_expression += f"{key} = :{key}, "
            expression_values[f":{key}"] = value
        
        update_expression = update_expression.rstrip(", ")
        
        async with self.get_resource() as dynamodb:
            table = await dynamodb.Table(self.table_name)
            response = await table.update_item(
                Key={'PK': f"USER#{user_id}", 'SK': f"USER#{user_id}"},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values,
                ReturnValues='ALL_NEW'
            )
            return response['Attributes']
    
    # Photo operations
    async def create_photo(self, photo_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new photo record"""
        photo_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        item = {
            'PK': f"PHOTO#{photo_id}",
            'SK': f"PHOTO#{photo_id}",
            'GSI1PK': f"USER#{photo_data['user_id']}",
            'GSI1SK': f"PHOTO#{timestamp}",
            'GSI2PK': 'PHOTOS',
            'GSI2SK': timestamp,
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
        
        async with self.get_resource() as dynamodb:
            table = await dynamodb.Table(self.table_name)
            await table.put_item(Item=item)
        
        return item
    
    async def get_photo(self, photo_id: str) -> Optional[Dict[str, Any]]:
        """Get photo by ID"""
        async with self.get_resource() as dynamodb:
            table = await dynamodb.Table(self.table_name)
            response = await table.get_item(
                Key={'PK': f"PHOTO#{photo_id}", 'SK': f"PHOTO#{photo_id}"}
            )
            return response.get('Item')
    
    async def list_user_photos(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """List photos by user"""
        async with self.get_resource() as dynamodb:
            table = await dynamodb.Table(self.table_name)
            response = await table.query(
                IndexName='GSI1',
                KeyConditionExpression=Key('GSI1PK').eq(f"USER#{user_id}") & Key('GSI1SK').begins_with('PHOTO#'),
                ScanIndexForward=False,  # Most recent first
                Limit=limit
            )
            return response.get('Items', [])
    
    async def list_recent_photos(self, limit: int = 20) -> List[Dict[str, Any]]:
        """List most recent photos across all users"""
        async with self.get_resource() as dynamodb:
            table = await dynamodb.Table(self.table_name)
            response = await table.query(
                IndexName='GSI2',
                KeyConditionExpression=Key('GSI2PK').eq('PHOTOS'),
                ScanIndexForward=False,  # Most recent first
                Limit=limit
            )
            return response.get('Items', [])
    
    # Comment operations
    async def create_comment(self, comment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new comment on a photo"""
        comment_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        photo_id = comment_data['photo_id']
        
        item = {
            'PK': f"PHOTO#{photo_id}",
            'SK': f"COMMENT#{comment_id}",
            'GSI1PK': f"USER#{comment_data['user_id']}",
            'GSI1SK': f"COMMENT#{timestamp}",
            'entity_type': 'COMMENT',
            'comment_id': comment_id,
            'photo_id': photo_id,
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
            response = await table.query(
                KeyConditionExpression=Key('PK').eq(f"PHOTO#{photo_id}") & Key('SK').begins_with('COMMENT#'),
                ScanIndexForward=True,  # Oldest first
                Limit=limit
            )
            return response.get('Items', [])
    
    # Shareable link operations
    async def create_shareable_link(self, link_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a shareable link for a photo"""
        link_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # Calculate expiration date
        expiration_days = link_data.get('expiration_days', DEFAULT_LINK_EXPIRATION_DAYS)
        expires_at_dt = datetime.now() + timedelta(days=expiration_days)
        expires_at = expires_at_dt.isoformat()
        
        # TTL attribute for DynamoDB auto-expiration (epoch timestamp)
        ttl_epoch = int(expires_at_dt.timestamp())
        
        item = {
            'PK': f"SHARE_LINK#{link_id}",
            'SK': f"SHARE_LINK#{link_id}",
            'GSI1PK': f"PHOTO#{link_data['photo_id']}",
            'GSI1SK': f"LINK#{timestamp}",
            'entity_type': 'SHARE_LINK',
            'link_id': link_id,
            'photo_id': link_data['photo_id'],
            'user_id': link_data['user_id'],
            'expires_at': expires_at,
            'ttl_epoch': ttl_epoch,  # DynamoDB TTL attribute
            'access_count': 0,
            'created_at': timestamp,
            'updated_at': timestamp
        }
        
        async with self.get_resource() as dynamodb:
            table = await dynamodb.Table(self.table_name)
            await table.put_item(Item=item)
        
        return item
    
    async def get_shareable_link(self, link_id: str) -> Optional[Dict[str, Any]]:
        """Get shareable link by ID and check if it's still valid"""
        async with self.get_resource() as dynamodb:
            table = await dynamodb.Table(self.table_name)
            response = await table.get_item(
                Key={'PK': f"SHARE_LINK#{link_id}", 'SK': f"SHARE_LINK#{link_id}"}
            )
            
            link = response.get('Item')
            if not link:
                return None
            
            # Check if link has expired
            expires_at = datetime.fromisoformat(link['expires_at'])
            if datetime.now() > expires_at:
                return None
            
            return link
    
    async def increment_link_access(self, link_id: str) -> None:
        """Increment access count for a shareable link"""
        async with self.get_resource() as dynamodb:
            table = await dynamodb.Table(self.table_name)
            await table.update_item(
                Key={'PK': f"SHARE_LINK#{link_id}", 'SK': f"SHARE_LINK#{link_id}"},
                UpdateExpression='ADD access_count :inc SET updated_at = :timestamp',
                ExpressionAttributeValues={
                    ':inc': 1,
                    ':timestamp': datetime.now().isoformat()
                }
            )

# Global DynamoDB service instance
dynamodb_service = DynamoDBService()