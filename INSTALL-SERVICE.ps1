# ============================================================
# INSTALL-SERVICE.ps1
# Install Smart HRMS + Cloudflare Tunnel as Windows Services
# Run as Administrator — does it once, then auto-starts on boot
# ============================================================
# Prerequisites:
#   1. Waitress installed:  pip install waitress
#   2. NSSM downloaded to C:\nssm\  from https://nssm.cc/download
#   3. cloudflared.exe in PATH or C:\cloudflared\
#   4. Cloudflare tunnel authenticated:
#        cloudflared tunnel login
#        cloudflared tunnel create smarthrms-tunnel
# ============================================================

$ErrorActionPreference = "Stop"
$ProjectRoot = "C:\Users\Administrator\Documents\HRMS\smart_hrms"
$PythonExe   = (Get-Command python).Source
$NssmExe     = "C:\nssm\win64\nssm.exe"

if (-not (Test-Path $NssmExe)) {
    Write-Host "ERROR: NSSM not found at $NssmExe" -ForegroundColor Red
    Write-Host "Download from https://nssm.cc/download and extract to C:\nssm\" -ForegroundColor Yellow
    exit 1
}

Write-Host "Installing Smart HRMS as Windows Service..." -ForegroundColor Cyan

# ── Service 1: Smart HRMS Web Server ────────────────────────
$svcName = "SmartHRMS"
& $NssmExe stop  $svcName 2>$null
& $NssmExe remove $svcName confirm 2>$null

& $NssmExe install $svcName $PythonExe "-m waitress --host=0.0.0.0 --port=80 --threads=8 wsgi:app"
& $NssmExe set $svcName AppDirectory   $ProjectRoot
& $NssmExe set $svcName AppEnvironmentExtra "FLASK_ENV=production"
& $NssmExe set $svcName DisplayName    "Smart HRMS Web Server"
& $NssmExe set $svcName Description    "Smart HRMS Flask application served by Waitress on port 80"
& $NssmExe set $svcName Start          SERVICE_AUTO_START
& $NssmExe set $svcName ObjectName     LocalSystem
& $NssmExe set $svcName AppStdout      "C:\Users\Administrator\Documents\HRMS\smart_hrms\logs\service_stdout.log"
& $NssmExe set $svcName AppStderr      "C:\Users\Administrator\Documents\HRMS\smart_hrms\logs\service_stderr.log"
& $NssmExe set $svcName AppRotateFiles 1
& $NssmExe set $svcName AppRotateBytes 10485760
& $NssmExe start $svcName

Write-Host "  SmartHRMS service installed and started." -ForegroundColor Green

# ── Service 2: Cloudflare Tunnel ────────────────────────────
$cfSvcName  = "SmartHRMSTunnel"
$cfExe      = (Get-Command cloudflared -ErrorAction SilentlyContinue)?.Source
if (-not $cfExe) { $cfExe = "C:\cloudflared\cloudflared.exe" }

if (Test-Path $cfExe) {
    & $NssmExe stop  $cfSvcName 2>$null
    & $NssmExe remove $cfSvcName confirm 2>$null

    & $NssmExe install $cfSvcName $cfExe "--config C:\smart_hrms_tunnel\config.yml tunnel run smarthrms-tunnel"
    & $NssmExe set $cfSvcName AppDirectory  "C:\smart_hrms_tunnel"
    & $NssmExe set $cfSvcName DisplayName   "Smart HRMS Cloudflare Tunnel"
    & $NssmExe set $cfSvcName Description   "Cloudflare Tunnel — smarthrms.online → 192.168.0.5:80"
    & $NssmExe set $cfSvcName Start         SERVICE_AUTO_START
    & $NssmExe set $cfSvcName ObjectName    LocalSystem
    & $NssmExe set $cfSvcName AppStdout     "C:\smart_hrms_tunnel\tunnel_stdout.log"
    & $NssmExe set $cfSvcName AppStderr     "C:\smart_hrms_tunnel\tunnel_stderr.log"
    & $NssmExe start $cfSvcName

    Write-Host "  SmartHRMSTunnel service installed and started." -ForegroundColor Green
} else {
    Write-Host "  WARNING: cloudflared.exe not found — tunnel service skipped." -ForegroundColor Yellow
    Write-Host "  Install cloudflared and re-run, or start tunnel manually:" -ForegroundColor Yellow
    Write-Host "    cloudflared --config C:\smart_hrms_tunnel\config.yml tunnel run smarthrms-tunnel" -ForegroundColor White
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  Services installed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "  Check status:" -ForegroundColor Cyan
Write-Host "    Get-Service SmartHRMS, SmartHRMSTunnel" -ForegroundColor White
Write-Host ""
Write-Host "  Test locally:" -ForegroundColor Cyan
Write-Host "    Invoke-WebRequest http://localhost/health" -ForegroundColor White
Write-Host "============================================================" -ForegroundColor Green
