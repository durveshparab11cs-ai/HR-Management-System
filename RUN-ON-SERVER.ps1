# Smart HRMS - Server Startup
# Run this on Windows Server with: powershell -ExecutionPolicy Bypass -File RUN-ON-SERVER.ps1

$ErrorActionPreference = "Stop"

Write-Host "`n" -NoNewline
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Smart HRMS Server - Starting Application" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

# Get project directory
$ProjectDir = Split-Path -Parent (Get-Item $PSCommandPath).FullName
Write-Host "`nProject Directory: $ProjectDir`n" -ForegroundColor Yellow

# Step 1: Ensure Virtual Environment
Write-Host "[STEP 1] Setting up Python environment..." -ForegroundColor Yellow

$venvDir = Join-Path $ProjectDir "venv"
if (-not (Test-Path "$venvDir\Scripts\Activate.ps1")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Gray
    python -m venv $venvDir
}

# Activate venv
& "$venvDir\Scripts\Activate.ps1"
Write-Host "✓ Virtual environment ready" -ForegroundColor Green

# Step 2: Install requirements
Write-Host "`n[STEP 2] Installing Python packages..." -ForegroundColor Yellow

$requirementsFile = Join-Path $ProjectDir "requirements.txt"
if (Test-Path $requirementsFile) {
    pip install -q -r $requirementsFile
    Write-Host "✓ Requirements installed" -ForegroundColor Green
} else {
    Write-Host "Installing core packages..." -ForegroundColor Gray
    pip install -q Flask Flask-SQLAlchemy Flask-Login python-dotenv psycopg2-binary gunicorn
    Write-Host "✓ Core packages installed" -ForegroundColor Green
}

# Step 3: Check/Start PostgreSQL
Write-Host "`n[STEP 3] Checking database..." -ForegroundColor Yellow

try {
    $dockerCheck = docker ps 2>&1
    if ($dockerCheck -like "*error*" -or $dockerCheck -like "*Cannot*") {
        Write-Host "⚠ Docker not responding. Attempting restart..." -ForegroundColor Yellow
        try {
            Start-Process "C:\Program Files\Docker\Docker\Docker.exe" -WindowStyle Hidden
            Start-Sleep -Seconds 5
        } catch {
            Write-Host "⚠ Docker might not be installed" -ForegroundColor Yellow
        }
    }
    
    $containerExists = docker ps -a --filter name=hrms-postgres --format "{{.Names}}" 2>&1 | Select-String "hrms-postgres"
    
    if (-not $containerExists) {
        Write-Host "Starting PostgreSQL container..." -ForegroundColor Gray
        docker run -d `
            --name hrms-postgres `
            -e POSTGRES_USER=hrms_user `
            -e POSTGRES_PASSWORD=SecurePassword123 `
            -e POSTGRES_DB=hrms_production `
            -p 5432:5432 `
            -v hrms_data:/var/lib/postgresql/data `
            postgres:15-alpine 2>&1 | Out-Null
        
        Start-Sleep -Seconds 3
        Write-Host "✓ PostgreSQL started" -ForegroundColor Green
    } else {
        $isRunning = docker ps --filter name=hrms-postgres --format "{{.Names}}" 2>&1 | Select-String "hrms-postgres"
        if (-not $isRunning) {
            Write-Host "Starting PostgreSQL container..." -ForegroundColor Gray
            docker start hrms-postgres 2>&1 | Out-Null
            Start-Sleep -Seconds 2
        }
        Write-Host "✓ PostgreSQL ready" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠ Database check failed (might still work)" -ForegroundColor Yellow
}

# Step 4: Set environment
Write-Host "`n[STEP 4] Configuring environment..." -ForegroundColor Yellow

$env:FLASK_ENV = "production"
$env:DATABASE_URL = "postgresql://hrms_user:SecurePassword123@localhost:5432/hrms_production"
$env:SERVER_NAME = "192.168.0.5:8000"

Write-Host "✓ Environment configured" -ForegroundColor Green

# Step 5: Display startup info
Write-Host "`n" -NoNewline
Write-Host "================================================" -ForegroundColor Green
Write-Host "  ✓ READY TO START" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green

Write-Host "`n📍 Access URL: http://192.168.0.5:8000" -ForegroundColor Cyan
Write-Host "🔑 Login: E-2603028 / Test@123`n" -ForegroundColor Cyan

# Step 6: Start application
Write-Host "[STEP 5] Starting application..." -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop`n" -ForegroundColor Gray
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray

cd $ProjectDir
gunicorn --workers 4 --bind 0.0.0.0:8000 --timeout 120 --access-logfile - run:app
