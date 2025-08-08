# Multi-stage build: Frontend
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy frontend package files
COPY frontend/package*.json ./

# Install frontend dependencies
RUN npm ci

# Copy frontend source code
COPY frontend/ ./

# Build frontend
RUN npm run build

# Backend stage
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Upgrade pip and install wheel first
RUN pip install --upgrade pip setuptools wheel

# Copy requirements from backend
COPY docker/backend-requirements.txt /app/requirements.txt

# Install full dependencies for complete AI functionality
RUN pip install --no-cache-dir -r requirements.txt

# Copy the full backend application
COPY backend/app/ /app/
COPY backend/app/main.py /app/main.py
COPY test_railway.py /app/test_railway.py
COPY start.sh /app/start.sh
COPY start_fullstack.sh /app/start_fullstack.sh
COPY test_start.sh /app/test_start.sh

# Copy built frontend files from frontend-builder stage
COPY --from=frontend-builder /app/frontend/dist /app/static

# Make startup scripts executable
RUN chmod +x /app/start.sh /app/start_fullstack.sh /app/test_start.sh

# Copy datasets for training (if needed)
COPY datasets/ /app/datasets/

# Create necessary directories
RUN mkdir -p /app/uploads \
    && mkdir -p /app/models \
    && mkdir -p /app/training_output \
    && mkdir -p /app/synthetic_data \
    && mkdir -p /app/data

# Set environment variables
ENV UPLOAD_DIR=/app/uploads
ENV PYTHONPATH=/app
ENV MODEL_PATH=/app/models
ENV TRAINING_OUTPUT_DIR=/app/training_output
ENV SYNTHETIC_DATA_DIR=/app/synthetic_data
ENV DATA_DIR=/app/data

# Expose port (Railway will map this to the dynamic PORT)
EXPOSE 8080

# Health check removed for Railway compatibility
# Railway has its own health checking mechanism

# Start command
CMD ["/app/start.sh"]