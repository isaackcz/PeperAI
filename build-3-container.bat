@echo off
echo ========================================
echo Bell Pepper Classification System
echo 3-Container Production Build
echo ========================================
echo.

echo This script builds and runs the 3-container architecture:
echo - Models Service (AI/ML): Port 8001
echo - Backend API (FastAPI): Port 8000  
echo - Frontend (React): Port 8080
echo.

echo [1/4] Stopping any existing containers...
docker-compose down
echo.

echo [2/4] Building all containers...
docker-compose build --no-cache
if %ERRORLEVEL% neq 0 (
    echo ERROR: Build failed!
    pause
    exit /b 1
)
echo.

echo [3/4] Starting all services...
docker-compose up -d
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to start services!
    pause
    exit /b 1
)
echo.

echo [4/4] Waiting for all services to be healthy...
echo This may take up to 2 minutes for models to load...
echo.

echo Waiting for Models Service (this takes the longest)...
timeout /t 15 /nobreak >nul
:check_models
curl -s http://localhost:8001/health >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Models service still loading, please wait...
    timeout /t 10 /nobreak >nul
    goto check_models
)
echo ✓ Models Service is ready!

echo Checking Backend API...
:check_backend
curl -s http://localhost:8000/health >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Backend API not ready, waiting...
    timeout /t 5 /nobreak >nul
    goto check_backend
)
echo ✓ Backend API is ready!

echo Checking Frontend...
:check_frontend
curl -s http://localhost:8080 >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Frontend not ready, waiting...
    timeout /t 3 /nobreak >nul
    goto check_frontend
)
echo ✓ Frontend is ready!

echo.
echo ========================================
echo 🎉 SUCCESS! All services are running!
echo ========================================
echo.
echo Access your application:
echo 🌐 Frontend:       http://localhost:8080
echo 🔧 Backend API:    http://localhost:8000
echo 🤖 Models Service: http://localhost:8001
echo.
echo Container Status:
docker-compose ps
echo.
echo Useful Commands:
echo - View logs:        docker-compose logs
echo - Stop services:    docker-compose down
echo - Restart service:  docker-compose restart [service-name]
echo - Check health:     curl http://localhost:8000/health
echo.
echo For development mode, use: build-3-container-dev.bat
echo.
pause