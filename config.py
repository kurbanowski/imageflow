import os
from typing import Optional

# Environment configuration
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
DEBUG = ENVIRONMENT == "development"

# AWS Configuration
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

# DynamoDB Configuration
DYNAMODB_REGION = AWS_REGION
DYNAMODB_ENDPOINT_URL = os.getenv("DYNAMODB_ENDPOINT_URL")  # For local DynamoDB
DYNAMODB_TABLE_NAME = os.getenv("DYNAMODB_TABLE_NAME", "photos")

# S3 Configuration for file storage
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "photo-host-918801323166-9222025")
S3_REGION = AWS_REGION

# Application Configuration
DEFAULT_LINK_EXPIRATION_DAYS = 30
MAX_FILE_SIZE_MB = 100
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
ALLOWED_IMAGE_TYPES = {
    "image/jpeg", "image/jpg", "image/png", "image/gif", 
    "image/webp", "image/bmp", "image/tiff"
}

# Authentication configuration
REPLIT_AUTH_DOMAIN = os.getenv("REPL_ID", "") + ".id.replit.com"
JWT_ISSUER_URL = f"https://{REPLIT_AUTH_DOMAIN}"

# Use mock services in development when AWS credentials are not available
USE_MOCK_SERVICES = ENVIRONMENT == "development" and not (AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY)

# Object Storage Configuration (from Replit integration - fallback)
PRIVATE_OBJECT_DIR = os.getenv("PRIVATE_OBJECT_DIR", "")
PUBLIC_OBJECT_SEARCH_PATHS = os.getenv("PUBLIC_OBJECT_SEARCH_PATHS", "")
DEFAULT_OBJECT_STORAGE_BUCKET_ID = os.getenv("DEFAULT_OBJECT_STORAGE_BUCKET_ID", "")

# Session Configuration
SESSION_SECRET = os.getenv("SESSION_SECRET", "")