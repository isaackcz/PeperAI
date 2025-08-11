@echo off
echo ========================================
echo Bell Pepper Vision Grade - Docker Setup Check
echo ========================================
echo.

set "all_good=1"

:: Check Docker
echo Checking Docker installation...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not installed or not running
    echo    Please install Docker Desktop from https://docker.com/products/docker-desktop
    echo    Make sure Docker Desktop is running
    set "all_good=0"
) else (
    for /f "tokens=3" %%i in ('docker --version 2^>^&1') do set docker_version=%%i
    echo ✓ Docker !docker_version! is installed
)

:: Check Docker Compose
echo Checking Docker Compose installation...
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker Compose is not available
    echo    Docker Compose should come with Docker Desktop
    set "all_good=0"
) else (
    for /f "tokens=3" %%i in ('docker-compose --version 2^>^&1') do set compose_version=%%i
    echo ✓ Docker Compose !compose_version! is installed
)

:: Check Docker daemon
echo Checking Docker daemon...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker daemon is not running
    echo    Please start Docker Desktop
    set "all_good=0"
) else (
    echo ✓ Docker daemon is running
)

:: Check available disk space
echo Checking available disk space...
for /f "tokens=3" %%i in ('dir /-c ^| find "bytes free"') do set free_space=%%i
if !free_space! lss 5000000000 (
    echo ⚠️  Warning: Low disk space (less than 5GB free)
    echo    Docker images require significant disk space
) else (
    echo ✓ Sufficient disk space available
)

:: Check project files
echo Checking project files...
if not exist "docker-compose.yml" (
    echo ❌ docker-compose.yml not found
    echo    Please run this script from the project root directory
    set "all_good=0"
) else (
    echo ✓ docker-compose.yml found
)

if not exist "docker\Dockerfile.backend" (
    echo ❌ Backend Dockerfile not found
    set "all_good=0"
) else (
    echo ✓ Backend Dockerfile found
)

if not exist "docker\Dockerfile.frontend" (
    echo ❌ Frontend Dockerfile not found
    set "all_good=0"
) else (
    echo ✓ Frontend Dockerfile found
)

if not exist "docker\Dockerfile.models" (
    echo ❌ Models Dockerfile not found
    set "all_good=0"
) else (
    echo ✓ Models Dockerfile found
)

echo.
echo ========================================
if "%all_good%"=="1" (
    echo ✅ Setup Check Complete - All requirements met!
    echo.
    echo You can now start the system with:
    echo   run.bat
    echo.
    echo Or manually with:
    echo   docker-compose up --build
) else (
    echo ❌ Setup Check Failed - Please fix the issues above
    echo.
    echo Common solutions:
    echo   1. Install Docker Desktop from https://docker.com
    echo   2. Start Docker Desktop application
    echo   3. Ensure you're in the project root directory
    echo   4. Free up disk space if needed
)
echo ========================================
echo.
echo Press any key to exit...
pause