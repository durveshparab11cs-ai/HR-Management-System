@echo off
REM ============================================
REM HRMS ONE-CLICK STARTUP SCRIPT
REM Double-click this file to start the app
REM ============================================

echo.
echo ========================================
echo Starting Smart HRMS Application...
echo ========================================
echo.

REM Kill any existing Python processes
echo [1/4] Stopping any running instances...
taskkill /F /IM python.exe >nul 2>&1
timeout /t 2 /nobreak

REM Navigate to app directory
cd /d C:\Users\Administrator\Documents\HRMS\smart_hrms
if errorlevel 1 (
    echo ERROR: Cannot find app directory!
    pause
    exit /b 1
)

REM Clear Python cache
echo [2/4] Clearing cache...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d" >nul 2>&1

REM Ensure we're on the right Git commit
echo [3/4] Checking out working version...
git reset --hard 8e6e6c4 >nul 2>&1

REM Start the application
echo [4/4] Starting application on port 8000...
echo.
echo ========================================
echo Smart HRMS is starting...
echo Access at: https://192.168.0.5:8000
echo OR: https://smarthrms.online/
echo ========================================
echo.

REM Run with waitress on port 8000
python -m waitress --host=0.0.0.0 --port=8000 --threads=8 wsgi:app

REM If it crashes, show error and pause
if errorlevel 1 (
    echo.
    echo ERROR: Application failed to start
    echo Press any key to close...
    pause
    exit /b 1
)
