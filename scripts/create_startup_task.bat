@echo off
echo Creating Windows startup task for Smart HRMS...

REM Create scheduled task to run at startup
schtasks /create /tn "SmartHRMS-Production" /tr "C:\Users\Administrator\Documents\HRMS\smart_hrms\scripts\start_production.bat" /sc onstart /ru SYSTEM /rl HIGHEST /f

if %errorlevel%==0 (
    echo ✓ Startup task created successfully!
    echo Smart HRMS will auto-start on Windows boot.
) else (
    echo ❌ Failed to create startup task. Run as Administrator.
)

echo.
echo To test the task manually:
echo   schtasks /run /tn "SmartHRMS-Production"
echo.
echo To remove the task:
echo   schtasks /delete /tn "SmartHRMS-Production" /f
pause