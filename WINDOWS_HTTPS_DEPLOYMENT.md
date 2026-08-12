# Smart HRMS HTTPS Deployment for Windows Server (Internal Network)

## Overview
Deploy Smart HRMS with HTTPS on internal company network using Nginx reverse proxy and self-signed certificate.

**Current State:**
- Flask app running on `http://192.168.0.5:3001`
- GPS geolocation blocked (requires HTTPS or localhost)
- Camera access blocked (requires HTTPS or localhost)

**Final State:**
- Flask app still runs internally on port 3001
- Nginx listens on port 443 (HTTPS)
- Employees access: `https://192.168.0.5` (or your internal domain)
- GPS and camera work on HTTPS

---

## Part 1: Generate Self-Signed Certificate for Internal Network

### Step 1.1: Download and Install OpenSSL

If not installed, download from: https://slproweb.com/products/Win32OpenSSL.html
- Choose "Win64 OpenSSL v3.x"
- Install to default location
- Add to PATH if prompted

### Step 1.2: Generate Certificate and Key

Run in PowerShell as Administrator:

```powershell
# Create certificates directory
mkdir C:\Smart_HRMS\certs
cd C:\Smart_HRMS\certs

# Generate private key and self-signed certificate (valid 10 years for internal use)
openssl req -x509 -nodes -days 3650 -newkey rsa:2048 `
  -keyout smart-hrms.key `
  -out smart-hrms.crt `
  -subj "/C=IN/ST=Maharashtra/L=YourCity/O=YourCompany/CN=192.168.0.5"

# Verify files created
dir

# Output should show:
#   smart-hrms.key  (private key)
#   smart-hrms.crt  (certificate)
```

**Files created:**
- `C:\Smart_HRMS\certs\smart-hrms.key` — Private key (keep secure)
- `C:\Smart_HRMS\certs\smart-hrms.crt` — Public certificate

---

## Part 2: Install Nginx on Windows

### Step 2.1: Download Nginx

1. Go to: http://nginx.org/en/download.html
2. Download: "nginx/Windows-1.x.x" (mainline or stable)
3. Extract to: `C:\Smart_HRMS\nginx`

### Step 2.2: Verify Installation

```powershell
cd C:\Smart_HRMS\nginx
.\nginx.exe -v
# Output: nginx version: nginx/1.x.x
```

---

## Part 3: Configure Nginx as Reverse Proxy

### Step 3.1: Create Nginx Configuration

Create file: `C:\Smart_HRMS\nginx\conf\nginx.conf`

```nginx
# ============================================================================
# Smart HRMS Nginx Configuration — HTTPS Reverse Proxy
# Internal Corporate Deployment (Self-Signed Certificate)
# ============================================================================

user nobody;
worker_processes auto;
error_log logs/error.log warn;
pid logs/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log logs/access.log main;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    # ========================================================================
    # HTTPS Server — Smart HRMS Reverse Proxy
    # ========================================================================
    server {
        listen 443 ssl;
        server_name 192.168.0.5;

        # SSL Certificate Configuration
        ssl_certificate C:/Smart_HRMS/certs/smart-hrms.crt;
        ssl_certificate_key C:/Smart_HRMS/certs/smart-hrms.key;

        # SSL Protocol and Cipher Security
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;
        ssl_prefer_server_ciphers on;
        ssl_session_cache shared:SSL:10m;
        ssl_session_timeout 10m;

        # Access Logs
        access_log logs/https_access.log main;
        error_log logs/https_error.log;

        # ====================================================================
        # Reverse Proxy to Flask Application
        # ====================================================================
        location / {
            proxy_pass http://127.0.0.1:3001;
            
            # ── Essential Headers ─────────────────────────────────────────
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header X-Forwarded-Host $server_name;

            # ── Session & Cookie Handling ──────────────────────────────────
            proxy_cookie_path / "/";
            proxy_cookie_flags ~ secure httponly;

            # ── Connection Handling ────────────────────────────────────────
            proxy_http_version 1.1;
            proxy_set_header Connection "";
            proxy_buffering off;
            proxy_request_buffering off;

            # ── Timeout Configuration ──────────────────────────────────────
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        # ====================================================================
        # Security Headers (preserve geolocation & camera access)
        # ====================================================================
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Referrer-Policy "strict-origin-when-cross-origin" always;
        
        # !! CRITICAL: Allow geolocation and camera !!
        # Without this, navigator.geolocation and camera are blocked.
        add_header Permissions-Policy "microphone=()" always;

        # Strict-Transport-Security (enforce HTTPS after first visit)
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    }

    # ========================================================================
    # HTTP Server — Redirect to HTTPS (security best practice)
    # ========================================================================
    server {
        listen 80;
        server_name 192.168.0.5;
        return 301 https://$server_name$request_uri;
    }
}
```

**Save this file exactly as shown.**

---

## Part 4: Start Nginx and Flask

### Step 4.1: Make Sure Flask is Running

On your Windows server, ensure Flask app is running on port 3001:

```powershell
# From your Smart HRMS project directory
cd C:\Users\YourUser\Downloads\HR\ management\ system\smart_hrms
python run.py
# Or if using a launcher script:
.\start-app.cmd
```

**Keep this PowerShell window open (Flask must stay running).**

### Step 4.2: Start Nginx

Open **NEW PowerShell window as Administrator**:

```powershell
cd C:\Smart_HRMS\nginx
.\nginx.exe

# Verify it's running
echo "Nginx started on port 443"

# To check if running:
netstat -ano | findstr :443

# You should see nginx.exe in the output
```

**Keep this window open too, or Nginx will stop.**

### Step 4.3: Test HTTPS Connection

Open browser on your server machine:

```
https://192.168.0.5
```

**Expected behavior:**
1. Browser shows "Not secure" or certificate warning (normal for self-signed cert)
2. Click "Advanced" → "Proceed to 192.168.0.5"
3. Smart HRMS attendance page loads
4. No more GPS error!

---

## Part 5: Trust Certificate on Employee Devices

### For Employee Devices to Trust the Certificate:

**Option A: Windows PC (Recommended for corporate)**

1. On the server, export certificate:
```powershell
# Export certificate to file
openssl x509 -in C:\Smart_HRMS\certs\smart-hrms.crt -outform DER -out C:\Smart_HRMS\certs\smart-hrms.cer

# Copy smart-hrms.cer to employee PCs via USB or share folder
```

2. On each employee PC, double-click `smart-hrms.cer`:
   - Select "Install Certificate"
   - Choose "Local Machine"
   - Select "Place all certificates in the following store"
   - Browse → Select "Trusted Root Certification Authorities"
   - Click OK
   - Reboot (recommended)

**Option B: Via Group Policy (If you have Active Directory)**
- IT can deploy certificate to all PCs via Group Policy
- Contact your IT department for assistance

**Option C: Chrome/Edge Managed Certificate (For testing)**
- Open `https://192.168.0.5`
- Let browser show warning
- Click "Advanced" → "Proceed" (one-time per browser per device)

---

## Part 6: Firewall Configuration

### Windows Firewall Rules

```powershell
# Allow HTTPS (port 443) inbound
netsh advfirewall firewall add rule name="Smart HRMS HTTPS" `
  dir=in action=allow protocol=tcp localport=443 profile=domain,private

# Allow HTTP (port 80) inbound for redirect
netsh advfirewall firewall add rule name="Smart HRMS HTTP Redirect" `
  dir=in action=allow protocol=tcp localport=80 profile=domain,private

# Verify rules added
netsh advfirewall firewall show rule name="Smart HRMS*"
```

---

## Part 7: Verify GPS and Camera Work

### Test GPS Functionality

1. Open `https://192.168.0.5/attendance/` from employee device
2. **Expected: No GPS error!**
3. GPS should show: "✓ GPS locked — Xm accuracy"
4. Allow geolocation when browser prompts

### Test Camera Functionality

1. On attendance page, click "Click to Open Camera"
2. Allow camera access when browser prompts
3. Should see live camera feed
4. Click "Capture Selfie" button
5. Preview image should appear below
6. Click "Check In Now" to submit

---

## Part 8: Production Setup (Optional Auto-Start)

### Auto-Start Flask on Windows Boot

Create file: `C:\Smart_HRMS\start-flask.cmd`

```batch
@echo off
cd C:\Users\YourUser\Downloads\HR\ management\ system\smart_hrms
python run.py
pause
```

Use Windows Task Scheduler to run this on startup:
1. Open Task Scheduler
2. Create Basic Task
3. Name: "Smart HRMS Flask"
4. Trigger: "At startup"
5. Action: "Start a program" → Browse to `start-flask.cmd`
6. Run whether user is logged in or not

### Auto-Start Nginx on Windows Boot

Create file: `C:\Smart_HRMS\start-nginx.cmd`

```batch
@echo off
cd C:\Smart_HRMS\nginx
start nginx.exe
echo Nginx started
```

Add to Task Scheduler same way as Flask.

---

## Part 9: Troubleshooting

### Nginx Won't Start

```powershell
# Check for errors
cd C:\Smart_HRMS\nginx
.\nginx.exe -t
# Should show: "successful" if config is valid

# Check if port 443 is already in use
netstat -ano | findstr :443

# If something is using port 443, stop it or change Nginx port in nginx.conf
```

### GPS Still Shows Error

1. Verify URL is HTTPS (not HTTP)
2. Verify Nginx is running: `netstat -ano | findstr :443`
3. Verify Flask is running on port 3001: `netstat -ano | findstr :3001`
4. Check browser console (F12) for errors
5. Check Nginx error log: `C:\Smart_HRMS\nginx\logs\error.log`

### Camera Not Working

1. Browser must show HTTPS and no certificate warnings
2. Click "Allow" when browser asks for camera permission
3. Check Nginx Permissions-Policy header is not blocking camera
4. Verify microphone permissions (Settings > Privacy & Security > Camera/Microphone)

### Certificate Warning Won't Go Away

This is **expected** for self-signed certificates. Employee devices must:
1. Click "Advanced"
2. Click "Proceed to 192.168.0.5"
3. OR install the certificate on their device (Part 5)

---

## Part 10: Verify Deployment

### Check Everything is Working

1. **HTTPS Connection:**
   ```
   https://192.168.0.5 → Should load Smart HRMS
   ```

2. **GPS Enabled:**
   - Go to Attendance page
   - Should show: "✓ GPS locked — Xm accuracy"
   - NOT: "GPS Error: Only secure origins..."

3. **Camera Enabled:**
   - Click "Click to Open Camera"
   - Should see live camera feed
   - NOT: "Camera: Cannot read properties of undefined"

4. **Check-In Works:**
   - Capture selfie
   - Check-in should succeed
   - Attendance recorded in database

5. **Device IP Endpoint (Super Admin):**
   - Navigate to: `https://192.168.0.5/attendance/api/current-device-ip`
   - Should show: `{"ip_address": "192.168.0.X", "is_allowed": true/false}`

---

## Important Notes

⚠️ **CRITICAL: Do NOT modify existing functionality!**
- Flask app code unchanged
- Database unchanged
- GPS radius logic unchanged
- Photo proof requirements unchanged
- Employee check-in/check-out logic unchanged
- Navigation UI unchanged

✅ **What was changed:**
- Added Nginx reverse proxy (external to Flask)
- Added SSL certificate (external to Flask)
- No Flask code modifications

✅ **What continues to work:**
- All attendance features
- GPS verification with 30m radius (or your configured radius)
- Photo proof capture
- Check-in/check-out notifications
- Leave approval
- Payroll
- All other HRMS features

---

## Next Steps

1. ✅ Generate certificate (Part 1)
2. ✅ Install Nginx (Part 2)
3. ✅ Create nginx.conf (Part 3)
4. ✅ Start Flask and Nginx (Part 4)
5. ✅ Test HTTPS connection (Part 4, Step 4.3)
6. ✅ Trust certificate on employee devices (Part 5)
7. ✅ Configure firewall (Part 6)
8. ✅ Verify GPS and camera (Part 7)
9. ✅ (Optional) Set up auto-start (Part 8)

---

## Support

If you encounter issues:
1. Check error logs: `C:\Smart_HRMS\nginx\logs\error.log`
2. Verify ports: `netstat -ano | findstr :443` and `netstat -ano | findstr :3001`
3. Test config: `C:\Smart_HRMS\nginx\nginx.exe -t`
4. Restart both services (stop and start)

---

**You're now ready to use Smart HRMS with HTTPS on your internal company network!**
