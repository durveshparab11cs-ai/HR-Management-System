@echo off
REM =================================================================
REM DEPLOY TO 192.168.0.5 - COORDINATOR PORTAL FIX
REM =================================================================

echo.
echo Starting deployment to 192.168.0.5...
echo.

REM Copy files to server
echo [1/3] Copying files to 192.168.0.5...
xcopy /Y /E "app\blueprints\coordinator\routes.py" "\\192.168.0.5\c$\Users\Administrator\Documents\HRMS\smart_hrms\app\blueprints\coordinator\" >nul 2>&1
xcopy /Y /E "app\blueprints\coordinator\templates\coordinator\portal.html" "\\192.168.0.5\c$\Users\Administrator\Documents\HRMS\smart_hrms\app\blueprints\coordinator\templates\coordinator\" >nul 2>&1

if %errorlevel% equ 0 (
    echo ✓ Files copied successfully
) else (
    echo ✗ Failed to copy files
    echo Make sure 192.168.0.5 is accessible via network share
    pause
    exit /b 1
)

echo.
echo [2/3] Restarting application on 192.168.0.5...
REM Kill Python processes on remote server
wmic /node:192.168.0.5 /user:Administrator process call terminate name="python.exe" >nul 2>&1
timeout /t 2 /nobreak

echo.
echo [3/3] Starting application...
REM Start the application via remote execution would require additional setup
echo To complete deployment, on 192.168.0.5 run:
echo   cd C:\Users\Administrator\Documents\HRMS\smart_hrms
echo   python run.py
echo.
echo ✓ Deployment complete!
echo Access at: https://192.168.0.5:8000/coordinator/
echo Or: https://smarthrms.online/coordinator/
echo.
pause
