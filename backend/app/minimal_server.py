#!/usr/bin/env python3
"""
Minimal FastAPI server for testing backend connection
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="Pepper Vision Backend", version="1.0.0")

# Allow CORS for local frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Vite dev server
        "http://localhost:3001",  # Another possible Vite port
        "http://localhost:8080",  # Production frontend
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:8080",
        "*"  # Fallback for development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Pepper Vision Backend is running!", "status": "healthy"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "pepper-vision-backend", "demo_mode": True}

@app.get("/model-status")
async def model_status():
    return {
        "anfis_loaded": True,
        "transfer_learning_loaded": True,
        "ensemble_available": True,
        "models_count": 5,
        "status": "Demo mode: Using fallback models for testing"
    }

@app.get("/test")
async def test():
    return {"message": "Backend is working!", "timestamp": "2024-01-01T00:00:00Z"}

# Create uploads directory
import os
import uuid
from fastapi import File, UploadFile, Form
from fastapi.staticfiles import StaticFiles

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Serve static files from uploads directory
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

@app.post("/select-object")
async def select_object(
    image: UploadFile = File(...),
    click_x: int = Form(...),
    click_y: int = Form(...)
):
    """Select object in image (demo mode)"""
    print(f"Received object selection request at ({click_x}, {click_y})")
    
    # Save uploaded image
    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}_{image.filename}")
    
    try:
        with open(file_path, "wb") as buffer:
            content = await image.read()
            buffer.write(content)
    except Exception as e:
        return {"error": f"Failed to save image: {e}"}
    
    # Demo response - return the same image with a region
    region = [click_x - 50, click_y - 50, 100, 100]  # 100x100 region around click
    
    return {
        "cropped_image": f"{file_id}_{image.filename}",
        "region": region
    }

if __name__ == "__main__":
    print("🚀 Starting Pepper Vision Backend...")
    print("📍 Server will be available at: http://localhost:8001")
    print("🔗 Health check: http://localhost:8001/health")
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")