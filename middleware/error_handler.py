"""
Global error handling middleware for FastAPI
"""
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import traceback
import logging
from typing import Any
import uuid

logger = logging.getLogger(__name__)

class ErrorHandlerMiddleware:
    """Global error handling middleware"""
    
    @staticmethod
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        """Handle HTTP exceptions"""
        error_id = str(uuid.uuid4())[:8]
        
        logger.warning(
            f"HTTP Exception {error_id}: {exc.status_code} - {exc.detail} "
            f"for {request.method} {request.url}"
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "HTTP_ERROR",
                "message": exc.detail,
                "error_id": error_id,
                "status_code": exc.status_code
            }
        )
    
    @staticmethod
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        """Handle validation errors"""
        error_id = str(uuid.uuid4())[:8]
        
        logger.warning(
            f"Validation Error {error_id}: {exc.errors()} "
            f"for {request.method} {request.url}"
        )
        
        return JSONResponse(
            status_code=422,
            content={
                "error": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": exc.errors(),
                "error_id": error_id
            }
        )
    
    @staticmethod
    async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle unexpected exceptions"""
        error_id = str(uuid.uuid4())[:8]
        
        logger.error(
            f"Unexpected Error {error_id}: {str(exc)} "
            f"for {request.method} {request.url}\n"
            f"Traceback: {traceback.format_exc()}"
        )
        
        return JSONResponse(
            status_code=500,
            content={
                "error": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "error_id": error_id
            }
        )

# Global error handler instance
error_handler = ErrorHandlerMiddleware()