# 🚀 Smart HRMS - START HERE

## One-Click Startup

**On your Windows Server (192.168.0.5):**

### Method 1: Double-Click (Easiest)
1. Double-click: `START-HRMS.bat`
2. Wait for PowerShell terminal to open
3. You're done!

### Method 2: PowerShell (if bat doesn't work)
```powershell
.\scripts\start-server-now.ps1
```

---

## Access Application

**From any computer on the network:**

```
http://192.168.0.5:8000
```

**Or from the server itself:**

```
http://localhost:8000
```

---

## Login Credentials

```
Employee Code: E-2603028
Password: Test@123
Department: Select from dropdown
```

---

## What Happens When You Start

1. ✓ Checks Docker is running
2. ✓ Starts PostgreSQL database (if not running)
3. ✓ Activates Python environment
4. ✓ Installs dependencies
5. ✓ Starts application on port 8000
6. ✓ Shows you the access URL

---

## Troubleshooting

### "This site can't be reached"
- Make sure `START-HRMS.bat` is still running (terminal is open)
- Check firewall allows port 8000
- Try `http://localhost:8000` on the server first

### "Connection refused"
- The script is still starting up, wait 10 seconds
- Check PowerShell window for errors

### "Docker command not found"
- Docker is not installed or not running
- Download from: https://www.docker.com/products/docker-desktop

### "Python not found"
- Python is not installed
- Download from: https://www.python.org/downloads/
- During install, check "Add Python to PATH"

---

## That's It!

Just double-click `START-HRMS.bat` and you're running! 🎉

All employees on the network can now access:
```
http://192.168.0.5:8000
```

---

## Keep It Running 24/7 (Optional)

Once confirmed working, to keep running on server startup:

```powershell
# As Administrator:
cd C:\nssm\win64
.\nssm.exe install HRMSApp "C:\Python312\python.exe" "C:\HRManagementSystem\run.py"
.\nssm.exe start HRMSApp
```

See `DEPLOY_TO_WINDOWS_SERVER.md` for details.

---

**Questions? Check the PowerShell terminal for errors.**
