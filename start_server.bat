@echo off
REM Smart HRMS HTTPS Server Startup
REM Simple direct HTTPS on port 443

title Smart HRMS Server
color 0A

echo.
echo ============================================================
echo           Smart HRMS HTTPS Server Starting
echo ============================================================
echo.

cd /d "%~dp0"

REM Kill any existing Python processes running Flask
taskkill /F /IM python.exe /FI "WINDOWTITLE eq Smart HRMS*" 2>nul
timeout /t 2 /nobreak > nul

REM Check requirements
if not exist .env (
    color 0C
    echo ERROR: .env file not found
    pause
    exit /b 1
)

if not exist "C:\Smart_HRMS\certs\smart-hrms.crt" (
    color 0C
    echo ERROR: SSL certificate not found
    pause
    exit /b 1
)

REM Start Flask
echo.
echo Starting Flask on HTTPS port 443...
echo.
python run_https.py

pause
