# Smart HRMS - Self-Hosted Production Deployment Guide

**Goal:** Deploy the HR Management System on your own infrastructure with 99.9% uptime reliability.

---

## Table of Contents
1. [System Requirements](#system-requirements)
2. [Database Setup (PostgreSQL)](#database-setup)
3. [Application Configuration](#application-configuration)
4. [Production Server Setup](#production-server-setup)
5. [SSL/HTTPS Setup](#ssltls-setup)
6. [Monitoring & Maintenance](#monitoring--maintenance)
7. [Troubleshooting](#troubleshooting)

---

## System Requirements

### Hardware
- **CPU:** 2+ cores
- **RAM:** 4+ GB
- **Storage:** 20+ GB SSD
- **Network:** Static IP or dynamic DNS

### Software
- **OS:** Windows Server 2016+, Ubuntu 20.04+, or CentOS 8+
- **Python:** 3.9+ (currently 3.12 on your system ✓)
- **Database:** PostgreSQL 12+ or MySQL 8+
- **Web Server:** Nginx or Apache
- **Supervisor/PM2:** Process manager for uptime

---

## Database Setup (PostgreSQL)

### Option 1: Windows - PostgreSQL Installation

```powershell
# Download PostgreSQL installer from https://www.postgresql.org/download/windows/
# Run the installer and follow the wizard

# Verify installation
psql --version
```

### Option 2: Docker (Recommended - Simpler)

```powershell
# Install Docker Desktop from https://www.docker.com/products/docker-desktop

# Run PostgreSQL container
docker run -d `
  --name hrms-postgres `
  -e POSTGRES_USER=hrms_user `
  -e POSTGRES_PASSWORD=SecurePassword123! `
  -e POSTGRES_DB=hrms_production `
  -p 5432:5432 `
  -v hrms_data:/var/lib/postgresql/data `
  postgres:15-alpine
```

### Create Database and User

```sql
-- Connect to PostgreSQL
psql -U postgres

-- Create database
CREATE DATABASE hrms_production;

-- Create user
CREATE USER hrms_user WITH PASSWORD 'SecurePassword123!';

-- Grant privileges
ALTER ROLE hrms_user SET client_encoding TO 'utf8';
ALTER ROLE hrms_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE hrms_user SET default_transaction_deferrable TO on;
ALTER ROLE hrms_user SET default_transaction_deferrable TO on;
GRANT ALL PRIVILEGES ON DATABASE hrms_production TO hrms_user;

-- Verify
\l
```

---

## Application Configuration

### 1. Create Production Environment File

Create `.env.production` in your project root:

```bash
# Database
DATABASE_URL=postgresql://hrms_user:SecurePassword123!@localhost:5432/hrms_production

# Flask
FLASK_ENV=production
SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')
DEBUG=False

# Server
SERVER_NAME=your-server-url.com
PREFERRED_URL_SCHEME=https

# Security
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax
PERMANENT_SESSION_LIFETIME=86400

# Mail (for password resets)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Backup
BACKUP_DIR=/var/backups/hrms
LOG_DIR=/var/log/hrms
```

### 2. Update config/settings.py

```python
# config/settings.py

import os
from datetime import timedelta

class ProductionConfig:
    """Production configuration."""
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'postgresql://hrms_user:SecurePassword123!@localhost:5432/hrms_production'
    )
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
    }
    
    # Security
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'CHANGE-THIS-IN-PRODUCTION')
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # Server
    SERVER_NAME = os.getenv('SERVER_NAME', 'localhost')
    PREFERRED_URL_SCHEME = 'https'
    
    # Logging
    LOG_DIR = os.getenv('LOG_DIR', '/var/log/hrms')
    LOG_LEVEL = 'INFO'
    
    # Upload folder
    UPLOAD_FOLDER = os.path.join(os.path.expanduser('~'), 'hrms_uploads')
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max file
    
    # Cache
    CACHE_TYPE = 'redis'
    CACHE_REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
```

---

## Production Server Setup

### Windows - Using NSSM (Non-Sucking Service Manager)

```powershell
# Download NSSM from https://nssm.cc/download

# Extract to C:\nssm

# Install as Windows Service
cd C:\nssm\win64
.\nssm.exe install HRMSApp "C:\Python312\python.exe" "c:\Users\durve\Downloads\HR management system\run.py"

# Set environment
.\nssm.exe set HRMSApp AppDirectory "c:\Users\durve\Downloads\HR management system"
.\nssm.exe set HRMSApp AppEnvironmentExtra DATABASE_URL=postgresql://hrms_user:pass@localhost/hrms_production

# Start service
.\nssm.exe start HRMSApp

# View logs
.\nssm.exe get HRMSApp AppStdout
```

### Linux - Using Systemd

Create `/etc/systemd/system/hrms.service`:

```ini
[Unit]
Description=Smart HRMS Application
After=network.target postgresql.service

[Service]
Type=notify
User=hrms
WorkingDirectory=/opt/hrms
Environment="DATABASE_URL=postgresql://hrms_user:password@localhost/hrms_production"
Environment="FLASK_ENV=production"
ExecStart=/usr/bin/gunicorn \
    --workers 4 \
    --worker-class sync \
    --bind 127.0.0.1:5000 \
    --access-logfile /var/log/hrms/access.log \
    --error-logfile /var/log/hrms/error.log \
    --log-level info \
    run:app

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable hrms
sudo systemctl start hrms
sudo systemctl status hrms
```

---

## Nginx Configuration (Reverse Proxy)

### Windows - Using Nginx

Download from https://nginx.org/en/download.html

Create `conf/nginx.conf`:

```nginx
upstream hrms_app {
    server 127.0.0.1:5000;
}

server {
    listen 80;
    server_name your-server-url.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-server-url.com;
    
    # SSL certificates (from Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/your-server-url.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-server-url.com/privkey.pem;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Gzip compression
    gzip on;
    gzip_types text/plain text/css text/xml application/json application/javascript;
    
    # Proxy settings
    location / {
        proxy_pass http://hrms_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Static files (cache for 30 days)
    location /static/ {
        alias /var/www/hrms/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # Uploads
    location /uploads/ {
        alias /var/www/hrms/uploads/;
        expires 7d;
    }
}
```

---

## SSL/TLS Setup

### Free SSL with Let's Encrypt

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Or on Windows, download from https://github.com/certbot/certbot/releases

# Get certificate
sudo certbot certonly --webroot -w /var/www/hrms -d your-server-url.com

# Auto-renew (Nginx)
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

---

## Deployment Steps

### 1. Install Dependencies

```powershell
cd 'c:\Users\durve\Downloads\HR management system'

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install packages
pip install -r requirements.txt
pip install gunicorn psycopg2-binary redis
```

### 2. Initialize Database

```powershell
# Export environment
$env:FLASK_ENV = "production"
$env:DATABASE_URL = "postgresql://hrms_user:password@localhost/hrms_production"

# Run migrations
flask db upgrade

# Seed initial data
flask seed-db
```

### 3. Collect Static Files

```powershell
# Copy all static files to serve via Nginx
New-Item -ItemType Directory -Path "C:\var\www\hrms\static" -Force
Copy-Item -Recurse "app\static\*" -Destination "C:\var\www\hrms\static\"
```

### 4. Test Locally

```powershell
# Run with Gunicorn locally
gunicorn --workers 2 --bind 127.0.0.1:5000 run:app

# Visit http://localhost:5000
```

### 5. Deploy as Service

```powershell
# Install NSSM as Windows Service (see section above)
```

---

## Monitoring & Maintenance

### Health Check Script

Create `scripts/health_check.py`:

```python
#!/usr/bin/env python
import requests
import sys
from datetime import datetime

def check_health():
    """Check if the application is running."""
    try:
        response = requests.get('https://your-server-url.com/health', timeout=10)
        if response.status_code == 200:
            print(f"[{datetime.now()}] ✓ Application healthy")
            return True
        else:
            print(f"[{datetime.now()}] ✗ Application returned {response.status_code}")
            return False
    except Exception as e:
        print(f"[{datetime.now()}] ✗ Health check failed: {e}")
        return False

if __name__ == '__main__':
    success = check_health()
    sys.exit(0 if success else 1)
```

Schedule this to run every 5 minutes via Task Scheduler (Windows) or Cron (Linux).

### Backup Strategy

```powershell
# Backup database daily
$BackupPath = "C:\Backups\HRMS"
$Timestamp = Get-Date -Format "yyyy-MM-dd_HHmmss"

pg_dump -U hrms_user hrms_production | gzip > "$BackupPath\hrms_$Timestamp.sql.gz"

# Keep only last 30 days
Get-ChildItem $BackupPath -Filter "hrms_*.sql.gz" | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) } | Remove-Item
```

---

## Server URL Options

### Option 1: Local Network (Company LAN)
- **URL:** `http://192.168.x.x` or `http://hrms-server.local`
- **Pros:** Fast, no internet needed
- **Cons:** Only works on company network

### Option 2: Static IP + Dynamic DNS
- **URL:** `https://your-company-hrms.com`
- **Setup:**
  ```
  1. Get static public IP from ISP
  2. Register domain (GoDaddy, Namecheap)
  3. Point DNS to your IP
  4. Install SSL certificate
  ```

### Option 3: VPN Access
- **URL:** `https://hrms.company-vpn.com`
- **Setup:**
  - Use WireGuard or OpenVPN
  - Connect employees remotely
  - Server stays on private network

---

## Quick Start (Windows)

```powershell
# 1. Install PostgreSQL (or Docker)
# 2. Create database and user
# 3. Update .env.production with your credentials
# 4. Install dependencies
pip install -r requirements.txt

# 5. Initialize database
$env:FLASK_ENV = "production"
$env:DATABASE_URL = "postgresql://hrms_user:password@localhost/hrms_production"
flask db upgrade

# 6. Run with Gunicorn
gunicorn --workers 4 --bind 0.0.0.0:8000 run:app

# 7. Access at http://localhost:8000 (or your server IP)
```

---

## Troubleshooting

### "Connection refused" on database
```powershell
# Check if PostgreSQL is running
Get-Service PostgreSQL* | Select-Object Status, Name

# Or test connection
psql -h localhost -U hrms_user -d hrms_production
```

### "Port already in use"
```powershell
# Find process using port 5000
Get-NetTCPConnection -LocalPort 5000

# Kill it
Stop-Process -Id <PID> -Force
```

### Application won't start
```powershell
# Check logs
Get-Content app.log -Tail 50

# Test locally first
python run.py
```

---

## Next Steps

1. **Choose your server URL** - Local network, static IP, or VPN
2. **Set up PostgreSQL** - Docker is easiest for Windows
3. **Configure .env.production** - Update database and server settings
4. **Test locally** - Run `gunicorn` and verify it works
5. **Deploy as service** - NSSM on Windows or Systemd on Linux
6. **Set up SSL** - Free via Let's Encrypt
7. **Configure Nginx** - Reverse proxy with security headers
8. **Enable backups** - Daily database backups
9. **Set up monitoring** - Health checks every 5 minutes

---

## Support & Questions

For issues:
1. Check logs: `/var/log/hrms/error.log` or Windows Event Viewer
2. Test connectivity: `curl https://your-server-url.com/health`
3. Verify database: `psql -l` or PostgreSQL Management Tool
4. Check services: Task Scheduler (Windows) or `systemctl status` (Linux)

