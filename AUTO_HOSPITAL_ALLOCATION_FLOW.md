# 🏥 Auto Hospital Allocation Flow

## Overview

The system **automatically fetches** an employee's hospital location, shift timing, and working hours during registration based on their employee code. This data is then used for GPS validation and attendance marking.

---

## 🔄 Complete Flow

### **Step 1: Import Employee Master Data (Admin)**

**When:** Before employees can register  
**Who:** HR Admin  
**Where:** Admin Panel → Import Employees

#### Process:
1. Admin uploads Excel file with columns:
   - `EMP-CODE` (Required) - Employee code (e.g., E-1104001)
   - `NAME` (Required) - Full name
   - `DEPARTMENT` (Optional)
   - `DESIGNATION` (Optional)
   - **`WORKING LOCATION`** (Optional) - Hospital name (e.g., "Head Office", "Claim Department")
   - **`FULL SHIFT TIMING`** (Optional) - Shift hours (e.g., "10:00 AM to 7:00 PM", "Flexible Shift")
   - **`WORKING STATUS`** (Optional) - Status (e.g., "Active", "Flexible")

2. System imports data into `employee_master` table:
```sql
INSERT INTO employee_master (
    employee_code,
    employee_name,
    department,
    designation,
    working_location,    -- "Head Office"
    shift_timing,        -- "10:00 AM to 7:00 PM"
    working_status,      -- "Active"
    is_registered
) VALUES (
    'E-1104001',
    'John Doe',
    'IT',
    'Developer',
    'Head Office',
    '10:00 AM to 7:00 PM',
    'Active',
    FALSE
);
```

---

### **Step 2: Employee Self-Registration**

**When:** Employee first-time login  
**Who:** Employee  
**Where:** Login Page → Register Tab

#### Process:

1. **Employee enters their code:**
   ```
   Employee Code: E-1104001
   ```

2. **System looks up master data** (`lookup_employee` AJAX call):
   ```sql
   SELECT 
       employee_code,
       employee_name,
       department,
       designation,
       working_location,  -- Fetched!
       shift_timing,      -- Fetched!
       working_status     -- Fetched!
   FROM employee_master
   WHERE employee_code = 'E-1104001'
     AND is_registered = FALSE;
   ```

3. **System shows employee name:**
   ```
   Employee Name: John Doe ✓
   Department: IT
   ```

4. **Employee sets password and clicks Register**

5. **System performs AUTO-ALLOCATION:**

   a) **Find matching hospital** (fuzzy match on working_location):
   ```sql
   SELECT id, hospital_name, latitude, longitude, allowed_radius_metres
   FROM hospitals
   WHERE status = 'Active';
   ```
   
   System compares "Head Office" (from master) with hospital names:
   - "Head Office" vs "Head Office" → 100% match ✓
   - "Head Office" vs "Mumbai Head Office" → 80% match ✓ (threshold: 60%)
   - "Head Office" vs "Claim Department" → 30% match ✗
   
   Result: `hospital_id = 1` (Head Office with coordinates 19.014847, 72.8452)

   b) **Parse shift timing** (from "10:00 AM to 7:00 PM"):
   ```python
   shift_info = {
       'shift_name': 'Morning Shift',
       'start_time': '10:00',
       'end_time': '19:00',
       'is_flexible': False,
       'required_hours': 9.0
   }
   ```
   
   If shift_timing was "Flexible Shift":
   ```python
   shift_info = {
       'shift_name': 'Flexible Shift',
       'start_time': None,
       'end_time': None,
       'is_flexible': True,
       'required_hours': 9.0
   }
   ```

   c) **Create employee profile with allocation**:
   ```sql
   INSERT INTO employee (
       user_id,
       employee_code,
       department,
       designation,
       hospital_id,           -- Auto-populated!
       current_shift,         -- Auto-populated!
       shift_start_time,      -- Auto-populated!
       shift_end_time,        -- Auto-populated!
       is_flexible_shift,     -- Auto-populated!
       required_working_hours -- Auto-populated!
   ) VALUES (
       123,                   -- user.id
       'E-1104001',
       'IT',
       'Developer',
       1,                     -- hospital_id (Head Office)
       'Morning Shift',
       '10:00',
       '19:00',
       0,                     -- FALSE (fixed shift)
       9
   );
   ```

6. **Success message:**
   ```
   "Account created as Employee. 
    Allocated to Head Office. 
    Morning Shift assigned. 
    You can now sign in."
   ```

7. **Mark as registered:**
   ```sql
   UPDATE employee_master
   SET is_registered = TRUE,
       user_id = 123,
       registered_at = NOW()
   WHERE employee_code = 'E-1104001';
   ```

---

### **Step 3: Employee Login**

**When:** After registration  
**Who:** Employee  
**Where:** Login Page

1. Employee enters credentials:
   ```
   Employee Code: E-1104001
   Password: ********
   Department: IT
   ```

2. System authenticates and loads employee profile with hospital allocation

---

### **Step 4: Check-In (Attendance)**

**When:** Employee wants to mark attendance  
**Who:** Employee  
**Where:** Attendance Page

#### Process:

1. **Employee clicks "Check In"**

2. **Browser captures GPS coordinates:**
   ```javascript
   navigator.geolocation.getCurrentPosition((pos) => {
       latitude: 19.014850,  // Near Head Office
       longitude: 72.845200,
       accuracy: 15 // meters
   });
   ```

3. **System fetches employee's allocated hospital:**
   ```python
   employee = Employee.query.filter_by(employee_code='E-1104001').first()
   
   # Check if employee has hospital allocation
   if employee.hospital_id:
       hospital = Hospital.query.get(employee.hospital_id)
       # Use hospital coordinates for validation
       reference_lat = hospital.latitude      # 19.014847
       reference_lon = hospital.longitude     # 72.8452
       allowed_radius = hospital.allowed_radius_metres  # 100m
   else:
       # Fallback to office settings
       office = OfficeSettings.query.first()
       reference_lat = office.latitude
       reference_lon = office.longitude
       allowed_radius = office.radius_metres
   ```

4. **GPS Validation:**
   ```python
   distance = haversine_distance(
       employee_lat=19.014850,
       employee_lon=72.845200,
       hospital_lat=19.014847,
       hospital_lon=72.8452
   )
   # Result: distance = 45.23 meters
   
   is_valid = distance <= 100  # allowed_radius
   # Result: TRUE ✓
   ```

5. **Check-In Meta Calculation (Attendance Engine):**
   ```python
   # Employee has is_flexible_shift = False
   # shift_start_time = '10:00'
   # current_time = '10:15'
   
   if not employee.is_flexible_shift:
       # Fixed shift logic
       is_late = current_time > shift_start_time
       late_minutes = 15
   else:
       # Flexible shift logic
       is_late = False
       late_minutes = 0
   ```

6. **Create attendance record:**
   ```sql
   INSERT INTO attendance (
       employee_id,
       date,
       check_in_time,
       check_in_latitude,
       check_in_longitude,
       check_in_accuracy,
       is_late,
       late_minutes,
       status
   ) VALUES (
       123,
       '2026-07-24',
       '2026-07-24 10:15:00 UTC',
       19.014850,
       72.845200,
       15,
       TRUE,
       15,
       'present'
   );
   ```

7. **Log GPS validation:**
   ```
   INFO: GPS validation using hospital reference: Head Office
   INFO: Hospital coordinates: 19.014847, 72.8452 with radius: 100m
   INFO: Employee distance from hospital: 45.23m
   INFO: GPS validation result: True
   ```

---

### **Step 5: Check-Out (Attendance)**

**When:** Employee ends work  
**Who:** Employee  
**Where:** Attendance Page

#### Process:

1. **Employee clicks "Check Out"**

2. **GPS validated same way** (against hospital coordinates)

3. **Calculate working hours:**
   ```python
   check_in = datetime(2026, 7, 24, 10, 15)   # 10:15 AM
   check_out = datetime(2026, 7, 24, 19, 30)  # 7:30 PM
   working_minutes = (check_out - check_in).seconds / 60
   # Result: 555 minutes = 9h 15m
   ```

4. **Attendance status based on shift type:**

   **For Fixed Shift:**
   ```python
   if working_minutes >= shift_duration:
       status = 'present'
       overtime = working_minutes - shift_duration
   elif working_minutes >= half_day_threshold:
       status = 'half_day'
   else:
       status = 'half_day'
   ```

   **For Flexible Shift:**
   ```python
   if working_minutes >= (required_working_hours * 60):
       status = 'present'  # >= 9 hours
   else:
       status = 'half_day'  # < 9 hours
   
   overtime = 0  # Never calculated for flexible
   ```

5. **Update attendance record:**
   ```sql
   UPDATE attendance
   SET check_out_time = '2026-07-24 19:30:00 UTC',
       check_out_latitude = 19.014855,
       check_out_longitude = 72.845190,
       working_minutes = 555,
       working_hours = 9.25,
       status = 'present',
       overtime_hours = 0.25
   WHERE id = 456;
   ```

---

## 📊 Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ 1. ADMIN IMPORTS EXCEL                                      │
│    employee master full upload.xlsx                         │
│    ↓                                                         │
│    employee_master table                                    │
│    • employee_code: E-1104001                               │
│    • employee_name: John Doe                                │
│    • working_location: Head Office                          │
│    • shift_timing: 10:00 AM to 7:00 PM                      │
│    • is_registered: FALSE                                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. EMPLOYEE REGISTERS                                       │
│    Enters: E-1104001 + Password                             │
│    ↓                                                         │
│    System LOOKS UP employee_master                          │
│    ↓                                                         │
│    System FINDS HOSPITAL: fuzzy match "Head Office"         │
│    ↓                                                         │
│    System PARSES SHIFT: "10:00 AM to 7:00 PM"               │
│    ↓                                                         │
│    Creates employee record with AUTO-POPULATED:             │
│    • hospital_id: 1 (Head Office)                           │
│    • current_shift: Morning Shift                           │
│    • shift_start_time: 10:00                                │
│    • shift_end_time: 19:00                                  │
│    • is_flexible_shift: FALSE                               │
│    • required_working_hours: 9                              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. EMPLOYEE CHECK-IN                                        │
│    Browser captures GPS: 19.014850, 72.845200               │
│    ↓                                                         │
│    System loads employee.hospital_id → Hospital             │
│    ↓                                                         │
│    GPS validation against hospital coordinates:             │
│    • Hospital: 19.014847, 72.8452                           │
│    • Distance: 45.23m                                       │
│    • Allowed: 100m                                          │
│    • Result: VALID ✓                                        │
│    ↓                                                         │
│    Check-in recorded with:                                  │
│    • is_late: TRUE (10:15 > 10:00)                          │
│    • late_minutes: 15                                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. EMPLOYEE CHECK-OUT                                       │
│    Browser captures GPS (validated same way)                │
│    ↓                                                         │
│    Calculate working hours: 9h 15m                          │
│    ↓                                                         │
│    Determine status:                                        │
│    • Fixed shift: Compare with shift duration               │
│    • Flexible shift: Compare with required_hours (9h)       │
│    ↓                                                         │
│    Update attendance: status = 'present'                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Key Features

### ✅ Automatic Hospital Allocation
- **No manual assignment needed**
- **Fetched from employee master during registration**
- **Fuzzy matching** handles name variations (60% similarity threshold)

### ✅ Automatic Shift Detection
- **Parses shift timing string** (e.g., "10:00 AM to 7:00 PM")
- **Detects flexible shifts** by keywords ("flexible", "9 hours", "not fixed")
- **Calculates shift duration** automatically

### ✅ GPS Validation Priority
1. **First:** Use employee's allocated hospital coordinates
2. **Fallback:** Use office settings coordinates
3. **Logging:** Clear indication which reference is used

### ✅ Attendance Logic
**Fixed Shift:**
- Late if check-in > shift_start_time
- Overtime if working_hours > shift_duration
- Early leave if check-out < shift_end_time

**Flexible Shift:**
- Never marked late
- Present if working_hours >= required_working_hours (default: 9)
- No overtime calculation
- No early leave concept

---

## 🔧 Database Schema

### employee_master (Source of Truth)
```sql
CREATE TABLE employee_master (
    id SERIAL PRIMARY KEY,
    employee_code VARCHAR(30) UNIQUE NOT NULL,
    employee_name VARCHAR(200) NOT NULL,
    department VARCHAR(100),
    designation VARCHAR(100),
    -- Hospital allocation fields (NEW)
    working_location VARCHAR(200),      -- "Head Office", "Claim Department"
    shift_timing VARCHAR(100),          -- "10:00 AM to 7:00 PM", "Flexible Shift"
    working_status VARCHAR(50),         -- "Active", "Flexible"
    -- Registration state
    is_registered BOOLEAN DEFAULT FALSE,
    user_id INTEGER,
    registered_at TIMESTAMP
);
```

### employee (Profile with Allocation)
```sql
CREATE TABLE employee (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    employee_code VARCHAR(30),
    department VARCHAR(100),
    designation VARCHAR(100),
    -- Hospital allocation (AUTO-POPULATED from master)
    hospital_id INTEGER REFERENCES hospitals(id),
    current_shift VARCHAR(50),           -- "Morning Shift", "Flexible Shift"
    shift_start_time VARCHAR(20),        -- "10:00"
    shift_end_time VARCHAR(20),          -- "19:00"
    is_flexible_shift INTEGER DEFAULT 0, -- 0=Fixed, 1=Flexible
    required_working_hours INTEGER DEFAULT 9
);
```

### hospitals (GPS Coordinates)
```sql
CREATE TABLE hospitals (
    id SERIAL PRIMARY KEY,
    hospital_name VARCHAR(200) NOT NULL,
    location VARCHAR(200),
    latitude DOUBLE PRECISION,           -- 19.014847
    longitude DOUBLE PRECISION,          -- 72.8452
    allowed_radius_metres INTEGER,       -- 100
    status VARCHAR(20)                   -- 'Active'
);
```

---

## 📝 Example Scenarios

### Scenario 1: Head Office Employee (Fixed Shift)

**Master Data:**
- Code: E-1104001
- Name: John Doe
- Working Location: Head Office
- Shift Timing: 10:00 AM to 7:00 PM
- Working Status: Active

**Registration:**
- System finds Hospital "Head Office" (19.014847, 72.8452)
- Parses shift: Morning Shift, 10:00-19:00
- Creates profile with hospital_id=1, fixed shift

**Check-In:**
- GPS: Within 100m of Head Office
- Time: 10:15 AM
- Result: Valid GPS ✓, Late 15 minutes

**Check-Out:**
- GPS: Within 100m of Head Office
- Time: 7:30 PM
- Working Hours: 9h 15m
- Result: Present, 15 minutes overtime

---

### Scenario 2: Claim Department Employee (Flexible Shift)

**Master Data:**
- Code: E-1507005
- Name: Jane Smith
- Working Location: Claim Department
- Shift Timing: Flexible Shift
- Working Status: Flexible

**Registration:**
- System finds Hospital "Claim Department" (19.014847, 72.8452)
- Detects flexible shift
- Creates profile with hospital_id=2, flexible shift

**Check-In:**
- GPS: Within 100m of Claim Department
- Time: 11:30 AM (any time OK)
- Result: Valid GPS ✓, Never late

**Check-Out:**
- GPS: Within 100m of Claim Department
- Time: 9:00 PM
- Working Hours: 9h 30m
- Result: Present (>= 9 hours), No overtime

---

### Scenario 3: Employee Not Allocated to Hospital

**Master Data:**
- Code: E-2603028
- Name: Bob Wilson
- Working Location: (empty)
- Shift Timing: (empty)

**Registration:**
- No hospital match found
- No shift timing
- Creates profile with hospital_id=NULL

**Check-In:**
- GPS validated against **office settings** (fallback)
- Office coordinates used instead of hospital
- Standard office hours applied

---

## 🚀 Benefits

### For Employees:
✅ **No manual input** - Everything fetched automatically  
✅ **Fast registration** - Just code + password  
✅ **Accurate GPS** - Validates against correct hospital  
✅ **Clear shift info** - Knows their schedule  

### For HR/Admin:
✅ **Single source** - Excel import does everything  
✅ **No duplication** - Master data used for registration  
✅ **Easy updates** - Re-import Excel to update allocations  
✅ **Audit trail** - Logs show hospital allocation history  

### For System:
✅ **Automated** - Zero manual configuration per employee  
✅ **Scalable** - Handles thousands of employees  
✅ **Flexible** - Supports multiple hospitals and shift types  
✅ **Reliable** - Fallback to office settings if no hospital  

---

## 📖 Summary

The system creates a **seamless flow** from Excel import to attendance marking:

1. **Admin imports Excel** → Stores allocation data in employee_master
2. **Employee registers** → System auto-fetches and populates hospital + shift
3. **Employee checks in** → GPS validates against hospital coordinates
4. **Attendance marked** → Follows shift rules (fixed/flexible)

**No manual intervention required!** Everything is automatic based on the employee code.

---

**Head Office & Claim Department Coordinates:** 19.014847°, 72.8452°  
**Recommended Radius:** 100 meters  
**System Status:** Ready for deployment
