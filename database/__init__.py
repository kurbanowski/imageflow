import os
from .dynamodb_service import dynamodb_service
from .mock_service import mock_dynamodb_service
from config import USE_MOCK_SERVICES, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY

def get_db_service():
    """Get the appropriate database service based on environment"""
    # Use production DynamoDB if credentials are available
    if not USE_MOCK_SERVICES:
        print("Using production DynamoDB service (credentials available)")
        return dynamodb_service
    else:
        print("Using mock DynamoDB service (no credentials available)")
        return mock_dynamodb_service

# Export the service instance
db_service = get_db_service()

__all__ = ['db_service', 'dynamodb_service', 'mock_dynamodb_service']