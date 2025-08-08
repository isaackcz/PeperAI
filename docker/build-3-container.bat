@echo off
echo ========================================
echo Bell Pepper Classification System
echo 3-Container Docker Build Script
echo ========================================
echo.

echo Building 3-container architecture...
echo - Frontend Container (React + Vite)
echo - Backend API Container (FastAPI Proxy)
echo - Models Service Container (AI/ML Models)
echo.

cd /d "%~dp0"

echo [1/4] Stopping existing containers...
docker-compose down
echo.

echo [2/4] Building containers...
docker-compose build --no-cache
if %ERRORLEVEL% neq 0 (
    echo ERROR: Build failed!
    pause
    exit /b 1
)
echo.

echo [3/4] Starting services...
docker-compose up -d
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to start services!
    pause
    exit /b 1
)
echo.

echo [4/4] Waiting for services to be ready...
echo Checking Models Service...
timeout /t 10 /nobreak >nul
:check_models
curl -s http://localhost:8001/health >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Models service not ready yet, waiting...
    timeout /t 5 /nobreak >nul
    goto check_models
)
echo ✓ Models Service is ready!

echo Checking Backend API...
:check_backend
curl -s http://localhost:8000/health >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Backend API not ready yet, waiting...
    timeout /t 3 /nobreak >nul
    goto check_backend
)
echo ✓ Backend API is ready!

echo Checking Frontend...
:check_frontend
curl -s http://localhost:8080 >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Frontend not ready yet, waiting...
    timeout /t 3 /nobreak >nul
    goto check_frontend
)
echo ✓ Frontend is ready!

echo.
echo ========================================
echo 🎉 SUCCESS! All services are running!
echo ========================================
echo.
echo Service URLs:
echo - Frontend:      http://localhost:8080
echo - Backend API:   http://localhost:8000
echo - Models Service: http://localhost:8001
echo.
echo Container Status:
docker-compose ps
echo.
echo To view logs: docker-compose logs
echo To stop:      docker-compose down
echo.
pause