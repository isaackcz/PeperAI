@echo off
title Pepper Vision AI - Development Build
color 0A

echo.
echo ========================================
echo    PEPPER VISION AI - DEVELOPMENT BUILD
echo ========================================
echo.

:: Backup original .dockerignore
if exist .dockerignore (
    echo [1/4] Backing up original .dockerignore...
    copy .dockerignore .dockerignore.backup
)

:: Use development .dockerignore
echo [2/4] Using development .dockerignore...
copy .dockerignore.dev .dockerignore

:: Build development containers
echo [3/4] Building development containers...
docker-compose -f docker/docker-compose.dev.yml build --no-cache

:: Restore original .dockerignore
echo [4/4] Restoring original .dockerignore...
if exist .dockerignore.backup (
    copy .dockerignore.backup .dockerignore
    del .dockerignore.backup
) else (
    del .dockerignore
)

echo.
echo ========================================
echo    DEVELOPMENT BUILD COMPLETE!
echo ========================================
echo.
echo To start the development environment:
echo docker-compose -f docker/docker-compose.dev.yml up
echo.
echo Or use the run-dev.bat script
echo.
pause 