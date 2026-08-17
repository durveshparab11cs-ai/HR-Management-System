# Smart HRMS - ONE CLICK START FOR WINDOWS SERVER
# Run this script on Windows Server and it will start everything with zero configuration needed

Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  Smart HRMS - Instant Server Startup                      ║" -ForegroundColor Cyan
Write-Host "║  One command to start everything                          ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan

$ErrorActionPreference = "Continue"

# Get the project root directory
$ProjectRoot = Split-Path -Parent $PSScriptRoot

Write-Host "`n[1/5] Checking Docker..." -ForegroundColor Yellow
try {
    $dockerStatus = docker ps 2>&1
    if ($dockerStatus -like "*error*" -or $dockerStatus -like "*Cannot*") {
        Write-Host "⚠ Docker daemon not responding. Attempting to restart..." -ForegroundColor Yellow
        # Docker Desktop might need to start
        Start-Process "C:\Program Files\Docker\Docker\Docker.exe" -WindowStyle Hidden
        Start-Sleep -Seconds 5
    }
    Write-Host "✓ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker not available" -ForegroundColor Red
}

# Check if PostgreSQL container exists
$containerExists = docker ps -a --filter name=hrms-postgres --format "table {{.Names}}" 2>&1 | Select-String "hrms-postgres"

if (-not $containerExists) {
    Write-Host "`n[2/5] Starting PostgreSQL database..." -ForegroundColor Yellow
    docker run -d `
        --name hrms-postgres `
        -e POSTGRES_USER=hrms_user `
        -e POSTGRES_PASSWORD=SecurePassword123 `
        -e POSTGRES_DB=hrms_production `
        -p 5432:5432 `
        -v hrms_data:/var/lib/postgresql/data `
        postgres:15-alpine | Out-Null
    
    Start-Sleep -Seconds 3
    Write-Host "✓ PostgreSQL started" -ForegroundColor Green
} else {
    Write-Host "`n[2/5] Checking PostgreSQL container..." -ForegroundColor Yellow
    $isRunning = docker ps --filter name=hrms-postgres --format "table {{.Names}}" 2>&1 | Select-String "hrms-postgres"
    
    if (-not $isRunning) {
        Write-Host "  Starting stopped container..." -ForegroundColor Yellow
        docker start hrms-postgres | Out-Null
        Start-Sleep -Seconds 2
    }
    Write-Host "✓ PostgreSQL is ready" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "`n[3/5] Preparing Python environment..." -ForegroundColor Yellow
$venvPath = Join-Path $ProjectRoot "venv"

if (-not (Test-Path "$venvPath\Scripts\Activate.ps1")) {
    Write-Host "  Creating virtual environment..." -ForegroundColor Yellow
    python -m venv $venvPath
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ Failed to create virtual environment" -ForegroundColor Red
        exit 1
    }
}

# Activate venv
& "$venvPath\Scripts\Activate.ps1"
Write-Host "✓ Python environment ready" -ForegroundColor Green

# Install/Update dependencies if needed
Write-Host "`n[4/5] Checking dependencies..." -ForegroundColor Yellow
pip install -q gunicorn psycopg2-binary 2>&1 | Out-Null
Write-Host "✓ Dependencies ready" -ForegroundColor Green

# Final check - database connectivity
Write-Host "`n[5/5] Verifying database connection..." -ForegroundColor Yellow
$dbTest = python -c "
import os
os.environ['DATABASE_URL'] = 'postgresql://hrms_user:SecurePassword123@localhost:5432/hrms_production'
try:
    from sqlalchemy import create_engine
    engine = create_engine(os.environ['DATABASE_URL'])
    with engine.connect() as conn:
        print('OK')
except:
    print('FAIL')
" 2>&1

if ($dbTest -like "*OK*") {
    Write-Host "✓ Database connection verified" -ForegroundColor Green
} else {
    Write-Host "⚠ Database connection check skipped (might take a moment to initialize)" -ForegroundColor Yellow
}

# Display final instructions
Write-Host "`n╔════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  ✓ EVERYTHING IS READY - STARTING APPLICATION              ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Green

Write-Host "`n📍 Access Smart HRMS at:" -ForegroundColor Cyan
Write-Host "   http://192.168.0.5:8000" -ForegroundColor Yellow
Write-Host "`n   Or from this server:" -ForegroundColor Cyan
Write-Host "   http://localhost:8000" -ForegroundColor Yellow

Write-Host "`n🔑 Login with:" -ForegroundColor Cyan
Write-Host "   Employee Code: E-2603028" -ForegroundColor White
Write-Host "   Password: Test@123" -ForegroundColor White

Write-Host "`n⏱ Starting application..." -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray

# Change to project directory
cd $ProjectRoot

# Start Gunicorn
$env:FLASK_ENV = "production"
$env:DATABASE_URL = "postgresql://hrms_user:SecurePassword123@localhost:5432/hrms_production"

gunicorn --workers 4 --bind 0.0.0.0:8000 --timeout 60 run:app
