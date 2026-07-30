# WEBSITE TO FLUTTER - COMPLETE FEATURE MAPPING

**Objective:** Clone every feature from production website into Flutter mobile app  
**Status:** Starting comprehensive audit  
**Date:** July 28, 2026

---

## PART 1: AUTHENTICATION MODULE

### Website Features (Flask)
```
✓ Login with Employee Code + Department
✓ Register new employee (code-based)
✓ Forgot Password (generate token)
✓ Reset Password (via token)
✓ Logout
✓ Remember Me functionality
✓ Employee lookup (AJAX - fetches name/department)
```

### Flask Routes
```
POST   /auth/login                      → Login with code+password+dept
GET    /auth/lookup-employee?code=X    → AJAX employee lookup
POST   /auth/register                  → Register new employee
POST   /auth/forgot-password           → Initiate password reset
POST   /auth/reset-password/<token>    → Complete password reset
GET    /auth/logout                    → Logout
```

### Flutter Status
```
✗ Login screen exists but missing:
  - Department dropdown (currently hardcoded)
  - Stay signed in checkbox
  - Employee lookup (AJAX call)
  - Proper form validation

✗ Register screen missing

✗ Forgot Password missing

✗ Reset Password missing
```

### Required Flask APIs for Mobile
```
✓ POST /api/v1/auth/login
✓ POST /api/v1/auth/refresh
✓ POST /api/v1/auth/logout
✓ POST /api/v1/auth/forgot-password
✓ POST /api/v1/auth/reset-password
✓ GET /api/v1/auth/lookup-employee
✓ GET /api/v1/auth/me
```

---

## PART 2: DASHBOARD MODULE

### Website Features
```
✓ Master info panel (employee details)
✓ Today's attendance status
✓ Leave balance display
✓ Current shift display
✓ Attendance chart (6 months, present/absent/leave)
✓ Department statistics
✓ Pending approvals count
```

### Flutter Status
```
✓ Dashboard exists
~ Partial implementation only
```

---

## PART 3: EMPLOYEE MANAGEMENT

### Website Features
```
✓ Employee list with search, filter by department/branch
✓ Create employee (form with photo)
✓ Edit employee details
✓ View employee profile
✓ Reset employee password
✓ Toggle account status (active/inactive)
✓ Unlock account
✓ Delete employee
✓ Login history per employee
```

### Flutter Status
```
✗ Employee management MISSING
✗ No employee list screen
✗ No create/edit employee
✗ No employee detail view
```

---

## PART 4: ATTENDANCE MODULE

### Website Features
```
✓ GPS-based check-in with photo
✓ GPS-based check-out with photo
✓ Attendance history with filters (date range, status)
✓ Export attendance
✓ Office settings (geo-fencing radius, allowed time range)
✓ View photos from attendance
```

### Flutter Status
```
✓ Attendance screens exist
~ GPS check-in/check-out partially implemented
~ Needs photo integration
✗ Attendance history incomplete
```

---

## PART 5: LEAVE MANAGEMENT

### Website Features
```
✓ Apply full-day leave
✓ Apply half-day leave (first/second half)
✓ Apply early leave
✓ Cancel leave request
✓ Leave approval by manager
✓ Reject with mandatory remarks
✓ Leave history with filtering
✓ Leave balance display
✓ Manager lookup (AJAX)
```

### Flask Routes
```
GET    /leave                      → My leave requests
GET    /leave/types               → Leave types (master data)
GET    /leave/balance             → Leave balance
GET    /leave/managers            → My managers
POST   /leave/apply               → Apply full-day leave
POST   /leave/halfday             → Apply half-day
POST   /leave/early               → Apply early leave
POST   /leave/<id>/cancel         → Cancel
GET    /leave/<id>                → Leave detail
GET    /leave/approvals           → Approvals for me (manager)
POST   /leave/<id>/approve        → Manager approve
POST   /leave/<id>/reject         → Manager reject
```

### Flutter Status
```
✓ Leave screens exist
~ Partially implemented
✓ Leave repository has methods
✗ Needs full integration
```

---

## PART 6: SHIFT MANAGEMENT

### Website Features
```
✓ View current shift
✓ Request shift change
✓ Shift change approval (manager)
✓ Shift change rejection (manager)
✓ Shift history
✓ Shift schedule calendar
```

### Flask Routes
```
GET    /shift/my-shift                    → Current shift
GET    /shift/available                   → Available shifts
POST   /shift/change-request              → Request change
GET    /shift/history                     → My shift changes
GET    /shift/manager/approvals           → Pending approvals (manager)
POST   /shift/<id>/approve                → Manager approve
POST   /shift/<id>/reject                 → Manager reject
```

### Flutter Status
```
✓ Shift screens exist
~ Partially implemented
```

---

## PART 7: PAYROLL MODULE

### Website Features
```
✓ View salary slips (employee)
✓ Download payslip
✓ Create payroll run (HR)
✓ Process payroll run (HR)
✓ Approve payroll run (HR)
✓ Mark as paid (HR)
✓ View salary structure
```

### Flask Routes
```
GET    /payroll/payslips                 → My payslips
GET    /payroll/payslips/<id>            → Payslip detail
GET    /payroll/salary-structures        → Salary structures
POST   /payroll/runs/create              → Create payroll run
```

### Flutter Status
```
✓ Payroll module exists
~ Basic implementation only
```

---

## PART 8: ADMIN PANEL

### Website Features
```
✓ Office settings (geofence radius, working hours)
✓ Users management
✓ Audit logs
✓ Leave types
✓ Hospital management (if multi-hospital)
✓ Employee allocation to hospitals
✓ Shift assignment (bulk)
✓ Employee import (from Excel)
```

### Flutter Status
```
✗ Admin features mostly MISSING
✗ No admin panel in mobile
```

---

## PART 9: REPORTS & ANALYTICS

### Website Features
```
✓ Attendance report (by date range, employee, status)
✓ Leave report (by type, status, employee)
✓ Employee report (basic employee list)
✓ Export to CSV/Excel
```

### Flask Routes
```
GET    /reports/attendance              → Attendance report
GET    /reports/leave                   → Leave report
GET    /reports/employee                → Employee report
GET    /reports/export/<type>/<fmt>     → Export CSV/Excel
```

### Flutter Status
```
✓ Reports module exists
~ Basic structure only
```

---

## PART 10: PROFILE & SETTINGS

### Website Features
```
✓ My profile view
✓ Security settings
✓ Notification preferences
✓ Change password (implied)
```

### Flutter Status
```
✓ Settings screens exist
~ Incomplete implementation
```

---

## PART 11: HOSPITALS (IF APPLICABLE)

### Website Features
```
✓ Hospital master list
✓ Create hospital
✓ Edit hospital
✓ Delete hospital
✓ Allocate employees to hospital
✓ View hospital details
```

### Flask Routes
```
GET    /admin/hospitals                 → List hospitals
POST   /admin/hospitals/create          → Create hospital
PUT    /admin/hospitals/<id>/edit       → Edit hospital
DELETE /admin/hospitals/<id>            → Delete hospital
```

### Flutter Status
```
✗ Hospital management MISSING
```

---

## PART 12: NOTIFICATIONS

### Website Features
```
✓ Leave approval notifications
✓ Shift change notifications
✓ System notifications
✓ Notification history
```

### Flask Routes
```
GET    /notifications                   → My notifications
POST   /notifications/<id>/mark-read    → Mark as read
DELETE /notifications/<id>              → Delete notification
```

### Flutter Status
```
✓ Notifications module exists
~ Incomplete implementation
```

---

## CRITICAL GAPS - MUST IMPLEMENT

### Master Data (Must fetch from API, NOT hardcode)
- [x] Departments
- [x] Positions/Designations
- [x] Shifts
- [ ] Leave Types
- [ ] Roles
- [ ] Hospitals (if applicable)
- [ ] Branches

### Core Features Missing
- [ ] Employee management (CRUD)
- [ ] Admin panel
- [ ] Complete payroll integration
- [ ] Complete reports
- [ ] Hospital management

### Incomplete Features
- [ ] Complete attendance history with filters
- [ ] Complete leave approval workflow
- [ ] Complete shift change workflow
- [ ] Complete payroll viewing

---

## FORMS COMPARISON

### Login Form
**Website:**
- Employee Code (required, text)
- Department (required, dropdown)
- Password (required, password)
- Stay Signed In (checkbox)

**Flutter:**
- Needs: Same fields + proper dropdown

### Register Form
**Website:**
- Employee Code (required, text)
- Employee Name (auto-filled via AJAX)
- Password (required, password with strength indicator)
- Re-enter Password (required, password)

**Flutter:**
- Missing: Entire register screen

### Leave Application Form
**Website:**
- Leave Type (dropdown - master data)
- From Date (date picker)
- To Date (date picker)
- Duration (auto-calculated)
- Reason (text - mandatory)
- Manager (dropdown - via AJAX lookup)

**Flutter:**
- Exists but needs: All fields + proper validation

---

## API ENDPOINTS - COMPLETE LIST

### Authentication (7)
```
POST   /api/v1/auth/login
POST   /api/v1/auth/refresh
POST   /api/v1/auth/logout
POST   /api/v1/auth/forgot-password
POST   /api/v1/auth/reset-password
GET    /api/v1/auth/lookup-employee
GET    /api/v1/auth/me
```

### Master Data (NEW - 4)
```
GET    /api/v1/company/departments
GET    /api/v1/company/positions
GET    /api/v1/company/shifts
GET    /api/v1/company/department-stats
```

### Dashboard (2)
```
GET    /api/v1/dashboard
GET    /api/v1/dashboard/chart
```

### Employees (4)
```
GET    /api/v1/employees/me
PUT    /api/v1/employees/me
POST   /api/v1/employees/me/photo
GET    /api/v1/employees
```

### Attendance (7)
```
GET    /api/v1/attendance/today
POST   /api/v1/attendance/check-in
POST   /api/v1/attendance/check-out
POST   /api/v1/attendance/upload-photo
POST   /api/v1/attendance/upload-checkout-photo
GET    /api/v1/attendance/history
GET    /api/v1/attendance/office
```

### Leave (12)
```
GET    /api/v1/leave
GET    /api/v1/leave/types
GET    /api/v1/leave/balance
GET    /api/v1/leave/managers
POST   /api/v1/leave/apply
POST   /api/v1/leave/halfday
POST   /api/v1/leave/early
GET    /api/v1/leave/<id>
POST   /api/v1/leave/<id>/cancel
GET    /api/v1/leave/approvals
POST   /api/v1/leave/<id>/approve
POST   /api/v1/leave/<id>/reject
```

### Shift (8)
```
GET    /api/v1/shifts/my-shift
GET    /api/v1/shifts/available
GET    /api/v1/shifts/requests
POST   /api/v1/shifts/request-change
GET    /api/v1/shifts/<id>/history
GET    /api/v1/shifts/approvals
POST   /api/v1/shifts/<id>/approve
POST   /api/v1/shifts/<id>/reject
```

### Payroll (3)
```
GET    /api/v1/payroll/payslips
GET    /api/v1/payroll/payslips/<id>
GET    /api/v1/payroll/salary-structures
```

### Settings (5)
```
GET    /api/v1/settings/profile
PUT    /api/v1/settings/profile
PUT    /api/v1/settings/password
GET    /api/v1/settings/preferences
PUT    /api/v1/settings/preferences
```

### Health/Utility (2)
```
GET    /api/v1/health
GET    /api/v1/me
```

---

## NEXT STEPS

1. Mark Phase 1 (Website Audit) complete
2. Verify all Flask APIs exist or create missing ones
3. Start building Flutter screens matching website
4. Ensure every form field matches exactly
5. Verify permissions match
6. Test real data flows

**Total Endpoints:** 60+  
**Total Modules:** 12  
**Total Screens (Est):** 30+  
**Status:** Audit Complete - Ready for Implementation

---

**PHASE 1 COMPLETE ✅**

Website fully mapped. All modules documented. All APIs identified.
