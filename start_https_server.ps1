#!/usr/bin/env pwsh
<#
.DESCRIPTION
Production HTTPS server startup for Smart HRMS
Starts Flask backend on port 5000 + Nginx reverse proxy on ports 80/443
#>

# Stop any existing processes
Write-Host "Stopping existing Flask/Nginx processes..." -ForegroundColor Cyan
Get-Process nginx -ErrorAction SilentlyContinue | Stop-Process -Force
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2

# Change to app directory
$appDir = "c:\Users\durve\Downloads\HR management system"
Push-Location $appDir

# Verify environment
Write-Host "Checking environment..." -ForegroundColor Cyan
if (-not (Test-Path ".env")) {
    Write-Host "ERROR: .env file not found" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path "C:\Smart_HRMS\certs\smart-hrms.crt")) {
    Write-Host "ERROR: SSL certificate not found at C:\Smart_HRMS\certs\smart-hrms.crt" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path "C:\Smart_HRMS\nginx\nginx.exe")) {
    Write-Host "ERROR: Nginx not found at C:\Smart_HRMS\nginx\nginx.exe" -ForegroundColor Red
    exit 1
}

# Start Flask backend (HTTP on 5000)
Write-Host "Starting Flask backend on port 5000..." -ForegroundColor Cyan
$flaskProc = Start-Process python -ArgumentList "wsgi.py" -PassThru -NoNewWindow
Write-Host "Flask process started (PID: $($flaskProc.Id))" -ForegroundColor Green
Start-Sleep -Seconds 3

# Verify Flask is listening
$flaskCheck = netstat -ano | Select-String "5000.*LISTENING"
if ($flaskCheck) {
    Write-Host "✓ Flask listening on port 5000" -ForegroundColor Green
} else {
    Write-Host "WARNING: Flask may not be listening on port 5000" -ForegroundColor Yellow
}

# Start Nginx reverse proxy (HTTPS on 443, HTTP redirect on 80)
Write-Host "Starting Nginx reverse proxy on ports 80/443..." -ForegroundColor Cyan
$nginxProc = Start-Process "C:\Smart_HRMS\nginx\nginx.exe" -PassThru -NoNewWindow
Write-Host "Nginx process started (PID: $($nginxProc.Id))" -ForegroundColor Green
Start-Sleep -Seconds 2

# Verify Nginx is listening
$nginxCheck443 = netstat -ano | Select-String "443.*LISTENING"
$nginxCheck80 = netstat -ano | Select-String "80.*LISTENING"
if ($nginxCheck443) {
    Write-Host "✓ Nginx listening on port 443 (HTTPS)" -ForegroundColor Green
} else {
    Write-Host "ERROR: Nginx not listening on port 443" -ForegroundColor Red
}
if ($nginxCheck80) {
    Write-Host "✓ Nginx listening on port 80 (HTTP redirect)" -ForegroundColor Green
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Smart HRMS Server Started Successfully" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Access the server at:" -ForegroundColor Yellow
Write-Host "  https://192.168.0.5" -ForegroundColor Cyan
Write-Host ""
Write-Host "Backend: Flask on http://127.0.0.1:5000" -ForegroundColor Gray
Write-Host "Proxy:   Nginx on https://192.168.0.5 (ports 80/443)" -ForegroundColor Gray
Write-Host "Database: Render PostgreSQL (connected)" -ForegroundColor Gray
Write-Host ""
Write-Host "To stop, run: Stop-Process -Name nginx,python -Force" -ForegroundColor Yellow
Write-Host ""

Pop-Location

# Keep window open
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
try {
    while ($true) { Start-Sleep -Seconds 10 }
} catch {
    Write-Host "`nShutting down..." -ForegroundColor Yellow
    Get-Process nginx -ErrorAction SilentlyContinue | Stop-Process -Force
    Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
}
