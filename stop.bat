@echo off
echo ========================================
echo Pepper Vision Grade - Docker Shutdown
echo ========================================
echo.
echo This script will stop all Docker containers and clean up.
echo.
echo Press any key to continue...
pause >nul

:: Set title for this window
title Pepper Vision - Docker Shutdown

echo.
echo [1/3] Stopping Docker Containers...
echo.

:: Check if Docker is available
docker --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not available
    echo Please ensure Docker Desktop is running
    pause
    exit /b 1
) else (
    echo ✓ Docker found
)

:: Stop Docker containers
echo Stopping Docker containers...
docker-compose down
if errorlevel 1 (
    echo WARNING: Error stopping containers or no containers running
) else (
    echo ✓ Docker containers stopped successfully
)

:: Remove any orphaned containers
echo Removing orphaned containers...
docker-compose down --remove-orphans >nul 2>&1

echo.
echo [2/3] Cleaning up Docker resources...
echo.

:: Clean up unused Docker resources (optional)
echo Cleaning up unused Docker images and volumes...
docker system prune -f >nul 2>&1
echo ✓ Docker cleanup completed

echo.
echo [3/3] Cleaning up temporary files...
echo.

:: Clean up uploads directory but preserve structure
if exist "backend\app\uploads" (
    echo Cleaning uploads directory...
    for /f %%i in ('dir /b "backend\app\uploads\*" 2^>nul') do (
        if not "%%i"==".gitkeep" (
            del /q "backend\app\uploads\%%i" >nul 2>&1
        )
    )
    echo ✓ Uploads cleaned (preserved .gitkeep)
)

:: Clean up any remaining cache files
if exist "backend\__pycache__" (
    echo Cleaning Python cache...
    rmdir /s /q "backend\__pycache__" >nul 2>&1
)

if exist "backend\app\__pycache__" (
    rmdir /s /q "backend\app\__pycache__" >nul 2>&1
)

if exist "backend\app\utils\__pycache__" (
    rmdir /s /q "backend\app\utils\__pycache__" >nul 2>&1
)

echo ✓ Cache cleanup completed

echo.
echo ========================================
echo Docker Shutdown Complete!
echo ========================================
echo.
echo All Docker services have been stopped:
echo ✓ Frontend container (port 8080)
echo ✓ Backend API container (port 8000)
echo ✓ Models service container (port 8001)
echo ✓ Docker resources cleaned
echo ✓ Temporary files cleaned
echo.
echo To restart the system: run.bat
echo To view container status: docker-compose ps
echo To view logs: docker-compose logs
echo.
echo Press any key to exit...
pause >nul