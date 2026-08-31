# IMMEDIATE ACTION REQUIRED - Fix Error 1016

## Current Status

✓ **DONE:**
- Flask app running on port 8000 (PID 9032)
- Coordinator Portal fully implemented
- All 8 files deployed to production
- Coordinator user created (coordinator_kiosk / CoordinatorPortal@2026)
- Database configured correctly

✗ **BLOCKED:**
- Cloudflare Error 1016 (Origin Unreachable)
- Cannot access https://smarthrms.online from browser
- Reason: Server is on private LAN (192.168.20.109), not publicly accessible

## The Fix (Cloudflare Tunnel)

Cloudflare Tunnel creates an outbound connection from your server to Cloudflare's network, eliminating the need for port forwarding or public IP exposure.

## What You Need To Do (3 Simple Steps)

### Step 1: Open PowerShell as Administrator

Press `Windows Key + R`, type:
```
powershell
```

Right-click and select "Run as Administrator"

### Step 2: Run the Setup Script

Copy and paste this command:
```powershell
cd C:\smart_hrms_tunnel
.\quick_tunnel_setup.ps1
```

### Step 3: Log In When Browser Opens

When the browser opens:
1. Log in with your **Cloudflare account credentials**
2. Select **smarthrms.online** domain
3. Authorize the tunnel
4. The script will complete automatically

## What Happens

```
✓ Setup Script Opens Browser
    ↓
✓ You Log Into Cloudflare
    ↓
✓ Tunnel Created Automatically
    ↓
✓ Config File Generated
    ↓
✓ Domain Routed to Your Server
    ↓
✓ Installation Complete!
```

## After Setup

Install as Windows Service (so it runs automatically):

```powershell
cd C:\smart_hrms_tunnel
.\install_and_run_tunnel.ps1
```

This will:
- Install cloudflared as a Windows Service
- Start automatically on reboot
- Run in background permanently

## Verify It Works

1. Open browser: https://smarthrms.online
2. You should see Smart HRMS login page
3. Try Coordinator login:
   - Username: `coordinator_kiosk`
   - Password: `CoordinatorPortal@2026`
4. You should see the 6-step workflow

## Files Provided

Located in: `C:\smart_hrms_tunnel\`

- **quick_tunnel_setup.ps1** ← Run this first (interactive setup)
- **install_and_run_tunnel.ps1** ← Run this after (service installation)
- **run_tunnel.bat** ← Manual testing (optional)
- **cloudflared.exe** ← Tunnel client (already downloaded)

## Technical Details

- **Problem:** Server on private LAN (192.168.20.109) with public IP 122.179.130.196
- **Solution:** Cloudflare Tunnel (outbound connection)
- **Architecture:** Browser → Cloudflare → Tunnel → Your Server:8000
- **Security:** All traffic encrypted, server stays private

## Timeline

- Step 1 (PowerShell): 1 minute
- Step 2 (Setup Script): 3-5 minutes (includes browser login)
- Step 3 (Service Installation): 2 minutes
- **Total Time: ~10 minutes**

## Success Indicators

After completing the setup, you should see:

✓ `Get-Service cloudflared` shows "Running"
✓ `https://smarthrms.online` opens without Error 1016
✓ Login page shows Coordinator tab (purple button)
✓ Coordinator login works with 6-step workflow
✓ Regular employees cannot see check-in buttons

## Need Help?

Read: `c:\Users\durve\Downloads\HR management system\smart_hrms\CLOUDFLARE_TUNNEL_SOLUTION.md`

---

**Start now:** Open PowerShell as Administrator and run the first command!
