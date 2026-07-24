# Database Reset - Quick Start Guide

## 🚀 Quick Commands

### Recommended (Creates Backup)
```bash
python reset_database_safe.py
```

### Basic (No Backup)
```bash
python reset_database.py
```

### PostgreSQL
```bash
python reset_database_postgres.py
```

## ✅ What Stays

- Employee Master Data
- User Logins
- Departments
- Company Info

## ❌ What Goes

- All Attendance
- All Leave Records
- All Notifications
- All Uploaded Photos

## 📝 Quick Test After Reset

```bash
# Test login
Visit: http://localhost:5000
Login with: existing employee credentials

# Check database
python -c "from app import create_app; from app.models import Attendance, Employee; app = create_app(); app.app_context().push(); print(f'Attendance: {Attendance.query.count()}'); print(f'Employees: {Employee.query.count()}')"

Expected:
Attendance: 0
Employees: 42 (your employee count)
```

## 🆘 If Something Goes Wrong

### Using Safe Reset?
```bash
# Your backup is at:
backups/reset_backup_YYYYMMDD_HHMMSS/

# To restore:
cp backups/reset_backup_*/smart_hrms.db instance/
cp -r backups/reset_backup_*/uploads/* instance/uploads/
```

### Database Locked?
```bash
# Stop application
# Close all connections
# Try again
```

## ⚡ Speed Reference

| Records | Time |
|---------|------|
| < 10K | ~5 sec |
| 10K-100K | ~30 sec |
| 100K+ | ~2 min |

## ✅ Success Check

After reset, verify:
- [ ] Can login as employee
- [ ] Dashboard loads
- [ ] No attendance shown
- [ ] No leaves shown
- [ ] Can check-in successfully

---

**Need detailed help?** Read `DATABASE_RESET_GUIDE.md`
