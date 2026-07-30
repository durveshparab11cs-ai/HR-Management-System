# Excel Import Mapping Guide

## Your Excel File Structure

Based on the provided Excel file, here's how the data is mapped:

### Column Mapping

| Excel Column | Column Name | Maps To | Example Data |
|--------------|-------------|---------|--------------|
| **A** | EMP-CODE | `employee_master.employee_code` | E-2603028 |
| **B** | NAME | `employee_master.employee_name` | Aastha Vishwakarma |
| **C** | WORKING STATUS | `employee_master.working_status` | Active, Active- OUTSTATION, Non-Active |
| **D** | WORKING LOCATION | `employee_master.working_location` | AIIMS Hospital (Gorakhpur), Claim Team |
| **E** | full Shift timing | `employee_master.shift_timing` | 8:00 AM to 5:00 PM, 10:00 AM to 7:00 PM |

---

## Sample Data Processing

### Example 1: AIIMS Hospital Employee

**Excel Row:**
```
EMP-CODE: E-2603028
NAME: Aastha Vishwakarma
WORKING STATUS: Active
WORKING LOCATION: AIIMS Hospital (Gorakhpur)
full Shift timing: 8:00 AM to 5:00 PM
```

**Stored in `employee_master`:**
```sql
INSERT INTO employee_master (
    employee_code,
    employee_name,
    working_status,
    working_location,
    shift_timing,
    is_registered
) VALUES (
    'E-2603028',
    'Aastha Vishwakarma',
    'Active',
    'AIIMS Hospital (Gorakhpur)',
    '8:00 AM to 5:00 PM',
    FALSE
);
```

**When Employee Registers:**

1. **Hospital Matching:**
   - System searches for hospitals matching "AIIMS Hospital (Gorakhpur)"
   - If hospital "AIIMS Hospital (Gorakhpur)" exists → Allocates
   - If not found → Tries fuzzy match with existing hospitals
   - Fallback → No hospital assigned (uses office settings)

2. **Shift Parsing:**
   ```python
   Input: "8:00 AM to 5:00 PM"
   
   Parsed Result:
   {
       'shift_name': 'Morning Shift',
       'start_time': '08:00',
       'end_time': '17:00',
       'is_flexible': False,
       'required_hours': 9.0
   }
   ```

3. **Employee Profile Created:**
   ```sql
   INSERT INTO employee (
       employee_code,
       employee_name,
       hospital_id,              -- ID of "AIIMS Hospital (Gorakhpur)"
       current_shift,            -- "Morning Shift"
       shift_start_time,         -- "08:00"
       shift_end_time,           -- "17:00"
       is_flexible_shift,        -- 0 (FALSE)
       required_working_hours    -- 9
   ) VALUES (...)
   ```

---

### Example 2: Claim Team Employee

**Excel Row:**
```
EMP-CODE: E-2406013
NAME: Ajay Mahesh Kanjotkar
WORKING STATUS: Active
WORKING LOCATION: Claim Team
full Shift timing: 10:00 AM to 7:00 PM
```

**Stored in `employee_master`:**
```sql
INSERT INTO employee_master VALUES (
    'E-2406013',
    'Ajay Mahesh Kanjotkar',
    'Active',
    'Claim Team',
    '10:00 AM to 7:00 PM',
    FALSE
);
```

**When Employee Registers:**

1. **Hospital Matching:**
   - System searches for "Claim Team"
   - Matches with "Claim Department" hospital (fuzzy match 70% similarity)
   - Uses coordinates: **19.014847, 72.8452**

2. **Shift Parsing:**
   ```python
   Input: "10:00 AM to 7:00 PM"
   
   Parsed Result:
   {
       'shift_name': 'Afternoon Shift',
       'start_time': '10:00',
       'end_time': '19:00',
       'is_flexible': False,
       'required_hours': 9.0
   }
   ```

3. **GPS Validation:**
   - Check-in must be within 100m of 19.014847, 72.8452
   - Late if check-in after 10:00 AM

---

### Example 3: Amravati Hospital Employee

**Excel Row:**
```
EMP-CODE: E-2407010
NAME: Naresh Kumar
WORKING STATUS: Active
WORKING LOCATION: Amravati Hospital
full Shift timing: 9:00 AM to 6:00 PM
```

**When Employee Registers:**

1. **Hospital Matching:**
   - Searches for "Amravati Hospital"
   - If exists → Allocates with its GPS coordinates
   - If not exists → No allocation (uses office settings)

2. **Shift Parsing:**
   ```python
   Input: "9:00 AM to 6:00 PM"
   
   Parsed Result:
   {
       'shift_name': 'Morning Shift',
       'start_time': '09:00',
       'end_time': '18:00',
       'is_flexible': False,
       'required_hours': 9.0
   }
   ```

---

### Example 4: Outstation Employee

**Excel Row:**
```
EMP-CODE: E-2506034
NAME: Akash Dubey
WORKING STATUS: Active- OUTSTATION
WORKING LOCATION: AIIMS Hospital (Gorakhpur)
full Shift timing: 11:00 AM to 8:00 PM
```

**When Employee Registers:**

1. **Hospital Matching:**
   - Matches "AIIMS Hospital (Gorakhpur)"
   - GPS coordinates assigned

2. **Shift Parsing:**
   ```python
   Input: "11:00 AM to 8:00 PM"
   
   Parsed Result:
   {
       'shift_name': 'Afternoon Shift',
       'start_time': '11:00',
       'end_time': '20:00',
       'is_flexible': False,
       'required_hours': 9.0
   }
   ```

3. **Status:**
   - `working_status` = "Active- OUTSTATION" (stored for reference)
   - Still gets GPS validation and shift tracking

---

## Shift Parsing Logic

### Supported Formats

| Input Format | Start Time | End Time | Shift Name |
|--------------|------------|----------|------------|
| `8:00 AM to 5:00 PM` | 08:00 | 17:00 | Morning Shift |
| `9:00 AM to 6:00 PM` | 09:00 | 18:00 | Morning Shift |
| `10:00 AM to 7:00 PM` | 10:00 | 19:00 | Afternoon Shift |
| `11:00 AM to 8:00 PM` | 11:00 | 20:00 | Afternoon Shift |
| `12:00 PM to 9:00 PM` | 12:00 | 21:00 | Afternoon Shift |
| `3:00 PM to 12:00 AM` | 15:00 | 00:00 | Evening Shift |
| `9:00 PM to 6:00 AM` | 21:00 | 06:00 | Night Shift |
| `Flexible Shift` | NULL | NULL | Flexible Shift (9-hour based) |

### Shift Type Detection

```python
def determine_shift_type(start_hour):
    """
    Determines shift name based on start time.
    
    Morning Shift: 5 AM - 10 AM
    Afternoon Shift: 10 AM - 3 PM
    Evening Shift: 3 PM - 8 PM
    Night Shift: 8 PM - 5 AM
    """
    if 5 <= start_hour < 10:
        return "Morning Shift"
    elif 10 <= start_hour < 15:
        return "Afternoon Shift"
    elif 15 <= start_hour < 20:
        return "Evening Shift"
    else:
        return "Night Shift"
```

### Flexible Shift Detection

Keywords that trigger flexible shift:
- "flexible"
- "flexi"
- "not fixed"
- "9 hours"
- "nine hours"

**Example:**
```
Input: "Flexible Shift" or "9 hours flexible"
Result: is_flexible_shift = TRUE, required_working_hours = 9
```

---

## Hospital Matching Logic

### Exact Match (100%)
```
Excel: "Claim Team"
Hospital DB: "Claim Team"
Result: ✓ Match (hospital_id assigned)
```

### Fuzzy Match (≥60% similarity)
```
Excel: "Claim Team"
Hospital DB: "Claim Department"
Similarity: 70%
Result: ✓ Match (hospital_id assigned)
```

### Partial Match
```
Excel: "AIIMS Hospital (Gorakhpur)"
Hospital DB: "AIIMS Gorakhpur"
Similarity: 85%
Result: ✓ Match
```

### No Match
```
Excel: "New Hospital ABC"
Hospital DB: (no similar hospital)
Result: ✗ No match (hospital_id = NULL, uses office settings)
```

---

## Complete Registration Flow

### Step 1: Admin Imports Excel

```
Admin → Import Employees → Upload your Excel file
↓
System reads columns A, B, C, D, E
↓
Inserts into employee_master table with ALL allocation data
```

### Step 2: Employee Registers

```
Employee enters: E-2603028
↓
System queries employee_master:
  - employee_code: E-2603028
  - employee_name: Aastha Vishwakarma
  - working_location: AIIMS Hospital (Gorakhpur)
  - shift_timing: 8:00 AM to 5:00 PM
  - working_status: Active
↓
System finds hospital: "AIIMS Hospital (Gorakhpur)"
  - hospital_id: 5
  - latitude: 26.7606
  - longitude: 83.3732
  - radius: 150m
↓
System parses shift: "8:00 AM to 5:00 PM"
  - shift_name: Morning Shift
  - start_time: 08:00
  - end_time: 17:00
  - is_flexible: FALSE
↓
Creates employee profile with:
  - hospital_id: 5
  - current_shift: Morning Shift
  - shift_start_time: 08:00
  - shift_end_time: 17:00
  - is_flexible_shift: 0
  - required_working_hours: 9
```

### Step 3: Employee Checks In

```
Employee opens attendance page
↓
Browser captures GPS: 26.7610, 83.3728
↓
System loads employee's hospital (ID 5)
  - Reference: 26.7606, 83.3732
  - Radius: 150m
↓
Calculates distance: 52m
↓
Validation: 52m < 150m → VALID ✓
↓
Checks time: 8:15 AM > 8:00 AM → LATE (15 minutes)
↓
Records attendance:
  - GPS validated against AIIMS Hospital coordinates
  - is_late: TRUE
  - late_minutes: 15
```

---

## Expected Results from Your Excel

### For Claim Team Employees (Rows 23-30 in your Excel)

All these employees will be allocated to **"Claim Department"** with coordinates **19.014847, 72.8452**:

| EMP-CODE | Name | Shift Timing | Expected Allocation |
|----------|------|--------------|---------------------|
| E-2406013 | Ajay Mahesh Kanjotkar | 10:00 AM to 7:00 PM | Claim Dept, 10:00-19:00 |
| E-2408028 | Akshay Dinesh Wagh | 10:00 AM to 8:00 PM | Claim Dept, 10:00-20:00 |
| E-2607022 | Ashish Mohan Dhake | 10:00 AM to 7:00 PM | Claim Dept, 10:00-19:00 |
| E-2606028 | Atharva Jadhav | 11:00 AM to 8:00 PM | Claim Dept, 11:00-20:00 |

### For AIIMS Hospital Employees (Rows 3-22 in your Excel)

All these employees will be allocated to **"AIIMS Hospital (Gorakhpur)"** with its GPS coordinates:

| EMP-CODE | Name | Shift Timing | Expected Allocation |
|----------|------|--------------|---------------------|
| E-2603028 | Aastha Vishwakarma | 8:00 AM to 5:00 PM | AIIMS, 08:00-17:00 |
| E-2405029 | Abhinay Tiwari | 11:00 AM to 8:00 PM | AIIMS, 11:00-20:00 |
| E-2506034 | Akash Dubey | 11:00 AM to 8:00 PM | AIIMS, 11:00-20:00 |

---

## Verification Steps

### 1. After Excel Import

Check employee_master table:
```sql
SELECT 
    employee_code,
    employee_name,
    working_location,
    shift_timing,
    working_status,
    is_registered
FROM employee_master
WHERE employee_code = 'E-2603028';
```

Expected:
```
employee_code: E-2603028
employee_name: Aastha Vishwakarma
working_location: AIIMS Hospital (Gorakhpur)
shift_timing: 8:00 AM to 5:00 PM
working_status: Active
is_registered: FALSE
```

### 2. After Employee Registers

Check employee table:
```sql
SELECT 
    e.employee_code,
    e.hospital_id,
    h.hospital_name,
    h.latitude,
    h.longitude,
    e.current_shift,
    e.shift_start_time,
    e.shift_end_time,
    e.is_flexible_shift
FROM employee e
LEFT JOIN hospitals h ON e.hospital_id = h.id
WHERE e.employee_code = 'E-2603028';
```

Expected:
```
employee_code: E-2603028
hospital_id: 5
hospital_name: AIIMS Hospital (Gorakhpur)
latitude: 26.7606
longitude: 83.3732
current_shift: Morning Shift
shift_start_time: 08:00
shift_end_time: 17:00
is_flexible_shift: 0
```

### 3. Check Registration Message

When employee completes registration, they see:
```
✅ Account created as Employee.
   Allocated to AIIMS Hospital (Gorakhpur).
   Morning Shift assigned.
   You can now sign in.
```

---

## Summary

✅ **Location Auto-Fetch:** Working location from column D automatically matched to hospitals  
✅ **Shift Auto-Fetch:** Shift timing from column E automatically parsed and assigned  
✅ **GPS Auto-Set:** Hospital coordinates used for attendance validation  
✅ **No Manual Entry:** Everything happens during registration automatically  

**Your Excel → System Flow:**
1. Admin imports Excel → Data stored in employee_master
2. Employee registers → Location & shift auto-fetched
3. Employee checks in → GPS validated against hospital
4. Attendance marked → Follows shift rules

**All automatic!** 🎯
