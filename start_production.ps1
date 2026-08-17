# PowerShell Script: Start Smart HRMS Production Environment
# Usage: .\start_production.ps1

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Starting Smart HRMS Production Server" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$flaskDir = "C:\Users\durve\Downloads\HR management system"
$nginxPath = "C:\nginx-1.27.0"
$domain = "smarthrms.tech"  # Change this to your domain

Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  Flask Dir: $flaskDir" -ForegroundColor Gray
Write-Host "  Nginx Path: $nginxPath" -ForegroundColor Gray
Write-Host "  Domain: $domain" -ForegroundColor Gray
Write-Host ""

# Step 1: Check if Flask is already running
Write-Host "[1/3] Checking Flask process..." -ForegroundColor Green
$flaskProcess = Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*run.py*" }
if ($flaskProcess) {
    Write-Host "✓ Flask is already running (PID: $($flaskProcess.Id))" -ForegroundColor Green
} else {
    Write-Host "Starting Flask (production mode)..." -ForegroundColor Yellow
    Push-Location $flaskDir
    Start-Process python -ArgumentList "run.py" -NoNewWindow
    Start-Sleep -Seconds 3
    Pop-Location
    Write-Host "✓ Flask started" -ForegroundColor Green
}

# Step 2: Check if Nginx is already running
Write-Host "[2/3] Checking Nginx process..." -ForegroundColor Green
$nginxProcess = Get-Process nginx -ErrorAction SilentlyContinue
if ($nginxProcess) {
    Write-Host "✓ Nginx is already running (PID: $($nginxProcess.Id))" -ForegroundColor Green
} else {
    Write-Host "Starting Nginx..." -ForegroundColor Yellow
    Push-Location $nginxPath
    Start-Process .\nginx.exe
    Start-Sleep -Seconds 2
    Pop-Location
    Write-Host "✓ Nginx started" -ForegroundColor Green
}

# Step 3: Verify services
Write-Host "[3/3] Verifying services..." -ForegroundColor Green
$flaskUp = Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*run.py*" }
$nginxUp = Get-Process nginx -ErrorAction SilentlyContinue

if ($flaskUp -and $nginxUp) {
    Write-Host "✓ Flask is running" -ForegroundColor Green
    Write-Host "✓ Nginx is running" -ForegroundColor Green
} else {
    if (-not $flaskUp) { Write-Host "✗ Flask not running" -ForegroundColor Red }
    if (-not $nginxUp) { Write-Host "✗ Nginx not running" -ForegroundColor Red }
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "Production Server Ready!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Access your application:" -ForegroundColor Yellow
Write-Host "  HTTPS: https://$domain" -ForegroundColor Cyan
Write-Host "  HTTP: http://$domain (redirects to HTTPS)" -ForegroundColor Cyan
Write-Host ""
Write-Host "Logs:" -ForegroundColor Yellow
Write-Host "  Flask: Shown in terminal" -ForegroundColor Gray
Write-Host "  Nginx: $nginxPath\logs\access.log" -ForegroundColor Gray
Write-Host "  Nginx Errors: $nginxPath\logs\error.log" -ForegroundColor Gray
Write-Host ""
Write-Host "To stop services:" -ForegroundColor Yellow
Write-Host "  Stop-Process -Name nginx" -ForegroundColor Gray
Write-Host "  Stop-Process -Name python" -ForegroundColor Gray
Write-Host ""
