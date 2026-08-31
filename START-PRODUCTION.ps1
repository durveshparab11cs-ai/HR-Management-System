# ============================================================
# START-PRODUCTION.ps1
# Smart HRMS — Production Startup Script (Windows Server)
# Runs Waitress on port 80, bound to all interfaces
# ============================================================
# Usage (run as Administrator):
#   Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
#   .\START-PRODUCTION.ps1
# ============================================================

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Smart HRMS — Production Server Startup" -ForegroundColor Cyan
Write-Host "  Server:  192.168.0.5:80" -ForegroundColor Cyan
Write-Host "  Domain:  https://smarthrms.online" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# ── Step 1: Verify Python ────────────────────────────────────
Write-Host "[1/6] Checking Python..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Python not found. Install Python 3.9+ and add to PATH." -ForegroundColor Red
    exit 1
}
Write-Host "      $pythonVersion" -ForegroundColor Green

# ── Step 2: Activate venv if present, else use system Python ─
Write-Host "[2/6] Checking virtual environment..." -ForegroundColor Yellow
$venvActivate = Join-Path $ProjectRoot "venv\Scripts\Activate.ps1"
if (Test-Path $venvActivate) {
    & $venvActivate
    Write-Host "      Virtual environment activated." -ForegroundColor Green
} else {
    Write-Host "      No venv found — using system Python." -ForegroundColor Yellow
}

# ── Step 3: Install / verify Waitress ────────────────────────
Write-Host "[3/6] Checking Waitress..." -ForegroundColor Yellow
$waitressCheck = python -c "import waitress; print(waitress.__version__)" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "      Waitress not found — installing..." -ForegroundColor Yellow
    pip install waitress
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Could not install Waitress." -ForegroundColor Red
        exit 1
    }
}
$waitressVersion = python -c "import waitress; print(waitress.__version__)" 2>&1
Write-Host "      Waitress $waitressVersion ready." -ForegroundColor Green

# ── Step 4: Verify database ──────────────────────────────────
Write-Host "[4/6] Verifying database..." -ForegroundColor Yellow
$dbPath = Join-Path $ProjectRoot "instance\smart_hrms_dev.db"
if (Test-Path $dbPath) {
    $dbSize = (Get-Item $dbPath).Length / 1MB
    Write-Host ("      Database OK: {0:N1} MB" -f $dbSize) -ForegroundColor Green
} else {
    Write-Host "      WARNING: Database not found at $dbPath" -ForegroundColor Red
    Write-Host "      Run: python create_coordinator_user.py" -ForegroundColor Yellow
    exit 1
}

# ── Step 5: Open firewall port 80 ────────────────────────────
Write-Host "[5/6] Ensuring firewall allows port 80..." -ForegroundColor Yellow
try {
    $existingRule = Get-NetFirewallRule -DisplayName "Smart HRMS HTTP" -ErrorAction SilentlyContinue
    if (-not $existingRule) {
        New-NetFirewallRule `
            -DisplayName "Smart HRMS HTTP" `
            -Direction Inbound `
            -Protocol TCP `
            -LocalPort 80 `
            -Action Allow `
            -Profile Any | Out-Null
        Write-Host "      Firewall rule created for port 80." -ForegroundColor Green
    } else {
        Write-Host "      Firewall rule already exists." -ForegroundColor Green
    }
} catch {
    Write-Host "      WARNING: Could not set firewall rule (may need admin): $_" -ForegroundColor Yellow
}

# ── Step 6: Start Waitress ───────────────────────────────────
Write-Host "[6/6] Starting Waitress on 0.0.0.0:80..." -ForegroundColor Yellow
Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  Server starting — access via:" -ForegroundColor Green
Write-Host "    Local:    http://192.168.0.5" -ForegroundColor Green
Write-Host "    Internet: https://smarthrms.online" -ForegroundColor Green
Write-Host "    Kiosk:    https://smarthrms.online/coordinator/" -ForegroundColor Green
Write-Host ""
Write-Host "  Coordinator Login:" -ForegroundColor Green
Write-Host "    Username: coordinator_kiosk" -ForegroundColor Green
Write-Host "    Password: CoordinatorPortal@2026" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop the server." -ForegroundColor Yellow
Write-Host ""

# Set production environment variable for this session
$env:FLASK_ENV = "production"

# Start Waitress with 8 threads (good for 10-50 concurrent users)
waitress-serve `
    --host=0.0.0.0 `
    --port=80 `
    --threads=8 `
    --channel-timeout=120 `
    --connection-limit=500 `
    --cleanup-interval=30 `
    --ident="SmartHRMS/1.0" `
    wsgi:app
