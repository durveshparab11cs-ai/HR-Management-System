# 🚀 Quick Start - Deploy Smart HRMS with Custom Domain

**Your Public IP**: 122.179.130.196  
**Time to deploy**: ~20 minutes  
**Cost**: $0-15/year (domain only)

---

## 🎯 What You Need to Do (4 Steps)

### Step 1️⃣: Buy Domain ($0.99-15/year) — 5 minutes
1. Go to **namecheap.com**
2. Search: `smarthrms.tech` (or pick your domain)
3. Add to cart → Checkout
4. Use code: **CHEAPDOMAIN** for discount
5. **Complete payment** ✅

**Save your login credentials!**

---

### Step 2️⃣: Point Domain to Your Server — 5 minutes
After buying domain:

1. Go to **Namecheap → My Domains → Manage**
2. Click **Advanced DNS** tab
3. Add A Record:
   - **Host**: @ (or blank)
   - **Value**: `122.179.130.196`
   - **TTL**: 3600
   - Click ✅

4. Wait **5-30 minutes** for DNS to update

**Test it works:**
```powershell
nslookup yourdomain.tech
```
Should show: `122.179.130.196` ✅

---

### Step 3️⃣: Setup SSL Certificate — 10 minutes

**Open PowerShell as Administrator** and run:

```powershell
cd "C:\Users\durve\Downloads\HR management system"
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\setup_ssl_production.ps1 -Domain "yourdomain.tech"
```

Replace `yourdomain.tech` with your actual domain!

**Wait for**: "Setup Complete!" message ✅

---

### Step 4️⃣: Start Production Server — 2 minutes

**Open 2 PowerShell windows:**

**Terminal 1 - Start Flask:**
```powershell
cd "C:\Users\durve\Downloads\HR management system"
python run.py
```
Wait for: `Running on http://127.0.0.1:5000`

**Terminal 2 - Start Nginx:**
```powershell
cd C:\nginx-1.27.0
.\nginx.exe
```
No output = working! ✅

---

## ✅ Your Site is Live!

Visit: **https://yourdomain.tech**

You should see:
- ✅ Login page loads
- ✅ Lock icon in browser (HTTPS)
- ✅ No certificate warnings

---

## 🔧 Next: Verify Everything Works

### Test 1: Login
- **Username**: e2606026 (or your admin account)
- **Password**: Your password
- Should show dashboard ✅

### Test 2: GPS Check-in
1. Go to **Attendance** page
2. Click **Check In**
3. Allow location access
4. Should show map with office location ✅

### Test 3: Camera Upload
1. Go to **Attendance**
2. Click **Photo** button
3. Allow camera access
4. Capture selfie
5. Should save in history ✅

### Test 4: Mobile Access
- Open on phone: **https://yourdomain.tech**
- Should work responsively
- GPS and camera should function ✅

---

## 📋 File References

| File | Purpose |
|------|---------|
| `DOMAIN_SETUP_GUIDE.md` | Detailed domain registration steps |
| `PRODUCTION_DEPLOYMENT_CHECKLIST.md` | Complete checklist with troubleshooting |
| `nginx-production.conf` | Nginx config (auto-uses for SSL) |
| `setup_ssl_production.ps1` | SSL automation script |
| `start_production.ps1` | Quick service starter |

---

## ❓ Troubleshooting

### DNS not working?
```powershell
nslookup yourdomain.tech
# If not showing 122.179.130.196:
# 1. Wait another 10 minutes
# 2. Check Namecheap DNS settings
# 3. Try: nslookup yourdomain.tech 8.8.8.8
```

### SSL certificate failed?
- Make sure port 80 is open in firewall
- Check DNS is pointing to 122.179.130.196
- Retry setup script

### Nginx not starting?
```powershell
# Check if port 80/443 in use:
netstat -ano | findstr :80
netstat -ano | findstr :443
# Kill other apps using those ports
```

### Flask connection refused?
- Make sure Flask is running in Terminal 1
- Check firewall allows port 5000

---

## 🎉 Done!

Your production server is now live with:
- ✅ Custom domain (yourdomain.tech)
- ✅ HTTPS/SSL certificate (Let's Encrypt)
- ✅ Automatic HTTP → HTTPS redirect
- ✅ GPS geolocation working
- ✅ Camera photo upload working
- ✅ Database connection working

**Certificate auto-renews** 30 days before expiry - no action needed!

---

## 📞 Need Help?

Check these files:
- **Deployment questions**: `PRODUCTION_DEPLOYMENT_CHECKLIST.md`
- **Domain/DNS issues**: `DOMAIN_SETUP_GUIDE.md`
- **SSL problems**: Check `C:\Certbot\logs\`
- **Nginx errors**: Check `C:\nginx-1.27.0\logs\error.log`
- **Flask errors**: Check Terminal 1 output

---

**Status**: Your app is production-ready! 🚀

**Next**: Buy domain and follow 4 steps above.
