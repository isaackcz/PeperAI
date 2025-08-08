# Lightweight build for Railway deployment
FROM python:3.9-alpine as backend

# Install system dependencies and build tools
RUN apk add --no-cache \
    curl \
    gcc \
    g++ \
    musl-dev \
    linux-headers \
    python3-dev \
    jpeg-dev \
    zlib-dev \
    freetype-dev \
    lcms2-dev \
    openjpeg-dev \
    tiff-dev \
    tk-dev \
    tcl-dev \
    libffi-dev \
    openssl-dev \
    blas-dev \
    lapack-dev \
    gfortran \
    pkgconfig

# Set working directory
WORKDIR /app

# Upgrade pip and install wheel first
RUN pip install --upgrade pip setuptools wheel

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
COPY start.sh /app/start.sh

# Make startup script executable
RUN chmod +x /app/start.sh

# Create necessary directories
RUN mkdir -p /app/uploads

# Set environment variables
ENV UPLOAD_DIR=/app/uploads
ENV PYTHONPATH=/app

# Expose port (Railway will map this to the dynamic PORT)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start command
CMD ["/app/start.sh"]