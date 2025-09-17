@echo off
REM AI Casino Docker Startup Script for Windows
REM Sequential startup with health checks

setlocal enabledelayedexpansion

echo 🎰 Starting AI Casino System with Docker...

REM Function to wait for service health
:wait_for_service
set service_name=%1
set max_attempts=30
set attempt=1

echo ⏳ Waiting for %service_name% to be healthy...

:health_check_loop
docker-compose ps %service_name% | findstr "healthy" >nul 2>&1
if !errorlevel! equ 0 (
    echo ✅ %service_name% is healthy!
    goto :eof
)

echo    Attempt !attempt!/%max_attempts% - %service_name% not ready yet...
timeout /t 10 /nobreak >nul 2>&1
set /a attempt=!attempt!+1

if !attempt! leq %max_attempts% goto health_check_loop

echo ❌ %service_name% failed to become healthy after %max_attempts% attempts
exit /b 1

REM Check if Docker is running
:check_docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not installed or not running
    exit /b 1
)

docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Compose is not installed
    exit /b 1
)

echo ✅ Docker and Docker Compose are available
goto :eof

REM Cleanup previous containers
:cleanup_containers
echo 🧹 Cleaning up previous containers...
docker-compose down --remove-orphans >nul 2>&1
docker system prune -f --volumes >nul 2>&1
echo ✅ Cleanup completed
goto :eof

REM Build images
:build_images
echo 🔨 Building Docker images...
docker-compose build --no-cache --parallel
if errorlevel 1 (
    echo ❌ Failed to build images
    exit /b 1
)
echo ✅ Images built successfully
goto :eof

REM Main execution
echo 📋 Pre-flight checks...
call :check_docker
if errorlevel 1 exit /b 1

echo 🧹 Preparation phase...
call :cleanup_containers

echo 🔨 Build phase...
call :build_images
if errorlevel 1 exit /b 1

echo 🚀 Starting services in sequence...

REM Step 1: Start Redis
echo 1️⃣ Starting Redis database...
docker-compose up -d redis
if errorlevel 1 (
    echo ❌ Failed to start Redis
    exit /b 1
)
call :wait_for_service redis
if errorlevel 1 exit /b 1

REM Step 2: Start Backend
echo 2️⃣ Starting Go backend service...
docker-compose up -d backend
if errorlevel 1 (
    echo ❌ Failed to start backend
    exit /b 1
)
call :wait_for_service backend
if errorlevel 1 exit /b 1

REM Step 3: Start Scraper and Frontend
echo 3️⃣ Starting scraper and frontend services...
docker-compose up -d scraper frontend
if errorlevel 1 (
    echo ❌ Failed to start scraper or frontend
    exit /b 1
)
call :wait_for_service frontend
if errorlevel 1 exit /b 1

echo 🎉 All services are running successfully!
echo.
echo 📊 Service Status:
docker-compose ps

echo.
echo 🌐 Access URLs:
echo   Frontend: http://localhost:3000
echo   Backend API: http://localhost:8080
echo   Redis: localhost:6379

echo.
echo 📝 Useful Commands:
echo   View logs: docker-compose logs -f [service_name]
echo   Stop all: docker-compose down
echo   Restart service: docker-compose restart [service_name]
echo   View status: docker-compose ps

pause