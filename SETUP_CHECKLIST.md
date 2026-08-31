# Cloudflare Tunnel - Setup Checklist

## Before You Start

- [ ] Flask app is running (port 8000)
- [ ] You have a Cloudflare account
- [ ] You can access cloudflare.com
- [ ] You have administrator rights on this computer
- [ ] You have internet connectivity

## Pre-Setup Verification

Run this to verify everything is ready:

```powershell
cd C:\smart_hrms_tunnel
.\verify_setup.ps1
```

Expected output:
```
[PASS] All critical checks passed!
```

If any check fails, fix it before continuing.

## Step-by-Step Setup

### Step 1: Open PowerShell as Administrator
- [ ] Press `Windows Key + R`
- [ ] Type `powershell`
- [ ] Right-click → "Run as Administrator"
- [ ] Click "Yes" to confirm

### Step 2: Run Tunnel Setup Script
- [ ] Copy this command:
  ```powershell
  cd C:\smart_hrms_tunnel
  .\quick_tunnel_setup.ps1
  ```
- [ ] Paste into PowerShell
- [ ] Press Enter

### Step 3: Browser Login
- [ ] Browser window opens automatically
- [ ] [ ] Log in with your Cloudflare account email and password
- [ ] [ ] Select **smarthrms.online** domain
- [ ] [ ] Click to authorize/confirm
- [ ] [ ] Browser may show success message
- [ ] [ ] Close browser (script continues)

### Step 4: Setup Script Completes
- [ ] Wait for script to finish (2-3 minutes)
- [ ] You should see:
  ```
  Setup Complete! To start the tunnel, run:
    cloudflared tunnel run smarthrms-tunnel
  ```

### Step 5: Install as Windows Service
- [ ] Run this command (still in PowerShell as Admin):
  ```powershell
  cd C:\smart_hrms_tunnel
  .\install_and_run_tunnel.ps1
  ```

### Step 6: Service Installation Completes
- [ ] Wait for script to finish (1-2 minutes)
- [ ] Should show: `✓ Service installed successfully`
- [ ] Should show: `✓ Service is running`

## Post-Setup Verification

### Check 1: Service is Running
```powershell
Get-Service cloudflared
```

Expected: `Status : Running`

- [ ] Service is running

### Check 2: Test Domain Access
- [ ] Open browser
- [ ] Visit: `https://smarthrms.online`
- [ ] You should see:
  - [ ] Smart HRMS login page
  - [ ] Employee tab
  - [ ] Coordinator tab (purple button)
  - [ ] HTTPS lock icon
  - [ ] NO "Error 1016" message

### Check 3: Test Coordinator Login
- [ ] Login with:
  - Username: `coordinator_kiosk`
  - Password: `CoordinatorPortal@2026`
- [ ] You should see:
  - [ ] 6-step workflow interface
  - [ ] Employee search field
  - [ ] Camera/GPS buttons

### Check 4: Test Employee Restrictions
- [ ] Logout and login with a regular employee account
- [ ] You should see:
  - [ ] Attendance history tab
  - [ ] NO check-in/check-out buttons
  - [ ] Can view own attendance only

## Troubleshooting Checklist

### If Domain Shows Error 1016 Still

- [ ] Service is running: `Get-Service cloudflared`
- [ ] Flask app is running: `netstat -ano | Select-String "8000"`
- [ ] Restart service:
  ```powershell
  Restart-Service cloudflared
  ```
- [ ] Wait 30 seconds and try again
- [ ] If still blocked, check:
  - [ ] Cloudflare DNS shows tunnel is active
  - [ ] Browser cache cleared (Ctrl+F5)

### If Login Fails During Setup

- [ ] Internet is working
- [ ] Can access https://cloudflare.com
- [ ] Correct Cloudflare email/password
- [ ] 2FA code entered if required
- [ ] Try setup again:
  ```powershell
  .\quick_tunnel_setup.ps1
  ```

### If Service Won't Start

- [ ] Flask app is running on port 8000
- [ ] No other cloudflared running:
  ```powershell
  Get-Process cloudflared
  ```
- [ ] Manual test first:
  ```powershell
  .\run_tunnel.bat
  ```

## Success Criteria

You'll know it's working when:

✓ `https://smarthrms.online` loads without Error 1016
✓ Login page shows Coordinator tab
✓ Coordinator can login and see 6-step workflow
✓ Regular employees cannot mark attendance
✓ Super admin can see all attendance records
✓ Service shows as "Running" in Services
✓ No errors in Event Viewer

## Files Created/Modified

After setup, these files will exist:

- `C:\smart_hrms_tunnel\config.yml` - Tunnel configuration
- `~\.cloudflared\[id].json` - Cloudflare credentials
- Windows Service: `cloudflared` - Auto-starts on reboot

## How to Verify Later

If you need to check status after reboot:

```powershell
# Check service
Get-Service cloudflared

# Check if responding
Invoke-WebRequest -Uri "https://smarthrms.online/login" -UseBasicParsing
```

## How to Stop Tunnel (If Needed)

```powershell
Stop-Service cloudflared
```

Or to disable permanently:
```powershell
Set-Service cloudflared -StartupType Disabled
```

## Need Help?

Read one of these documents:

- **Quick overview:** `IMMEDIATE_ACTION_REQUIRED.md`
- **Full guide:** `CLOUDFLARE_TUNNEL_SOLUTION.md`
- **Step-by-step:** `TUNNEL_SETUP_GUIDE.md`

---

## Time Estimate

- Setup script: 3-5 minutes (includes Cloudflare login)
- Service installation: 2 minutes
- Verification: 3-5 minutes
- **Total: ~15 minutes**

---

**Ready?** Run this command:
```powershell
cd C:\smart_hrms_tunnel
.\verify_setup.ps1
```

Then follow the "Setup Complete!" instructions.
