#!/usr/bin/env python3
"""
Working FastAPI server for Pepper Vision Backend
Avoids virtual environment issues and provides all necessary endpoints
"""

import os
import sys
import json
import random
import uuid
from pathlib import Path
from typing import Optional

# Try to import FastAPI, fallback to simple HTTP server if not available
try:
    from fastapi import FastAPI, File, UploadFile, Form
    from fastapi.staticfiles import StaticFiles
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    print("FastAPI not available, using simple HTTP server")
    FASTAPI_AVAILABLE = False

# Create uploads directory
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

if FASTAPI_AVAILABLE:
    app = FastAPI(title="Pepper Vision Backend", version="1.0.0")
    
    # Serve static files from uploads directory
    app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
    
    # Allow CORS for local frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",  # Vite dev server
            "http://localhost:8080",  # Production frontend
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8080",
            "*"  # Fallback for development
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Demo mode label mapping
    LABEL_MAPPING = {
        0: 'damaged',
        1: 'dried', 
        2: 'old',
        3: 'ripe',
        4: 'unripe'
    }
    
    @app.get("/")
    async def root():
        return {"message": "Pepper Vision Backend is running!", "status": "healthy"}
    
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "pepper-vision-backend", "demo_mode": True}
    
    @app.get("/model-status")
    async def model_status():
        """Get the status of AI models (demo mode)"""
        return {
            "anfis_loaded": True,  # Demo mode
            "transfer_learning_loaded": True,  # Demo mode
            "ensemble_available": True,  # Demo mode
            "models_count": len(LABEL_MAPPING),
            "status": "Demo mode: Using fallback models for testing"
        }
    
    def predict_with_demo(image_path: str, model_type: str = "ensemble") -> dict:
        """Demo prediction function"""
        categories = list(LABEL_MAPPING.values())
        category = random.choice(categories)
        
        # Different confidence ranges for different models
        if model_type == "transfer":
            confidence = random.uniform(0.7, 0.98)
        elif model_type == "anfis":
            confidence = random.uniform(0.6, 0.95)
        else:  # ensemble
            confidence = random.uniform(0.75, 0.96)
        
        # Create realistic probabilities
        probabilities = {}
        for cat in categories:
            if cat == category:
                probabilities[cat] = confidence
            else:
                probabilities[cat] = random.uniform(0.01, 0.3)
        
        return {
            'category': category,
            'confidence': confidence,
            'probabilities': probabilities,
            'message': f'{model_type.title()} demo: classified as {category} with {confidence:.3f} confidence'
        }
    
    @app.post("/predict")
    async def predict(
        image: UploadFile = File(...),
        region: Optional[str] = Form(None),
        model_type: Optional[str] = Form("ensemble")
    ):
        """Predict bell pepper category using AI models"""
        print(f"Received prediction request with model_type: {model_type}")
        
        # Save uploaded image locally
        file_id = str(uuid.uuid4())
        file_path = os.path.join(UPLOAD_DIR, f"{file_id}_{image.filename}")
        
        try:
            with open(file_path, "wb") as buffer:
                content = await image.read()
                buffer.write(content)
            print(f"Saved image to {file_path}")
        except Exception as e:
            print(f"Error saving image: {e}")
            return JSONResponse({"error": f"Failed to save image: {e}"}, status_code=500)
        
        # Get demo prediction
        ai_result = predict_with_demo(file_path, model_type)
        
        # Map AI category to defect result for compatibility
        defect_result = {
            'defect_type': ai_result['category'],
            'confidence': ai_result['confidence'],
            'probability': ai_result['confidence'],
            'features': ai_result['probabilities'],
            'message': ai_result['message'],
            'model_type': model_type
        }
        
        # Return response with both color grading and defect detection
        return JSONResponse({
            "is_bell_pepper": True,
            "ripeness": ai_result['category'],  # Use AI category as ripeness
            "freshness_score": int(ai_result['confidence'] * 100),
            "color": "auto",
            "size": "medium",
            "defects": [],
            "grade": "Grade A" if ai_result['confidence'] > 0.8 else "Grade B",
            "confidence": int(ai_result['confidence'] * 100),
            "freshness": "Excellent" if ai_result['confidence'] > 0.9 else "Good",
            "recommendation": f"This bell pepper is classified as {ai_result['category']} with {ai_result['confidence']:.1%} confidence.",
            "ai_defect_detection": defect_result
        })
    
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
            return JSONResponse({"error": f"Failed to save image: {e}"}, status_code=500)
        
        # Demo response - return the same image with a region
        region = [click_x - 50, click_y - 50, 100, 100]  # 100x100 region around click
        
        return JSONResponse({
            "cropped_image": f"/uploads/{file_id}_{image.filename}",
            "region": region
        })
    
    if __name__ == "__main__":
        print("🚀 Starting Pepper Vision Backend (Demo Mode)...")
        print("📍 Backend will be available at: http://localhost:8000")
        print("🔗 API Documentation: http://localhost:8000/docs")
        print("🫑 Demo mode: All AI predictions are simulated")
        print("=" * 50)
        
        uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")

else:
    # Fallback simple HTTP server
    from http.server import HTTPServer, BaseHTTPRequestHandler
    import urllib.parse
    
    class SimplePepperVisionHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/health":
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                response = {"status": "healthy", "service": "pepper-vision-backend", "demo_mode": True}
                self.wfile.write(json.dumps(response).encode())
            elif self.path == "/model-status":
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                response = {
                    "anfis_loaded": True,
                    "transfer_learning_loaded": True,
                    "ensemble_available": True,
                    "models_count": 5,
                    "status": "Demo mode: Using fallback models for testing"
                }
                self.wfile.write(json.dumps(response).encode())
            else:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                response = {"message": "Pepper Vision Backend is running!", "status": "healthy"}
                self.wfile.write(json.dumps(response).encode())
        
        def do_POST(self):
            if self.path == "/predict":
                # Simple demo prediction
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                categories = ['damaged', 'dried', 'old', 'ripe', 'unripe']
                category = random.choice(categories)
                confidence = random.uniform(0.7, 0.95)
                
                response = {
                    "is_bell_pepper": True,
                    "ripeness": category,
                    "freshness_score": int(confidence * 100),
                    "color": "auto",
                    "size": "medium",
                    "defects": [],
                    "grade": "Grade A" if confidence > 0.8 else "Grade B",
                    "confidence": int(confidence * 100),
                    "freshness": "Excellent" if confidence > 0.9 else "Good",
                    "recommendation": f"This bell pepper is classified as {category} with {confidence:.1%} confidence.",
                    "ai_defect_detection": {
                        "defect_type": category,
                        "confidence": confidence,
                        "probability": confidence,
                        "features": {cat: random.uniform(0.01, 0.3) for cat in categories},
                        "message": f"Demo: classified as {category} with {confidence:.3f} confidence",
                        "model_type": "ensemble"
                    }
                }
                self.wfile.write(json.dumps(response).encode())
            else:
                self.send_response(404)
                self.end_headers()
        
        def do_OPTIONS(self):
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
    
    if __name__ == "__main__":
        print("🚀 Starting Pepper Vision Backend (Simple HTTP Server)...")
        print("📍 Backend will be available at: http://localhost:8000")
        print("🫑 Demo mode: All AI predictions are simulated")
        print("=" * 50)
        
        server = HTTPServer(('localhost', 8000), SimplePepperVisionHandler)
        print("✅ Server started successfully!")
        print("🔄 Server is running... Press Ctrl+C to stop")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server stopped by user")
            server.server_close()