#!/usr/bin/env python3
"""
Railway entry point for Pepper Vision AI
Imports the FastAPI app from the backend module
"""

import sys
import os
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Import the FastAPI app from backend
try:
    from backend.app.main import app
except ImportError as e:
    print(f"Error importing backend app: {e}")
    # Fallback to a simple FastAPI app
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    
    app = FastAPI(title="Pepper Vision AI", version="1.0.0")
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.get("/")
    async def root():
        return {"message": "Pepper Vision AI Backend", "status": "running"}
    
    @app.get("/health")
    async def health():
        return {"status": "healthy", "service": "pepper-vision-backend"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)