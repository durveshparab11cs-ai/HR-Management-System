@echo off
REM Smart HRMS - Emergency Fix and Start
REM Run this on Windows Server to diagnose and fix all issues

cd /d "%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0EMERGENCY-FIX.ps1"

pause
