import os
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager
import uvicorn

from database import db_service
from routers import photos, comments, share_links, auth
from middleware.error_handler import error_handler
from config import USE_MOCK_SERVICES, ENVIRONMENT
from services.s3_service import s3_service

if USE_MOCK_SERVICES:
    print("Using mock DynamoDB service for development")
else:
    print(f"Using production AWS services in {ENVIRONMENT} environment")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Initializing application...")
    try:
        await db_service.create_table_if_not_exists()
        print("Database initialization complete")
    except Exception as e:
        print(f"Database initialization failed: {str(e)}")
        print("Application may have limited functionality")
    
    # Check S3 bucket access if not using mock services
    if not USE_MOCK_SERVICES:
        try:
            bucket_exists = await s3_service.check_bucket_exists()
            if bucket_exists:
                print("S3 bucket access verified")
            else:
                print("Warning: S3 bucket access failed - file uploads may not work")
        except Exception as e:
            print(f"Warning: S3 service check failed: {str(e)}")
    
    yield
    # Shutdown
    print("Application shutdown")

app = FastAPI(
    title="Photo Sharing App", 
    description="A FastAPI application with DynamoDB integration for photo sharing",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5000"],  # Development origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# Add error handlers
app.add_exception_handler(HTTPException, error_handler.http_exception_handler)
app.add_exception_handler(StarletteHTTPException, error_handler.http_exception_handler)
app.add_exception_handler(RequestValidationError, error_handler.validation_exception_handler)
app.add_exception_handler(Exception, error_handler.general_exception_handler)

# Include routers
app.include_router(auth.router)
app.include_router(photos.router)
app.include_router(comments.router)
app.include_router(share_links.router)

# Serve static files
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main application page"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Photo Sharing App</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            .upload-area {
                border: 2px dashed #ccc;
                border-radius: 10px;
                padding: 50px;
                text-align: center;
                margin: 20px 0;
                transition: border-color 0.3s ease;
            }
            .upload-area:hover {
                border-color: #007bff;
            }
            .photo-card {
                margin-bottom: 20px;
            }
        </style>
    </head>
    <body>
        <div class="container mt-4">
            <h1 class="mb-4">📸 Photo Sharing App</h1>
            
            <div class="row">
                <div class="col-md-8">
                    <div class="card">
                        <div class="card-header">
                            <h5>Upload Photo</h5>
                        </div>
                        <div class="card-body">
                            <div class="upload-area" id="uploadArea">
                                <i class="bi bi-cloud-upload" style="font-size: 2rem;"></i>
                                <p>Drag & drop your photos here or click to browse</p>
                                <input type="file" id="fileInput" accept="image/*" style="display: none;">
                                <button class="btn btn-primary" onclick="document.getElementById('fileInput').click()">
                                    Choose Photos
                                </button>
                            </div>
                            <div class="mt-3">
                                <label for="photoTitle" class="form-label">Photo Title</label>
                                <input type="text" class="form-control" id="photoTitle" placeholder="Enter photo title">
                            </div>
                            <div class="mt-3">
                                <label for="photoDescription" class="form-label">Description</label>
                                <textarea class="form-control" id="photoDescription" rows="3" placeholder="Enter photo description"></textarea>
                            </div>
                            <button class="btn btn-success mt-3" id="uploadBtn" disabled>
                                Upload Photo
                            </button>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-header">
                            <h5>Recent Photos</h5>
                        </div>
                        <div class="card-body" id="photosList">
                            <p class="text-muted">No photos uploaded yet.</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            // Basic file upload functionality
            const fileInput = document.getElementById('fileInput');
            const uploadArea = document.getElementById('uploadArea');
            const uploadBtn = document.getElementById('uploadBtn');
            
            fileInput.addEventListener('change', function(e) {
                if (e.target.files.length > 0) {
                    uploadBtn.disabled = false;
                    uploadArea.innerHTML = `
                        <p>Selected: ${e.target.files[0].name}</p>
                        <button class="btn btn-primary" onclick="document.getElementById('fileInput').click()">
                            Choose Different Photo
                        </button>
                    `;
                }
            });
            
            uploadBtn.addEventListener('click', async function() {
                const file = fileInput.files[0];
                const title = document.getElementById('photoTitle').value;
                const description = document.getElementById('photoDescription').value;
                
                if (!file) {
                    alert('Please select a photo');
                    return;
                }
                
                if (!title.trim()) {
                    alert('Please enter a photo title');
                    return;
                }
                
                // Disable button and show loading
                uploadBtn.disabled = true;
                uploadBtn.innerHTML = 'Uploading...';
                
                try {
                    // Create form data for upload
                    const formData = new FormData();
                    formData.append('file', file);
                    formData.append('title', title);
                    formData.append('description', description);
                    
                    // Upload to API
                    const response = await fetch('/api/photos/upload', {
                        method: 'POST',
                        body: formData
                    });
                    
                    if (!response.ok) {
                        const error = await response.json();
                        throw new Error(error.detail || 'Upload failed');
                    }
                    
                    const result = await response.json();
                    
                    // Success - clear form and refresh photos
                    document.getElementById('photoTitle').value = '';
                    document.getElementById('photoDescription').value = '';
                    fileInput.value = '';
                    uploadArea.innerHTML = `
                        <i class="bi bi-cloud-upload" style="font-size: 2rem;"></i>
                        <p>Drag & drop your photos here or click to browse</p>
                        <input type="file" id="fileInput" accept="image/*" style="display: none;">
                        <button class="btn btn-primary" onclick="document.getElementById('fileInput').click()">
                            Choose Photos
                        </button>
                    `;
                    
                    alert('Photo uploaded successfully!');
                    loadRecentPhotos(); // Refresh the photos list
                    
                } catch (error) {
                    alert('Upload failed: ' + error.message);
                } finally {
                    uploadBtn.disabled = false;
                    uploadBtn.innerHTML = 'Upload Photo';
                }
            });
            
            // Load recent photos
            async function loadRecentPhotos() {
                try {
                    const response = await fetch('/api/photos/');
                    if (response.ok) {
                        const photos = await response.json();
                        const photosList = document.getElementById('photosList');
                        
                        if (photos.length === 0) {
                            photosList.innerHTML = '<p class="text-muted">No photos uploaded yet.</p>';
                        } else {
                            photosList.innerHTML = photos.slice(0, 5).map(photoData => `
                                <div class="mb-2 p-2 border rounded">
                                    <h6 class="mb-1">${photoData.photo.title}</h6>
                                    <small class="text-muted">by ${photoData.user.first_name || 'Unknown'}</small>
                                    <br><small class="text-muted">${new Date(photoData.photo.created_at).toLocaleDateString()}</small>
                                </div>
                            `).join('');
                        }
                    }
                } catch (error) {
                    console.error('Failed to load photos:', error);
                }
            }
            
            // Load photos on page load
            loadRecentPhotos();
        </script>
    </body>
    </html>
    """

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Photo Sharing App is running"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)