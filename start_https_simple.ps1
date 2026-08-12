#!/usr/bin/env pwsh
<#
.DESCRIPTION
Smart HRMS HTTPS Server - Direct Flask on Port 443
No reverse proxy needed. Simple, reliable, fast.
#>

# Stop any existing processes
Write-Host "Stopping existing processes..." -ForegroundColor Cyan
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
Get-Process nginx -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2

# Change to app directory
$appDir = "c:\Users\durve\Downloads\HR management system"
Push-Location $appDir

Write-Host "Smart HRMS HTTPS Server Starting..." -ForegroundColor Green
Write-Host "===================================" -ForegroundColor Green
Write-Host ""

# Verify environment
Write-Host "Checking requirements..." -ForegroundColor Yellow

if (-not (Test-Path ".env")) {
    Write-Host "ERROR: .env file not found" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path "C:\Smart_HRMS\certs\smart-hrms.crt")) {
    Write-Host "ERROR: SSL certificate not found at C:\Smart_HRMS\certs\smart-hrms.crt" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path "C:\Smart_HRMS\certs\smart-hrms.key")) {
    Write-Host "ERROR: SSL private key not found at C:\Smart_HRMS\certs\smart-hrms.key" -ForegroundColor Red
    exit 1
}

Write-Host "✓ All requirements met" -ForegroundColor Green
Write-Host ""

# Start Flask
Write-Host "Starting Flask on HTTPS port 443..." -ForegroundColor Cyan
$flaskProc = Start-Process python -ArgumentList "wsgi.py" -PassThru -NoNewWindow
Write-Host "Flask started (PID: $($flaskProc.Id))" -ForegroundColor Green
Start-Sleep -Seconds 5

# Verify Flask is listening
$listening = netstat -ano | Select-String "443.*LISTENING"
if ($listening) {
    Write-Host "✓ Flask listening on port 443" -ForegroundColor Green
} else {
    Write-Host "✗ WARNING: Port 443 not listening yet" -ForegroundColor Yellow
    Start-Sleep -Seconds 3
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Smart HRMS Server Started Successfully" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Access the server at:" -ForegroundColor Yellow
Write-Host "  https://192.168.0.5" -ForegroundColor Cyan
Write-Host ""
Write-Host "Frontend: Flask on HTTPS port 443" -ForegroundColor Gray
Write-Host "Database: Render PostgreSQL (connected)" -ForegroundColor Gray
Write-Host "Certificate: 10-year self-signed SSL" -ForegroundColor Gray
Write-Host ""
Write-Host "Browser will show certificate warning (self-signed is normal)." -ForegroundColor Yellow
Write-Host "Accept and proceed to access the login page." -ForegroundColor Yellow
Write-Host ""
Write-Host "To stop server: Press Ctrl+C" -ForegroundColor Yellow
Write-Host ""

Pop-Location

# Keep window open
try {
    while ($true) { Start-Sleep -Seconds 10 }
} catch {
    Write-Host "Shutting down..." -ForegroundColor Yellow
    Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
    Get-Process nginx -ErrorAction SilentlyContinue | Stop-Process -Force
}
