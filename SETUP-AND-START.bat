@echo off
REM Smart HRMS - Complete Setup and Start
REM This script will install Docker if needed, then start the application

cls
color 0a
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║  Smart HRMS - Complete Setup                              ║
echo ║  Installing Docker and Starting Application               ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM Check if Python is installed
echo [1/3] Checking Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo OK - Python is installed
echo.

REM Check if Docker is installed
echo [2/3] Checking Docker...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Docker not found. Installing...
    echo Please run as Administrator for Docker installation
    echo.
    powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\install-docker.ps1"
    if %errorlevel% neq 0 (
        echo.
        echo ERROR: Docker installation failed
        echo Please install manually: https://www.docker.com/products/docker-desktop
        pause
        exit /b 1
    )
)
echo OK - Docker is available
echo.

REM Start the application
echo [3/3] Starting Smart HRMS...
echo.
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start-server-now.ps1"

pause
