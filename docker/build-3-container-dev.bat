@echo off
echo ========================================
echo Bell Pepper Classification System
echo 3-Container Development Build Script
echo ========================================
echo.

echo Building 3-container development environment...
echo - Frontend Dev Container (React + Vite + Hot Reload)
echo - Backend API Dev Container (FastAPI + Hot Reload)
echo - Models Service Container (AI/ML Models)
echo.

cd /d "%~dp0"

echo [1/4] Stopping existing containers...
docker-compose -f docker-compose.dev.yml down
echo.

echo [2/4] Building development containers...
docker-compose -f docker-compose.dev.yml build --no-cache
if %ERRORLEVEL% neq 0 (
    echo ERROR: Build failed!
    pause
    exit /b 1
)
echo.

echo [3/4] Starting development services...
docker-compose -f docker-compose.dev.yml up -d
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to start services!
    pause
    exit /b 1
)
echo.

echo [4/4] Waiting for services to be ready...
echo Checking Models Service...
timeout /t 15 /nobreak >nul
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

echo Checking Frontend Dev Server...
:check_frontend
curl -s http://localhost:3000 >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Frontend dev server not ready yet, waiting...
    timeout /t 5 /nobreak >nul
    goto check_frontend
)
echo ✓ Frontend Dev Server is ready!

echo.
echo ========================================
echo 🎉 SUCCESS! Development environment is running!
echo ========================================
echo.
echo Development URLs:
echo - Frontend Dev:   http://localhost:3000 (Hot Reload)
echo - Backend API:    http://localhost:8000 (Hot Reload)
echo - Models Service: http://localhost:8001
echo.
echo Container Status:
docker-compose -f docker-compose.dev.yml ps
echo.
echo Development Features:
echo - Frontend: Hot reload enabled for React/Vite
echo - Backend: Hot reload enabled for FastAPI
echo - Models: Full AI/ML capabilities
echo.
echo To view logs: docker-compose -f docker-compose.dev.yml logs
echo To stop:      docker-compose -f docker-compose.dev.yml down
echo.
pause