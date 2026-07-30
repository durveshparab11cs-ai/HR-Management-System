# Hospital Allocation System - Deployment Guide

## Overview
Complete hospital allocation system with GPS validation, flexible shifts, and Excel import capabilities.

## Coordinates Reference
**Head Office & Claim Department:**
- **Latitude:** 19.014847°
- **Longitude:** 72.8452°
- **Recommended Radius:** 100 meters

---

## Pre-Deployment Checklist

### 1. Database Migration
Run the migration to create tables and extend employee schema:

```bash
# Local/Development
psql -U your_user -d your_database -f migrations/add_hospital_allocation.sql

# Production (Render/Heroku)
psql $DATABASE_URL -f migrations/add_hospital_allocation.sql
```

**What this creates:**
- `hospitals` table (id, name, location, latitude, longitude, radius, status, created_at, updated_at)
- `import_logs` table (audit trail for Excel imports)
- Employee columns: hospital_id, current_shift, shift_start_time, shift_end_time, is_flexible_shift, required_working_hours

### 2. Verify Auto-Migration
The app will automatically add employee columns on startup if missing. Check logs:
```
INFO: Auto-migration: Adding hospital_id column to employee table
INFO: Auto-migration: Adding shift-related columns to employee table
```

---

## Step-by-Step Deployment

### Step 1: Create Head Office Hospital Record

**Option A: Via Admin UI**
1. Login as admin
2. Navigate to: **Admin → Hospitals → Add New Hospital**
3. Fill in:
   - **Hospital Name:** Head Office
   - **Location:** Mumbai Head Office
   - **Latitude:** 19.014847
   - **Longitude:** 72.8452
   - **Allowed Radius:** 100 (meters)
   - **Status:** Active

**Option B: Via SQL**
```sql
INSERT INTO hospitals (name, location, latitude, longitude, allowed_radius_metres, status)
VALUES 
  ('Head Office', 'Mumbai Head Office', 19.014847, 72.8452, 100, 'active'),
  ('Claim Department', 'Mumbai Claim Center', 19.014847, 72.8452, 100, 'active');
```

### Step 2: Import Hospital Data from Excel

**File:** `HOSIPTALS DETAILS.xlsx`

**Column Mapping:**
- "Hospital  Name" → hospital.name
- "Location" → hospital.location
- "Latitude" → hospital.latitude
- "Longitude" → hospital.longitude
- "Status" → hospital.status

**Process:**
1. Navigate to: **Admin → Hospitals → Import from Excel**
2. Upload: `HOSIPTALS DETAILS.xlsx`
3. Review preview
4. Click "Import"
5. Check import log for results

**Expected Results:**
- Duplicate hospitals skipped (by name similarity)
- Invalid coordinates flagged
- Success count displayed

### Step 3: Import Employee Allocations from Excel

**File:** `employee master full upload.xlsx`

**Column Mapping:**
- "EMP-CODE" → employee.employee_code
- "WORKING LOCATION" → matched to hospital.name
- "full Shift timing" → parsed into shift fields
- "WORKING STATUS" → determines flexible shift

**Shift Parsing Examples:**
```
"10:00 AM to 7:00 PM"      → Morning Shift, fixed, 10:00-19:00
"9:00 AM to 6:00 PM"       → Morning Shift, fixed, 09:00-18:00
"Flexible Shift"           → Flexible Shift, is_flexible_shift=True
"10:00 am to 7:00 pm"      → Afternoon Shift, fixed, 10:00-19:00
```

**Process:**
1. Navigate to: **Admin → Employee Allocation → Import from Excel**
2. Upload: `employee master full upload.xlsx`
3. Review preview showing:
   - Employees to be updated
   - Hospital matches
   - Shift assignments
4. Click "Import"
5. Check import log

**Expected Results:**
- Employees matched by employee_code
- Hospital allocated based on "WORKING LOCATION"
- Shift times parsed and stored
- Flexible shift flag set automatically
- Employees not found are logged

### Step 4: Verify Allocations

**SQL Verification:**
```sql
-- Check employees allocated to Head Office
SELECT 
  e.employee_code,
  e.name,
  h.name as hospital_name,
  e.current_shift,
  e.is_flexible_shift,
  e.shift_start_time,
  e.shift_end_time
FROM employee e
LEFT JOIN hospitals h ON e.hospital_id = h.id
WHERE h.name LIKE '%Head Office%' OR h.name LIKE '%Claim%'
LIMIT 20;

-- Check flexible shift employees
SELECT 
  employee_code,
  name,
  current_shift,
  is_flexible_shift,
  required_working_hours
FROM employee
WHERE is_flexible_shift = true
LIMIT 10;

-- Hospital statistics
SELECT 
  h.name,
  h.location,
  COUNT(e.id) as employee_count,
  h.status
FROM hospitals h
LEFT JOIN employee e ON e.hospital_id = h.id
GROUP BY h.id, h.name, h.location, h.status
ORDER BY employee_count DESC;
```

---

## Feature Testing

### Test 1: GPS Validation with Hospital Coordinates

**Scenario:** Employee allocated to Head Office checks in

**Expected Behavior:**
1. Employee opens attendance page
2. Browser captures GPS: near (19.014847, 72.8452)
3. System validates against **hospital coordinates** (not office settings)
4. If within 100m radius → GPS valid
5. If outside radius → GPS validation fails

**Log Check:**
```
INFO: GPS validation using hospital reference: Head Office
INFO: Hospital coordinates: 19.014847, 72.8452 with radius: 100m
INFO: Employee distance from hospital: 45.23m
INFO: GPS validation result: True
```

**Fallback:** If employee has no hospital_id, system uses office_settings coordinates.

### Test 2: Flexible Shift Attendance

**Scenario:** Flexible shift employee completes 9+ hours

**Expected Behavior:**
1. Check-in at any time → **Never marked late**
2. Check-out after 9+ hours worked → **Marked Present**
3. Check-out with <9 hours → **Marked Half-day**
4. No overtime calculation
5. No early leave concept

**SQL Verification:**
```sql
SELECT 
  a.date,
  a.employee_id,
  e.employee_code,
  e.is_flexible_shift,
  a.check_in_time,
  a.check_out_time,
  a.working_hours,
  a.status,
  a.is_late,
  a.overtime_hours
FROM attendance a
JOIN employee e ON a.employee_id = e.id
WHERE e.is_flexible_shift = true
  AND a.date >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY a.date DESC;
```

**Expected Results:**
- `is_late` = false (always)
- `status` = 'Present' if working_hours >= 9.0
- `status` = 'Half-day' if working_hours < 9.0
- `overtime_hours` = 0.0 (always)

### Test 3: Fixed Shift Attendance (No Change)

**Scenario:** Fixed shift employee follows existing logic

**Expected Behavior:**
1. Check-in after shift_start_time → **Marked late**
2. Check-out before shift_end_time → **Early leave**
3. Working hours > shift duration → **Overtime calculated**
4. Existing attendance logic unchanged

---

## System Features

### Hospital Management
- **List View:** Search, filter by status, statistics dashboard
- **Create/Edit:** Form with coordinate validation
- **Import:** Bulk Excel upload with duplicate detection
- **Status Control:** Active/Inactive toggle

### Employee Allocation
- **Bulk Assignment:** Excel import with hospital matching
- **Shift Parsing:** Automatic detection of shift types
- **Flexible Detection:** Keywords: "flexible", "9 hours", "not fixed"
- **Validation:** Employee existence check, hospital matching

### GPS Validation Priority
1. **First:** Check `employee.hospital_id` → use hospital coordinates + radius
2. **Fallback:** Use `employee.office_settings_id` → existing logic
3. **Logging:** Clear indication which reference is used

### Attendance Engine Updates
- **Flexible Shift Path:**
  - Check-in: Never late, capture time
  - Check-out: Calculate working hours, status based on >= required_hours
  - No overtime, no early leave
  
- **Fixed Shift Path (unchanged):**
  - Check-in: Compare with shift_start_time, mark late if applicable
  - Check-out: Calculate overtime, early leave
  - Working hours based on shift duration

---

## Excel File Formats

### Hospital Import File
**Required Columns:**
```
| Hospital  Name | Location | Latitude | Longitude | Status |
|----------------|----------|----------|-----------|--------|
| Head Office    | Mumbai   | 19.01485 | 72.8452   | Active |
| Hospital ABC   | Pune     | 18.52043 | 73.85674  | Active |
```

**Notes:**
- Latitude/Longitude must be valid decimal degrees
- Status: Active, Inactive, Closed (case-insensitive)
- Duplicate names are skipped with warning

### Employee Allocation File
**Required Columns:**
```
| EMP-CODE | WORKING LOCATION | full Shift timing      | WORKING STATUS |
|----------|------------------|------------------------|----------------|
| EMP001   | Head Office      | 10:00 AM to 7:00 PM    | Active         |
| EMP002   | Claim Department | Flexible Shift         | Active         |
| EMP003   | Hospital ABC     | 9:00 am to 6:00 pm     | Active         |
```

**Notes:**
- EMP-CODE must match existing employee.employee_code
- WORKING LOCATION is fuzzy-matched to hospital.name
- Shift timing formats supported:
  - "HH:MM AM to HH:MM PM"
  - "HH:MM am to HH:MM pm"
  - "Flexible Shift" / "Flexible" / "9 hours"
  - Any format with "flexible", "not fixed" keywords

---

## Troubleshooting

### Issue: GPS Validation Fails for Head Office Employees

**Check:**
1. Employee has hospital_id set
2. Hospital coordinates are correct: 19.014847, 72.8452
3. Radius is reasonable: 100m (recommended)
4. Employee's actual GPS coordinates are within radius

**Debug:**
```sql
SELECT 
  e.employee_code,
  e.name,
  e.hospital_id,
  h.name as hospital_name,
  h.latitude,
  h.longitude,
  h.allowed_radius_metres
FROM employee e
LEFT JOIN hospitals h ON e.hospital_id = h.id
WHERE e.employee_code = 'EMP001';
```

### Issue: Flexible Employee Marked Late

**Check:**
1. `employee.is_flexible_shift = true`
2. `employee.required_working_hours = 9.0` (default)
3. Attendance engine logic updated

**Debug:**
```sql
SELECT 
  employee_code,
  name,
  is_flexible_shift,
  required_working_hours,
  current_shift
FROM employee
WHERE employee_code = 'EMP001';
```

**Fix if needed:**
```sql
UPDATE employee 
SET is_flexible_shift = true,
    required_working_hours = 9.0
WHERE current_shift LIKE '%Flexible%';
```

### Issue: Import Shows "Employee Not Found"

**Cause:** EMP-CODE in Excel doesn't match database

**Solution:**
1. Check employee_code format (case-sensitive)
2. Verify employee exists:
```sql
SELECT employee_code, name FROM employee WHERE employee_code = 'EMP001';
```
3. Update Excel or database to match

### Issue: Hospital Not Matched During Import

**Cause:** Fuzzy matching threshold not met

**Solution:**
1. Check hospital name in Excel vs database
2. Ensure similarity > 60%
3. Consider exact match or manual assignment

**Example:**
- Excel: "Claim Team"
- Database: "Claim Department"
- Match: YES (similar enough)

- Excel: "ABC Hospital"
- Database: "XYZ Clinic"
- Match: NO (too different)

---

## Post-Deployment Verification

### 1. Run Full System Check
```bash
# Check database
psql $DATABASE_URL -c "SELECT COUNT(*) FROM hospitals;"
psql $DATABASE_URL -c "SELECT COUNT(*) FROM employee WHERE hospital_id IS NOT NULL;"
psql $DATABASE_URL -c "SELECT COUNT(*) FROM employee WHERE is_flexible_shift = true;"

# Check logs
tail -n 100 logs/application.log | grep -i hospital
tail -n 100 logs/application.log | grep -i flexible
```

### 2. Test User Workflows
- [ ] Admin can view hospitals list
- [ ] Admin can create new hospital with coordinates
- [ ] Admin can import hospitals from Excel
- [ ] Admin can import employee allocations from Excel
- [ ] Employee with hospital allocation: GPS validates against hospital
- [ ] Employee without hospital: GPS validates against office (fallback)
- [ ] Flexible employee: Never late, 9-hour based attendance
- [ ] Fixed employee: Existing shift logic works

### 3. Monitor Import Logs
```sql
SELECT 
  import_type,
  filename,
  total_rows,
  successful_rows,
  failed_rows,
  created_at,
  created_by
FROM import_logs
ORDER BY created_at DESC
LIMIT 10;
```

---

## Rollback Plan

If issues arise, rollback with:

```sql
-- Remove hospital allocations
UPDATE employee SET 
  hospital_id = NULL,
  current_shift = NULL,
  shift_start_time = NULL,
  shift_end_time = NULL,
  is_flexible_shift = false,
  required_working_hours = 9.0;

-- Delete hospitals
DELETE FROM import_logs WHERE import_type IN ('hospital', 'employee_allocation');
DELETE FROM hospitals;

-- Drop columns (if needed)
ALTER TABLE employee DROP COLUMN IF EXISTS hospital_id;
ALTER TABLE employee DROP COLUMN IF EXISTS current_shift;
ALTER TABLE employee DROP COLUMN IF EXISTS shift_start_time;
ALTER TABLE employee DROP COLUMN IF EXISTS shift_end_time;
ALTER TABLE employee DROP COLUMN IF EXISTS is_flexible_shift;
ALTER TABLE employee DROP COLUMN IF EXISTS required_working_hours;

-- Drop tables
DROP TABLE IF EXISTS import_logs;
DROP TABLE IF EXISTS hospitals;
```

**Note:** GPS validation and attendance engine will automatically fall back to original behavior (office_settings only).

---

## Support & Maintenance

### Logs to Monitor
- `logs/application.log` - General app operations
- `logs/attendance.log` - Attendance check-in/out events
- `logs/audit.log` - Import activities

### Key Metrics
- Hospital allocation coverage: `SELECT COUNT(*) FROM employee WHERE hospital_id IS NOT NULL;`
- Flexible shift adoption: `SELECT COUNT(*) FROM employee WHERE is_flexible_shift = true;`
- Import success rate: `SELECT AVG(successful_rows * 100.0 / total_rows) FROM import_logs;`

### Regular Tasks
1. **Weekly:** Review import logs for patterns
2. **Monthly:** Verify GPS radius settings match actual site coverage
3. **Quarterly:** Audit flexible vs fixed shift distribution

---

## Coordinates Summary

For quick reference during hospital creation:

| Location | Latitude | Longitude | Radius (m) |
|----------|----------|-----------|------------|
| Head Office | 19.014847 | 72.8452 | 100 |
| Claim Department | 19.014847 | 72.8452 | 100 |

**Use these coordinates when:**
- Creating Head Office hospital record
- Creating Claim Department hospital record
- Testing GPS validation for Mumbai employees
- Configuring office settings for central location

---

## Success Criteria

✅ **Deployment is successful when:**
1. Migration completes without errors
2. Hospitals import from Excel with >90% success rate
3. Employee allocations import with >90% match rate
4. Head Office employees validate GPS against 19.014847, 72.8452
5. Flexible shift employees never marked late
6. Flexible shift employees marked Present with 9+ working hours
7. Fixed shift employees continue existing attendance logic
8. Import logs show audit trail
9. Admin UI accessible and functional
10. No errors in application logs related to hospital/GPS features

---

## Next Steps

1. ✅ Complete code implementation (DONE)
2. ⏳ Run database migration
3. ⏳ Create Head Office hospital with coordinates 19.014847, 72.8452
4. ⏳ Import hospitals from Excel
5. ⏳ Import employee allocations from Excel
6. ⏳ Test GPS validation
7. ⏳ Test flexible shift attendance
8. ⏳ Monitor logs for 48 hours
9. ⏳ Commit and push to production
10. ⏳ Train admin users on new features

---

**Deployment Date:** _____________  
**Deployed By:** _____________  
**Verified By:** _____________  
**Sign-off:** _____________
