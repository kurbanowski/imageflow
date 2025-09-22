#!/bin/bash

# FastAPI Photo Sharing App Deployment Script for EC2
# This script sets up and runs the application on your EC2 instance

set -e  # Exit on any error

echo "🚀 Starting FastAPI Photo Sharing App deployment..."

# Check if Python 3.9+ is installed
python3 --version || { echo "Python 3.9+ is required. Please install it first."; exit 1; }

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip and install requirements
echo "📋 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Set environment variables for production
export ENVIRONMENT=production
export DYNAMODB_TABLE_NAME=${DYNAMODB_TABLE_NAME:-photos}
export S3_BUCKET_NAME=${S3_BUCKET_NAME:-photo-host-918801323166-9222025}
export AWS_REGION=${AWS_REGION:-us-east-1}

# AWS credentials should be set via IAM role or environment variables
# AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY should be set in your environment

echo "🏗️  Environment configuration:"
echo "  - Environment: $ENVIRONMENT"
echo "  - DynamoDB Table: $DYNAMODB_TABLE_NAME"
echo "  - S3 Bucket: $S3_BUCKET_NAME"
echo "  - AWS Region: $AWS_REGION"

# Check AWS credentials
if [ -z "$AWS_ACCESS_KEY_ID" ] && [ -z "$AWS_PROFILE" ]; then
    echo "⚠️  Warning: No AWS credentials found. Make sure your EC2 instance has an IAM role with DynamoDB and S3 permissions"
fi

# Create static directory if it doesn't exist
mkdir -p static

echo "🚀 Starting FastAPI application..."
echo "📡 Application will be available at: http://your-ec2-public-ip:5000"
echo "📖 API documentation at: http://your-ec2-public-ip:5000/docs"
echo ""
echo "Press Ctrl+C to stop the application"

# Start the application with production settings
# For production, consider using gunicorn with uvicorn workers
# gunicorn -k uvicorn.workers.UvicornWorker -w 2 -b 0.0.0.0:5000 main:app
uvicorn main:app --host 0.0.0.0 --port 5000