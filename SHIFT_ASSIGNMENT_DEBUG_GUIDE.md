# Shift Assignment Debugging Guide

## Issue: "Error assigning shift" when selecting shift for employee

### What We've Added for Debugging:

**1. Enhanced JavaScript Logging** (`shift_assignment.html`)
- Console logs for DEBUG and error cases
- Logs request parameters: `{employeeId, shiftId, effectiveDate}`
- Logs response status and actual JSON response
- Better error capture with response text

**2. Enhanced Python Logging** (`shift_assignment.py`)
- Detailed logging at each step:
  - Request parameters logged with user_id
  - Date parsing with validation errors
  - Employee/Shift lookup results
  - Current assignment check
  - Assignment closure (if replacing previous)
  - Final success with all details

**3. New Debug Endpoints** (`admin/routes.py`)
- `/admin/debug-shift-data` - Shows:
  - Total employees in DB
  - Total active shifts in DB
  - Total assignments in DB
  - Sample employee info
  - Sample shift info
  - Current logged-in user

### How to Debug:

#### Step 1: Open Browser Developer Tools
- Press `F12` or right-click → Inspect
- Go to Console tab

#### Step 2: Try to Assign a Shift
- Select a shift from dropdown
- Set effective date
- Click on a shift assignment dropdown
- Open Console to see logs

#### Step 3: Check What Was Logged
Expected console output:
```
DEBUG: assigning shift {employeeId: 1, shiftId: 5, effectiveDate: "2026-08-05"}
DEBUG: response status 200
DEBUG: response data {success: true, message: "✅ Shift assigned successfully", ...}
```

#### Step 4: If Error, Check:
1. **Response Status** - Is it 200, 400, 404, 500?
2. **Response Data** - What error message?
3. **Network Tab** - Check actual request being sent

#### Step 5: Check Server Logs
Look for files in: `smart_hrms/logs/`
Search for pattern: `SHIFT_ASSIGN_*`

#### Step 6: Run Debug Endpoint
Visit: `http://yourserver/admin/debug-shift-data`
This will show if employees and shifts actually exist in DB

### Common Issues & Solutions:

| Issue | Likely Cause | Check |
|-------|--------------|-------|
| "Employee not found" | Employee ID doesn't exist | Run debug endpoint, verify employee exists |
| "Shift not found" | Shift ID doesn't exist | Run debug endpoint, verify shifts seeded |
| "Already assigned" | Employee has active shift for same date | Remove existing assignment first |
| 500 Error | Database transaction error | Check server logs for full traceback |
| JSON parse error | Response is not JSON (maybe HTML error page) | Check Network tab, see what response looks like |

### Files Modified:
1. `smart_hrms/app/blueprints/admin/templates/admin/shift_assignment.html` - Added console logging
2. `smart_hrms/app/blueprints/admin/shift_assignment.py` - Added detailed logging
3. `smart_hrms/app/blueprints/admin/routes.py` - Added `/debug-shift-data` endpoint

### Next Steps:
1. Run the app and try to assign a shift
2. Open dev console (F12)
3. Share the console output from your shift assignment attempt
4. This will tell us exactly what the error is
