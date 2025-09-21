import os
from typing import Optional

# DynamoDB Configuration
DYNAMODB_REGION = os.getenv("AWS_REGION", "us-east-1")
DYNAMODB_ENDPOINT_URL = os.getenv("DYNAMODB_ENDPOINT_URL")  # For local DynamoDB
DYNAMODB_TABLE_NAME = os.getenv("DYNAMODB_TABLE_NAME", "photo-sharing-app")

# AWS Credentials (for production)
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

# Application Configuration
DEFAULT_LINK_EXPIRATION_DAYS = 30
MAX_FILE_SIZE_MB = 100
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}

# Object Storage Configuration (from Replit integration)
PRIVATE_OBJECT_DIR = os.getenv("PRIVATE_OBJECT_DIR", "")
PUBLIC_OBJECT_SEARCH_PATHS = os.getenv("PUBLIC_OBJECT_SEARCH_PATHS", "")
DEFAULT_OBJECT_STORAGE_BUCKET_ID = os.getenv("DEFAULT_OBJECT_STORAGE_BUCKET_ID", "")

# Session Configuration
SESSION_SECRET = os.getenv("SESSION_SECRET", "")