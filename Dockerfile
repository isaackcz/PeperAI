# Lightweight build for Railway deployment
FROM python:3.9-slim as backend

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Create minimal requirements for Railway (demo mode)
RUN echo "fastapi==0.104.1" > /app/requirements.txt && \
    echo "uvicorn[standard]==0.24.0" >> /app/requirements.txt && \
    echo "python-multipart==0.0.6" >> /app/requirements.txt && \
    echo "requests==2.31.0" >> /app/requirements.txt && \
    echo "aiofiles==23.2.1" >> /app/requirements.txt && \
    echo "Pillow==10.0.1" >> /app/requirements.txt && \
    echo "numpy==1.24.3" >> /app/requirements.txt && \
    echo "python-dotenv==1.0.0" >> /app/requirements.txt

# Install minimal dependencies (no PyTorch/ML libraries)
RUN pip install --no-cache-dir -r requirements.txt

# Copy only the lightweight main file for Railway
COPY railway_main.py /app/main.py

# Create necessary directories
RUN mkdir -p /app/uploads

# Set environment variables
ENV UPLOAD_DIR=/app/uploads
ENV PYTHONPATH=/app

# Expose port
EXPOSE $PORT

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Start command
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}