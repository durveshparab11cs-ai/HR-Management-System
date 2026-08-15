# Quick Start: Self-Hosted HR Management System

Deploy Smart HRMS on your own infrastructure in **5 steps**.

---

## Step 1: Prerequisites (5 minutes)

### On Windows:

**Install PostgreSQL** (Option A - Direct Install)
```powershell
# Download: https://www.postgresql.org/download/windows/
# Run installer, set password to: SecurePassword123

# Verify
psql --version
```

**OR Install PostgreSQL** (Option B - Docker, Easier)
```powershell
# Download Docker Desktop: https://www.docker.com/products/docker-desktop

# Run PostgreSQL
docker run -d `
  --name hrms-postgres `
  -e POSTGRES_USER=hrms_user `
  -e POSTGRES_PASSWORD=SecurePassword123 `
  -e POSTGRES_DB=hrms_production `
  -p 5432:5432 `
  postgres:15-alpine

# Verify
docker ps
```

### Create Database

```powershell
# Using psql command line
psql -U postgres

# Then run these commands:
CREATE DATABASE hrms_production;
CREATE USER hrms_user WITH PASSWORD 'SecurePassword123';
ALTER ROLE hrms_user SET client_encoding TO 'utf8';
GRANT ALL PRIVILEGES ON DATABASE hrms_production TO hrms_user;
\q
```

---

## Step 2: Clone & Configure (5 minutes)

```powershell
# Navigate to your project
cd 'c:\Users\durve\Downloads\HR management system'

# Create production config
Copy-Item .env.production.example .env.production

# Edit .env.production with your settings
notepad .env.production
```

**Minimum required in `.env.production`:**
```bash
DATABASE_URL=postgresql://hrms_user:SecurePassword123@localhost:5432/hrms_production
FLASK_ENV=production
SECRET_KEY=your-secret-key-12345
SERVER_NAME=hr-management-system.local
```

---

## Step 3: Run Deployment Script (5 minutes)

```powershell
# Run the deployment script
.\scripts\deploy-windows.ps1
```

This will automatically:
- ✓ Create Python virtual environment
- ✓ Install all dependencies
- ✓ Test database connection
- ✓ Initialize database
- ✓ Collect static files
- ✓ Test application

---

## Step 4: Start the Application (2 minutes)

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Start with Gunicorn
gunicorn --workers 4 --bind 0.0.0.0:8000 run:app
```

You should see:
```
[2026-08-13 12:34:56 +0000] [1234] [INFO] Listening at: http://0.0.0.0:8000
[2026-08-13 12:34:56 +0000] [1234] [INFO] Using worker: sync
```

---

## Step 5: Access & Test (1 minute)

**Open browser and go to:**
```
http://localhost:8000
```

**Login with:**
- Employee Code: `E-2603028`
- Password: `Test@123` (or set your own)
- Department: Select from dropdown

✓ You're running on your infrastructure!

---

## Access from Other Machines

### Option A: Same Network (LAN)

1. **Find your IP:**
   ```powershell
   ipconfig | findstr "IPv4"
   # Look for: IPv4 Address . . . . . . . . . . . : 192.168.x.x
   ```

2. **Access from another computer:**
   ```
   http://192.168.x.x:8000
   ```

### Option B: External Access (Internet)

1. **Port Forward on Router:**
   - Login to router (192.168.1.1 or similar)
   - Port Forward: External 80/443 → Internal 192.168.x.x:8000
   - Enable UPnP (if available)

2. **Get Static IP (or use DynamicDNS):**
   - Set static IP in router: 192.168.x.x
   - Or register free domain at DuckDNS, NoIP, etc.

3. **Access from anywhere:**
   ```
   http://your-ip-or-domain.com
   ```

---

## Production Setup (Install as Service)

### Windows Service with NSSM

```powershell
# 1. Download NSSM
# https://nssm.cc/download

# 2. Extract to C:\nssm

# 3. Install service (as Administrator)
cd C:\nssm\win64
.\nssm.exe install HRMSApp "C:\Python312\python.exe" "c:\Users\durve\Downloads\HR management system\run.py"

# 4. Set working directory
.\nssm.exe set HRMSApp AppDirectory "c:\Users\durve\Downloads\HR management system"

# 5. Set environment
.\nssm.exe set HRMSApp AppEnvironmentExtra DATABASE_URL=postgresql://hrms_user:SecurePassword123@localhost/hrms_production

# 6. Start service
.\nssm.exe start HRMSApp

# 7. Check status
.\nssm.exe status HRMSApp

# 8. View logs
.\nssm.exe get HRMSApp AppStdout
```

**Service is now:**
- ✓ Running automatically on startup
- ✓ Restarts if it crashes
- ✓ Accessible 24/7
- ✓ Appears in Windows Services

---

## Add SSL/HTTPS (Optional but Recommended)

### Free SSL with Let's Encrypt (on Linux/Mac)

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot certonly --webroot -w /var/www/hrms -d your-domain.com

# Auto-renew
sudo systemctl enable certbot.timer
```

### On Windows with Nginx

See `DEPLOYMENT_GUIDE.md` for Nginx setup with free SSL.

---

## Troubleshooting

### "Connection refused" on port 5432
```powershell
# Check if PostgreSQL is running
Get-Service PostgreSQL* | Select-Object Status, Name

# Or if using Docker
docker ps

# If not running, start it
docker start hrms-postgres
```

### "Port 8000 already in use"
```powershell
# Find what's using port 8000
Get-NetTCPConnection -LocalPort 8000

# Kill the process
taskkill /PID <process-id> /F
```

### Application won't start
```powershell
# Run in foreground to see errors
python run.py

# Check if all imports work
python -c "from app import create_app; print('✓ Imports OK')"
```

### Can't connect from other machines
```powershell
# Check firewall allows port 8000
netsh advfirewall firewall add rule name="Allow HRMS" dir=in action=allow protocol=tcp localport=8000

# Or disable firewall for testing
netsh advfirewall set allprofiles state off
```

---

## Monitor & Maintain

### Health Check

```powershell
# Test if application is running
Invoke-WebRequest http://localhost:8000/health

# Should return: {"status": "ok"}
```

### View Logs

```powershell
# If running as service
Get-EventLog -LogName Application -Source HRMSApp -Newest 20

# If running in terminal
# Scroll up to see console output
```

### Backup Database

```powershell
# Backup PostgreSQL
$BackupPath = "C:\Backups\HRMS"
New-Item -ItemType Directory -Path $BackupPath -Force
pg_dump -U hrms_user hrms_production | gzip > "$BackupPath\hrms_backup_$(Get-Date -Format 'yyyy-MM-dd').sql.gz"

# Restore from backup
gunzip < $BackupPath\hrms_backup_2026-08-13.sql.gz | psql -U hrms_user hrms_production
```

---

## Performance Optimization

### Increase Workers (if slow)

```powershell
# Edit .env.production
WORKERS=8  # Increase from 4 to 8

# Restart service
.\nssm.exe restart HRMSApp
```

### Enable Redis Cache (optional)

```powershell
# Install Redis
docker run -d `
  --name hrms-redis `
  -p 6379:6379 `
  redis:7-alpine

# Add to .env.production
REDIS_URL=redis://localhost:6379/0
CACHE_TYPE=redis

# Restart application
```

---

## Summary

| Step | Time | Command |
|------|------|---------|
| 1. PostgreSQL | 5 min | Docker or installer |
| 2. Configure | 5 min | Edit `.env.production` |
| 3. Deploy | 5 min | `.\scripts\deploy-windows.ps1` |
| 4. Start | 1 min | `gunicorn --workers 4 ...` |
| 5. Access | 1 min | http://localhost:8000 |

**Total: 17 minutes to production!**

---

## Next Level: Advanced

- [x] Self-hosted on your infrastructure
- [ ] Set up SSL/HTTPS for security
- [ ] Configure Nginx reverse proxy
- [ ] Enable automated backups
- [ ] Set up monitoring & alerting
- [ ] Scale to multiple servers
- [ ] Use Docker Compose for easy deployment
- [ ] Set up CI/CD for auto-deployment

See `DEPLOYMENT_GUIDE.md` for advanced topics.

---

## Support

If you get stuck:
1. Check `DEPLOYMENT_GUIDE.md` for detailed guides
2. Review Troubleshooting section above
3. Check application logs
4. Verify database connection
5. Test network connectivity

**Your Smart HRMS is now fully self-hosted! 🚀**
