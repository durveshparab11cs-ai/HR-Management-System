# 🚀 Smart HRMS - Server Management Guide

## Quick Start

### Option 1: Double-Click to Start (Easiest)
```
1. Go to: C:\Users\durve\Downloads\HR management system\
2. Double-click: START_SERVER.bat
3. Server starts automatically with auto-restart enabled
```

### Option 2: Command Line
```powershell
cd "C:\Users\durve\Downloads\HR management system\smart_hrms"
python run_production.py
```

---

## ✅ Server Features

### Auto-Restart on Crash
- ✅ Crashes detected automatically
- ✅ Server restarts within 5-30 seconds
- ✅ No manual intervention needed
- ✅ Infinite restarts (never stops)

### Comprehensive Logging
- ✅ All events logged to: `smart_hrms/logs/production_server.log`
- ✅ Errors logged separately to: `smart_hrms/logs/production_errors.log`
- ✅ Timestamps on all log entries
- ✅ Easy debugging with error traces

### Health Monitoring
- ✅ Check if server is running: `python health_check.py`
- ✅ Verify all endpoints responding
- ✅ Get instant status report

---

## 🔍 How to Check Server Status

### Method 1: Health Check Script (Recommended)
```powershell
cd "C:\Users\durve\Downloads\HR management system\smart_hrms"
python health_check.py
```

**Output example:**
```
╔════════════════════════════════════════════════════════════════════════════╗
║  Smart HRMS - Health Check                                                 ║
╚════════════════════════════════════════════════════════════════════════════╝

Checking endpoints...

  ✅ Home                 → 302
  ✅ Coordinator         → 302
  ✅ Employee Portal     → 200
  ✅ Admin               → 302
  ✅ Login               → 200

================================================================================
SUMMARY
================================================================================
  ✅ Passed: 5/5
  ❌ Failed: 0/5

  🎉 Server is HEALTHY and all endpoints responding!
================================================================================
```

### Method 2: Try Accessing in Browser
```
https://192.168.0.205:8000/coordinator/
```

Should see login page or coordinator dashboard.

### Method 3: Check Log Files
```powershell
# View live logs (last 20 lines)
Get-Content "smart_hrms/logs/production_server.log" -Tail 20

# View error logs
Get-Content "smart_hrms/logs/production_errors.log" -Tail 20
```

---

## 🛑 How to Stop Server

### Method 1: Press Ctrl+C in Terminal
```
Server will stop gracefully
All connections will be closed
Logs will be written
```

### Method 2: Kill Process (if unresponsive)
```powershell
# Find Flask process
Get-Process python | Where-Object {$_.ProcessName -like "*python*"}

# Kill process (replace PID with actual number)
Stop-Process -Id <PID> -Force
```

---

## 📊 Log File Locations

### Production Server Log
```
C:\Users\durve\Downloads\HR management system\smart_hrms\logs\production_server.log
```

Contains:
- Server startup/shutdown messages
- Request logs
- Restart notifications
- General information

### Error Log
```
C:\Users\durve\Downloads\HR management system\smart_hrms\logs\production_errors.log
```

Contains:
- Exception traces
- Error details
- Stack traces
- Crash information

### Attendance Module Log
```
C:\Users\durve\Downloads\HR management system\smart_hrms\logs\attendance.log
```

Contains:
- Check-in/check-out details
- GPS validation results
- Photo upload logs

---

## 🔧 Troubleshooting

### Problem: Server Won't Start

**Solution 1: Check Python is Installed**
```powershell
python --version
```

Should show Python 3.x

**Solution 2: Check Dependencies**
```powershell
cd "smart_hrms"
pip install -r requirements.txt
```

**Solution 3: Check Certificate Files**
```powershell
ls "C:\Smart_HRMS\certs\"
```

Should show:
- smart-hrms.crt
- smart-hrms.key

**Solution 4: Check Port 8000 is Available**
```powershell
netstat -ano | findstr :8000
```

If port is in use, kill the process:
```powershell
Stop-Process -Id <PID> -Force
```

### Problem: Server Crashes Repeatedly

**Check Error Log:**
```powershell
Get-Content "smart_hrms/logs/production_errors.log" -Tail 50
```

Look for:
- Import errors → Check dependencies
- Database errors → Check database connection
- SSL errors → Check certificate files
- Memory errors → Restart server, reduce load

**Solution: Clear Logs and Restart**
```powershell
rm "smart_hrms/logs/*.log"
cd "smart_hrms"
python run_production.py
```

### Problem: Can't Access https://192.168.0.205:8000

**Checklist:**
1. ✅ Server running? → Check process: `Get-Process python`
2. ✅ HTTPS working? → Check browser console for SSL errors
3. ✅ Port 8000? → Check: `netstat -ano | findstr :8000`
4. ✅ Network? → Ping: `ping 192.168.0.205`
5. ✅ Firewall? → Allow port 8000

**Solution: Restart Everything**
```powershell
# Stop old process
Stop-Process -Name python -Force -ErrorAction SilentlyContinue

# Wait 2 seconds
Start-Sleep -Seconds 2

# Start fresh
cd "C:\Users\durve\Downloads\HR management system\smart_hrms"
python run_production.py
```

### Problem: "This site can't be reached" (ERR_CONNECTION_TIMED_OUT)

**Means:** Server process is not responding

**Immediate Fix:**
1. Open Task Manager (Ctrl+Shift+Esc)
2. Find "python.exe" processes
3. Right-click → End Task
4. Wait 3 seconds
5. Double-click START_SERVER.bat to restart
6. Try browser again

**Permanent Fix (Auto-Restart Enabled):**
- Server WILL auto-restart on crash
- No manual intervention needed
- System has 999 restart attempts configured

---

## 📈 Monitoring Server Health

### Real-Time Monitoring
```powershell
# Watch logs in real-time
Get-Content -Path "smart_hrms/logs/production_server.log" -Wait
```

### Daily Health Check
Run this every morning:
```powershell
python "C:\Users\durve\Downloads\HR management system\smart_hrms\health_check.py"
```

### Weekly Log Review
```powershell
# Check error count
(Get-Content "smart_hrms/logs/production_errors.log" | Measure-Object -Line).Lines

# Check crash count  
(Get-Content "smart_hrms/logs/production_server.log" | Select-String "crashed" | Measure-Object).Count
```

---

## 🔐 Security Notes

### SSL Certificate
- Valid for 10 years (until 2036-08-11)
- Self-signed (browser will warn)
- Encryption working correctly

### Access Control
- Coordinator portal: Login required
- Employee portal: Public access
- Admin dashboard: Login required

### Firewall
- Port 8000 must be open on company LAN
- HTTPS uses port 443 in production (port 8000 for development)

---

## 📝 Configuration Files

### Main Configuration
```
smart_hrms/config/settings.py
```

Contains:
- Database connection
- Security settings
- Session timeout
- Mail configuration

### Environment Variables (.env)
```
FLASK_ENV=production
DATABASE_URL=...
SECRET_KEY=...
```

### Server Startup Script
```
run_production.py  ← Main server runner
START_SERVER.bat   ← Windows batch file
health_check.py    ← Health monitoring
```

---

## 🎯 Expected Behavior

### Normal Startup (< 5 seconds)
```
Step 1: Importing Flask modules... ✅
Step 2: Creating Flask application... ✅
Step 3: Configuring SSL/HTTPS... ✅
✅ Server is now LIVE and listening...
```

### Server Responding
- All endpoints return 200 or 302
- Health check shows all ✅
- Logs show no errors

### Server Crashes (Auto-Restart)
```
ERROR: Server crashed
⚠️  Server crashed, restarting in 5 seconds...
▶️  Attempt 2 (retry)
...server restarts automatically
```

---

## 🚨 Critical Issues

### Issue 1: Coordinator Portal 404 Not Found
**Cause:** Blueprint not registered  
**Fix:** Restart server, check logs for import errors

### Issue 2: Database Connection Failed
**Cause:** Database not running or connection string wrong  
**Fix:** Check DATABASE_URL in .env, verify database service

### Issue 3: SSL Certificate Error
**Cause:** Certificate files missing or corrupted  
**Fix:** Regenerate certificates, check C:\Smart_HRMS\certs\

### Issue 4: Port 8000 Already in Use
**Cause:** Another process using port 8000  
**Fix:** Kill process using port 8000, wait 5 seconds, restart

---

## 📞 Quick Support Checklist

| Issue | Command |
|-------|---------|
| Server down? | `python health_check.py` |
| Can't access? | Check logs: `Get-Content smart_hrms/logs/*.log -Tail 50` |
| Slow? | Restart server: `Ctrl+C`, then `python run_production.py` |
| Crashes repeatedly? | Check error log for root cause |
| Port in use? | `netstat -ano \| findstr :8000` then kill process |

---

## ✅ Maintenance Schedule

### Daily
- ✅ Verify server is running (health check)
- ✅ Check error logs for issues

### Weekly
- ✅ Review log files for errors
- ✅ Monitor CPU/memory usage
- ✅ Test all endpoints

### Monthly
- ✅ Backup database
- ✅ Rotate log files
- ✅ Update dependencies if needed

### Quarterly
- ✅ Full system backup
- ✅ Security audit
- ✅ Performance optimization

---

## 🎓 Training

### For IT Support
- Read this entire guide
- Test server startup/shutdown
- Practice troubleshooting with error logs
- Know how to restart on crash

### For System Admin
- Monitor weekly health checks
- Maintain log files
- Plan capacity upgrades
- Document any issues

### For Users
- Just use the system!
- Report if access problems
- Check user guides for features

---

## 📞 Support Contacts

### Technical Issues
Email: [IT Support]  
Phone: [IT Hotline]

### Coordinator Portal Help
Email: [HR Manager]  
Desk: [HR Office]

### Database/System
Email: [DBA]  
Phone: [DBA Hotline]

---

**Last Updated:** August 14, 2026  
**Version:** 1.0  
**Status:** ✅ Production Ready

---

## 🎉 You're All Set!

Server has auto-restart enabled. Even if it crashes, it will automatically restart without any manual intervention.

**TO START SERVER:**
1. Double-click `START_SERVER.bat`
2. Access `https://192.168.0.205:8000`
3. System will auto-restart on any crash

**THAT'S IT! No more issues! 🚀**
