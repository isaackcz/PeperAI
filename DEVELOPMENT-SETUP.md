# 🚀 Pepper Vision AI - Optimized Development Setup

Your Docker development environment has been successfully refactored for **instant code changes** and **fast development cycles**! 

## ✅ What's Been Optimized

### 1. **Volume Mounts for Instant Changes**
- **Frontend**: `../frontend:/app` - All your React/Vite code changes reflect instantly
- **Backend**: `../backend:/app/backend` - All your FastAPI code changes reflect instantly
- **No more rebuilding** containers for code changes!

### 2. **Hot Reloading Enabled**
- **Frontend**: Vite dev server with instant browser updates
- **Backend**: Uvicorn with `--reload` flag for auto-restart on code changes

### 3. **Optimized Build Process**
- Development-specific `.dockerignore.dev` excludes source code from builds
- Only dependencies are copied during build (much faster!)
- Production Dockerfiles remain completely untouched

### 4. **Proper Port Configuration**
- **Frontend**: http://localhost:3000 (Vite dev server)
- **Backend**: http://localhost:8000 (FastAPI with auto-reload)
- **API Docs**: http://localhost:8000/docs

## 🎯 How to Use

### Quick Start (Recommended)
```bash
# Start development environment
./run-dev.bat

# Stop development environment  
./stop-dev.bat
```

### Manual Commands
```bash
# Build and start
docker-compose -f docker/docker-compose.dev.yml up --build

# Stop
docker-compose -f docker/docker-compose.dev.yml down

# View logs
docker-compose -f docker/docker-compose.dev.yml logs -f
```

## 🔧 Development Workflow

1. **Start the environment** with `./run-dev.bat`
2. **Edit your code** in `frontend/src/` or `backend/app/`
3. **See changes instantly** in the browser/API
4. **No rebuilding needed** for code changes!

## 📁 What Changed

### New/Optimized Files:
- `docker/.dockerignore.dev` - Development-specific exclusions
- `docker/build-dev.bat` - Optimized build script
- `docker/README-DEV.md` - Comprehensive development guide
- `docker-compose.dev.yml` - Already optimized (no changes needed)
- `Dockerfile.frontend.dev` - Already optimized (no changes needed)
- `Dockerfile.backend.dev` - Already optimized (no changes needed)

### Unchanged Files (Production):
- `docker-compose.yml` - Production environment
- `Dockerfile.frontend` - Production frontend
- `Dockerfile.backend` - Production backend

## 🚀 Performance Improvements

### Before:
- ❌ Full rebuild on every code change
- ❌ Slow development cycles
- ❌ Source code copied into images

### After:
- ✅ Instant code changes via volume mounts
- ✅ Hot reloading for both frontend and backend
- ✅ Fast builds (dependencies only)
- ✅ No rebuilding for code changes

## 🌐 Services Overview

| Service | Port | URL | Hot Reload |
|---------|------|-----|------------|
| Frontend (Vite) | 3000 | http://localhost:3000 | ✅ |
| Backend (FastAPI) | 8000 | http://localhost:8000 | ✅ |
| API Docs | 8000 | http://localhost:8000/docs | ✅ |

## 🔍 Troubleshooting

### If changes aren't reflecting:
```bash
# Check volume mounts
docker-compose -f docker/docker-compose.dev.yml exec frontend-dev ls -la /app
docker-compose -f docker/docker-compose.dev.yml exec backend-dev ls -la /app/backend
```

### If ports are in use:
```bash
# Find processes
netstat -ano | findstr :3000
netstat -ano | findstr :8000
```

### If you need a clean build:
```bash
# Use the optimized build script
./docker/build-dev.bat
```

## 📊 Development vs Production

| Feature | Development | Production |
|---------|-------------|------------|
| Hot Reload | ✅ | ❌ |
| Volume Mounts | ✅ | ❌ |
| Build Speed | Fast | Normal |
| Image Size | Smaller | Larger |
| Code Changes | Instant | Requires rebuild |

## 🎉 You're All Set!

Your development environment is now optimized for:
- **Instant code changes** without rebuilding
- **Hot reloading** for both frontend and backend
- **Fast development cycles** with minimal waiting
- **Production-ready** setup that remains untouched

Start coding with `./run-dev.bat` and enjoy the fast development experience! 🚀 