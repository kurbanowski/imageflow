"""
S3 service for file upload and management
"""
import aioboto3
import boto3
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import os
from config import (
    AWS_REGION,
    AWS_ACCESS_KEY_ID, 
    AWS_SECRET_ACCESS_KEY,
    S3_BUCKET_NAME,
    S3_REGION
)

class S3Service:
    """AWS S3 service for file storage operations"""
    
    def __init__(self):
        self.bucket_name = S3_BUCKET_NAME
        self.region = S3_REGION
        
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
    
    def get_client(self):
        """Get async S3 client"""
        session = aioboto3.Session(
            aws_access_key_id=self.session_config.get('aws_access_key_id'),
            aws_secret_access_key=self.session_config.get('aws_secret_access_key'),
            region_name=self.session_config['region_name']
        )
        return session.client('s3')
    
    async def upload_file(self, file_obj, user_id: str, original_filename: str, content_type: str) -> Dict[str, Any]:
        """Upload a file to S3 and return file information"""
        
        # Generate unique filename with user folder structure
        file_extension = os.path.splitext(original_filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        s3_key = f"photos/{user_id}/{unique_filename}"
        
        try:
            async with self.get_client() as s3:
                # Upload file to S3
                await s3.upload_fileobj(
                    file_obj,
                    self.bucket_name,
                    s3_key,
                    ExtraArgs={
                        'ContentType': content_type,
                        'ServerSideEncryption': 'AES256'
                    }
                )
                
                # Generate file URL
                file_url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{s3_key}"
                
                return {
                    'file_path': s3_key,
                    'file_url': file_url,
                    'bucket': self.bucket_name,
                    'unique_filename': unique_filename,
                    'original_filename': original_filename
                }
                
        except Exception as e:
            raise Exception(f"Failed to upload file to S3: {str(e)}")
    
    async def generate_presigned_url(self, s3_key: str, expiration: int = 3600) -> str:
        """Generate a presigned URL for accessing a private S3 object"""
        try:
            # Use synchronous boto3 client for presigned URLs (aioboto3 doesn't support generate_presigned_url)
            import boto3
            s3_client = boto3.client(
                's3',
                aws_access_key_id=self.session_config.get('aws_access_key_id'),
                aws_secret_access_key=self.session_config.get('aws_secret_access_key'),
                region_name=self.session_config['region_name']
            )
            
            url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=expiration
            )
            return url
        except Exception as e:
            raise Exception(f"Failed to generate presigned URL: {str(e)}")
    
    async def delete_file(self, s3_key: str) -> bool:
        """Delete a file from S3"""
        try:
            async with self.get_client() as s3:
                await s3.delete_object(Bucket=self.bucket_name, Key=s3_key)
                return True
        except Exception as e:
            print(f"Failed to delete file from S3: {str(e)}")
            return False
    
    async def check_bucket_exists(self) -> bool:
        """Check if the S3 bucket exists and is accessible"""
        try:
            async with self.get_client() as s3:
                await s3.head_bucket(Bucket=self.bucket_name)
                return True
        except Exception as e:
            print(f"S3 bucket check failed: {str(e)}")
            return False

# Global S3 service instance
s3_service = S3Service()