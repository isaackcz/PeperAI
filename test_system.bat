@echo off
echo ========================================
echo Pepper Vision - Docker System Test
echo ========================================
echo.
echo Testing Docker system components...
echo.

:: Test Docker
echo [1/3] Testing Docker...
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker not found - Please install Docker Desktop
    echo Visit: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
) else (
    echo ✅ Docker found
    docker --version
)

:: Test Docker Compose
echo.
echo [2/3] Testing Docker Compose...
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Compose not found
    pause
    exit /b 1
) else (
    echo ✅ Docker Compose found
    docker-compose --version
)

:: Test Docker containers
echo.
echo [3/3] Testing Docker Containers...
echo Building and testing containers...
docker-compose build >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker build failed
    echo Run 'docker-compose build' to see detailed errors
    pause
    exit /b 1
) else (
    echo ✅ Docker containers built successfully
)

:: Test container startup
echo Testing container startup...
docker-compose up -d >nul 2>&1
if errorlevel 1 (
    echo ❌ Container startup failed
    echo Run 'docker-compose up' to see detailed errors
) else (
    echo ✅ Containers started successfully
    
    :: Wait a moment for services to initialize
    timeout /t 5 >nul
    
    :: Check container health
    echo Checking container health...
    docker-compose ps
    
    :: Stop containers after test
    echo Stopping test containers...
    docker-compose down >nul 2>&1
    echo ✅ Test containers stopped
)

echo.
echo ========================================
echo Docker System Test Complete!
echo ========================================
echo.
echo If all tests passed, you can start the system with:
echo   run.bat
echo.
echo To view detailed logs:
echo   docker-compose logs
echo.
echo Press any key to exit...
pause >nul