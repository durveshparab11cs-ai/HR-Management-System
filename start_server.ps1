# Smart HRMS Production Server - PowerShell Launcher

Write-Host ""
Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "   Smart HRMS Production Server - HTTPS" -ForegroundColor Green
Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""

# Check certificates
$cert = "C:\Smart_HRMS\certs\smart-hrms.crt"
$key = "C:\Smart_HRMS\certs\smart-hrms.key"

if (-not (Test-Path $cert)) {
    Write-Host "ERROR: Certificate not found: $cert" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $key)) {
    Write-Host "ERROR: Private key not found: $key" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Certificates verified" -ForegroundColor Green
Write-Host ""
Write-Host "Starting Flask HTTPS server..." -ForegroundColor Cyan
Write-Host ""
Write-Host "Access: https://192.168.0.5" -ForegroundColor Green
Write-Host ""

# Run production server
python wsgi.py
