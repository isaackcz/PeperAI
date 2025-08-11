@echo off
echo ========================================
echo Pepper Vision Grade - Docker Only
echo ========================================
echo.
echo This script will start the entire system using Docker containers only.
echo.
echo IMPORTANT: If this window closes immediately, there might be an error.
echo Check the error messages below before the window closes.
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
echo Checking Docker installation...
docker --version 2>&1
if errorlevel 1 (
    echo.
    echo ❌ ERROR: Docker is not installed or not running
    echo.
    echo SOLUTION:
    echo 1. Install Docker Desktop from: https://www.docker.com/products/docker-desktop
    echo 2. Start Docker Desktop and wait for it to fully load
    echo 3. Ensure Docker is running (check system tray icon)
    echo 4. Run this script again
    echo.
    echo Press any key to exit...
    pause
    exit /b 1
) else (
    echo ✓ Docker found and running
)

:: Check if Docker Compose is available
echo Checking Docker Compose...
docker-compose --version 2>&1
if errorlevel 1 (
    echo.
    echo ❌ ERROR: Docker Compose is not available
    echo.
    echo SOLUTION:
    echo Docker Compose should come with Docker Desktop.
    echo If you're using an older version, please update Docker Desktop.
    echo.
    echo Press any key to exit...
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
docker-compose down 2>&1
echo.

:: Start Docker containers with detailed output
echo Starting Docker containers (this may take a few minutes for first run)...
echo.
docker-compose up -d
if errorlevel 1 (
    echo.
    echo ❌ ERROR: Failed to start Docker containers
    echo.
    echo TROUBLESHOOTING:
    echo 1. Check detailed logs below:
    echo.
    docker-compose logs --tail=20
    echo.
    echo 2. Common solutions:
    echo    - Ensure Docker Desktop has enough memory (4GB+ recommended)
    echo    - Check if ports 8000, 8001, 8080 are available
    echo    - Try: docker system prune -f (to clean up)
    echo    - Restart Docker Desktop
    echo.
    echo 3. For device compatibility issues, run: test_device_compatibility.bat
    echo.
    echo Press any key to exit...
    pause
    exit /b 1
) else (
    echo ✓ Docker containers started successfully
)

echo.
echo [3/3] Waiting for services to be ready...
echo.

:: Wait for services to start
echo Waiting for services to initialize (this may take 30-60 seconds)...
echo.
timeout /t 15 /nobreak >nul

:: Check if services are running
echo Checking service health...
docker-compose ps
echo.

:: Verify services are actually responding
echo Verifying service connectivity...
echo Testing backend service...
curl -f http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Backend service not ready yet, waiting longer...
    timeout /t 15 /nobreak >nul
    curl -f http://localhost:8000/health >nul 2>&1
    if errorlevel 1 (
        echo ❌ Backend service failed to start properly
        echo Check logs: docker-compose logs backend
    ) else (
        echo ✓ Backend service is ready
    )
) else (
    echo ✓ Backend service is ready
)

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
echo.
echo ========================================
echo TROUBLESHOOTING TIPS:
echo ========================================
echo If services fail to start:
echo 1. Check Docker Desktop is running and has enough resources
echo 2. Ensure ports 8000, 8001, 8080 are not in use
echo 3. Run: test_device_compatibility.bat
echo 4. Check logs: docker-compose logs
echo 5. Clean restart: docker-compose down && docker system prune -f
echo.
echo Press any key to open the frontend in your browser...
pause >nul

:: Test if frontend is accessible before opening browser
echo Testing frontend accessibility...
curl -f http://localhost:8080 >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Frontend not ready, waiting a bit more...
    timeout /t 10 /nobreak >nul
    curl -f http://localhost:8080 >nul 2>&1
    if errorlevel 1 (
        echo ❌ Frontend failed to start. Check logs: docker-compose logs frontend
        echo You can still try opening: http://localhost:8080
    )
)

:: Open frontend in default browser
start http://localhost:8080

echo.
echo ✓ Frontend opened in browser!
echo.
echo 🌶️  PEPPER VISION GRADE SYSTEM READY!
echo.
echo Available services:
echo • Frontend: http://localhost:8080
echo • Backend API: http://localhost:8000
echo • Models Service: http://localhost:8001
echo • API Documentation: http://localhost:8000/docs
echo.
echo You can now:
echo 1. Upload bell pepper images
echo 2. Select AI models (Transfer Learning recommended)
echo 3. Get real-time classification results
echo.
echo IMPORTANT:
echo • Keep this window open to monitor the system
echo • To stop all services: docker-compose down
echo • To view logs: docker-compose logs
echo • To restart: docker-compose restart
echo.
echo Press any key to continue monitoring (or Ctrl+C to exit)...
pause >nul

echo.
echo System is running! You can close this window safely.
echo The Docker containers will continue running in the background.
echo.
echo To stop the system later, run: docker-compose down
echo.
echo Press any key to exit this monitoring window...
pause