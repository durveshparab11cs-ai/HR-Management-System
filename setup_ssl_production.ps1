# PowerShell Script: Setup SSL Certificate for Smart HRMS Production
# Run as Administrator
# Usage: .\setup_ssl_production.ps1 -Domain "smarthrms.tech"

param(
    [Parameter(Mandatory=$true)]
    [string]$Domain = "smarthrms.tech"
)

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Smart HRMS - SSL Certificate Setup" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Domain: $Domain" -ForegroundColor Yellow
Write-Host "Public IP: 122.179.130.196" -ForegroundColor Yellow
Write-Host ""

# Check if running as Administrator
$isAdmin = [bool]([System.Security.Principal.WindowsIdentity]::GetCurrent().Groups -match "S-1-5-32-544")
if (-not $isAdmin) {
    Write-Host "ERROR: This script must run as Administrator!" -ForegroundColor Red
    exit 1
}

# Step 1: Install Certbot
Write-Host "[1/5] Installing Certbot..." -ForegroundColor Green
pip install --upgrade certbot 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install Certbot" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Certbot installed" -ForegroundColor Green

# Step 2: Create Certbot directory
Write-Host "[2/5] Creating Certbot directories..." -ForegroundColor Green
$certbotPath = "C:\Certbot"
if (-not (Test-Path $certbotPath)) {
    New-Item -ItemType Directory -Path $certbotPath | Out-Null
}
Write-Host "✓ Directories created at $certbotPath" -ForegroundColor Green

# Step 3: Stop Nginx to allow port 80 access
Write-Host "[3/5] Stopping Nginx (if running)..." -ForegroundColor Green
$nginxProcess = Get-Process nginx -ErrorAction SilentlyContinue
if ($nginxProcess) {
    Stop-Process -Name nginx -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    Write-Host "✓ Nginx stopped" -ForegroundColor Green
} else {
    Write-Host "✓ Nginx not running (OK)" -ForegroundColor Green
}

# Step 4: Get SSL Certificate from Let's Encrypt
Write-Host "[4/5] Requesting SSL certificate from Let's Encrypt..." -ForegroundColor Green
Write-Host "This may take 30-60 seconds..." -ForegroundColor Yellow
Write-Host ""

certbot certonly `
    --standalone `
    --non-interactive `
    --agree-tos `
    -m admin@$Domain `
    -d $Domain `
    -d "www.$Domain" `
    --config-dir "$certbotPath" `
    --work-dir "$certbotPath\work" `
    --logs-dir "$certbotPath\logs" `
    2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ SSL certificate obtained successfully!" -ForegroundColor Green
} else {
    Write-Host "ERROR: Failed to obtain certificate. Check:" -ForegroundColor Red
    Write-Host "  1. Port 80 is open on firewall" -ForegroundColor Yellow
    Write-Host "  2. Domain DNS points to 122.179.130.196" -ForegroundColor Yellow
    Write-Host "  3. Wait 5+ minutes after DNS change" -ForegroundColor Yellow
    exit 1
}

# Step 5: Display certificate information
Write-Host ""
Write-Host "[5/5] Certificate Information:" -ForegroundColor Green
$certPath = "$certbotPath\live\$Domain\cert.pem"
if (Test-Path $certPath) {
    Write-Host "Certificate Path: $certPath" -ForegroundColor Cyan
    Write-Host "Private Key Path: $certbotPath\live\$Domain\privkey.pem" -ForegroundColor Cyan
    Write-Host ""
    
    # Show cert details
    $certDetails = openssl x509 -in $certPath -noout -text 2>&1
    $subject = $certDetails | Select-String "Subject:" | Select-Object -First 1
    $issuer = $certDetails | Select-String "Issuer:" | Select-Object -First 1
    $validFrom = $certDetails | Select-String "Not Before:" | Select-Object -First 1
    $validTo = $certDetails | Select-String "Not After:" | Select-Object -First 1
    
    Write-Host $subject -ForegroundColor Cyan
    Write-Host $issuer -ForegroundColor Cyan
    Write-Host $validFrom -ForegroundColor Cyan
    Write-Host $validTo -ForegroundColor Cyan
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Update nginx-production.conf with certificate paths" -ForegroundColor White
Write-Host "2. Start Flask: python run.py" -ForegroundColor White
Write-Host "3. Start Nginx: C:\nginx-1.27.0\nginx.exe" -ForegroundColor White
Write-Host "4. Test: https://$Domain" -ForegroundColor White
Write-Host ""
Write-Host "Certificate will auto-renew 30 days before expiry" -ForegroundColor Cyan
Write-Host ""
