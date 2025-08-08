from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional
import shutil
import os
import uuid
import httpx
import asyncio
from pathlib import Path

app = FastAPI(title="Bell Pepper Backend API", version="1.0.0")

UPLOAD_DIR = "backend/app/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Serve static files from uploads directory
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Vite dev server
        "http://localhost:3001",  # Vite dev server (alternative port)
        "http://localhost:8080",  # Production frontend
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:8080",
        "http://frontend:80",     # Docker frontend service
        "*"  # Fallback for development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models service URL
MODELS_SERVICE_URL = os.getenv("MODELS_SERVICE_URL", "http://models:8001")

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Bell Pepper Classification API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check if models service is available
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MODELS_SERVICE_URL}/health", timeout=5.0)
            models_healthy = response.status_code == 200
    except Exception:
        models_healthy = False
    
    return {
        "status": "healthy",
        "models_service": "healthy" if models_healthy else "unhealthy"
    }

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload and save file"""
    try:
        # Generate unique filename
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
        unique_filename = f"{uuid.uuid4()}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return {
            "filename": unique_filename,
            "original_filename": file.filename,
            "file_path": f"/uploads/{unique_filename}",
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

@app.post("/predict")
async def predict_pepper_grade(
    image: UploadFile = File(...),
    region: Optional[str] = Form(None),
    model_type: Optional[str] = Form("ensemble")
):
    """Predict bell pepper grade by forwarding to models service"""
    try:
        # Forward the file and parameters to models service
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Prepare file for forwarding
            file_content = await image.read()
            files = {"image": (image.filename, file_content, image.content_type)}
            
            # Prepare form data
            data = {"model_type": model_type}
            if region:
                data["region"] = region
            
            # Make request to models service
            response = await client.post(
                f"{MODELS_SERVICE_URL}/predict",
                files=files,
                data=data
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Models service error: {response.text}"
                )
                
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Models service timeout")
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Models service unavailable")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@app.post("/predict-uploaded")
async def predict_uploaded_file(filename: str = Form(...)):
    """Predict bell pepper grade for already uploaded file"""
    try:
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        # Read file and forward to models service
        async with httpx.AsyncClient(timeout=30.0) as client:
            with open(file_path, "rb") as f:
                files = {"file": (filename, f.read(), "image/jpeg")}
            
            response = await client.post(
                f"{MODELS_SERVICE_URL}/predict",
                files=files
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Models service error: {response.text}"
                )
                
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Models service timeout")
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Models service unavailable")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@app.get("/models/status")
async def get_models_status():
    """Get status of models from models service"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MODELS_SERVICE_URL}/models/status", timeout=10.0)
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Models service error: {response.text}"
                )
                
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Models service timeout")
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Models service unavailable")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get models status: {str(e)}")

@app.post("/models/reload")
async def reload_models():
    """Reload models in models service"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{MODELS_SERVICE_URL}/models/reload", timeout=30.0)
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Models service error: {response.text}"
                )
                
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Models service timeout")
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Models service unavailable")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reload models: {str(e)}")

@app.post("/select-object")
async def select_object(
    image: UploadFile = File(...),
    click_x: int = Form(...),
    click_y: int = Form(...)
):
    """Select object in image using YOLO segmentation"""
    # Save uploaded image
    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}_{image.filename}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)
    
    # Use YOLOv8-seg for segmentation with safe unpickling for PyTorch 2.6+
    import torch
    from ultralytics import YOLO
    from ultralytics.nn.tasks import SegmentationModel
    import cv2
    from PIL import Image
    import numpy as np
    from torch.nn.modules.container import Sequential, ModuleList
    from ultralytics.nn.modules.conv import Conv
    from ultralytics.nn.modules.block import C2f
    from torch.nn.modules.conv import Conv2d
    from torch.nn.modules.batchnorm import BatchNorm2d
    from torch.nn.modules.activation import SiLU
    
    try:
        # Load YOLO model without safe_globals for PyTorch 2.0.1 compatibility
        model = YOLO('yolov8n-seg.pt')  # Make sure you have a segmentation model
        results = model(file_path)
        masks = results[0].masks
        boxes = [list(map(lambda x: int(x), box[:4])) for box in results[0].boxes.xyxy.cpu().numpy()]
        
        found = None
        mask_idx = None
        print(f"Click coordinates: x={click_x}, y={click_y}")
        print(f"Detected boxes: {boxes}")
        
        for i, box in enumerate(boxes):
            x1, y1, x2, y2 = box
            print(f"Checking box {i}: {box}")
            if x1 <= click_x <= x2 and y1 <= click_y <= y2:
                found = [int(x1), int(y1), int(x2), int(y2)]
                mask_idx = i
                print(f"Found object at index {i} with box {found}")
                break
        
        if found is None or mask_idx is None or masks is None:
            print(f"No object detected at click location. Boxes: {boxes}, found: {found}, mask_idx: {mask_idx}, masks: {masks}")
            return JSONResponse({
                "error": "No object detected at the selected location.",
                "boxes": boxes
            }, status_code=404)
        
        # Extract mask and create segmented image
        mask = masks.data[mask_idx].cpu().numpy()
        original_img = cv2.imread(file_path)
        
        # Resize mask to match image dimensions
        mask_resized = cv2.resize(mask, (original_img.shape[1], original_img.shape[0]))
        
        # Create RGBA image with transparency
        rgba_img = cv2.cvtColor(original_img, cv2.COLOR_BGR2RGBA)
        rgba_img[:, :, 3] = (mask_resized * 255).astype(np.uint8)
        
        # Save segmented image
        segmented_filename = f"segmented_{file_id}_{image.filename.rsplit('.', 1)[0]}.png"
        segmented_path = os.path.join(UPLOAD_DIR, segmented_filename)
        cv2.imwrite(segmented_path, rgba_img)
        
        return JSONResponse({
            "cropped_image": f"/uploads/{segmented_filename}",
            "region": found,
            "mask_applied": True
        })
        
    except Exception as e:
        print(f"Error in object selection: {e}")
        return JSONResponse({
            "error": f"Object selection failed: {str(e)}"
        }, status_code=500)

# Legacy endpoints for backward compatibility
@app.post("/classify")
async def classify_pepper(file: UploadFile = File(...)):
    """Legacy classify endpoint - redirects to predict"""
    return await predict_pepper_grade(file)

@app.get("/api/health")
async def api_health():
    """Alternative health endpoint"""
    return await health_check()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)