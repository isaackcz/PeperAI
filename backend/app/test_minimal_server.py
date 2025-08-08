#!/usr/bin/env python3
"""
Minimal FastAPI server for testing backend connection
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="Pepper Vision Backend Test", version="1.0.0")

# Allow CORS for local frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Pepper Vision Backend Test is running!", "status": "healthy"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "pepper-vision-backend-test"}

@app.get("/model-status")
async def model_status():
    return {
        "anfis_loaded": True,
        "transfer_learning_loaded": True,
        "ensemble_available": True,
        "models_count": 5,
        "status": "Test mode: Using mock models"
    }

if __name__ == "__main__":
    print("🚀 Starting Pepper Vision Backend Test...")
    print("📍 Server will be available at: http://localhost:8000")
    print("🔗 Health check: http://localhost:8000/health")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")