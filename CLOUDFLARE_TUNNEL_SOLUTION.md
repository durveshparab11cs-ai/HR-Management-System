# Cloudflare Tunnel Solution - Fix Error 1016

## Problem

Your smarthrms.online is showing **Cloudflare Error 1016 (Origin Unreachable)** because:
- Your server is on a private LAN: `192.168.20.109`
- Your public IP is: `122.179.130.196`
- Cloudflare cannot reach a private IP from the internet
- No port forwarding is configured on your router

## Solution: Cloudflare Tunnel

Instead of trying to expose your private server to the internet, use **Cloudflare Tunnel** which:
- Creates an **outbound** connection from your server to Cloudflare
- Routes all traffic through that tunnel
- Requires no port forwarding or firewall changes
- Keeps your server private and secure

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│ User's Browser                                          │
│ https://smarthrms.online                               │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│ Cloudflare DNS (Public)                                 │
│ Hosted globally, returns Cloudflare IP                 │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│ Cloudflare Network (Global)                             │
│ Cloudflare Tunnel entry point                          │
└──────────────────────┬──────────────────────────────────┘
                       │
         ┌─────────────▼─────────────┐
         │ Cloudflare Tunnel         │
         │ (Established by your      │
         │  server's outbound link)  │
         └─────────────┬─────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│ Your Private Network                                    │
│ (192.168.20.0/24)                                      │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│ Windows Server                                          │
│ 192.168.20.109:8000                                    │
│ Flask App (Smart HRMS)                                 │
│ ✓ Running with adhoc SSL/HTTPS                         │
│ ✓ Coordinator Portal enabled                           │
│ ✓ All features working                                 │
└─────────────────────────────────────────────────────────┘
```

## Setup Instructions

### Prerequisites
- Cloudflare account with smarthrms.online domain
- Windows Server with Python 3.12 (already installed ✓)
- Administrator access on Windows Server
- Flask app running on port 8000 (already running ✓)

### Step 1: Verify Flask App

```powershell
# Confirm port 8000 is listening
netstat -ano | Select-String "8000"
```

Should show:
```
TCP    0.0.0.0:8000    0.0.0.0:0    LISTENING    9032
```

### Step 2: Run Tunnel Setup

Open **PowerShell as Administrator** and run:

```powershell
cd C:\smart_hrms_tunnel
.\quick_tunnel_setup.ps1
```

**What happens:**
1. Browser opens to Cloudflare login page
2. You log in with your Cloudflare account
3. Select smarthrms.online domain
4. Tunnel is created automatically
5. Configuration file is generated

### Step 3: Install as Windows Service (Recommended)

Run this to install as a service that starts automatically:

```powershell
cd C:\smart_hrms_tunnel
.\install_and_run_tunnel.ps1
```

**This will:**
- Install cloudflared as a Windows Service
- Start the service immediately
- Set it to restart on reboot
- Verify connectivity automatically

### Alternative: Run Tunnel Manually

If you want to test first without installing as a service:

```powershell
cd C:\smart_hrms_tunnel
.\run_tunnel.bat
```

You should see output:
```
INFO Connection established.
INFO Connecting tunnel ingress
INFO Tunnel running at https://smarthrms.online
```

Press `Ctrl+C` to stop.

## Verification Steps

### 1. Check Service Status

```powershell
Get-Service cloudflared
```

Should show: `Status : Running`

### 2. Test Web Access

Open your browser and visit:
```
https://smarthrms.online
```

You should see:
- ✓ Smart HRMS login page
- ✓ HTTPS (lock icon)
- ✓ Coordinator tab (purple button)
- ✗ No "Error 1016" message

### 3. Test Coordinator Login

```
Username: coordinator_kiosk
Password: CoordinatorPortal@2026
```

You should see:
- ✓ 6-step workflow
- ✓ Employee search
- ✓ Camera access
- ✓ GPS capture

### 4. Test Employee Restrictions

Login with a regular employee account. You should:
- ✓ NOT see check-in/check-out buttons
- ✓ See only your own attendance records
- ✗ Cannot access attendance marking

### 5. Check Logs

```powershell
# View tunnel logs
Get-EventLog -LogName Application | Where-Object {$_.Source -eq 'cloudflared'} | Format-Table -AutoSize
```

## Troubleshooting

### Error: "Tunnel not responding"

**Solution:**
1. Verify Flask app is running: `netstat -ano | Select-String "8000"`
2. Restart tunnel: `Restart-Service cloudflared`
3. Check firewall isn't blocking port 8000

### Error: "SSL certificate verification failed"

**Why:** The tunnel uses HTTPS to connect to your Flask app's adhoc SSL
**Solution:** This is normal. The config file has `originRequest.noTLSVerify: true` which handles it.

### Error: "Cannot login to Cloudflare"

**Solution:**
1. Make sure you have internet connectivity
2. Try logging in to cloudflare.com in your browser first
3. Run setup again: `.\quick_tunnel_setup.ps1`

### Port 8000 shows but no tunnel connection

**Check:**
```powershell
# Verify tunnel service
Get-Service cloudflared -ErrorAction SilentlyContinue | Format-List

# Manually test tunnel
C:\smart_hrms_tunnel\cloudflared.exe tunnel run smarthrms-tunnel
```

## Key Files

- `cloudflared.exe` - Tunnel client (52 MB)
- `config.yml` - Tunnel configuration (created after login)
- `quick_tunnel_setup.ps1` - Interactive setup script
- `install_and_run_tunnel.ps1` - Service installation
- `run_tunnel.bat` - Manual tunnel runner

## Important Notes

1. **Your server remains private** - Only outbound connection to Cloudflare
2. **Always secure** - Traffic encrypted through Cloudflare network
3. **Automatic restart** - If installed as service, tunnel restarts on reboot
4. **No configuration needed** - Cloudflare DNS automatically updated

## Next Steps After Setup

1. ✓ Verify https://smarthrms.online works
2. ✓ Test Coordinator Portal
3. ✓ Test employee restrictions
4. ✓ Deploy Coordinator files if not already deployed
5. ✓ Create backups of database before production use

## Rollback

If you need to disable the tunnel:

```powershell
# Stop service
Stop-Service cloudflared

# Remove service
sc delete cloudflared

# Or just disable it
Set-Service cloudflared -StartupType Disabled
```

Then update Cloudflare DNS A record back to your public IP if you want direct access (requires port forwarding).

---

**Questions?** Check the setup scripts or run `.\quick_tunnel_setup.ps1` for step-by-step guidance.
