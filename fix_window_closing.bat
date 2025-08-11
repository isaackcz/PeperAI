@echo off
echo ========================================
echo Fix: Command Window Closing Issue
echo ========================================
echo.
echo If run.bat closes immediately, this script provides solutions.
echo.

:: Set title for this window
title Pepper Vision - Window Closing Fix

echo PROBLEM: run.bat opens and closes immediately
echo.
echo COMMON CAUSES:
echo 1. Docker is not installed or running
echo 2. Script is run from wrong directory
echo 3. Missing project files
echo 4. System compatibility issues
echo.

echo IMMEDIATE SOLUTIONS:
echo ========================================
echo.
echo [Option 1] Run Diagnostics
echo This will check what's wrong:
echo   diagnose_startup_issues.bat
echo.
echo [Option 2] Check Device Compatibility
echo This will test your system:
echo   test_device_compatibility.bat
echo.
echo [Option 3] Manual Docker Commands
echo Run these commands one by one:
echo   docker --version
echo   docker-compose --version
echo   docker-compose up -d
echo.
echo [Option 4] Run with Error Catching
echo This keeps the window open to see errors:
echo.

echo Creating error-catching version of run.bat...
echo.

:: Create a version that catches errors
echo @echo off > run_with_errors.bat
echo echo Starting Pepper Vision with error catching... >> run_with_errors.bat
echo echo. >> run_with_errors.bat
echo echo Checking Docker... >> run_with_errors.bat
echo docker --version >> run_with_errors.bat
echo if errorlevel 1 goto docker_error >> run_with_errors.bat
echo echo. >> run_with_errors.bat
echo echo Starting containers... >> run_with_errors.bat
echo docker-compose up -d >> run_with_errors.bat
echo if errorlevel 1 goto compose_error >> run_with_errors.bat
echo echo. >> run_with_errors.bat
echo echo Success! Opening http://localhost:8080 >> run_with_errors.bat
echo start http://localhost:8080 >> run_with_errors.bat
echo goto end >> run_with_errors.bat
echo. >> run_with_errors.bat
echo :docker_error >> run_with_errors.bat
echo echo ERROR: Docker not found or not running >> run_with_errors.bat
echo echo Install Docker Desktop and start it >> run_with_errors.bat
echo goto end >> run_with_errors.bat
echo. >> run_with_errors.bat
echo :compose_error >> run_with_errors.bat
echo echo ERROR: Docker Compose failed >> run_with_errors.bat
echo echo Check: docker-compose logs >> run_with_errors.bat
echo goto end >> run_with_errors.bat
echo. >> run_with_errors.bat
echo :end >> run_with_errors.bat
echo echo. >> run_with_errors.bat
echo echo Press any key to exit... >> run_with_errors.bat
echo pause >> run_with_errors.bat

echo ✓ Created: run_with_errors.bat
echo.

echo STEP-BY-STEP TROUBLESHOOTING:
echo ========================================
echo.
echo 1. First, try running: run_with_errors.bat
echo    (This will show you exactly what's failing)
echo.
echo 2. If Docker is the issue:
echo    - Install Docker Desktop
    echo    - Start Docker Desktop and wait for it to load
echo    - Look for Docker whale icon in system tray
echo.
echo 3. If you're in wrong directory:
echo    - Navigate to the project folder
echo    - Look for backend/ and frontend/ folders
echo    - Run the script from there
echo.
echo 4. If ports are busy:
echo    - Close other applications using ports 8000, 8001, 8080
echo    - Or run: docker-compose down
echo.
echo 5. If system compatibility:
echo    - Run: test_device_compatibility.bat
echo    - Check if your system supports Docker
echo.
echo ALTERNATIVE STARTUP METHODS:
echo ========================================
echo.
echo Method 1 - Manual Docker:
echo   docker-compose down
echo   docker-compose up -d
echo   start http://localhost:8080
echo.
echo Method 2 - Development Mode:
echo   cd docker
echo   docker-compose -f docker-compose.dev.yml up -d
echo.
echo Method 3 - Oracle Cloud (if configured):
echo   docker-compose -f docker-compose.oracle.yml up -d
echo.
echo GETTING HELP:
echo ========================================
echo.
echo If none of these work:
echo 1. Run: diagnose_startup_issues.bat
echo 2. Check the output and error messages
echo 3. Look at: DEVICE_COMPATIBILITY_GUIDE.md
echo 4. Check Docker logs: docker-compose logs
echo.
echo Press any key to exit and try the solutions above...
pause