# Coordinator Portal & Employee Self-Service System

## Overview

Smart HRMS now has a **multi-center attendance system** where:

- **Coordinators** (HR staff) log in and mark attendance for employees at their location
- **Employees** access a self-service portal (no login) to view their attendance and request leave
- **Super Admin** sees all attendance across all centers

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Smart HRMS System                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌────────────────────┐  ┌──────────────────┐  ┌─────────────┐  │
│  │  SUPER ADMIN       │  │  COORDINATOR     │  │  EMPLOYEE   │  │
│  │  (Dashboard)       │  │  (Portal)        │  │  (No Login) │  │
│  ├────────────────────┤  ├──────────────────┤  ├─────────────┤  │
│  │ ✓ All attendance   │  │ ✓ Search emp     │  │ ✓ My attend │  │
│  │ ✓ All centers      │  │ ✓ Mark check-in  │  │ ✓ Apply lvs │  │
│  │ ✓ Reports/exports  │  │ ✓ Mark check-out │  │ ✓ Calendar  │  │
│  │ ✓ System settings  │  │ ✓ Today summary  │  │ ✓ Shifts    │  │
│  └────────────────────┘  └──────────────────┘  └─────────────┘  │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 1. Coordinator Portal (HR Staff)

### Access URL
```
https://192.168.0.205:8000/coordinator/
```

### Requirements
- HR Staff role or above
- Must log in with employee code + password

### Features

#### 1.1 Employee Search
- Search by employee code (e.g., `E-2603028`)
- Search by name (e.g., `John`, `Doe`)
- Search by department (e.g., `Sales`, `IT`)
- Filter by location/center

**API Endpoint:**
```
POST /coordinator/search
{
  "query": "E-2603",
  "location_id": 1
}
```

#### 1.2 Mark Check-In
- Select employee from search results
- Click "Mark Check-In"
- System records check-in with:
  - Current timestamp (IST)
  - Office location GPS (pre-configured)
  - Late calculation if applicable
  - Automatic status = "present"

**API Endpoint:**
```
POST /coordinator/checkin
{
  "employee_id": 123,
  "location_id": 1
}
```

**Response:**
```json
{
  "success": true,
  "message": "✅ John Doe checked in at 09:15 IST"
}
```

#### 1.3 Mark Check-Out
- Select employee
- Click "Mark Check-Out"
- System records check-out with:
  - Current timestamp
  - Working hours calculation
  - Overtime calculation
  - Status computation

**API Endpoint:**
```
POST /coordinator/checkout
{
  "employee_id": 123,
  "location_id": 1
}
```

**Response:**
```json
{
  "success": true,
  "message": "✅ John Doe checked out at 18:30 IST. Worked: 9h 15m"
}
```

#### 1.4 Today's Attendance Summary
Live dashboard showing:
- Total employees at location
- Checked in count
- Checked out count
- Absent count
- On leave count
- Late arrivals count

### Database Model
Attendance is stored in `attendance` table:
```python
Attendance {
  id: int
  employee_id: int (FK)
  date: date
  check_in_time: datetime
  check_out_time: datetime
  status: str  # "present", "absent", "on_leave", etc.
  is_late: bool
  late_minutes: int
  working_minutes: int
  overtime_minutes: int
}
```

---

## 2. Employee Self-Service Portal (No Login)

### Access URL
```
https://192.168.0.205:8000/coordinator/employee
```

### Features (No Authentication Required)

#### 2.1 Quick Links Dashboard
Employees can access (after login to their own account):

1. **My Attendance** → View daily check-in/check-out history
2. **Apply Leave** → Request vacation, sick leave, half-day
3. **Half Day** → Request half-day leave
4. **Calendar** → View leave calendar & holidays

#### 2.2 Employee Workflows

**When Checking In/Out:**
1. Coordinator calls employee name
2. Employee sits on center PC (kiosk mode)
3. Coordinator searches employee by code
4. Coordinator clicks "Mark Check-In" button
5. Employee's attendance is recorded automatically
6. No phone/personal login needed

**When Requesting Leave:**
1. Employee (from anywhere) logs in with their employee code
2. Clicks "Apply Leave"
3. Selects leave type & dates
4. Manager reviews & approves/rejects
5. Approved leaves show in calendar

**When Checking Leave Status:**
1. Employee logs in
2. Views calendar with all approved leaves
3. Sees notifications for approvals/rejections

---

## 3. Super Admin Dashboard

### Access URL
```
https://192.168.0.205:8000/admin/
```

### Features

#### 3.1 All-Center Attendance View
- Real-time attendance across all locations
- Filter by center, date, department
- Late arrivals tracking
- Absent employees report

#### 3.2 Reports
- Daily attendance report
- Weekly attendance trends
- Monthly absence patterns
- Leave utilization
- Overtime report

#### 3.3 System Settings
- Configure office locations & GPS radius
- Manage leave types & balances
- User role & permission management
- Audit logs & security

---

## 4. Technical Implementation

### File Structure
```
smart_hrms/
├── app/
│   └── blueprints/
│       └── coordinator/
│           ├── __init__.py           # Blueprint definition
│           ├── routes.py             # URL routes
│           ├── service.py            # Business logic
│           └── templates/
│               └── coordinator/
│                   ├── dashboard.html        # Coordinator panel
│                   ├── employee_portal.html  # Employee info portal
│                   └── reports.html
```

### Routes

| Method | URL | Access | Purpose |
|--------|-----|--------|---------|
| GET | `/coordinator/` | HR Staff+ | Dashboard & search |
| POST | `/coordinator/search` | HR Staff+ | AJAX search employees |
| POST | `/coordinator/checkin` | HR Staff+ | AJAX mark check-in |
| POST | `/coordinator/checkout` | HR Staff+ | AJAX mark check-out |
| GET | `/coordinator/summary` | HR Staff+ | AJAX get today's summary |
| GET | `/coordinator/reports` | HR Staff+ | Attendance reports |
| GET | `/coordinator/employee` | Public | Employee self-service |

### Coordinator Service

**CoordinatorService** class provides:

```python
class CoordinatorService:
    def search_employees(query, location_id, limit=20)
        → List[{id, code, name, department, branch, status}]
    
    def get_today_attendance_summary(location_id)
        → {date, total, checked_in, checked_out, absent, on_leave, records}
    
    def mark_checkin_for_employee(employee_id, location_id)
        → (success: bool, message: str)
    
    def mark_checkout_for_employee(employee_id, location_id)
        → (success: bool, message: str)
    
    def get_coordinator_locations()
        → List[{id, name, address, latitude, longitude, radius}]
```

### GPS & Location

**How it works:**
- Each office location has pre-configured GPS coordinates
- When coordinator marks attendance, system uses office coordinates (not employee GPS)
- This bypasses GPS validation since it's kiosk-based
- Radius check passes because office is at its own center

---

## 5. User Flows

### Coordinator Flow
```
1. HR Staff logs in with employee code + password
   ↓
2. Sees coordinator dashboard
   ↓
3. Selects location (center)
   ↓
4. Searches employee by code/name
   ↓
5. Employee appears in list
   ↓
6. Clicks "Mark Check-In" or "Mark Check-Out"
   ↓
7. Attendance recorded in database
   ↓
8. Summary updates in real-time
```

### Employee Flow
```
Option A: Coordinator marks attendance
1. Coordinator calls employee name
2. Employee sits on center PC
3. Coordinator searches employee
4. Coordinator marks check-in/out
5. Employee can later log in and view their attendance

Option B: Employee self-service (leaving, applying leave, etc.)
1. Employee logs in from any device
2. Views their attendance history
3. Applies for leave/shift change
4. Gets notified when approved
5. Sees all events in calendar
```

### Super Admin Flow
```
1. Logs in with admin credentials
2. Sees dashboard with all centers
3. Views real-time attendance across organization
4. Generates reports
5. Configures system settings
```

---

## 6. Setup Instructions

### Step 1: Initialize Coordinator Blueprint
The blueprint is automatically registered in `/app/blueprints/__init__.py`

### Step 2: Configure Office Locations
In Admin Panel → Settings:
1. Add each work center (office location)
2. Set center name, address, GPS coordinates
3. Set attendance radius (e.g., 50 meters)
4. Assign employees to centers

### Step 3: Assign Coordinator Role
1. Create HR Staff users
2. Assign role = `hr_staff` or `hr_manager`
3. Users can now access `/coordinator/`

### Step 4: Deploy to Production
```bash
# Start Flask with new blueprint loaded
python run.py

# Or with Nginx reverse proxy
sudo systemctl restart nginx
```

---

## 7. API Reference

### Search Employees
```bash
curl -X POST https://192.168.0.205:8000/coordinator/search \
  -H "Content-Type: application/json" \
  -H "Cookie: session=..." \
  -d '{
    "query": "E-2603",
    "location_id": 1
  }'

# Response
{
  "success": true,
  "results": [
    {
      "id": 123,
      "code": "E-2603028",
      "name": "John Doe",
      "department": "Sales",
      "branch": "Delhi",
      "status": "active"
    }
  ]
}
```

### Mark Check-In
```bash
curl -X POST https://192.168.0.205:8000/coordinator/checkin \
  -H "Content-Type: application/json" \
  -H "Cookie: session=..." \
  -d '{
    "employee_id": 123,
    "location_id": 1
  }'

# Response
{
  "success": true,
  "message": "✅ John Doe checked in at 09:15 IST"
}
```

### Mark Check-Out
```bash
curl -X POST https://192.168.0.205:8000/coordinator/checkout \
  -H "Content-Type: application/json" \
  -H "Cookie: session=..." \
  -d '{
    "employee_id": 123,
    "location_id": 1
  }'

# Response
{
  "success": true,
  "message": "✅ John Doe checked out at 18:30 IST. Worked: 9h 15m"
}
```

### Get Today's Summary
```bash
curl https://192.168.0.205:8000/coordinator/summary?location_id=1 \
  -H "Cookie: session=..."

# Response
{
  "success": true,
  "summary": {
    "date": "2026-08-14",
    "total_employees": 50,
    "checked_in": 45,
    "checked_out": 40,
    "absent": 3,
    "on_leave": 2,
    "late": 4,
    "attendance_records": [...]
  }
}
```

---

## 8. Database Queries

### View Today's Attendance
```sql
SELECT 
  a.id,
  e.employee_code,
  CONCAT(u.first_name, ' ', u.last_name) as name,
  e.department,
  a.check_in_time,
  a.check_out_time,
  a.status,
  a.is_late,
  a.working_minutes
FROM attendance a
JOIN employees e ON a.employee_id = e.id
JOIN users u ON e.user_id = u.id
WHERE a.date = CURDATE()
ORDER BY a.check_in_time DESC;
```

### Late Employees Report
```sql
SELECT 
  e.employee_code,
  CONCAT(u.first_name, ' ', u.last_name) as name,
  e.department,
  a.check_in_time,
  a.late_minutes
FROM attendance a
JOIN employees e ON a.employee_id = e.id
JOIN users u ON e.user_id = u.id
WHERE a.date = CURDATE()
  AND a.is_late = 1
ORDER BY a.late_minutes DESC;
```

---

## 9. Security & Access Control

### Access Levels
- **Public** (no login): `/coordinator/employee`
- **HR Staff+** (must log in): `/coordinator/`
- **Admin+** (must log in): `/admin/`

### Decorators
```python
@coordinator_required  # Checks if user has HR staff role or above
@login_required        # Checks if user is authenticated
```

### CSRF Protection
- All POST routes are CSRF-protected
- AJAX requests include CSRF token
- Safe from cross-site attacks

---

## 10. Testing Checklist

- [ ] Coordinator login works
- [ ] Employee search finds employees
- [ ] Check-in marks attendance with current time
- [ ] Check-out calculates working hours
- [ ] Late calculation works correctly
- [ ] Today's summary updates live
- [ ] Employee portal loads without login
- [ ] Attendance history shows correct records
- [ ] Leave application submits successfully
- [ ] Calendar shows approved leaves
- [ ] Super admin sees all centers
- [ ] Reports generate correctly
- [ ] No GPS validation errors on kiosk

---

## 11. FAQ

### Q: How do employees check in if they can't log in?
**A:** Coordinator marks them in on the center PC using employee code search. No login needed for check-in.

### Q: What if coordinator marks wrong employee?
**A:** Edit from Admin panel → Attendance → Regularization. Mark correct employee and document reason.

### Q: Can employees check in from home?
**A:** No, check-in must be done on center PC by coordinator. Only coordinator portal supports check-in.

### Q: How many employees can coordinator handle?
**A:** No limit. Search is real-time. UI handles thousands of employees efficiently.

### Q: What about multiple shifts?
**A:** Each employee has assigned shift time. Late calculation uses their shift start time.

### Q: Can coordinator work from home?
**A:** Yes, if coordinator PC has HTTPS access to 192.168.0.205:8000. Can be accessed from any device on network.

---

## 12. Troubleshooting

### Coordinator Can't Login
- Check if user has `hr_staff` role or above
- Verify employee code and password
- Check account status = "active"

### Check-In Shows "Office Not Configured"
- Go to Admin → Settings → Office Locations
- Ensure office location exists for employee
- Verify GPS coordinates are set
- Add employee to correct office

### Search Returns No Results
- Check employee code spelling
- Try searching by name instead
- Verify employee is not deleted
- Check employee is assigned to location

### Time Shows Incorrectly
- Ensure server timezone = Asia/Kolkata (IST)
- Check database stored in UTC, frontend converts to IST
- Verify browser locale settings

---

## 13. Future Enhancements

- [ ] Biometric integration for multi-factor auth
- [ ] Mobile app for coordinators
- [ ] SMS notifications for employees
- [ ] QR code check-in system
- [ ] Facial recognition for kiosk
- [ ] Advanced analytics & dashboards
- [ ] Bulk import from third-party systems
- [ ] WhatsApp notifications

---

**Version:** 1.0  
**Last Updated:** August 14, 2026  
**Status:** Production Ready
