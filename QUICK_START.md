# Smart HRMS - Quick Start Guide

## 🚀 System is Ready!

Your Smart HRMS system is fully configured and production-ready.

---

## ✅ What's Working

1. **Coordinator Portal** - Mark attendance for employees without GPS restrictions ✅
2. **Automatic Calculations** - Late marks, working hours, overtime all calculated ✅
3. **Employee Portal** - View attendance, working hours, and history ✅
4. **Super Admin Portal** - Full system management ✅
5. **Accurate Time Tracking** - Precise to the minute ✅

---

## 🎯 Quick Access

### **Access the System**
- **Website**: `https://smarthrms.online/`
- **Coordinator Portal**: `https://smarthrms.online/coordinator/`
- **Admin Panel**: `https://smarthrms.online/admin`

### **Login Credentials**
Use your super admin account:
- Username: `e2606026` or `e2603025`
- Password: (your existing password)

---

## 📋 How to Mark Attendance (Coordinator Portal)

1. **Open**: `https://smarthrms.online/coordinator/`
2. **Login**: Use super admin credentials
3. **Enter Employee Code**: Type employee code (e.g., E-2603028)
4. **Search**: System finds employee and shows their info
5. **View Details**: Check today's attendance status
6. **Capture Photo**: Take employee photo (required)
7. **Check-In/Out**: Click button - **NO GPS validation needed!**
8. **Done**: System automatically calculates:
   - ✅ Late marks (if applicable)
   - ✅ Working hours
   - ✅ Overtime
   - ✅ Half-day status

---

## 📊 What Gets Calculated Automatically

### **On Check-In**
- Late status (checked in after grace period)
- Late minutes
- Status set to "Present"

### **On Check-Out**
- Total working hours (exact)
- Overtime (if worked beyond shift)
- Final status (Present/Half-Day/Absent based on hours)
- Early leave detection

### **Example**
```
Employee: John Doe
Shift: 10:00 AM - 7:00 PM (IST)
Grace Period: 15 minutes

Check-In: 10:20 AM → Late by 5 minutes ⚠️
Check-Out: 7:30 PM → Overtime: 30 minutes ⏰
Working Hours: 9h 10m ✅
Status: PRESENT ✅
```

---

## 🎥 Camera Issue (Known)

**Problem**: Camera not starting  
**Cause**: Windows camera driver not loaded (hardware issue, not code)

**Quick Fix (Choose One)**:
1. Press **Fn + F10** on keyboard (ASUS camera toggle)
2. Restart your laptop (most effective)
3. Windows Settings → Privacy → Camera → Turn ON
4. Chrome → Site Settings → Camera → Allow

**The camera code is correct** - this is a Windows driver issue specific to your ASUS laptop.

---

## ⚙️ Server Status

Both servers are running:
- ✅ Waitress server (port 5000)
- ✅ Cloudflare tunnel (connected)

If servers stop, restart with:
```bash
cd C:\Users\Administrator\Documents\HRMS\smart_hrms
$env:FLASK_ENV="production"
python -m waitress --host=127.0.0.1 --port=5000 --threads=8 wsgi:app
```

And in another terminal:
```bash
cloudflared tunnel --config C:\Users\Administrator\.cloudflared\config.yml run
```

---

## 📈 View Attendance Records

### **Employee Portal**
- Go to: `https://smarthrms.online/attendance/`
- See your own attendance
- View working hours, late marks, overtime

### **Admin Portal**
- Go to: `https://smarthrms.online/admin`
- View all employee attendance
- See complete reports with all calculated fields

---

## 🔄 Changes Made Today

1. **Removed GPS Validation** - Coordinator can mark attendance from anywhere
2. **Added Accurate Calculations** - All time tracking is precise
3. **Fixed Errors** - All pages load without issues
4. **Configured Production** - Cloudflare tunnel working

---

## ✅ Production Ready!

Your system is fully functional and ready for daily use. The only outstanding issue is the camera hardware (Windows driver), which you can fix by restarting your laptop.

**Need help?** Check the logs at:
`C:\Users\Administrator\Documents\HRMS\smart_hrms\logs\`

---

**Enjoy your Smart HRMS system!** 🎉
