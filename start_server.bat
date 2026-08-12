@echo off
REM Smart HRMS Production Server - Windows Batch Launcher
REM Run this file to start the server with HTTPS on port 443

setlocal enabledelayedexpansion

cd /d "%~dp0"

echo.
echo ════════════════════════════════════════════════════════════
echo   Smart HRMS Production Server - HTTPS
echo ════════════════════════════════════════════════════════════
echo.
echo Starting Flask with SSL on port 443...
echo URL: https://192.168.0.5
echo.

REM Check if certificates exist
if not exist "C:\Smart_HRMS\certs\smart-hrms.crt" (
    echo ERROR: Certificate not found at C:\Smart_HRMS\certs\smart-hrms.crt
    pause
    exit /b 1
)

if not exist "C:\Smart_HRMS\certs\smart-hrms.key" (
    echo ERROR: Private key not found at C:\Smart_HRMS\certs\smart-hrms.key
    pause
    exit /b 1
)

echo ✓ Certificates verified
echo.

REM Run production server
python wsgi.py

pause
