# Smart HRMS HTTPS Deployment Guide

**Server:** Windows Internal Network  
**IP Address:** 192.168.0.5  
**Date Deployed:** August 12, 2026  
**Status:** ✅ Production Ready

---

## 🎯 Quick Start

### Access the Server

```
https://192.168.0.5
```

**Note:** Your browser will show a security warning because the SSL certificate is self-signed. This is normal for internal network deployments. Accept the warning to proceed.

### Starting the Server

Run the PowerShell startup script:

```powershell
PowerShell -ExecutionPolicy Bypass -File "c:\Users\durve\Downloads\HR management system\start_https_server.ps1"
```

Or use the batch file:

```batch
"c:\Users\durve\Downloads\HR management system\start_server.bat"
```

---

## 🏗️ Architecture

### Component Stack

```
Browser (HTTPS)
    ↓
[Nginx Reverse Proxy]  — Ports 80, 443
    ↓ (HTTP)
[Flask Backend]        — Port 5000 (127.0.0.1)
    ↓
[PostgreSQL]           — Render Cloud Database
```

### Why This Architecture?

- **Nginx on 443 (HTTPS)** → Handles SSL/TLS encryption, provides reverse proxy
- **Flask on 5000 (HTTP)** → Internal backend, only accessible locally
- **Port 80** → Automatic redirect to HTTPS
- **Render PostgreSQL** → Cloud database for scalability

### Ports Configuration

| Port | Service | Purpose |
|------|---------|---------|
| 80   | Nginx   | HTTP redirect to HTTPS |
| 443  | Nginx   | HTTPS reverse proxy (external) |
| 5000 | Flask   | Backend server (internal only) |

---

## 🔐 SSL/TLS Configuration

### Certificate Details

- **Type:** Self-signed X.509 certificate
- **Path:** `C:\Smart_HRMS\certs\smart-hrms.crt`
- **Private Key:** `C:\Smart_HRMS\certs\smart-hrms.key`
- **Validity:** 10 years (2026-2036)
- **Created:** August 10, 2026

### Certificate Installation

The certificate is automatically loaded by Nginx. To install in Windows for browser trust:

1. Open `C:\Smart_HRMS\certs\smart-hrms.crt` with Notepad
2. Copy the entire certificate content
3. Open Windows Certificate Manager
4. Go to **Trusted Root Certification Authorities** → **Certificates**
5. Right-click → **All Tasks** → **Import**
6. Paste the certificate
7. Accept all prompts

After installation, the browser warning will disappear.

---

## 🚀 Deployment Files

### Server Startup Scripts

| File | Purpose |
|------|---------|
| `start_https_server.ps1` | PowerShell startup script (recommended) |
| `start_server.bat` | Batch file starter (Windows only) |
| `start_server.ps1` | Legacy PowerShell script |
| `start_production_https.ps1` | Gunicorn variant (not recommended) |

**Recommended:** Use `start_https_server.ps1` for reliable production startup.

### Configuration Files

| File | Location | Purpose |
|------|----------|---------|
| `nginx.conf` | `C:\Smart_HRMS\nginx\conf\nginx.conf` | Nginx reverse proxy configuration |
| `.env` | Project root | Flask environment variables |
| `wsgi.py` | Project root | Flask WSGI entry point (port 5000) |

### Nginx Configuration

Located at: `C:\Smart_HRMS\nginx\conf\nginx.conf`

```nginx
# HTTPS on 443
server {
    listen 443 ssl;
    server_name 192.168.0.5 localhost 127.0.0.1;
    
    ssl_certificate C:/Smart_HRMS/certs/smart-hrms.crt;
    ssl_certificate_key C:/Smart_HRMS/certs/smart-hrms.key;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# HTTP redirect to HTTPS on port 80
server {
    listen 80;
    server_name 192.168.0.5 localhost 127.0.0.1;
    return 301 https://$server_name$request_uri;
}
```

---

## 🔧 System Requirements

- **OS:** Windows 10 or later
- **Network:** Internal LAN (192.168.x.x)
- **Disk Space:** 500 MB minimum
- **RAM:** 2 GB minimum (4 GB recommended)
- **Python:** 3.9+
- **Nginx:** 1.26.1 (included in `C:\Smart_HRMS\nginx\`)

---

## 📝 Environment Configuration

### .env File

Located in project root:

```env
FLASK_ENV=production
DATABASE_URL=postgresql://smart_hrms_user:PASSWORD@dpg-d9bl4t7aqgkc739jhup0-a.singapore-postgres.render.com/smart_hrms
SECRET_KEY=smart-hrms-production-secret-key-2026
```

**Do NOT commit .env to version control.**

### Database Connection

- **Provider:** Render PostgreSQL
- **Region:** Singapore
- **Connection:** Automatic via DATABASE_URL
- **Pool Size:** 10 connections

---

## ✅ Verification Checklist

After starting the server, verify:

### 1. Port Availability

```powershell
netstat -ano | Select-String "80|443|5000"
```

Expected output:
```
TCP 0.0.0.0:80 LISTENING
TCP 0.0.0.0:443 LISTENING
TCP 127.0.0.1:5000 LISTENING
```

### 2. Flask Backend

```powershell
curl http://127.0.0.1:5000/health
```

Expected response:
```json
{"status": "ok"}
```

### 3. HTTPS Connection

Open in browser:
```
https://192.168.0.5
```

Expected: Login page loads (may show certificate warning)

### 4. Browser Console

- No JavaScript errors
- No CORS warnings
- No mixed-content warnings

---

## 🎯 Features Enabled by HTTPS

With HTTPS deployment, the following browser APIs now work:

### ✅ GPS Geolocation
```javascript
navigator.geolocation.getCurrentPosition(...)
```
**Status:** Available on https://192.168.0.5

### ✅ Camera/Microphone
```javascript
navigator.mediaDevices.getUserMedia(...)
```
**Status:** Available on https://192.168.0.5

### ✅ Attendance Check-in
- GPS location capture
- Photo proof with camera
- Real-time attendance sync

---

## 🔧 Troubleshooting

### Port 443 Listening but Getting 404

**Cause:** Nginx not forwarding to Flask on port 5000

**Fix:**
1. Verify `C:\Smart_HRMS\nginx\conf\nginx.conf` has `proxy_pass http://127.0.0.1:5000;`
2. Restart Nginx: `Stop-Process -Name nginx -Force && Start-Process C:\Smart_HRMS\nginx\nginx.exe`
3. Check Flask is running: `netstat -ano | Select-String 5000`

### Certificate Warning in Browser

**Cause:** Self-signed certificate

**Fix (Permanent):** Install the certificate in Windows (see "Certificate Installation" above)

**Fix (Temporary):** Accept the warning and proceed

### Flask Connection Refused

**Cause:** Flask process crashed

**Solution:**
1. Stop all processes: `Get-Process python,nginx | Stop-Process -Force`
2. Restart: `start_https_server.ps1`

### Database Connection Error

**Cause:** PostgreSQL connection failed

**Check:**
1. Verify DATABASE_URL in `.env` file
2. Test connection: `python -c "from app import create_app; app = create_app()"`
3. Check network: Ping database host from firewall

---

## 📊 Monitoring

### Check Running Processes

```powershell
Get-Process | Where-Object {$_.Name -match "nginx|python"}
```

### View Recent Logs

```powershell
Get-Content "c:\Users\durve\Downloads\HR management system\logs\error.log" -Tail 50
```

### Monitor Network Connections

```powershell
netstat -an | Select-String "80|443|5000|ESTABLISHED|LISTENING"
```

---

## 🔒 Security Notes

### Current Configuration

- ✅ HTTPS enabled (TLS 1.2+)
- ✅ Self-signed certificate (internal network)
- ✅ Port 5000 only accessible locally
- ✅ HTTP redirects to HTTPS
- ✅ Secure cookies enabled
- ✅ CSRF protection enabled

### Recommendations for Production

1. **Certificate:** Replace self-signed with purchased/CA-signed certificate
2. **Firewall:** Only allow port 443 from authorized networks
3. **Database:** Use private VPC for database access
4. **Backups:** Daily automated backups of PostgreSQL
5. **Monitoring:** Set up alerts for failed logins
6. **Rate Limiting:** Configure Nginx rate limiting for login endpoint

---

## 📞 Support

### Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| "Server refused connection" | Check if port 443 is open in Windows Firewall |
| "Certificate not trusted" | Install certificate or accept browser warning |
| "Login not working" | Check database connection in .env |
| "GPS/Camera not working" | Verify browser permissions in Settings |
| "Slow performance" | Check database connection pool settings |

### Logs Location

- **Flask Logs:** `c:\Users\durve\Downloads\HR management system\logs\`
- **Nginx Logs:** `C:\Smart_HRMS\nginx\logs\`
- **Windows Event Viewer:** Applications and Services Logs

---

## 🎓 Next Steps

1. **Test Login:** Navigate to https://192.168.0.5 and log in with employee credentials
2. **Check-in Test:** Go to Attendance section and verify GPS/camera work
3. **Browser Compatibility:** Test on Chrome, Firefox, Edge
4. **Mobile Access:** Test from mobile device on same network
5. **Certificate Distribution:** Share certificate with team for automatic trust

---

## ✅ Deployment Summary

| Component | Status | Version |
|-----------|--------|---------|
| Flask | ✅ Running | 2.3.x |
| Nginx | ✅ Running | 1.26.1 |
| PostgreSQL | ✅ Connected | Render Cloud |
| SSL/TLS | ✅ Enabled | 10-year cert |
| Geolocation | ✅ Working | HTML5 Geolocation API |
| Camera | ✅ Working | WebRTC |

**Status:** 🟢 PRODUCTION READY

---

*Last Updated: August 12, 2026*  
*Deployment Engineer: Kiro AI*
