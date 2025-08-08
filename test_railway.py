from fastapi import FastAPI
import os

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello Railway!", "port": os.environ.get("PORT", "8000")}

@app.get("/health")
async def health():
    return {"status": "ok"}