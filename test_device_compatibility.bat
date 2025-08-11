@echo off
echo ========================================
echo    Device Compatibility Test
echo ========================================
echo.

echo 🔍 Checking system architecture...
echo Architecture: %PROCESSOR_ARCHITECTURE%
echo Processor: %PROCESSOR_IDENTIFIER%
echo.

echo 🐳 Checking Docker availability...
docker --version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Docker is available
    docker --version
) else (
    echo ❌ Docker is not available or not in PATH
    echo Please install Docker Desktop from https://docker.com
    goto :end
)
echo.

echo 🔧 Checking Docker platform support...
docker buildx version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Docker Buildx is available (multi-platform support)
    docker buildx ls
) else (
    echo ⚠️  Docker Buildx not available (limited platform support)
)
echo.

echo 📊 Checking system resources...
echo Memory:
wmic computersystem get TotalPhysicalMemory /format:value | findstr "="
echo.
echo CPU Cores:
wmic cpu get NumberOfCores /format:value | findstr "="
echo.

echo 🧪 Testing Docker build capability...
echo Testing basic Docker functionality...
docker run --rm hello-world >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Docker can run containers successfully
) else (
    echo ❌ Docker cannot run containers
    echo Please check Docker Desktop is running and WSL2 is enabled
)
echo.

echo 🎯 Recommended configuration for your device:
if "%PROCESSOR_ARCHITECTURE%"=="AMD64" (
    echo - Platform: linux/amd64
    echo - Use: docker-compose -f docker-compose.oracle.yml up --build
    echo - For better performance, ensure 8GB+ RAM available for Docker
) else if "%PROCESSOR_ARCHITECTURE%"=="ARM64" (
    echo - Platform: linux/arm64
    echo - Use: docker-compose -f docker-compose.oracle.yml up --build
    echo - Native ARM64 performance expected
) else (
    echo - Platform: Auto-detect
    echo - May need manual platform specification
)
echo.

echo 🚀 Quick start commands:
echo 1. Full system: run.bat
echo 2. Oracle deployment: docker-compose -f docker-compose.oracle.yml up -d
echo 3. Development mode: docker\build-dev.bat
echo.

echo 📚 For detailed troubleshooting, see:
echo - DEVICE_COMPATIBILITY_GUIDE.md
echo - DEVELOPMENT-SETUP.md
echo - ORACLE_CLOUD_DEPLOYMENT_GUIDE.md
echo.

:end
echo ========================================
echo Test completed. Press any key to exit.
pause >nul