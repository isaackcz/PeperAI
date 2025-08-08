# Pepper Vision AI - Development Environment

This directory contains the Docker configuration for the Pepper Vision AI development environment, optimized for fast development with hot reloading.

## 🚀 Quick Start

### Option 1: Use the provided scripts (Recommended)
```bash
# Start development environment
./run-dev.bat

# Stop development environment
./stop-dev.bat
```

### Option 2: Manual Docker commands
```bash
# Build and start development containers
docker-compose -f docker/docker-compose.dev.yml up --build

# Stop development containers
docker-compose -f docker/docker-compose.dev.yml down
```

## 🏗️ Architecture

The development environment consists of two main services:

### Frontend (Vite + React)
- **Port**: 3000
- **URL**: http://localhost:3000
- **Hot Reload**: ✅ Enabled
- **Volume Mounts**: 
  - `../frontend:/app` (source code)
  - `/app/node_modules` (dependencies)

### Backend (FastAPI + Uvicorn)
- **Port**: 8000
- **URL**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Hot Reload**: ✅ Enabled with `--reload`
- **Volume Mounts**:
  - `../backend:/app/backend` (source code)
  - Data directories (uploads, models, etc.)

## 🔧 Development Features

### ✅ Hot Reloading
- **Frontend**: Vite dev server with instant updates
- **Backend**: Uvicorn with `--reload` flag for auto-restart

### ✅ Volume Mounts
- Source code changes reflect instantly without rebuilding
- No need to rebuild containers for code changes
- Dependencies are preserved in containers

### ✅ Optimized Builds
- Development-specific `.dockerignore` excludes unnecessary files
- Faster build times for development
- Production Dockerfiles remain untouched

### ✅ Network Communication
- All services on the same Docker network (`bell-pepper-network`)
- Frontend can communicate with backend via `http://localhost:8000`

## 📁 File Structure

```
docker/
├── docker-compose.dev.yml      # Development environment
├── docker-compose.yml          # Production environment
├── Dockerfile.frontend.dev     # Frontend development image
├── Dockerfile.backend.dev      # Backend development image
├── Dockerfile.frontend         # Frontend production image
├── Dockerfile.backend          # Backend production image
├── .dockerignore.dev           # Development-specific exclusions
├── build-dev.bat               # Optimized build script
└── README-DEV.md              # This file
```

## 🛠️ Development Workflow

1. **Start Development Environment**:
   ```bash
   ./run-dev.bat
   ```

2. **Make Code Changes**:
   - Edit files in `frontend/src/` or `backend/app/`
   - Changes reflect instantly in the browser/API

3. **View Logs**:
   ```bash
   docker-compose -f docker/docker-compose.dev.yml logs -f
   ```

4. **Stop Environment**:
   ```bash
   ./stop-dev.bat
   ```

## 🔍 Troubleshooting

### Port Already in Use
If ports 3000 or 8000 are already in use:
```bash
# Find processes using the ports
netstat -ano | findstr :3000
netstat -ano | findstr :8000

# Kill the processes or change ports in docker-compose.dev.yml
```

### Container Build Issues
```bash
# Clean build (removes cache)
docker-compose -f docker/docker-compose.dev.yml build --no-cache

# Or use the optimized build script
./docker/build-dev.bat
```

### Volume Mount Issues
If changes aren't reflecting:
```bash
# Check if volumes are mounted correctly
docker-compose -f docker/docker-compose.dev.yml exec frontend-dev ls -la /app
docker-compose -f docker/docker-compose.dev.yml exec backend-dev ls -la /app/backend
```

### Node Modules Issues
If frontend dependencies are missing:
```bash
# Rebuild frontend container
docker-compose -f docker/docker-compose.dev.yml build frontend-dev
```

## 🌐 Environment Variables

### Frontend Environment
- `VITE_API_URL=http://localhost:8000` - Backend API URL
- `NODE_ENV=development` - Development mode

### Backend Environment
- `PYTHONPATH=/app` - Python path
- `ENVIRONMENT=development` - Development mode
- Various data directory paths for uploads, models, etc.

## 📊 Performance Optimizations

### Build Optimizations
- Development `.dockerignore` excludes source code (mounted as volumes)
- Only dependencies are copied during build
- Faster subsequent builds due to Docker layer caching

### Runtime Optimizations
- Volume mounts for instant code changes
- Hot reloading for both frontend and backend
- Minimal container overhead

## 🔄 Production vs Development

| Feature | Development | Production |
|---------|-------------|------------|
| Hot Reload | ✅ | ❌ |
| Volume Mounts | ✅ | ❌ |
| Source Code in Image | ❌ | ✅ |
| Build Time | Fast | Slower |
| Image Size | Smaller | Larger |
| Security | Development | Production |

## 📝 Notes

- The development environment is completely separate from production
- Production Dockerfiles remain untouched
- All development optimizations are in separate files
- The main `docker-compose.yml` is for production use
- Development uses `docker-compose.dev.yml`

## 🆘 Support

If you encounter issues:
1. Check the troubleshooting section above
2. View container logs: `docker-compose -f docker/docker-compose.dev.yml logs`
3. Ensure Docker Desktop is running
4. Verify ports 3000 and 8000 are available 