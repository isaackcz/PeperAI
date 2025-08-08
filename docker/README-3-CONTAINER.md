# Bell Pepper Classification - 3-Container Docker Architecture

This document describes the new 3-container Docker architecture for the Bell Pepper Classification system.

## Architecture Overview

The system is now split into 3 separate containers for better scalability, maintainability, and resource management:

### 1. Frontend Container (`frontend`)
- **Port**: 8080 (production) / 3000 (development)
- **Technology**: React + Vite + TypeScript
- **Purpose**: User interface for uploading images and viewing classification results
- **Dependencies**: Backend container

### 2. Backend API Container (`backend`)
- **Port**: 8000
- **Technology**: FastAPI + Python
- **Purpose**: 
  - Handle file uploads
  - Serve static files
  - Proxy requests to models service
  - Provide REST API endpoints
- **Dependencies**: Models container

### 3. Models Service Container (`models`)
- **Port**: 8001
- **Technology**: FastAPI + Python + TensorFlow + ANFIS
- **Purpose**:
  - Load and manage AI/ML models (ANFIS, Transfer Learning)
  - Perform image classification
  - Handle model training and evaluation
  - Provide model-specific API endpoints
- **Dependencies**: None (base service)

## Container Communication

```
Frontend (8080) → Backend API (8000) → Models Service (8001)
```

- **Frontend** communicates with **Backend API** via HTTP requests
- **Backend API** forwards prediction requests to **Models Service**
- **Models Service** processes images and returns predictions

## Quick Start

### Production Deployment

```bash
# Navigate to docker directory
cd docker

# Build and start all services
docker-compose up --build

# Or run in background
docker-compose up --build -d
```

### Development Mode

```bash
# Navigate to docker directory
cd docker

# Start development environment with hot reload
docker-compose -f docker-compose.dev.yml up --build
```

### Stop Services

```bash
# Stop all containers
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

## Service URLs

### Production
- **Frontend**: http://localhost:8080
- **Backend API**: http://localhost:8000
- **Models Service**: http://localhost:8001

### Development
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Models Service**: http://localhost:8001

## API Endpoints

### Backend API (Port 8000)
- `GET /` - Root endpoint
- `GET /health` - Health check
- `POST /upload` - Upload image file
- `POST /predict` - Predict pepper grade
- `POST /predict-uploaded` - Predict from uploaded file
- `GET /models/status` - Get models status
- `POST /models/reload` - Reload models

### Models Service (Port 8001)
- `GET /health` - Health check
- `POST /predict` - Direct prediction endpoint
- `GET /models/status` - Model status and info
- `POST /models/reload` - Reload all models

## Health Checks

All containers include health checks:
- **Models Service**: 40s start period (model loading time)
- **Backend API**: 20s start period
- **Frontend**: 10s start period

Containers start in dependency order with health check conditions.

## Volume Mounts

### Production
- `../backend/models:/app/models` (Models container)
- `../backend/training_output:/app/training_output` (Models container)
- `../backend/app/uploads:/app/backend/app/uploads` (Backend container)

### Development
- Additional volume mounts for hot reload
- Frontend source code mounted for live updates

## Environment Variables

### Models Service
- `MODEL_PATH=/app/models`
- `TRAINING_OUTPUT_DIR=/app/training_output`
- `SYNTHETIC_DATA_DIR=/app/synthetic_data`
- `DATA_DIR=/app/data`

### Backend API
- `UPLOAD_DIR=/app/backend/app/uploads`
- `MODELS_SERVICE_URL=http://models:8001`

### Frontend
- `VITE_API_URL=http://localhost:8000` (development)

## Troubleshooting

### Check Container Status
```bash
docker-compose ps
```

### View Logs
```bash
# All services
docker-compose logs

# Specific service
docker-compose logs models
docker-compose logs backend
docker-compose logs frontend
```

### Restart Specific Service
```bash
docker-compose restart models
```

### Rebuild Specific Service
```bash
docker-compose up --build models
```

### Check Health Status
```bash
# Models service health
curl http://localhost:8001/health

# Backend API health
curl http://localhost:8000/health
```

## Model Management

### Check Model Status
```bash
curl http://localhost:8001/models/status
```

### Reload Models
```bash
curl -X POST http://localhost:8001/models/reload
```

### Add New Models
1. Place model files in `../backend/models/`
2. Update model loading logic in `model_service.py`
3. Restart models container: `docker-compose restart models`

## Performance Considerations

### Resource Allocation
- **Models Service**: High CPU/Memory (AI/ML processing)
- **Backend API**: Low CPU/Memory (proxy service)
- **Frontend**: Low CPU/Memory (static files)

### Scaling
- Models service can be scaled horizontally for load balancing
- Backend API can be scaled for high request volumes
- Frontend is stateless and easily scalable

### Optimization
- Models are loaded once at startup
- Persistent volumes for model storage
- Health checks prevent premature traffic routing

## Security

- Services communicate via internal Docker network
- Only necessary ports are exposed
- No direct external access to models service
- File uploads are validated and sandboxed

## Migration from Previous Architecture

The new architecture maintains API compatibility with the previous single-container setup. Existing frontend code should work without modifications.

### Key Changes
- Models processing moved to separate service
- Backend API now acts as a proxy
- Improved separation of concerns
- Better resource utilization
- Enhanced scalability

## Development Workflow

1. **Frontend Development**: Use `docker-compose -f docker-compose.dev.yml up frontend-dev`
2. **Backend Development**: Modify `docker/backend_api.py` and restart backend service
3. **Models Development**: Modify model files and restart models service
4. **Full Stack**: Use development compose file for hot reload on all services

For more information, see the main project README and individual service documentation.