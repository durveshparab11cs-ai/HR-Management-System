# Smart HRMS - Production Deployment Checklist

**Your Public IP**: 122.179.130.196 (Mumbai, Bharti Airtel)

---

## PHASE 1: Domain Registration (5 mins)

### [ ] 1.1 Choose Domain Name
Suggested names:
- `smarthrms.tech` (~$12/year)
- `smarthrms.app` (~$15/year)
- `hrms.company.in` (~$5/year)
- `attendance.tech` (~$12/year)

**Selected domain**: ________________

### [ ] 1.2 Purchase Domain
1. Go to **Namecheap.com** (or GoDaddy/Hostinger)
2. Search your domain
3. Use coupon: `CHEAPDOMAIN` for first-year discount
4. Complete checkout
5. **Save receipt & login credentials**

---

## PHASE 2: DNS Configuration (5-10 mins)

### [ ] 2.1 Access Domain Control Panel
- Go to registrar's account
- Find "Manage DNS" or "Nameservers"

### [ ] 2.2 Add A Record
| Field | Value |
|-------|-------|
| Type | A |
| Host | @ (or blank) |
| Value | 122.179.130.196 |
| TTL | 3600 |

### [ ] 2.3 Add WWW A Record (optional)
| Field | Value |
|-------|-------|
| Type | A |
| Host | www |
| Value | 122.179.130.196 |
| TTL | 3600 |

### [ ] 2.4 Verify DNS
Wait 5-30 minutes, then test:
```powershell
nslookup yourdomain.tech
```
Should return: 122.179.130.196

---

## PHASE 3: Server Setup (Windows Server)

### [ ] 3.1 Install Nginx
1. Download: https://nginx.org/en/download.html (stable version)
2. Extract to: `C:\nginx-1.27.0`
3. Test: `C:\nginx-1.27.0\nginx.exe -v`

### [ ] 3.2 Install Python Dependencies
```powershell
cd "C:\Users\durve\Downloads\HR management system"
pip install -r requirements.txt
pip install gunicorn
pip install certbot
```

### [ ] 3.3 Update Production Environment
Edit `.env`:
```env
FLASK_ENV=production
DEBUG=0
SECRET_KEY=<generate-with-secrets.token_urlsafe(32)>
DATABASE_URL=postgresql://... # Your Render DB
ALLOWED_HOSTS=yourdomain.tech,www.yourdomain.tech
```

### [ ] 3.4 Copy Nginx Configuration
```powershell
Copy-Item nginx-production.conf "C:\nginx-1.27.0\conf\nginx.conf" -Force
```
**OR** manually edit and replace your domain name in:
- `C:\nginx-1.27.0\conf\nginx.conf`

### [ ] 3.5 Verify Firewall Rules
```powershell
# Check port 80 (HTTP)
netstat -ano | findstr :80

# Check port 443 (HTTPS)
netstat -ano | findstr :443

# Check port 5000 (Flask)
netstat -ano | findstr :5000
```
Make sure no other service is using these ports.

---

## PHASE 4: SSL Certificate Setup (10 mins)

### [ ] 4.1 Run SSL Setup Script
**Replace `smarthrms.tech` with your domain:**
```powershell
cd "C:\Users\durve\Downloads\HR management system"
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\setup_ssl_production.ps1 -Domain "smarthrms.tech"
```

**Wait for certificate to be issued (30-60 seconds)**

### [ ] 4.2 Verify Certificate Files
Check if these files exist:
```
C:\Certbot\live\yourdomain.tech\cert.pem
C:\Certbot\live\yourdomain.tech\privkey.pem
```

### [ ] 4.3 Update Nginx Config with Cert Paths
Edit `C:\nginx-1.27.0\conf\nginx.conf`:
```nginx
ssl_certificate C:/Certbot/live/yourdomain.tech/cert.pem;
ssl_certificate_key C:/Certbot/live/yourdomain.tech/privkey.pem;
```

### [ ] 4.4 Test Nginx Configuration
```powershell
cd C:\nginx-1.27.0
.\nginx.exe -t
```
Should output: `successful` (green)

---

## PHASE 5: Start Services

### [ ] 5.1 Start Flask (Terminal 1)
```powershell
cd "C:\Users\durve\Downloads\HR management system"
python run.py
```
Should show: `Running on http://127.0.0.1:5000`

### [ ] 5.2 Start Nginx (Terminal 2)
```powershell
cd C:\nginx-1.27.0
.\nginx.exe
```
Should start silently (no error output = good)

### [ ] 5.3 Verify Both Running
```powershell
Get-Process nginx
Get-Process python
```

---

## PHASE 6: Testing (10 mins)

### [ ] 6.1 Test HTTP → HTTPS Redirect
```
Visit: http://yourdomain.tech
Should redirect to: https://yourdomain.tech
```

### [ ] 6.2 Test HTTPS Access
```
Visit: https://yourdomain.tech
Should show: Login page (no SSL warnings)
```

### [ ] 6.3 Test SSL Certificate
```
Click lock icon in browser → View Certificate
Should show:
  - Issued to: yourdomain.tech
  - Issued by: Let's Encrypt
  - Valid until: Next year
```

### [ ] 6.4 Test Login Functionality
```
Username: admin / e2606026
Password: Your password
Should login and show dashboard
```

### [ ] 6.5 Test GPS Check-in
```
Go to Attendance page
Allow location access
Click Check In
Should show location on map
```

### [ ] 6.6 Test Camera Upload
```
Click photo upload button
Allow camera access
Take photo
Should save and show in history
```

### [ ] 6.7 Test Database Connection
```
Go to Employees page
Should load employee list from Render PostgreSQL
```

### [ ] 6.8 Test Mobile Access
```
On mobile phone:
Visit: https://yourdomain.tech
Should be responsive
GPS and camera should work
```

---

## PHASE 7: Monitoring & Maintenance

### [ ] 7.1 Monitor Logs
```powershell
# Flask logs (in terminal running Flask)
# Check for errors

# Nginx access logs
Get-Content "C:\nginx-1.27.0\logs\access.log" -Tail 20

# Nginx error logs
Get-Content "C:\nginx-1.27.0\logs\error.log" -Tail 20
```

### [ ] 7.2 Monitor SSL Certificate Expiry
Certificate auto-renews 30 days before expiry.
Next renewal: Check `C:\Certbot\renewal\yourdomain.tech.conf`

### [ ] 7.3 Test Auto-Renewal (Optional)
```powershell
certbot renew --dry-run
```

### [ ] 7.4 Create Windows Startup Script
To auto-start services on reboot:
1. Open Task Scheduler
2. Create New Task
3. Trigger: At System Startup
4. Action: Run `start_production.ps1`

---

## PHASE 8: Post-Deployment

### [ ] 8.1 Update Team
- Share new domain URL with team
- Update mobile app settings if needed
- Update documentation

### [ ] 8.2 Backup Configuration
```powershell
# Backup cert
Copy-Item "C:\Certbot" "C:\Backup\Certbot_backup" -Recurse

# Backup nginx config
Copy-Item "C:\nginx-1.27.0\conf" "C:\Backup\nginx_conf_backup" -Recurse

# Backup app
git commit -am "Production deployment configuration"
git push
```

### [ ] 8.3 Monitor Performance
- Check response times
- Monitor CPU/Memory usage
- Check error logs daily first week

### [ ] 8.4 Enable Monitoring (Optional)
Consider setting up:
- Health checks: https://yourdomain.tech/health
- Error alerts via email
- Uptime monitoring (Uptimerobot, etc.)

---

## Troubleshooting

### Issue: Domain not resolving
```powershell
# Test DNS
nslookup yourdomain.tech
# Should return 122.179.130.196

# If not working:
# 1. Wait 10-30 minutes for DNS propagation
# 2. Check registrar DNS settings
# 3. Try different DNS resolver: 8.8.8.8
```

### Issue: SSL certificate error
```
Possible causes:
1. Port 80 not open during certificate request
2. Firewall blocking Let's Encrypt servers
3. Domain not pointing to correct IP

Solution:
- Check firewall allows ports 80, 443
- Run: .\setup_ssl_production.ps1 again
- Verify DNS with nslookup
```

### Issue: Nginx connection refused
```powershell
# Check if Nginx is running
Get-Process nginx

# Check port 80/443 not in use
netstat -ano | findstr :80
netstat -ano | findstr :443

# Test Nginx config
C:\nginx-1.27.0\nginx.exe -t
```

### Issue: Flask 500 errors
```
Check Flask logs in terminal
Common issues:
1. DATABASE_URL incorrect
2. Missing environment variables
3. Port 5000 already in use

Solution:
- Restart Flask
- Check .env file
- Kill other Python processes: taskkill /IM python.exe /F
```

---

## Success Metrics

✅ Domain resolves to your server  
✅ HTTPS works without certificate warnings  
✅ Login page loads  
✅ Employee data displays  
✅ GPS check-in works  
✅ Camera photo upload works  
✅ Mobile responsive  
✅ Performance acceptable  

---

## Support Resources

- Nginx docs: https://nginx.org/en/docs/
- Let's Encrypt: https://letsencrypt.org/
- Certbot docs: https://certbot.eff.org/
- Flask production: https://flask.palletsprojects.com/deployment/
- DNS checker: https://dnschecker.org

---

**Next Step**: Go to PHASE 1 and start with domain registration!
