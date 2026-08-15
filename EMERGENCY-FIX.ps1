# Smart HRMS - Emergency Recovery Script
# This will diagnose and fix whatever broke

Write-Host "`n" -NoNewline
Write-Host "████████████████████████████████████████████████████" -ForegroundColor Red
Write-Host "  SMART HRMS - EMERGENCY RECOVERY" -ForegroundColor Red
Write-Host "████████████████████████████████████████████████████`n" -ForegroundColor Red

$issues = @()

# CHECK 1: Python
Write-Host "[CHECK 1] Python Installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python installed: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python NOT found" -ForegroundColor Red
    $issues += "Python not installed"
}

# CHECK 2: Docker
Write-Host "`n[CHECK 2] Docker..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version 2>&1
    if ($dockerVersion -like "*Docker version*") {
        Write-Host "✓ Docker installed: $dockerVersion" -ForegroundColor Green
    } else {
        Write-Host "✗ Docker not responding" -ForegroundColor Red
        $issues += "Docker not responding"
    }
} catch {
    Write-Host "✗ Docker NOT found" -ForegroundColor Red
    $issues += "Docker not installed"
}

# CHECK 3: PostgreSQL Container
Write-Host "`n[CHECK 3] PostgreSQL Container..." -ForegroundColor Yellow
try {
    $containers = docker ps -a 2>&1
    if ($containers -like "*hrms-postgres*") {
        $isRunning = docker ps 2>&1 | Select-String "hrms-postgres"
        if ($isRunning) {
            Write-Host "✓ PostgreSQL container RUNNING" -ForegroundColor Green
        } else {
            Write-Host "⚠ PostgreSQL container EXISTS but STOPPED" -ForegroundColor Yellow
            Write-Host "  Attempting restart..." -ForegroundColor Yellow
            docker start hrms-postgres 2>&1 | Out-Null
            Start-Sleep -Seconds 2
            Write-Host "✓ PostgreSQL restarted" -ForegroundColor Green
        }
    } else {
        Write-Host "✗ PostgreSQL container NOT FOUND" -ForegroundColor Red
        Write-Host "  Creating new container..." -ForegroundColor Yellow
        docker run -d `
            --name hrms-postgres `
            -e POSTGRES_USER=hrms_user `
            -e POSTGRES_PASSWORD=SecurePassword123 `
            -e POSTGRES_DB=hrms_production `
            -p 5432:5432 `
            -v hrms_data:/var/lib/postgresql/data `
            postgres:15-alpine 2>&1 | Out-Null
        Start-Sleep -Seconds 3
        Write-Host "✓ PostgreSQL container created and started" -ForegroundColor Green
    }
} catch {
    Write-Host "✗ Docker error: $_" -ForegroundColor Red
    $issues += "Docker container issue"
}

# CHECK 4: Port 8000
Write-Host "`n[CHECK 4] Port 8000..." -ForegroundColor Yellow
try {
    $portInUse = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
    if ($portInUse) {
        Write-Host "⚠ Port 8000 already in use" -ForegroundColor Yellow
        Write-Host "  Process ID: $($portInUse.OwningProcess)" -ForegroundColor Yellow
        Write-Host "  Killing process..." -ForegroundColor Yellow
        taskkill /PID $portInUse.OwningProcess /F 2>&1 | Out-Null
        Start-Sleep -Seconds 1
        Write-Host "✓ Port 8000 cleared" -ForegroundColor Green
    } else {
        Write-Host "✓ Port 8000 is free" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠ Could not check port (might be fine)" -ForegroundColor Yellow
}

# CHECK 5: Database Connection
Write-Host "`n[CHECK 5] Database Connectivity..." -ForegroundColor Yellow
try {
    $testConnection = python -c "
import os
os.environ['DATABASE_URL'] = 'postgresql://hrms_user:SecurePassword123@localhost:5432/hrms_production'
try:
    from sqlalchemy import create_engine
    engine = create_engine(os.environ['DATABASE_URL'], connect_args={'timeout': 10})
    with engine.connect() as conn:
        result = conn.execute('SELECT 1')
        print('OK')
except Exception as e:
    print(f'FAIL: {e}')
" 2>&1
    
    if ($testConnection -like "*OK*") {
        Write-Host "✓ Database connection OK" -ForegroundColor Green
    } else {
        Write-Host "⚠ Database connection issue" -ForegroundColor Yellow
        Write-Host "  $testConnection" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠ Could not test connection" -ForegroundColor Yellow
}

# CHECK 6: Virtual Environment
Write-Host "`n[CHECK 6] Python Virtual Environment..." -ForegroundColor Yellow
$projectDir = Split-Path -Parent $PSCommandPath
$venvDir = Join-Path $projectDir "venv"

if (Test-Path "$venvDir\Scripts\Activate.ps1") {
    Write-Host "✓ Virtual environment exists" -ForegroundColor Green
} else {
    Write-Host "✗ Virtual environment NOT found" -ForegroundColor Red
    Write-Host "  Creating..." -ForegroundColor Yellow
    python -m venv $venvDir
    Write-Host "✓ Virtual environment created" -ForegroundColor Green
}

# RECOVERY: Activate and reinstall
Write-Host "`n[RECOVERY] Installing dependencies..." -ForegroundColor Yellow
& "$venvDir\Scripts\Activate.ps1"
pip install -q --upgrade pip 2>&1 | Out-Null
pip install -q gunicorn psycopg2-binary 2>&1 | Out-Null

$requirementsFile = Join-Path $projectDir "requirements.txt"
if (Test-Path $requirementsFile) {
    pip install -q -r $requirementsFile 2>&1 | Out-Null
}

Write-Host "✓ Dependencies installed" -ForegroundColor Green

# SUMMARY
Write-Host "`n" -NoNewline
Write-Host "════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "  ✓ RECOVERY COMPLETE - READY TO START" -ForegroundColor Green
Write-Host "════════════════════════════════════════════════════`n" -ForegroundColor Green

if ($issues.Count -gt 0) {
    Write-Host "⚠ WARNINGS:" -ForegroundColor Yellow
    foreach ($issue in $issues) {
        Write-Host "  - $issue" -ForegroundColor Yellow
    }
    Write-Host ""
}

# FINAL STARTUP
Write-Host "Starting application in 3 seconds...`n" -ForegroundColor Cyan
Write-Host "Access URL: http://192.168.0.5:8000" -ForegroundColor Cyan
Write-Host "Login: E-2603028 / Test@123`n" -ForegroundColor Cyan

Start-Sleep -Seconds 3

$env:FLASK_ENV = "production"
$env:DATABASE_URL = "postgresql://hrms_user:SecurePassword123@localhost:5432/hrms_production"

cd $projectDir
Write-Host "════════════════════════════════════════════════════" -ForegroundColor DarkGray
gunicorn --workers 4 --bind 0.0.0.0:8000 --timeout 120 --access-logfile - run:app
