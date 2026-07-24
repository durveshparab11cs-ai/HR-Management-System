# Database Reset Guide - Smart HRMS

## 📋 Overview

This guide explains how to safely reset your Smart HRMS database to a fresh state while preserving all employee master data.

## 🎯 What Gets Reset

### ✅ PRESERVED (Kept Safe)
- ✓ Employee Master Data
- ✓ User Accounts & Login Credentials
- ✓ Departments
- ✓ Designations/Positions
- ✓ Roles & Permissions
- ✓ Company Information
- ✓ Office Settings
- ✓ Shift Master Data
- ✓ Employee Profiles
- ✓ System Configuration

### ❌ DELETED (Removed)
- ✗ All Attendance Records
- ✗ All Leave Applications
- ✗ All Half-Day Requests
- ✗ All Shift Change Requests
- ✗ All Payroll Records
- ✗ All Notifications
- ✗ All Approval History
- ✗ All Uploaded Photos
- ✗ All GPS Logs
- ✗ All Session Data
- ✗ All Audit Logs

## 🛠️ Available Reset Scripts

### 1. **reset_database.py** (Basic)
Simple reset without backup.

**When to use:**
- Development environment
- You have recent backup
- Quick reset needed

**Command:**
```bash
python reset_database.py
```

### 2. **reset_database_safe.py** (Recommended)
Creates automatic backup before reset.

**When to use:**
- Production/staging environment
- Want recovery option
- First time resetting

**Command:**
```bash
python reset_database_safe.py
```

### 3. **reset_database_postgres.py** (PostgreSQL)
Optimized for PostgreSQL databases.

**When to use:**
- Using PostgreSQL (not SQLite)
- Production server with PostgreSQL
- Need proper sequence handling

**Command:**
```bash
python reset_database_postgres.py
```

## 📖 Step-by-Step Instructions

### Option A: Safe Reset (Recommended)

```bash
# 1. Navigate to project directory
cd smart_hrms

# 2. Run safe reset (creates backup)
python reset_database_safe.py

# 3. Confirm when prompted
# Type: YES

# 4. Wait for completion

# 5. Restart application
# Render: Push to trigger redeploy
# Local: Restart Flask server
```

### Option B: Basic Reset

```bash
# 1. Navigate to project directory
cd smart_hrms

# 2. Run reset
python reset_database.py

# 3. Confirm when prompted
# Type: RESET DATABASE

# 4. Wait for completion

# 5. Restart application
```

### Option C: PostgreSQL Reset

```bash
# 1. Navigate to project directory
cd smart_hrms

# 2. Ensure using PostgreSQL
# Check config.py or .env

# 3. Run PostgreSQL reset
python reset_database_postgres.py

# 4. Confirm when prompted
# Type: RESET DATABASE

# 5. Wait for completion
```

## 🔍 What Happens During Reset

### Phase 1: Backup (Safe Reset Only)
```
📁 Creating backup folder...
   backups/reset_backup_YYYYMMDD_HHMMSS/
   
📦 Backing up database...
   ✅ smart_hrms.db copied
   
📦 Backing up uploads...
   ✅ All photos copied
   
✅ Backup complete
```

### Phase 2: File Cleanup
```
🗑️ Cleaning uploaded files...
   ✅ attendance_photos/
   ✅ checkin_photos/
   ✅ checkout_photos/
   ✅ shift_changes/
   ✅ leave_attachments/
   ✅ temp/
   
📊 Total files deleted: XXX
```

### Phase 3: Database Reset
```
🔄 Starting transaction...
   
✅ gps_logs: XXX records deleted
✅ attendance_photos: XXX records deleted
✅ attendance_logs: XXX records deleted
✅ attendance: XXX records deleted
✅ leave_requests: XXX records deleted
✅ half_day_requests: XXX records deleted
✅ shift_change_requests: XXX records deleted
✅ payroll_runs: XXX records deleted
✅ notifications: XXX records deleted
   
✅ Transaction committed
```

### Phase 4: Verification
```
✅ Master Data Preserved:
   ✓ User Accounts: XX records
   ✓ Employee Records: XX records
   ✓ Departments: XX records
   ✓ Positions: XX records
   
✅ Transactional Data Deleted:
   ✓ Attendance: Empty
   ✓ Leave Applications: Empty
   ✓ Notifications: Empty
```

### Phase 5: Report
```
📊 Summary:
   Duration: X.XX seconds
   Tables Cleared: XX
   Records Deleted: X,XXX
   Files Removed: XXX
   Master Records Preserved: XXX
   
✅ DATABASE RESET SUCCESSFUL!
```

## 🎯 Expected Results

After successful reset:

```
✅ All employees can still log in
✅ Employee data intact
✅ Departments preserved
✅ Roles preserved
✅ No attendance records exist
✅ No leave records exist
✅ No notifications exist
✅ No uploaded photos exist
✅ System ready for fresh testing
```

## 🧪 Testing After Reset

### 1. Verify Login
```bash
# Test employee login
Username: employee_code
Password: existing_password

Expected: ✅ Login successful
```

### 2. Check Dashboard
```
Expected:
✅ Dashboard loads
✅ No attendance shown
✅ No leave records shown
✅ Clean slate
```

### 3. Test Attendance
```
1. Click "Check In"
2. Submit location
Expected: ✅ First check-in recorded
```

### 4. Verify Database
```python
# Run this check
python -c "
from app import create_app
from app.models import Attendance, Employee
app = create_app()
with app.app_context():
    att_count = Attendance.query.count()
    emp_count = Employee.query.count()
    print(f'Attendance: {att_count}')
    print(f'Employees: {emp_count}')
"

Expected:
Attendance: 0
Employees: XX (non-zero)
```

## 🔄 Restoring from Backup

If you used `reset_database_safe.py`, you can restore:

### Step 1: Locate Backup
```bash
cd backups
ls -la
# Find: reset_backup_YYYYMMDD_HHMMSS/
```

### Step 2: Stop Application
```bash
# Local: Stop Flask server
# Render: Not applicable
```

### Step 3: Restore Database
```bash
# Copy backup database
cp backups/reset_backup_YYYYMMDD_HHMMSS/smart_hrms.db instance/
```

### Step 4: Restore Uploads
```bash
# Copy backup uploads
cp -r backups/reset_backup_YYYYMMDD_HHMMSS/uploads/* instance/uploads/
```

### Step 5: Restart
```bash
# Local: Start Flask server
# Render: Push code to redeploy
```

## ⚠️ Important Warnings

### DO NOT Run This:
❌ In production without backup
❌ Without confirmation from stakeholders
❌ If you need the transactional data
❌ During active business hours

### DO Run This:
✅ In development/testing environment
✅ After creating backup
✅ During maintenance window
✅ When starting fresh testing cycle

## 🆘 Troubleshooting

### Problem: "Table does not exist"
**Solution:** Table may not be created yet. This is normal.

### Problem: "Foreign key constraint failed"
**Solution:** Script handles this automatically. Check order of deletion.

### Problem: "Master data deleted accidentally"
**Solution:** 
1. Stop immediately
2. Restore from backup
3. Contact support

### Problem: "Employee can't login after reset"
**Cause:** User accounts are preserved, so this shouldn't happen
**Solution:** 
1. Check if user table was accidentally cleared
2. Restore from backup
3. Reset passwords if needed

### Problem: "Database locked"
**Solution:**
1. Stop all application instances
2. Close all database connections
3. Run reset again

## 📊 Performance

### Typical Reset Times:

| Database Size | Records | Duration |
|---------------|---------|----------|
| Small | < 10K | 1-5 seconds |
| Medium | 10K-100K | 5-30 seconds |
| Large | 100K-1M | 30-120 seconds |
| Very Large | > 1M | 2-5 minutes |

## 🔐 Security Considerations

1. **Backup First:** Always create backup before reset
2. **Confirm Users:** Verify all stakeholders approve
3. **Off-Hours:** Run during low-traffic periods
4. **Access Control:** Only admins should have access
5. **Audit Trail:** Keep logs of reset operations

## 📞 Support

If you encounter issues:

1. **Check Logs:** Review error messages in output
2. **Verify Backup:** Ensure backup was created
3. **Test Restore:** Try restoring from backup
4. **Contact Admin:** Reach out to system administrator

## ✅ Checklist

Before reset:
- [ ] Backup created (if using safe reset)
- [ ] All users notified
- [ ] Maintenance window scheduled
- [ ] Stakeholders approved
- [ ] Testing plan ready

After reset:
- [ ] Login tested
- [ ] Dashboard verified
- [ ] Master data confirmed
- [ ] Transactional data cleared
- [ ] Test transactions successful
- [ ] Backup stored safely

## 🎉 Success Criteria

Your reset is successful when:

✅ All employees can log in
✅ Employee master data is intact
✅ No attendance records exist
✅ No leave records exist
✅ No notifications exist
✅ Dashboard shows clean state
✅ New transactions work properly
✅ System behaves like fresh install

---

## 📝 Example Output

```
================================================================================
SMART HRMS - SAFE DATABASE RESET TOOL (WITH BACKUP)
================================================================================
Started at: 2026-07-23 23:30:00

⚠️  This will:
  1. Create a backup of your current database
  2. Delete all transactional data
  3. Preserve employee master data

Type 'YES' to proceed with safe reset: YES

================================================================================
CREATING BACKUP
================================================================================

📁 Backup location: backups/reset_backup_20260723_233000
✅ Database backed up (15.42 MB)
✅ Uploads folder backed up (1,247 files)
✅ Backup info saved: backups/reset_backup_20260723_233000/backup_info.txt

📦 Backup complete: backups/reset_backup_20260723_233000

================================================================================
CLEANING UPLOADED FILES
================================================================================

✅ Cleaned instance/uploads/attendance_photos: 523 files deleted
✅ Cleaned instance/uploads/checkin_photos: 412 files deleted
✅ Cleaned instance/uploads/checkout_photos: 312 files deleted
ℹ️  instance/uploads/shift_changes: Already empty
ℹ️  instance/uploads/temp: Already empty

📊 Total files deleted: 1,247

================================================================================
RESETTING TRANSACTIONAL TABLES
================================================================================

🔄 Starting database transaction...

✅ gps_logs: 1,856 records deleted
✅ attendance_photos: 935 records deleted
✅ attendance_logs: 2,341 records deleted
✅ attendance: 845 records deleted
✅ leave_requests: 127 records deleted
✅ half_day_requests: 89 records deleted
✅ shift_change_requests: 23 records deleted
✅ employee_shift_assignments: 67 records deleted
✅ payroll_runs: 12 records deleted
✅ payslips: 456 records deleted
✅ notifications: 789 records deleted
✅ login_history: 2,145 records deleted

✅ Transaction committed successfully

================================================================================
VERIFYING MASTER DATA PRESERVATION
================================================================================

✅ User Accounts: 45 records preserved
✅ Employee Records: 42 records preserved
✅ Employee Master Data: 42 records preserved
✅ Departments: 8 records preserved
✅ Positions/Designations: 15 records preserved
✅ Shift Master: 4 records preserved
✅ Office Settings: 1 records preserved
✅ Company Information: 1 records preserved

================================================================================
VERIFYING TRANSACTIONAL DATA DELETION
================================================================================

✅ Attendance Records: Empty (0 records)
✅ Attendance Logs: Empty (0 records)
✅ Attendance Photos: Empty (0 records)
✅ GPS Logs: Empty (0 records)
✅ Leave Applications: Empty (0 records)
✅ Half-Day Requests: Empty (0 records)
✅ Early Leave Requests: Empty (0 records)
✅ Shift Change Requests: Empty (0 records)
✅ Shift Assignments: Empty (0 records)
✅ Payroll Runs: Empty (0 records)
✅ Payslips: Empty (0 records)
✅ Notifications: Empty (0 records)
✅ Login History: Empty (0 records)

================================================================================
RESET COMPLETE - FINAL REPORT
================================================================================

📊 Summary:
   Start Time: 2026-07-23 23:30:00
   End Time: 2026-07-23 23:30:15
   Duration: 15.24 seconds

🗑️  Transactional Data Deleted:
   Total Tables Cleared: 13
   Total Records Deleted: 9,685

   Breakdown:
      • login_history: 2,145 records
      • attendance_logs: 2,341 records
      • gps_logs: 1,856 records
      • attendance_photos: 935 records
      • attendance: 845 records
      • notifications: 789 records
      • payslips: 456 records
      • leave_requests: 127 records
      • half_day_requests: 89 records
      • employee_shift_assignments: 67 records
      • shift_change_requests: 23 records
      • payroll_runs: 12 records
      • early_leave_requests: 0 records

📁 Files Deleted:
   Total Files Removed: 1,247

✅ Master Data Preserved:
   ✓ User Accounts: 45 records
   ✓ Employee Records: 42 records
   ✓ Employee Master Data: 42 records
   ✓ Departments: 8 records
   ✓ Positions/Designations: 15 records
   ✓ Shift Master: 4 records
   ✓ Office Settings: 1 records
   ✓ Company Information: 1 records

================================================================================
✅ DATABASE RESET SUCCESSFUL!
================================================================================

Your HRMS is now in a fresh state:
  • All employees can still log in
  • Employee master data is intact
  • No transactional data exists
  • Ready for fresh testing

Next steps:
  1. Restart the application
  2. Test employee login
  3. Start fresh attendance/leave/shift transactions

💾 Backup available at: backups/reset_backup_20260723_233000
   (Keep this backup for recovery if needed)
```

---

**Created by:** Kiro AI  
**Version:** 1.0  
**Last Updated:** July 23, 2026
