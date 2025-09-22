import os
from .dynamodb_service import dynamodb_service
from .mock_service import mock_dynamodb_service
from config import USE_MOCK_SERVICES

def get_db_service():
    """Get the appropriate database service based on environment"""
    if USE_MOCK_SERVICES:
        print("Using mock DynamoDB service for development")
        return mock_dynamodb_service
    else:
        print("Using production DynamoDB service")
        return dynamodb_service

# Export the service instance
db_service = get_db_service()

__all__ = ['db_service', 'dynamodb_service', 'mock_dynamodb_service']