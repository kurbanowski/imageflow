import os
from .dynamodb_service import dynamodb_service
from .mock_service import mock_dynamodb_service

# Use mock service for development if no AWS credentials
def get_db_service():
    """Get the appropriate database service based on environment"""
    aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    
    if aws_access_key and aws_secret_key:
        return dynamodb_service
    else:
        print("Using mock DynamoDB service for development")
        return mock_dynamodb_service

# Export the service instance
db_service = get_db_service()

__all__ = ['db_service', 'dynamodb_service', 'mock_dynamodb_service']