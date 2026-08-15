# Smart HRMS - Windows Production Deployment Script
# Run this script to deploy the application on Windows

param(
    [string]$Action = "deploy",
    [string]$DatabaseUrl = "postgresql://hrms_user:SecurePassword123@localhost:5432/hrms_production"
)

# Colors for output
function Write-Success { Write-Host $args -ForegroundColor Green }
function Write-Error { Write-Host $args -ForegroundColor Red }
function Write-Info { Write-Host $args -ForegroundColor Cyan }

Write-Info "════════════════════════════════════════════════════════════"
Write-Info "Smart HRMS - Windows Deployment"
Write-Info "════════════════════════════════════════════════════════════"

$ProjectRoot = Split-Path -Parent $PSScriptRoot

# ─────────────────────────────────────────────────────────
# 1. Setup Python Virtual Environment
# ─────────────────────────────────────────────────────────

Write-Info "`n[1/8] Setting up Python virtual environment..."

$VenvPath = Join-Path $ProjectRoot "venv"

if (-not (Test-Path $VenvPath)) {
    Write-Info "Creating virtual environment..."
    python -m venv $VenvPath
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to create virtual environment"
        exit 1
    }
    Write-Success "✓ Virtual environment created"
} else {
    Write-Info "Virtual environment already exists"
}

# Activate venv
& "$VenvPath\Scripts\Activate.ps1"
Write-Success "✓ Virtual environment activated"

# ─────────────────────────────────────────────────────────
# 2. Install Dependencies
# ─────────────────────────────────────────────────────────

Write-Info "`n[2/8] Installing dependencies..."

pip install --upgrade pip setuptools wheel | Out-Null

if (Test-Path (Join-Path $ProjectRoot "requirements.txt")) {
    pip install -r (Join-Path $ProjectRoot "requirements.txt") | Out-Null
    Write-Success "✓ Requirements installed from requirements.txt"
} else {
    Write-Error "requirements.txt not found"
    exit 1
}

# Install production dependencies
pip install gunicorn psycopg2-binary redis python-dotenv | Out-Null
Write-Success "✓ Production dependencies installed"

# ─────────────────────────────────────────────────────────
# 3. Setup Environment
# ─────────────────────────────────────────────────────────

Write-Info "`n[3/8] Setting up environment..."

$EnvFile = Join-Path $ProjectRoot ".env.production"

if (-not (Test-Path $EnvFile)) {
    Write-Info "Creating .env.production..."
    $ExampleEnv = Join-Path $ProjectRoot ".env.production.example"
    
    if (Test-Path $ExampleEnv) {
        Copy-Item $ExampleEnv $EnvFile
        Write-Info "✓ Created .env.production from template"
        Write-Error "⚠ IMPORTANT: Edit .env.production with your actual values"
    } else {
        Write-Error ".env.production.example not found"
        exit 1
    }
} else {
    Write-Info "✓ .env.production already exists"
}

# Load environment
$env:FLASK_ENV = "production"
$env:DATABASE_URL = $DatabaseUrl

Write-Success "✓ Environment configured"

# ─────────────────────────────────────────────────────────
# 4. Test Database Connection
# ─────────────────────────────────────────────────────────

Write-Info "`n[4/8] Testing database connection..."

$PythonTest = @"
import os
import sys
try:
    from sqlalchemy import create_engine
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("ERROR: DATABASE_URL not set")
        sys.exit(1)
    engine = create_engine(db_url)
    with engine.connect() as conn:
        result = conn.execute("SELECT 1")
        print("✓ Database connection successful")
    sys.exit(0)
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
"@

python -c $PythonTest
if ($LASTEXITCODE -ne 0) {
    Write-Error "Database connection failed. Check DATABASE_URL in .env.production"
    exit 1
}

Write-Success "✓ Database connection verified"

# ─────────────────────────────────────────────────────────
# 5. Initialize Database
# ─────────────────────────────────────────────────────────

Write-Info "`n[5/8] Initializing database..."

$InitScript = @"
import os
os.chdir('$ProjectRoot')
from app import create_app
from app.extensions.database import db

app = create_app('production')
with app.app_context():
    db.create_all()
    print("✓ Database tables created")
"@

python -c $InitScript
if ($LASTEXITCODE -ne 0) {
    Write-Error "Database initialization failed"
    exit 1
}

Write-Success "✓ Database initialized"

# ─────────────────────────────────────────────────────────
# 6. Collect Static Files
# ─────────────────────────────────────────────────────────

Write-Info "`n[6/8] Collecting static files..."

$StaticDest = "C:\var\www\hrms\static"
New-Item -ItemType Directory -Path $StaticDest -Force | Out-Null

$StaticSrc = Join-Path $ProjectRoot "app\static"
if (Test-Path $StaticSrc) {
    Copy-Item -Recurse "$StaticSrc\*" -Destination $StaticDest -Force
    Write-Success "✓ Static files collected to $StaticDest"
} else {
    Write-Info "No static files found (optional)"
}

$SmartStaticSrc = Join-Path $ProjectRoot "smart_hrms\app\static"
if (Test-Path $SmartStaticSrc) {
    Copy-Item -Recurse "$SmartStaticSrc\*" -Destination $StaticDest -Force
    Write-Success "✓ Additional static files merged"
}

# ─────────────────────────────────────────────────────────
# 7. Test Application
# ─────────────────────────────────────────────────────────

Write-Info "`n[7/8] Testing application startup..."

$TestScript = @"
import os
import sys
os.chdir('$ProjectRoot')

try:
    from app import create_app
    app = create_app('production')
    
    with app.app_context():
        # Test database
        from app.extensions.database import db
        result = db.session.execute("SELECT 1")
        
    print("✓ Application test passed")
    sys.exit(0)
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
"@

python -c $TestScript
if ($LASTEXITCODE -ne 0) {
    Write-Error "Application test failed"
    exit 1
}

Write-Success "✓ Application test passed"

# ─────────────────────────────────────────────────────────
# 8. Setup Windows Service (optional)
# ─────────────────────────────────────────────────────────

Write-Info "`n[8/8] Windows Service Setup..."

Write-Info "`nTo install as a Windows Service:"
Write-Info "1. Download NSSM: https://nssm.cc/download"
Write-Info "2. Extract to C:\nssm"
Write-Info "3. Run this command in PowerShell (as Administrator):"
Write-Info ""
Write-Host "cd C:\nssm\win64" -ForegroundColor Yellow
Write-Host ".\nssm.exe install HRMSApp `"C:\Python312\python.exe`" `"$ProjectRoot\run.py`"" -ForegroundColor Yellow
Write-Host ".\nssm.exe set HRMSApp AppDirectory `"$ProjectRoot`"" -ForegroundColor Yellow
Write-Host ".\nssm.exe start HRMSApp" -ForegroundColor Yellow
Write-Info ""

# ─────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────

Write-Info "`n════════════════════════════════════════════════════════════"
Write-Success "✓ Deployment preparation complete!"
Write-Info "════════════════════════════════════════════════════════════"

Write-Info "`nNext steps:"
Write-Info "1. ✓ Virtual environment: $VenvPath"
Write-Info "2. ✓ Dependencies installed"
Write-Info "3. ✓ Database verified"
Write-Info "4. ✓ Application tested"
Write-Info ""
Write-Info "To start the application:"
Write-Host "  gunicorn --workers 4 --bind 0.0.0.0:8000 run:app" -ForegroundColor Yellow
Write-Info ""
Write-Info "Then access at: http://localhost:8000"
Write-Info ""
Write-Info "To stop the virtual environment:"
Write-Host "  deactivate" -ForegroundColor Yellow

Write-Success "`nDeployment ready!"
