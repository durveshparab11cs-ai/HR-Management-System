@echo off
REM ============================================================================
REM  Smart HRMS - Server Startup Script (Windows)
REM  
REM  Double-click this file to start the server
REM  Server will auto-restart on crash
REM ============================================================================

title Smart HRMS Production Server
color 0A

echo.
echo ================================================================================
echo  Smart HRMS - Production Server
echo ================================================================================
echo.
echo Starting server...
echo Please wait while the application initializes...
echo.

cd /d "%~dp0smart_hrms"

python run_production.py

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Server failed to start
    echo Check the logs directory for details
    echo.
    pause
)
