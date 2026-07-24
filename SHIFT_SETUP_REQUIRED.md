# ⚠️ SHIFT SETUP REQUIRED

**Issue:** No shifts available in shift assignment dropdown  
**Status:** 🔴 **ACTION REQUIRED**

---

## Problem

The shift assignment page shows:
- **0 Available Shifts** 
- Empty dropdown: "-- Select Shift --"
- Cannot assign shifts to employees

---

## Root Cause

**No shifts have been created in the system yet.**

The Shift Assignment feature requires shifts to exist in the database before they can be assigned to employees.

---

## Solution: Create Shifts First

### Step 1: Navigate to Shift Management

1. Login as **Super Admin** or **Admin**
2. Go to: **Company** → **Shifts**
3. Or visit directly: `https://hr-management-system-muq3.onrender.com/company/shifts`

### Step 2: Create Your First Shift

Click **"Add Shift"** or **"Create Shift"** button

**Required Fields:**
- **Shift Name:** General Shift / Morning Shift / Night Shift
- **Shift Code:** GEN / MORNING / NIGHT (unique)
- **Start Time:** 10:00 AM
- **End Time:** 07:00 PM
- **Grace Minutes:** 15 (late tolerance)
- **Break Minutes:** 60 (lunch break)
- **Working Days:** Mon-Fri / Mon-Sat
- **Is Night Shift:** No

### Step 3: Common Shift Examples

#### Example 1: General Day Shift
```
Name: General Shift
Code: GEN
Start Time: 10:00 AM
End Time: 07:00 PM
Grace: 15 minutes
Break: 60 minutes
Working Days: Mon-Fri
Night Shift: No
```

#### Example 2: Morning Shift
```
Name: Morning Shift
Code: MORNING
Start Time: 08:00 AM
End Time: 05:00 PM
Grace: 10 minutes
Break: 60 minutes
Working Days: Mon-Sat
Night Shift: No
```

#### Example 3: Afternoon Shift
```
Name: Afternoon Shift
Code: AFTERNOON
Start Time: 02:00 PM
End Time: 11:00 PM
Grace: 15 minutes
Break: 60 minutes
Working Days: Mon-Fri
Night Shift: No
```

#### Example 4: Night Shift
```
Name: Night Shift
Code: NIGHT
Start Time: 10:00 PM
End Time: 07:00 AM
Grace: 20 minutes
Break: 60 minutes
Working Days: Mon-Fri
Night Shift: Yes
```

---

## Step-by-Step Guide

### 1. Access Shift Management

**Via Navigation:**
```
Login → Company Menu → Shifts → Add Shift
```

**Direct URL:**
```
https://hr-management-system-muq3.onrender.com/company/shifts/create
```

### 2. Fill the Form

**Shift Name:**  
Enter a descriptive name (e.g., "General Shift")

**Shift Code:**  
Enter a unique code (e.g., "GEN")  
⚠️ Must be unique across all shifts

**Start Time:**  
Select or type: `10:00 AM`

**End Time:**  
Select or type: `07:00 PM`

**Grace Minutes:**  
Enter: `15`  
(Employees can check in up to 15 minutes late without being marked late)

**Break Minutes:**  
Enter: `60`  
(1 hour lunch break deducted from working hours)

**Working Days:**  
Select from dropdown or enter: `Mon-Fri`

**Is Night Shift:**  
Check if shift crosses midnight

**Description (Optional):**  
"Standard office hours for IT department"

### 3. Save the Shift

Click **"Save"** or **"Create Shift"**

You should see:
✅ "Shift created successfully"

### 4. Verify Shift Created

1. Go back to **Company → Shifts**
2. You should see your shift in the list
3. Status should be **Active**

---

## After Creating Shifts

### Next Steps

Once shifts are created, go back to **Admin Panel → Shift Assignment**

You should now see:
- **Available Shifts:** 1 (or more)
- Dropdown shows your shifts
- Can assign shifts to employees

### Assign Shifts to Employees

**Single Assignment:**
1. Find employee in the list
2. Select shift from dropdown
3. Shift automatically saves

**Bulk Assignment:**
1. Select "Default Shift for All" at the top
2. Choose a shift
3. Click "Apply to All Unassigned"
4. Or click "Assign All" to assign to everyone

---

## Quick Setup Script (Optional)

If you have database access, you can create shifts directly:

### SQL Script

```sql
-- Insert default shifts
INSERT INTO shifts (
    name, code, start_time, end_time, 
    grace_minutes, break_minutes, 
    working_days, is_night_shift, 
    is_active, is_deleted,
    created_at, updated_at
) VALUES
(
    'General Shift', 
    'GEN', 
    '10:00:00', 
    '19:00:00',  -- 7:00 PM in 24-hour
    15, 
    60,
    'Mon-Fri', 
    false,
    true,
    false,
    NOW(),
    NOW()
),
(
    'Morning Shift',
    'MORNING',
    '08:00:00',
    '17:00:00',  -- 5:00 PM
    10,
    60,
    'Mon-Sat',
    false,
    true,
    false,
    NOW(),
    NOW()
);
```

### Python Script (Flask Shell)

```python
from app import app, db
from app.models.company import Shift
from datetime import time

with app.app_context():
    # Create General Shift
    shift1 = Shift(
        name="General Shift",
        code="GEN",
        start_time=time(10, 0),  # 10:00 AM
        end_time=time(19, 0),    # 7:00 PM
        grace_minutes=15,
        break_minutes=60,
        working_days="Mon-Fri",
        is_night_shift=False,
        is_active=True,
        description="Standard office hours"
    )
    
    # Create Morning Shift
    shift2 = Shift(
        name="Morning Shift",
        code="MORNING",
        start_time=time(8, 0),   # 8:00 AM
        end_time=time(17, 0),    # 5:00 PM
        grace_minutes=10,
        break_minutes=60,
        working_days="Mon-Sat",
        is_night_shift=False,
        is_active=True,
        description="Early morning shift"
    )
    
    db.session.add(shift1)
    db.session.add(shift2)
    db.session.commit()
    
    print("✅ Shifts created successfully!")
    print(f"- {shift1.name} ({shift1.code})")
    print(f"- {shift2.name} ({shift2.code})")
```

**Run this in Flask shell:**
```bash
cd smart_hrms
python -m flask shell
# Then paste the Python script above
```

---

## Troubleshooting

### Issue: "Shift code already exists"
**Solution:** Use a different unique code (e.g., GEN2, SHIFT1)

### Issue: "Cannot access Shifts page"
**Solution:** 
- Ensure you're logged in as Admin or Super Admin
- Check URL: `/company/shifts`
- Verify user role in database

### Issue: Shifts created but still not showing
**Solution:**
1. Check `is_active` field in database (should be `true`)
2. Check `is_deleted` field (should be `false`)
3. Refresh the shift assignment page
4. Clear browser cache

### Issue: Shifts show but assignment fails
**Solution:**
- Check server logs for errors
- Verify database connection
- Check `employee_shift_assignments` table exists

---

## System Requirements

### Database Tables Required

✅ `shifts` - Stores shift definitions  
✅ `employees` - Employee records  
✅ `employee_shift_assignments` - Links employees to shifts  
✅ `users` - User accounts with roles  

### User Permissions Required

To create shifts:
- **Role:** Super Admin OR Admin
- **Access:** Company → Shifts

To assign shifts:
- **Role:** Super Admin OR HR Manager OR Admin
- **Access:** Admin Panel → Shift Assignment

---

## Expected Workflow

1. ✅ **Create Shifts** (Company → Shifts → Add Shift)
2. ✅ **Verify Shifts** (Should see in list, status Active)
3. ✅ **Assign Shifts** (Admin Panel → Shift Assignment)
4. ✅ **Verify Assignments** (Check employee list shows assigned shifts)
5. ✅ **Test Attendance** (Employees can now check in/out with shift validation)

---

## Visual Guide

### Before Creating Shifts
```
Shift Assignment Page:
┌─────────────────────────────────┐
│ Available Shifts: 0             │
│ Dropdown: [-- Select Shift --]  │ ← Empty
│ Employees: 3                     │
│ Assigned: 0                      │
│ Unassigned: 3                    │
└─────────────────────────────────┘
```

### After Creating Shifts
```
Shift Assignment Page:
┌─────────────────────────────────┐
│ Available Shifts: 2             │
│ Dropdown:                        │
│   ├─ General Shift (10AM-7PM)   │ ← Shows shifts
│   └─ Morning Shift (8AM-5PM)    │
│ Employees: 3                     │
│ Assigned: 0                      │
│ Unassigned: 3                    │
└─────────────────────────────────┘
```

---

## Additional Resources

### Related Pages
- **Company Management:** `/company`
- **Shift List:** `/company/shifts`
- **Create Shift:** `/company/shifts/create`
- **Shift Assignment:** `/admin/shift-assignment`
- **Employee Master:** `/admin/employee-master`

### Documentation
- Shift Management: How shifts work in HRMS
- Attendance System: How shifts validate check-in/out
- Grace Period: Late tolerance configuration
- Working Hours: Break time calculation

---

## FAQ

**Q: How many shifts should I create?**  
A: Create as many as your organization needs. Common: 1-4 shifts (Morning, Day, Evening, Night)

**Q: Can I edit shifts later?**  
A: Yes, go to Company → Shifts → Edit. Note: Changes affect new assignments only.

**Q: Can I delete shifts?**  
A: Yes, but only if no employees are currently assigned to them.

**Q: What happens if employee has no shift?**  
A: They see "No shift assigned" warning and attendance may not work properly.

**Q: Can employees have different shifts?**  
A: Yes! Each employee can have their own shift. Use bulk assignment for convenience.

**Q: Can shifts change over time?**  
A: Yes! The system tracks shift history with effective dates.

---

## Priority Action

🚨 **IMMEDIATE NEXT STEP:**

1. **Login to system**
2. **Navigate to:** Company → Shifts → Add Shift
3. **Create at least ONE shift** (use General Shift example above)
4. **Return to:** Admin Panel → Shift Assignment
5. **Verify dropdown now shows the shift**

---

## Success Criteria

After completing setup, you should be able to:

✅ See shifts in Company → Shifts  
✅ See "Available Shifts: 1+" in shift assignment page  
✅ Select shifts from dropdown  
✅ Assign shifts to employees  
✅ See "Assigned" badge on employees  
✅ Employees can check in/out with shift validation  

---

**Status:** 🔴 **BLOCKED - No Shifts Created**  
**Action Required:** Create shifts using Company → Shifts → Add Shift  
**Priority:** 🔥 **HIGH** - Required for shift assignment to work  

---

**Next:** Once shifts are created, shift assignment will work immediately. No code changes needed.
