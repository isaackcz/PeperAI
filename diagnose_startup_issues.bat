@echo off
echo ========================================
echo Pepper Vision - Startup Diagnostics
echo ========================================
echo.
echo This script will help diagnose why run.bat might be failing.
echo.

:: Set title for this window
title Pepper Vision - Diagnostics

echo [1/6] System Information
echo ========================================
echo Current Directory: %CD%
echo User: %USERNAME%
echo Computer: %COMPUTERNAME%
echo Date/Time: %DATE% %TIME%
echo.

echo [2/6] Checking Project Structure
echo ========================================
if exist "backend" (
    echo ✓ backend folder found
) else (
    echo ❌ backend folder missing - you might be in wrong directory
)

if exist "frontend" (
    echo ✓ frontend folder found
) else (
    echo ❌ frontend folder missing
)

if exist "docker-compose.yml" (
    echo ✓ docker-compose.yml found
) else (
    echo ❌ docker-compose.yml missing
)

if exist "run.bat" (
    echo ✓ run.bat found
) else (
    echo ❌ run.bat missing
)
echo.

echo [3/6] Docker Installation Check
echo ========================================
echo Checking Docker...
docker --version 2>&1
if errorlevel 1 (
    echo ❌ Docker not found or not running
    echo.
    echo SOLUTION:
    echo 1. Install Docker Desktop from: https://www.docker.com/products/docker-desktop
    echo 2. Start Docker Desktop
    echo 3. Wait for Docker to fully initialize
) else (
    echo ✓ Docker is available
)
echo.

echo Checking Docker Compose...
docker-compose --version 2>&1
if errorlevel 1 (
    echo ❌ Docker Compose not found
) else (
    echo ✓ Docker Compose is available
)
echo.

echo [4/6] Docker Service Status
echo ========================================
echo Checking if Docker daemon is running...
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker daemon is not running
    echo Please start Docker Desktop and wait for it to fully load
) else (
    echo ✓ Docker daemon is running
)
echo.

echo [5/6] Port Availability Check
echo ========================================
echo Checking if required ports are available...
netstat -an | findstr ":8000" >nul
if errorlevel 1 (
    echo ✓ Port 8000 is available
) else (
    echo ⚠️  Port 8000 is in use (Backend)
)

netstat -an | findstr ":8001" >nul
if errorlevel 1 (
    echo ✓ Port 8001 is available
) else (
    echo ⚠️  Port 8001 is in use (Models)
)

netstat -an | findstr ":8080" >nul
if errorlevel 1 (
    echo ✓ Port 8080 is available
) else (
    echo ⚠️  Port 8080 is in use (Frontend)
)
echo.

echo [6/6] System Resources
echo ========================================
echo Available Memory:
wmic computersystem get TotalPhysicalMemory /value | findstr "="
echo.
echo CPU Information:
wmic cpu get Name /value | findstr "="
echo.

echo ========================================
echo DIAGNOSTIC COMPLETE
echo ========================================
echo.
echo If you found issues above:
echo 1. Fix Docker installation/startup issues first
echo 2. Free up ports if they're in use
echo 3. Ensure you're in the correct project directory
echo 4. Try running: test_device_compatibility.bat
echo 5. If still failing, check: docker-compose logs
echo.
echo Common Solutions:
echo • Restart Docker Desktop
echo • Run as Administrator if needed
echo • Ensure Windows features (Hyper-V/WSL2) are enabled
echo • Check antivirus isn't blocking Docker
echo.
echo Press any key to exit...
pause