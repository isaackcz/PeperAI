# Multi-stage build for Railway deployment
FROM python:3.9-slim as backend

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy backend requirements and install dependencies
COPY docker/backend-requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application
COPY backend/ /app/backend/
COPY datasets/ /app/datasets/

# Create necessary directories
RUN mkdir -p /app/backend/app/uploads \
    && mkdir -p /app/backend/models \
    && mkdir -p /app/backend/training_output \
    && mkdir -p /app/backend/synthetic_data \
    && mkdir -p /app/backend/data

# Set environment variables
ENV UPLOAD_DIR=/app/backend/app/uploads
ENV MODEL_PATH=/app/backend/models
ENV TRAINING_OUTPUT_DIR=/app/backend/training_output
ENV SYNTHETIC_DATA_DIR=/app/backend/synthetic_data
ENV DATA_DIR=/app/backend/data
ENV MODELS_SERVICE_URL=http://localhost:8001
ENV PYTHONPATH=/app/backend

# Expose port
EXPOSE $PORT

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$PORT/health || exit 1

# Start command
CMD cd /app/backend/app && uvicorn main:app --host 0.0.0.0 --port $PORT