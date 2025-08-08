from fastapi import FastAPI, File, UploadFile, Form
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional
import shutil
import os
import uuid
import random
import numpy as np
from pathlib import Path
from PIL import Image

app = FastAPI()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001", 
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:8080",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Demo mode variables
label_mapping = {
    0: 'damaged',
    1: 'dried', 
    2: 'old',
    3: 'ripe',
    4: 'unripe'
}

def predict_demo(image_path: str, model_type: str = "ensemble") -> dict:
    """Demo prediction function that returns realistic results"""
    categories = ['damaged', 'dried', 'old', 'ripe', 'unripe']
    category = random.choice(categories)
    confidence = random.uniform(0.7, 0.95)
    
    # Generate realistic probabilities
    probabilities = {}
    for cat in categories:
        if cat == category:
            probabilities[cat] = confidence
        else:
            probabilities[cat] = random.uniform(0.1, 0.4)
    
    # Normalize probabilities
    total = sum(probabilities.values())
    probabilities = {k: v/total for k, v in probabilities.items()}
    
    # Determine ripeness
    if category in ['ripe']:
        ripeness = 'Ready to harvest'
    elif category in ['unripe']:
        ripeness = 'Needs more time'
    else:
        ripeness = 'Past optimal harvest'
    
    return {
        'category': category,
        'confidence': probabilities[category],
        'probabilities': probabilities,
        'ripeness': ripeness,
        'message': f'{model_type.title()} demo: classified as {category} with {probabilities[category]:.3f} confidence. Ripeness: {ripeness}',
        'display_analysis': {
            'ripeness': ripeness,
            'confidence_level': 'High' if probabilities[category] > 0.8 else 'Medium',
            'recommendation': f'This pepper appears to be {category}. {ripeness}.'
        }
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Pepper Vision Backend API (Railway Demo)", "status": "running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "pepper-vision-backend-demo"}

@app.get("/model-status")
async def model_status():
    """Get the status of loaded AI models"""
    return {
        "anfis_loaded": True,
        "transfer_learning_loaded": True,
        "ensemble_available": True,
        "models_count": 5,
        "status": "Demo mode: Using simulated AI models for Railway deployment"
    }

@app.post("/predict")
async def predict_pepper(
    image: UploadFile = File(...),
    model_type: str = Form("ensemble")
):
    """Predict bell pepper category and ripeness"""
    try:
        # Save uploaded file
        file_id = str(uuid.uuid4())
        file_extension = os.path.splitext(image.filename)[1]
        file_path = os.path.join(UPLOAD_DIR, f"{file_id}_{image.filename}")
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        
        # Validate image
        try:
            with Image.open(file_path) as img:
                img.verify()
        except Exception:
            return JSONResponse({
                "status": "error",
                "message": "Invalid image file"
            }, status_code=400)
        
        # Get demo prediction
        result = predict_demo(file_path, model_type)
        
        return JSONResponse({
            "status": "success",
            "prediction": result,
            "file_path": f"/uploads/{os.path.basename(file_path)}",
            "model_used": model_type
        })
        
    except Exception as e:
        print(f"Error in prediction: {e}")
        return JSONResponse({
            "status": "error",
            "message": f"Failed to process image: {str(e)}"
        }, status_code=500)

@app.post("/predict-ensemble")
async def predict_ensemble_endpoint(image: UploadFile = File(...)):
    """Predict using ensemble method"""
    return await predict_pepper(image, "ensemble")

@app.post("/predict-transfer")
async def predict_transfer_endpoint(image: UploadFile = File(...)):
    """Predict using transfer learning"""
    return await predict_pepper(image, "transfer_learning")

@app.post("/predict-anfis")
async def predict_anfis_endpoint(image: UploadFile = File(...)):
    """Predict using ANFIS"""
    return await predict_pepper(image, "anfis")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("railway_main:app", host="0.0.0.0", port=8000, reload=True)