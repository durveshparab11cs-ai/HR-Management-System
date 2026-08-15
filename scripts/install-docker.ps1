# Install Docker Desktop on Windows Server
# Run this as Administrator

Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  Docker Desktop Installer for Windows Server              ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")

if (-not $isAdmin) {
    Write-Host "`n✗ ERROR: This script must run as Administrator" -ForegroundColor Red
    Write-Host "  Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

Write-Host "`n1. Downloading Docker Desktop installer..." -ForegroundColor Yellow
$dockerUrl = "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe"
$dockerInstaller = "$env:TEMP\DockerInstaller.exe"

try {
    Invoke-WebRequest -Uri $dockerUrl -OutFile $dockerInstaller -UseBasicParsing
    Write-Host "✓ Downloaded" -ForegroundColor Green
} catch {
    Write-Host "✗ Download failed" -ForegroundColor Red
    Write-Host "  Manual install: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    exit 1
}

Write-Host "`n2. Starting Docker Desktop installation..." -ForegroundColor Yellow
Write-Host "  Follow the installation wizard" -ForegroundColor Gray

Start-Process -FilePath $dockerInstaller -Wait

Write-Host "`n3. Waiting for Docker to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Start Docker if not running
$dockerProcess = Get-Process Docker -ErrorAction SilentlyContinue
if (-not $dockerProcess) {
    Write-Host "  Starting Docker..." -ForegroundColor Yellow
    Start-Process "C:\Program Files\Docker\Docker\Docker.exe" -WindowStyle Hidden
    Start-Sleep -Seconds 10
}

# Verify Docker installation
Write-Host "`n4. Verifying Docker installation..." -ForegroundColor Yellow

$dockerVersion = docker --version 2>&1
if ($dockerVersion -like "*Docker version*") {
    Write-Host "✓ Docker is installed: $dockerVersion" -ForegroundColor Green
} else {
    Write-Host "⚠ Docker installed but not responding yet" -ForegroundColor Yellow
    Write-Host "  Please restart your computer and try again" -ForegroundColor Gray
}

Write-Host "`n╔════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  ✓ Docker Desktop installation complete!                  ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Green

Write-Host "`nNext step: Run START-HRMS.bat" -ForegroundColor Cyan
Write-Host "         .\START-HRMS.bat" -ForegroundColor Yellow

Read-Host "`nPress Enter to close"
