@echo off
REM Smart HRMS - Start Now
REM Just run this file on the Windows Server

cd /d "%~dp0"

echo.
echo ================================================
echo   Smart HRMS - Starting Application
echo ================================================
echo.

REM Run PowerShell script
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0RUN-ON-SERVER.ps1"

if %errorlevel% neq 0 (
    echo.
    echo ERROR occurred. Check the output above.
    pause
)
