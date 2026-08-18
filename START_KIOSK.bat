@echo off
REM START COORDINATOR KIOSK
REM Run this file to start the Flask app and access the kiosk

echo.
echo =====================================
echo Starting Coordinator Attendance Kiosk
echo =====================================
echo.

REM Kill any existing Python processes
taskkill /F /IM python.exe /T 2>nul

REM Wait a moment
timeout /t 2 /nobreak

REM Start Flask
echo Starting Flask app...
echo.
python run.py

echo.
echo If Flask started, open browser and go to:
echo https://192.168.0.5:8000/coordinator/
echo.
pause
