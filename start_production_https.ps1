# Smart HRMS Production HTTPS Server
# Runs Flask with Gunicorn and SSL on port 443

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║   Smart HRMS Production Server - HTTPS (Direct Flask)     ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""

$cert = "C:\Smart_HRMS\certs\smart-hrms.crt"
$key = "C:\Smart_HRMS\certs\smart-hrms.key"

# Verify certificates exist
if (-not (Test-Path $cert) -or -not (Test-Path $key)) {
    Write-Host "ERROR: SSL certificates not found!" -ForegroundColor Red
    Write-Host "Expected: $cert" -ForegroundColor Red
    Write-Host "Expected: $key" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Certificates found" -ForegroundColor Green
Write-Host "✓ Starting Flask HTTPS server on port 443..." -ForegroundColor Green
Write-Host ""
Write-Host "Access: https://192.168.0.5" -ForegroundColor Cyan
Write-Host ""

# Run production Flask with SSL
python -c @"
import os
os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_DEBUG'] = '0'

from wsgi import app

print("\n" + "="*60)
print("Server Status: RUNNING")
print("="*60)
print("URL: https://192.168.0.5")
print("Port: 443 (HTTPS)")
print("Certificate: Self-signed (10 years)")
print("Database: Render PostgreSQL")
print("="*60 + "\n")

app.run(
    host='0.0.0.0',
    port=443,
    debug=False,
    use_reloader=False,
    ssl_context=('$cert', '$key')
)
"@
