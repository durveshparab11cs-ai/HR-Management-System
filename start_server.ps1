#!/usr/bin/env pwsh
<#
.DESCRIPTION
Smart HRMS HTTPS Server Startup
Simple, direct HTTPS on port 443 - no Nginx needed
#>

param(
    [switch]$NoWait
)

# Kill any existing processes
Write-Host "Stopping any existing Flask processes..." -ForegroundColor Yellow
Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match "run_https|wsgi" } | Stop-Process -Force
Start-Sleep -Seconds 2

# Go to project directory
cd "c:\Users\durve\Downloads\HR management system"

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║                                                              ║" -ForegroundColor Green
Write-Host "║           Smart HRMS HTTPS Server Starting...               ║" -ForegroundColor Green
Write-Host "║                                                              ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""

# Verify environment
Write-Host "Checking requirements..." -ForegroundColor Yellow

$checks = @(
    @{ name = ".env file"; path = ".env" },
    @{ name = "SSL Certificate"; path = "C:\Smart_HRMS\certs\smart-hrms.crt" },
    @{ name = "SSL Private Key"; path = "C:\Smart_HRMS\certs\smart-hrms.key" },
    @{ name = "run_https.py"; path = "run_https.py" }
)

$allOK = $true
foreach ($check in $checks) {
    if (Test-Path $check.path) {
        Write-Host "  ✅ $($check.name)" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $($check.name) - NOT FOUND" -ForegroundColor Red
        $allOK = $false
    }
}

if (-not $allOK) {
    Write-Host ""
    Write-Host "❌ Missing required files. Cannot start server." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Starting Flask..." -ForegroundColor Cyan
python run_https.py

if (-not $NoWait) {
    Write-Host ""
    Write-Host "To stop, press Ctrl+C"
}
