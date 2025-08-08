@echo off
echo ========================================
echo Pepper Vision Grade - Docker Only
echo ========================================
echo.
echo This script will start the entire system using Docker containers only.
echo.
echo Press any key to continue...
pause >nul

:: Set title for this window
title Pepper Vision - Docker Startup

:: Check if we're in the right directory
if not exist "backend" (
    echo ERROR: Please run this script from the project root directory
    echo Current directory: %CD%
    pause
    exit /b 1
)

echo.
echo [1/3] Checking Docker availability...
echo.

:: Check if Docker is available
docker --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not installed or not running
    echo Please install Docker Desktop and ensure it's running
    echo This system now requires Docker for operation
    pause
    exit /b 1
) else (
    echo ✓ Docker found
)

:: Check if Docker Compose is available
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker Compose is not available
    echo Please ensure Docker Compose is installed
    pause
    exit /b 1
) else (
    echo ✓ Docker Compose found
)

echo.
echo [2/3] Starting Docker containers...
echo.

:: Stop any existing containers
echo Stopping any existing containers...
docker-compose down >nul 2>&1

:: Start Docker containers
echo Starting Docker containers...
docker-compose up -d
if errorlevel 1 (
    echo ERROR: Failed to start Docker containers
    echo Please check Docker logs: docker-compose logs
    pause
    exit /b 1
) else (
    echo ✓ Docker containers started successfully
)

echo.
echo [3/3] Waiting for services to be ready...
echo.

:: Wait for services to start
echo Waiting for services to initialize...
timeout /t 10 /nobreak >nul

:: Check if services are running
echo Checking service health...
docker-compose ps

echo.
echo ========================================
echo System Startup Complete!
echo ========================================
echo.
echo All services are running in Docker containers:
echo • Frontend: http://localhost:8080
echo • Backend API: http://localhost:8000
echo • Models Service: http://localhost:8001
echo • API Documentation: http://localhost:8000/docs
echo.
echo To stop all services: docker-compose down
echo To view logs: docker-compose logs
echo To restart: docker-compose restart
echo.
echo Press any key to open the frontend in your browser...
pause >nul

:: Open frontend in default browser
start http://localhost:8080

echo.
echo Frontend opened in browser!
echo.
echo You can now:
echo 1. Upload bell pepper images
echo 2. Select AI models (Transfer Learning recommended)
echo 3. Get real-time classification results
echo.
echo Keep this window open to monitor the system.
echo Press Ctrl+C to stop monitoring (containers will keep running).
echo.

:: Keep the window open
pause