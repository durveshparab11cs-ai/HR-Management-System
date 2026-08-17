@echo off
REM Smart HRMS - One Click Startup Script
REM Double-click this file to start the application

cls
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║  Smart HRMS - Instant Startup                             ║
echo ║  Starting all services...                                  ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM Get the script directory
cd /d "%~dp0"

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.9+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Run PowerShell script
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start-server-now.ps1"

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to start application
    pause
    exit /b 1
)
