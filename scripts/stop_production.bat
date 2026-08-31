@echo off
echo Stopping Smart HRMS Production Services...

REM Kill Waitress processes
echo Stopping Waitress server...
taskkill /f /im python.exe /fi "WINDOWTITLE eq HRMS-Waitress*" 2>nul

REM Kill Cloudflared processes  
echo Stopping Cloudflare tunnel...
taskkill /f /im cloudflared.exe 2>nul

echo.
echo ✓ Production services stopped.
pause