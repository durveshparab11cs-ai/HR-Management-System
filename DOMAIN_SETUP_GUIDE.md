# Smart HRMS - Domain Setup & Production Guide

## Your Server Details
- **Public IP**: 122.179.130.196
- **Current URL**: https://192.168.0.205:443 (internal network)
- **Target**: Custom domain with HTTPS

---

## Step 1: Register Domain (5 minutes, $0.99/year)

### Option A: Namecheap (Recommended)
1. Go to https://www.namecheap.com
2. Search for domain: `smarthrms.tech` or `smarthrms.in` (~$0.99-3 first year)
3. Add to cart → Checkout
4. **Skip optional extras** (hosting, SSL, etc.)
5. Complete payment
6. Go to "My Domains" → manage domain

### Option B: GoDaddy
1. Go to https://www.godaddy.com
2. Search for domain
3. Add to cart → Checkout
4. Complete payment

---

## Step 2: Configure DNS (After buying domain)

In your domain registrar's control panel:

### Add A Record:
- **Type**: A (IPv4 address)
- **Host**: @ (or blank)
- **Value**: 122.179.130.196
- **TTL**: 3600 (default)

### Also Add (Optional but recommended):
- **Type**: A
- **Host**: www
- **Value**: 122.179.130.196

**Save changes** - DNS updates take 5-30 minutes to propagate

---

## Step 3: Setup Production on Windows Server

### 3.1 Install Nginx (if not already installed)
Download from: https://nginx.org/en/download.html
Extract to: `C:\nginx-1.27.0`

### 3.2 Install Certbot for Let's Encrypt SSL
```powershell
pip install certbot certbot-dns-route53
```

### 3.3 Create Nginx Configuration
See `nginx-production.conf` file in this repo

### 3.4 Get SSL Certificate
Once domain is pointing to your IP:
```powershell
certbot certonly --standalone -d smarthrms.tech
```
(Replace `smarthrms.tech` with your actual domain)

Certificate will be saved to:
```
C:\Certbot\live\smarthrms.tech\
  - cert.pem
  - privkey.pem
```

### 3.5 Update Nginx Config with Certificate Paths
Edit `nginx-production.conf` and set:
```nginx
ssl_certificate C:/Certbot/live/smarthrms.tech/cert.pem;
ssl_certificate_key C:/Certbot/live/smarthrms.tech/privkey.pem;
```

### 3.6 Start Services in Order:
```powershell
# 1. Start Flask (production mode)
python run.py

# 2. Start Nginx (in another terminal)
cd C:\nginx-1.27.0
nginx.exe

# 3. Test:
https://yourdomain.tech
```

---

## Step 4: Update Environment Variables

Edit `.env`:
```env
FLASK_ENV=production
SECRET_KEY=<generate-random-key>
DATABASE_URL=postgresql://...  # Your Render DB
ALLOWED_HOSTS=smarthrms.tech,www.smarthrms.tech
```

---

## Step 5: SSL Certificate Auto-Renewal

Schedule renewal with Windows Task Scheduler:
```powershell
certbot renew --quiet
```

---

## Testing Checklist

- [ ] Domain resolves: `nslookup smarthrms.tech`
- [ ] HTTPS works: Visit https://smarthrms.tech
- [ ] Redirect works: http://smarthrms.tech → https://smarthrms.tech
- [ ] Login works: Can authenticate
- [ ] GPS works: Can check-in with location
- [ ] Camera works: Can upload photos
- [ ] Database works: Can load employee data

---

## Troubleshooting

### Domain not resolving?
- Wait 10-30 minutes for DNS propagation
- Check DNS: https://dnschecker.org

### SSL certificate error?
- Make sure port 80/443 are open
- Check firewall allows HTTP/HTTPS

### Nginx not starting?
- Check port 80/443 not in use: `netstat -ano | findstr :80`
- Check nginx config syntax: `nginx.exe -t`

### Flask connection refused?
- Make sure Flask is running on port 5000
- Check firewall allows localhost:5000

---

## Next Steps

1. **Buy domain** (Namecheap recommended)
2. **Point DNS** to 122.179.130.196
3. **Run setup scripts** provided
4. **Test and verify** everything works

Questions? Let me know!
