# Compensatory Off (Comp Off) System - Implementation Guide

## Overview
Comp Off is a special leave type where employees earn compensatory time off by working on holidays. The system enforces strict rules: 1 day comp off per holiday worked, valid for 90 days only, and usable only once.

## System Components

### 1. **Database Model** (app/models/leave.py)
`LeaveRequest` model has comp off-specific fields:
- `comp_off_work_date` (DATE) - Date employee worked on holiday
- `comp_off_expiry_date` (DATE) - 90 days from approval (today + 90 days)
- `comp_off_used_on` (DATETIME) - When employee actually used the comp off
- `comp_off_notified` (BOOLEAN) - Whether HR was notified

### 2. **Comp Off Service** (app/blueprints/leave/comp_off_service.py)
New dedicated service with these methods:

#### `earn_comp_off(employee_id, work_date, holiday_name)`
- Records that employee worked on holiday
- Auto-creates approved leave request (comp off earned)
- Sets expiry to work_date + 90 days
- Returns: (success, message)

**Example:**
```python
comp_svc = CompOffService()
ok, msg = comp_svc.earn_comp_off(
    employee_id=5,
    work_date=date(2026, 8, 15),  # Worked on Independence Day
    holiday_name="Independence Day"
)
# Returns: (True, "Comp off earned for 15 Aug 2026. Valid until 13 Nov 2026.")
```

#### `get_available_comp_offs(employee_id)`
- Returns list of earned, non-expired, unused comp offs
- Filters: status="approved", comp_off_work_date != NULL, comp_off_expiry_date >= today, comp_off_used_on = NULL
- Sorted by expiry date (earliest first)

#### `mark_comp_off_used(leave_request_id, employee_id)`
- Marks comp off as used when employee applies for it
- Automatically notifies all HR/Admin users
- Returns: (success, message)

#### `check_expired_comp_offs(employee_id)`
- Returns dict with:
  - `expired_count` - Total expired unused comp offs
  - `expiring_soon` - List of comp offs expiring in next 7 days
  - `expired` - List of already expired comp offs

### 3. **Leave Service Integration** (app/blueprints/leave/service.py)

#### `get_balance(employee_id)` - Updated
Returns balance for 4 leave types including Comp Off:
- **CL (Casual Leave)**: Unlimited
- **SL (Sick Leave)**: Unlimited
- **PL (Paid Leave)**: 12 days/year
- **CO (Comp Off)**: 
  - Shows 1 available if earned & not expired & not used
  - Shows 0 available if not earned, expired, or already used
  - Includes expiry date in response

#### `apply_leave()` - Updated
- When CO (Comp Off) is applied:
  - Sets `comp_off_used_on = datetime.utcnow()` immediately
  - Triggers HR notification via `_notify_hr_compoff_used()`

#### `approve_leave()` - Updated
- When CO is approved:
  - Sets `comp_off_expiry_date = today + timedelta(days=90)`
  - Logs approval with expiry date

#### `_notify_hr_compoff_used()` - New
- Called when employee applies for comp off
- Finds all users with roles: `admin`, `hr_manager`, `hr_staff`
- Creates notification for each with message: "{emp_name} ({emp_code}) has used their compensatory off."
- Logs the notification event

### 4. **Routes** (app/blueprints/leave/routes.py)

#### Employee Routes

**GET `/leave/comp-off/status`** (AJAX)
```json
Response:
{
  "available_count": 1,
  "available_comp_offs": [
    {
      "id": 42,
      "work_date": "2026-08-15",
      "expiry_date": "2026-11-13",
      "days_left": 95
    }
  ],
  "expiry_info": {
    "expired_count": 0,
    "expiring_soon": [],
    "expired": []
  }
}
```

#### Admin Routes

**POST `/leave/admin/comp-off/earn`**
```json
Request Body:
{
  "employee_id": 5,
  "work_date": "2026-08-15",
  "holiday_name": "Independence Day"
}

Response:
{
  "success": true,
  "message": "Comp off earned for 15 Aug 2026. Valid until 13 Nov 2026."
}
```

**GET `/leave/admin/comp-off/list`**
```
Query Parameters:
- status: earned | used | expired (default: earned)
- employee_id: (optional) filter by employee
- page: pagination page (default: 1)

Response:
{
  "total": 42,
  "page": 1,
  "pages": 3,
  "comp_offs": [
    {
      "id": 42,
      "employee_id": 5,
      "employee_code": "E-2601020",
      "employee_name": "John Doe",
      "work_date": "2026-08-15",
      "expiry_date": "2026-11-13",
      "used_on": null,
      "status": "available"
    }
  ]
}
```

## Workflow

### Employee Earns Comp Off
1. **Holiday occurs** (e.g., Independence Day - Aug 15, 2026)
2. **Employee works** on that holiday
3. **HR/Admin marks** in system via `/leave/admin/comp-off/earn`
4. **System creates** approved LeaveRequest with:
   - `status = "approved"`
   - `comp_off_work_date = 2026-08-15`
   - `comp_off_expiry_date = 2026-11-13` (90 days)
   - `comp_off_used_on = NULL`
5. **Employee sees** 1 available Comp Off in leave balance

### Employee Uses Comp Off
1. **Employee goes** to Leave Portal
2. **Selects** "Compensatory Off" card
3. **Applies** for comp off (e.g., for Aug 22, 2026)
4. **System records**:
   - `comp_off_used_on = 2026-08-22 14:30:45` (timestamp)
5. **HR/Admin notification** fires immediately:
   - All users with role `admin`, `hr_manager`, `hr_staff` get notification
   - Title: "⏰ Compensatory Off Used"
   - Message: "John Doe (E-2601020) has used their compensatory off."
6. **Comp Off marked as used** (can't be used again)

### 90-Day Expiry
- Comp off earned on 2026-08-15 expires on 2026-11-13
- After 2026-11-13, it's no longer available
- Employee sees it as "expired" in comp off status
- Can be viewed in admin comp off list with status="expired"

## Validation Rules

### Earning Comp Off
- ✅ Employee must exist
- ✅ Comp Off leave type (CO) must exist and be active
- ✅ Can earn multiple comp offs (one per holiday worked)
- ✅ Automatically approved when earned

### Using Comp Off
- ✅ Must have available (unused, non-expired) comp off
- ✅ Can only use within 90-day window from work date
- ✅ Can only use ONCE per comp off earned
- ✅ HR notified immediately when used

### Balance Calculation
- If earned & not expired & not used: **Available = 1**
- If multiple comp offs earned: **Shows first available one** (earliest expiry)
- If all used/expired: **Available = 0**

## Database Queries

### Find Available Comp Offs for Employee
```python
from datetime import date
from sqlalchemy import and_

available = LeaveRequest.query.filter(
    and_(
        LeaveRequest.employee_id == 5,
        LeaveRequest.status == "approved",
        LeaveRequest.comp_off_work_date != None,
        LeaveRequest.comp_off_expiry_date >= date.today(),
        LeaveRequest.comp_off_used_on == None,
        LeaveRequest.is_deleted == False,
    )
).order_by(LeaveRequest.comp_off_expiry_date.asc()).all()
```

### Find All Used Comp Offs
```python
used = LeaveRequest.query.filter(
    and_(
        LeaveRequest.employee_id == 5,
        LeaveRequest.comp_off_used_on != None,
        LeaveRequest.is_deleted == False,
    )
).all()
```

### Find Expired Comp Offs (Never Used)
```python
from datetime import date

expired = LeaveRequest.query.filter(
    and_(
        LeaveRequest.employee_id == 5,
        LeaveRequest.comp_off_expiry_date < date.today(),
        LeaveRequest.comp_off_used_on == None,
        LeaveRequest.is_deleted == False,
    )
).all()
```

## Logging

All comp off events are logged with these formats:

```
COMP_OFF_EARNED | emp=5 | work_date=2026-08-15 | expiry=2026-11-13 | holiday=Independence Day
COMP_OFF_APPROVED | lr_id=42 | expiry_date=2026-11-13
COMP_OFF_USED | emp=5 | lr_id=42 | used_on=2026-08-22 14:30:45 | notified_hr=4
HR_NOTIFIED_COMPOFF_USED | emp=5 | emp_code=E-2601020 | lr_id=42 | hr_users=4
```

## Testing Checklist

- [ ] Create comp off via `earn_comp_off()` - check expiry is 90 days
- [ ] Get available comp offs - verify filtering logic
- [ ] Apply for comp off - verify `comp_off_used_on` is set
- [ ] Check HR notification - verify all admin/hr_manager/hr_staff users notified
- [ ] Verify can't use twice - second use attempt fails
- [ ] Test expiry - try using after 90 days (should fail)
- [ ] Check balance display - shows "1/1" with expiry date
- [ ] List admin comp offs - filter by earned/used/expired
- [ ] View in logs - all events properly logged

## API Examples

### Python (Backend)
```python
from app.blueprints.leave.comp_off_service import CompOffService
from datetime import date

comp_svc = CompOffService()

# Earn comp off
success, msg = comp_svc.earn_comp_off(
    employee_id=5,
    work_date=date(2026, 8, 15),
    holiday_name="Independence Day"
)

# Get available
available = comp_svc.get_available_comp_offs(5)
print(f"Employee has {len(available)} available comp offs")

# Check expiry
expiry_info = comp_svc.check_expired_comp_offs(5)
print(f"Expiring soon: {len(expiry_info['expiring_soon'])}")
```

### JavaScript (Frontend)
```javascript
// Get comp off status
fetch('/leave/comp-off/status')
  .then(r => r.json())
  .then(data => {
    console.log(`Available: ${data.available_count}`);
    data.available_comp_offs.forEach(co => {
      console.log(`Expires in ${co.days_left} days`);
    });
  });

// Admin: Earn comp off
fetch('/leave/admin/comp-off/earn', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    employee_id: 5,
    work_date: '2026-08-15',
    holiday_name: 'Independence Day'
  })
})
.then(r => r.json())
.then(data => console.log(data.message));

// Admin: List comp offs
fetch('/leave/admin/comp-off/list?status=earned&employee_id=5')
  .then(r => r.json())
  .then(data => {
    console.log(`Total: ${data.total}`);
    data.comp_offs.forEach(co => {
      console.log(`${co.employee_name}: expires ${co.expiry_date}`);
    });
  });
```

## Files Modified/Created

**Created:**
- `app/blueprints/leave/comp_off_service.py` - Dedicated comp off service

**Modified:**
- `app/blueprints/leave/service.py` - Updated `get_balance()`, `apply_leave()`, `approve_leave()`, added `_notify_hr_compoff_used()`
- `app/blueprints/leave/routes.py` - Added 3 new routes, updated imports
- `app/models/leave.py` - Already has comp off fields

## Summary

✅ **Comp Off is earned** when employee works on holiday  
✅ **Valid for 90 days** from approval date  
✅ **Can use only once** per comp off earned  
✅ **HR notified immediately** when used  
✅ **Proper balance tracking** in leave portal  
✅ **Admin can manage** holiday rosters and comp offs  
