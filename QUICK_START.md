# Smart HRMS HTTPS - Quick Start

## Status: ✅ LIVE AND OPERATIONAL

All services are running. Employees can access Smart HRMS over HTTPS with GPS and camera working.

---

## Employee Access

### URL
```
https://192.168.0.5
```

### What They'll See
1. Certificate warning (first time only) → Click "Advanced" → "Proceed"
2. Smart HRMS login page
3. Go to Attendance → GPS shows "✓ Locked"
4. Camera button works → live feed appears
5. Check-in/check-out works with photo proof

---

## What's Running

| Service | Port | Status |
|---------|------|--------|
| Nginx HTTP Redirect | 80 | ✅ Running |
| Nginx HTTPS Proxy | 443 | ✅ Running |
| Flask Backend | 3001 | ✅ Running |

---

## Files Location

```
C:\Smart_HRMS\
├── certs/                  (SSL certificates)
├── nginx/                  (Reverse proxy)
└── logs/                   (Error & access logs)

Original App (unchanged):
C:\Users\durve\Downloads\HR management system\
```

---

## Documentation

**Full Details:** `HTTPS_DEPLOYMENT_COMPLETE.md`
- Detailed setup instructions
- Employee device certificate installation
- Troubleshooting guide
- Monitoring & logs
- Permanent auto-start setup

---

## For Employees: Install Certificate (Optional - Removes Warning)

**Windows PC:**
1. Get file: `C:\Smart_HRMS\certs\smart-hrms.cer`
2. Double-click it
3. "Install Certificate" → "Local Machine" → "Trusted Root Certification Authorities"
4. Finish & Reboot
5. No more warnings

**After Installation:** `https://192.168.0.5` shows as "Secure" ✓

---

## Device IP Whitelisting (Optional)

If you want only specific office computers to do check-in/check-out:

Provide me the IPs:
```
192.168.0.100
192.168.0.101
```

I'll register them and only those devices can check-in.

---

## Monitoring

**Check everything is running:**
```powershell
Get-Process nginx
```

**View Nginx error log:**
```powershell
Get-Content C:\Smart_HRMS\nginx\logs\error.log -Tail 20
```

**View access log:**
```powershell
Get-Content C:\Smart_HRMS\nginx\logs\https_access.log -Tail 10
```

---

## Need to Restart?

**Stop Nginx:**
```powershell
C:\Smart_HRMS\nginx\nginx.exe -s quit
```

**Stop Flask:**
- Close Kiro window

**Start Again:**
```powershell
C:\Smart_HRMS\deploy.ps1
```

---

## Troubleshooting

**GPS Still Says "Only secure origins"?**
- Make sure URL is `https://192.168.0.5` (not http://)
- Refresh page (Ctrl+F5)
- Check Flask is running

**Camera not working?**
- Check browser permissions (Settings → Camera)
- Allow camera for the site
- Check HTTPS is working (no warning)

**Can't access from other computer?**
- Check firewall allows port 443
- Verify server IP is 192.168.0.5
- Check Nginx is running

---

## Important

⚠️ **Keep Kiro active** - Flask stops if Kiro closes

For permanent auto-start on server reboot, see `HTTPS_DEPLOYMENT_COMPLETE.md` section "Permanent Setup"

---

## Summary

✅ Smart HRMS is live on HTTPS
✅ GPS working
✅ Camera working  
✅ All features working
✅ Ready for employees

**That's it! 🎉**

---

For detailed information: See `HTTPS_DEPLOYMENT_COMPLETE.md`
