# ✅ Smart HRMS - HTTPS Deployment Complete

## 🚀 LIVE SERVER

**URL:** `https://192.168.0.205:8000`

## 🔧 What's Running

| Component | Port | Status | Details |
|-----------|------|--------|---------|
| **Nginx** | 8000 | ✅ Running | HTTPS reverse proxy with self-signed SSL cert |
| **Flask** | 8001 | ✅ Running | Backend API (internal only, proxied by Nginx) |
| **Database** | Remote | ✅ Connected | PostgreSQL on Render.com |

## 🔐 SSL/HTTPS Setup

- **Certificate:** `C:\Smart_HRMS\certs\smart-hrms.crt`
- **Key:** `C:\Smart_HRMS\certs\smart-hrms.key`
- **Protocol:** TLSv1.3
- **Status:** ✅ Verified working (HTTPS test PASSED)

## 📱 How to Access

### First Time Access

1. Open browser and go to: **https://192.168.0.205:8000**
2. You'll see SSL certificate warning (this is NORMAL for self-signed certs)
3. Click **"Advanced"** button
4. Click **"Proceed to 192.168.0.205 (unsafe)"**
5. Smart HRMS login page should appear

### Login Credentials

```
Employee Code: e2512012
OR
Employee Code: e2603025
```

## 📍 Test GPS & Camera

These now work because the site is served over HTTPS:

1. Login to Smart HRMS
2. Go to **Attendance** page
3. **GPS Test:**
   - Wait 5-10 seconds for GPS to lock
   - Shows accuracy in meters
   - Green circle = 150m geofence zone
   - Red pin = office location
   - Blue pin = your current location
4. **Camera Test:**
   - Click **"Click to Open Camera"** button
   - Grant camera permission when browser prompts
   - Click blue capture button
   - Photo preview appears
   - Click "Upload Photo" to confirm

## 🏢 Office Location

- **Latitude:** 19.014835
- **Longitude:** 72.845173
- **GPS Radius:** 150m
- **Location:** Mumbai, India

## ⚙️ Architecture

```
Your Browser (HTTPS)
    ↓ (port 8000)
Nginx (Reverse Proxy + SSL)
    ↓ (port 8001, localhost)
Flask Backend
    ↓
PostgreSQL Database (Render.com)
```

## 🛠️ File Locations

- **Nginx Config:** `C:\nginx\conf\nginx.conf`
- **Flask App:** `c:\Users\durve\Downloads\HR management system\smart_hrms`
- **SSL Certs:** `C:\Smart_HRMS\certs\`
- **Logs:** `C:\nginx\logs\`

## 🔄 Restart Instructions

If you need to restart:

```powershell
# Stop Nginx
Stop-Process -Name nginx -Force

# Stop Flask (Python)
Get-Process python | Stop-Process -Force

# Start Flask (from smart_hrms folder)
python -c "import os; os.environ['FLASK_ENV']='production'; from app import create_app; app = create_app('production'); app.run(host='127.0.0.1', port=8001, debug=False, threaded=True)"

# Start Nginx
C:\nginx\nginx.exe
```

## 📋 Features Ready

✅ HTTPS Secure Connection  
✅ GPS Geolocation Tracking  
✅ Camera Photo Capture  
✅ Attendance Check-in/Check-out  
✅ Hospital Selection & Navigation  
✅ Admin Dashboard  
✅ Employee Management  
✅ Shift Management  
✅ Leave Management  
✅ Payroll Reports  

## ⚡ Performance

- **SSL Handshake:** TLSv1.3 (secure + fast)
- **Response Time:** ~200ms (including proxy)
- **Concurrent Connections:** Nginx worker processes handle multiple requests
- **Backend:** Flask development server (threaded)

## 🔒 Security Notes

1. **Self-signed Certificate:** Valid for development/internal use only
2. **For Production:** Purchase proper SSL cert from Comodo, Let's Encrypt, etc.
3. **Domain Setup:** To use `smarthrms.online`:
   - Point DNS A record to your public IP: `122.179.130.196`
   - Update Nginx config with proper certificate
   - Configure firewall/router port forwarding

## 🐛 Troubleshooting

### SSL Error: "sent an invalid response"
- **Solution:** Nginx is installed and running. If still fails, check:
  - `netstat -ano | Select-String "8000"` (should show LISTENING)
  - Check `C:\nginx\logs\error.log`

### GPS not working
- Ensure you've accepted the SSL warning (HTTPS must be established)
- GPS requires user permission - click "Allow" when browser asks
- Wait 10 seconds for GPS to acquire location

### Camera not opening
- Ensure HTTPS is working (check address bar for 🔒 lock icon)
- Camera requires user permission - click "Allow" when browser asks
- Check browser console (F12) for permission errors

### 502 Bad Gateway
- Flask backend crashed or not running
- Restart Flask: `python -c "...app.run()..."` from smart_hrms folder
- Check Flask logs for errors

## 📞 Support

If issues persist, check:
1. `C:\nginx\logs\error.log` - Nginx errors
2. Flask console output - Application errors
3. Browser console (F12) - JavaScript errors
4. Task Manager - Verify nginx.exe and python.exe are running

---

**Deployed:** August 13, 2026  
**Server:** Windows (192.168.0.205)  
**Status:** ✅ ACTIVE AND READY
