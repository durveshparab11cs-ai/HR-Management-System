# trust_cert.ps1
# Installs the self-signed certificate into Windows Trusted Root CA store
# so Chrome accepts https://127.0.0.1:5000 without warnings.
# Run once as Administrator: powershell -ExecutionPolicy Bypass -File scripts\trust_cert.ps1

$certPath = Join-Path $PSScriptRoot "..\instance\cert.pem"
$certPath = Resolve-Path $certPath

Write-Host "Installing certificate: $certPath" -ForegroundColor Cyan

$cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($certPath)
$store = New-Object System.Security.Cryptography.X509Certificates.X509Store(
    [System.Security.Cryptography.X509Certificates.StoreName]::Root,
    [System.Security.Cryptography.X509Certificates.StoreLocation]::LocalMachine
)
$store.Open([System.Security.Cryptography.X509Certificates.OpenFlags]::ReadWrite)
$store.Add($cert)
$store.Close()

Write-Host "Certificate installed successfully." -ForegroundColor Green
Write-Host "Restart Chrome and open: https://127.0.0.1:5000" -ForegroundColor Yellow
