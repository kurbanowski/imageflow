import os
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
import uvicorn

from database import db_service

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
    yield
    # Shutdown
    print("Application shutdown")

app = FastAPI(
    title="Photo Sharing App", 
    description="A FastAPI application with DynamoDB integration for photo sharing",
    lifespan=lifespan
)

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
                
                // This will be implemented later with actual upload functionality
                alert('Upload functionality will be implemented with DynamoDB integration');
            });
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