#!/usr/bin/env python3
"""
Simple FastAPI server for testing
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()

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

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "pepper-vision-backend"}

@app.get("/test")
async def test():
    return {"message": "Backend is working!"}

if __name__ == "__main__":
    print("Starting simple FastAPI server...")
    uvicorn.run(app, host="127.0.0.1", port=8000)