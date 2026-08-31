@echo off
echo Starting Smart HRMS Production Services...

REM Change to project directory
cd /d "C:\Users\Administrator\Documents\HRMS\smart_hrms"

REM Start Waitress server
echo Starting Waitress server...
start "HRMS-Waitress" cmd /k "set FLASK_ENV=production && python -m waitress --host=0.0.0.0 --port=80 --threads=8 wsgi:app"

REM Wait 5 seconds for server to start
timeout /t 5 /nobreak

REM Start Cloudflare tunnel
echo Starting Cloudflare tunnel...
start "HRMS-Tunnel" cmd /k "cloudflared tunnel --url http://localhost:80"

echo.
echo ✓ Production services started:
echo   - Waitress server: http://localhost:80
echo   - Cloudflare tunnel: connecting to smarthrms.online
echo.
echo Services are running in separate windows.
echo Close this window safely - services will continue running.
pause