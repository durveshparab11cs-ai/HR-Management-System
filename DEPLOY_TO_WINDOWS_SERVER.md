# Deploy Smart HRMS to Windows Server (192.168.0.5)

**Goal:** Get HR Management System running on company server, accessible to all employees.

**Setup Time:** 1 hour  
**Cost:** $0  
**Uptime:** 24/7  
**Access:** http://192.168.0.5:8000 from any company PC

---

## Prerequisites Check

Before starting, verify:
- [ ] Windows Server is always on
- [ ] Server is on company network (192.168.0.5)
- [ ] You have admin access to the server
- [ ] Server has internet (to download Python, Docker)
- [ ] Python 3.9+ not installed yet (we'll install fresh)

---

## Phase 1: Prepare on Your Development Machine (10 minutes)

### Step 1a: Create Deployment Package

On your current Windows machine, create a deployment package:

```powershell
cd 'c:\Users\durve\Downloads\HR management system'

# Create deployment folder
New-Item -ItemType Directory -Path ".\deployment" -Force

# Copy entire project
Copy-Item -Recurse "." -Destination ".\deployment\hrms" -Exclude ".git","venv","__pycache__","*.pyc"

# Create deployment readme
@"
# Smart HRMS Server Deployment

## Quick Start

1. Install Python: https://www.python.org/downloads/
2. Install Docker: https://www.docker.com/products/docker-desktop
3. Run: .\scripts\deploy-windows.ps1
4. Start: gunicorn --workers 4 --bind 0.0.0.0:8000 run:app
5. Access: http://192.168.0.5:8000

## Files
- QUICK_START_SELF_HOSTED.md (detailed guide)
- DEPLOYMENT_GUIDE.md (reference)
- .env.production.example (configuration template)
- scripts/deploy-windows.ps1 (automated setup)
"@ | Out-File ".\deployment\README.txt" -Encoding UTF8
```

### Step 1b: Create USB Drive or Network Share

**Option A: USB Drive** (simplest)
```powershell
# Copy deployment folder to USB
# Connect USB drive (assume D:)
Copy-Item -Recurse ".\deployment\hrms" -Destination "D:\hrms"
```

**Option B: Network Share** (if you have one)
```powershell
# Copy to shared folder on server
Copy-Item -Recurse ".\deployment\hrms" -Destination "\\192.168.0.5\shared\hrms"
```

**Option C: GitHub** (recommended - version control)
```powershell
# Already committed to GitHub, just clone on server
# (see Phase 2, Step 2a)
```

---

## Phase 2: Deploy on Windows Server (40 minutes)

### Step 2a: Connect to Server

**Option 1: Remote Desktop** (easiest)
```powershell
mstsc /v:192.168.0.5
# Login with server credentials
```

**Option 2: Physical Access**
- Walk to server room
- Use keyboard/mouse

**Option 3: SSH/PowerShell Remoting**
```powershell
Enter-PSSession -ComputerName 192.168.0.5 -Credential (Get-Credential)
```

### Step 2b: Get Project Files on Server

**Option 1: From USB**
```powershell
# Connect USB drive
# Copy from USB to server
Copy-Item -Recurse "D:\hrms" -Destination "C:\HRManagementSystem"
```

**Option 2: From Network Share**
```powershell
Copy-Item -Recurse "\\192.168.0.5\shared\hrms" -Destination "C:\HRManagementSystem"
```

**Option 3: From GitHub** (my recommended)
```powershell
# Install Git if not present
# Then clone:
cd C:\
git clone https://github.com/durveshparab11cs-ai/HR-Management-System.git HRManagementSystem
cd HRManagementSystem
```

### Step 2c: Install Python (5 minutes)

On the server:

```powershell
# Download Python installer
# Go to: https://www.python.org/downloads/
# Download Python 3.12 Windows Installer

# Run installer:
# 1. Check "Add Python to PATH" ✓
# 2. Click "Install Now"
# 3. Wait for completion

# Verify
python --version
pip --version
```

### Step 2d: Install Docker (5 minutes)

On the server:

```powershell
# Download Docker Desktop
# Go to: https://www.docker.com/products/docker-desktop
# Run installer and follow wizard
# Restart server when prompted

# Verify
docker --version
docker run hello-world
```

### Step 2e: Start PostgreSQL (2 minutes)

On the server:

```powershell
docker run -d `
  --name hrms-postgres `
  -e POSTGRES_USER=hrms_user `
  -e POSTGRES_PASSWORD=SecurePassword123 `
  -e POSTGRES_DB=hrms_production `
  -p 5432:5432 `
  -v hrms_data:/var/lib/postgresql/data `
  postgres:15-alpine

# Verify
docker ps
```

### Step 2f: Configure Application (5 minutes)

On the server:

```powershell
cd C:\HRManagementSystem

# Copy example environment file
Copy-Item .env.production.example .env.production

# Edit with your settings
notepad .env.production
```

**Update these lines in .env.production:**

```bash
# DATABASE
DATABASE_URL=postgresql://hrms_user:SecurePassword123@localhost:5432/hrms_production

# SERVER (use server IP)
SERVER_NAME=192.168.0.5:8000
PREFERRED_URL_SCHEME=http

# FLASK
FLASK_ENV=production
SECRET_KEY=change-this-to-random-value

# SECURITY
SESSION_COOKIE_SECURE=False
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax
```

### Step 2g: Run Deployment Script (10 minutes)

On the server:

```powershell
cd C:\HRManagementSystem

# Run deployment script (automated)
.\scripts\deploy-windows.ps1
```

This will:
- ✓ Create virtual environment
- ✓ Install dependencies
- ✓ Test database connection
- ✓ Initialize database
- ✓ Collect static files
- ✓ Test application

### Step 2h: Start Application (1 minute)

On the server:

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Start application
gunicorn --workers 4 --bind 0.0.0.0:8000 run:app
```

You should see:
```
[2026-08-13 12:00:00 +0000] [1234] [INFO] Listening at: http://0.0.0.0:8000
[2026-08-13 12:00:00 +0000] [1234] [INFO] Using worker: sync
[2026-08-13 12:00:00 +0000] [1234] [INFO] Spawned 4 workers
```

✓ **Application is running!**

---

## Phase 3: Test from Company PCs (5 minutes)

### From Any Company PC:

Open browser and go to:
```
http://192.168.0.5:8000
```

You should see Smart HRMS login page.

**Test login:**
- Employee Code: `E-2603028`
- Password: `Test@123`
- Department: (select from dropdown)

✓ **If login works, you're done!**

---

## Phase 4: Make it Permanent (Optional - for 24/7 uptime)

### Option A: Run as Windows Service (Recommended)

```powershell
# 1. Download NSSM: https://nssm.cc/download
# 2. Extract to C:\nssm

# 3. On server, run as Administrator:
cd C:\nssm\win64

# Install service
.\nssm.exe install HRMSApp "C:\Python312\python.exe" "C:\HRManagementSystem\run.py"

# Set working directory
.\nssm.exe set HRMSApp AppDirectory "C:\HRManagementSystem"

# Set environment
.\nssm.exe set HRMSApp AppEnvironmentExtra DATABASE_URL=postgresql://hrms_user:SecurePassword123@localhost/hrms_production

# Start service
.\nssm.exe start HRMSApp

# Check status
.\nssm.exe status HRMSApp
```

Now application:
- ✓ Starts automatically on server reboot
- ✓ Runs 24/7 in background
- ✓ Auto-restarts if it crashes
- ✓ No terminal window needed

### Option B: Task Scheduler (Alternative)

Create a scheduled task to start application at boot:
```powershell
# Create task to run at startup
$action = New-ScheduledTaskAction -Execute "C:\HRManagementSystem\start-hrms.bat"
$trigger = New-ScheduledTaskTrigger -AtStartup
Register-ScheduledTask -Action $action -Trigger $trigger -TaskName "HRMS-StartUp" -RunLevel Highest
```

---

## Access URLs for All Employees

### Share with your team:

**Application URL:**
```
http://192.168.0.5:8000
```

**Create bookmark in browser**

**QR Code for mobile:**
```
You can create QR code at: https://www.qr-code-generator.com/
Encode: http://192.168.0.5:8000
```

---

## Troubleshooting

### "Connection Refused" from other PCs
```powershell
# On server, check firewall allows port 8000
netsh advfirewall firewall add rule name="Allow HRMS" dir=in action=allow protocol=tcp localport=8000

# Or disable firewall temporarily for testing
netsh advfirewall set allprofiles state off
```

### "Connection to database failed"
```powershell
# Check PostgreSQL container is running
docker ps | findstr hrms-postgres

# If not running, start it
docker start hrms-postgres

# If crashed, remove and recreate
docker rm hrms-postgres
# Then run: docker run -d --name hrms-postgres ...
```

### Application won't start
```powershell
# Check Python is installed
python --version

# Check virtual environment
cd C:\HRManagementSystem
.\venv\Scripts\Activate.ps1

# Try running app directly
python run.py
```

### Port 8000 already in use
```powershell
# Find process using port 8000
Get-NetTCPConnection -LocalPort 8000

# Kill it
taskkill /PID <process-id> /F

# Or use different port
gunicorn --workers 4 --bind 0.0.0.0:9000 run:app
```

---

## Monitoring

### Check if running
```powershell
# From any company PC
Invoke-WebRequest http://192.168.0.5:8000/health

# Should return: {"status": "ok"}
```

### View logs
```powershell
# If running as service with NSSM
cd C:\nssm\win64
.\nssm.exe get HRMSApp AppStdout
```

### Restart service
```powershell
# If running as service
.\nssm.exe restart HRMSApp
```

---

## Next Steps

1. ✓ Deploy to server (you are here)
2. ✓ Test from all company PCs
3. [ ] Set up as Windows Service for 24/7
4. [ ] Create user accounts for each employee
5. [ ] Train employees on usage
6. [ ] Set up automated backups
7. [ ] Monitor uptime

---

## Quick Reference

| Component | Status | URL |
|-----------|--------|-----|
| Application | Running | http://192.168.0.5:8000 |
| Health Check | Ready | http://192.168.0.5:8000/health |
| Database | PostgreSQL 15 | localhost:5432 |
| Server | Windows Server | 192.168.0.5 |

---

## Support Commands

```powershell
# Check everything is running
docker ps  # Should show hrms-postgres

# Verify network connectivity
Test-Connection 192.168.0.5 -Count 1

# Check port 8000 is open
Test-NetConnection -ComputerName 192.168.0.5 -Port 8000

# View server IP
ipconfig
```

---

**Deployment complete! Your Smart HRMS is now live on company network! 🎉**

All employees can access: **http://192.168.0.5:8000**
