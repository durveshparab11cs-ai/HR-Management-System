# Phase 1: Smart HRMS Module Audit & REST API Blueprint

## 📋 Project Structure Overview

```
app/
├── blueprints/          # Flask blueprints (modules)
│   ├── admin/          ✅ Admin panel, shift assignment
│   ├── api/            ✅ REST API v1 (skeleton exists)
│   ├── attendance/     ✅ Check-in, check-out, GPS, photos
│   ├── authentication/ ✅ Login, register, password reset
│   ├── company/        ✅ Company settings, shifts, holidays
│   ├── dashboard/      ✅ Main dashboard, stats
│   ├── employees/      ✅ Employee management
│   ├── foss/           ✅ Field operations, GPS tracking
│   ├── leave/          ✅ Leave requests, approvals
│   ├── notifications/  ✅ FCM notifications (completed)
│   ├── payroll/        ✅ Payroll processing
│   ├── reports/        ✅ Reports generation
│   ├── settings/       ✅ User settings, profile
│   └── shift_change/   ✅ Shift change requests
├── models/             # Database models
├── constants/          # Enums, limits, configs
├── core/               # Core business logic
├── extensions/         # Flask extensions
├── middleware/         # Custom middleware
├── utils/              # Helper utilities
└── static/             # Frontend assets
```

---

## 🎯 Modules Identified (14 Modules)

### 1. **Authentication Module** ✅
**Current State:** HTML login/register forms  
**Blueprint:** `app/blueprints/authentication/`  
**Models:** `User`, `LoginHistory`

**Existing Routes:**
- `/auth/login` (GET/POST) - Form-based login
- `/auth/register` (GET/POST) - Employee registration
- `/auth/logout` (GET)
- `/auth/forgot-password` (GET/POST)
- `/auth/reset-password/<token>` (GET/POST)
- `/auth/lookup-employee` (AJAX)

**APIs Needed for Mobile:**
```
POST /api/v1/auth/login              # Login with employee_code + password
POST /api/v1/auth/refresh            # Refresh access token
POST /api/v1/auth/logout             # Logout
POST /api/v1/auth/forgot-password    # Request password reset
POST /api/v1/auth/reset-password     # Reset password with token
GET  /api/v1/auth/me                 # Get current user info
```

**Service Layer:** ✅ `AuthService` exists
**Repository:** ✅ Exists

---

### 2. **Dashboard Module** ✅
**Current State:** HTML dashboard with stats  
**Blueprint:** `app/blueprints/dashboard/`  
**Models:** Aggregates from other models

**Existing Routes:**
- `/dashboard` (GET) - Main dashboard page

**APIs Needed for Mobile:**
```
GET /api/v1/dashboard                # Summary stats
GET /api/v1/dashboard/attendance     # Today's attendance status
GET /api/v1/dashboard/leave-balance  # Leave balance summary
GET /api/v1/dashboard/quick-actions  # Available actions
GET /api/v1/dashboard/recent-activity # Recent updates
```

**Service Layer:** Needs creation
**Repository:** N/A (aggregates)

---

### 3. **Employee Module** ✅
**Current State:** Employee CRUD with HTML forms  
**Blueprint:** `app/blueprints/employees/`  
**Models:** `Employee`, `EmployeeMaster`

**Existing Routes:**
- `/employees` (GET) - List employees
- `/employees/create` (GET/POST)
- `/employees/<id>` (GET)
- `/employees/<id>/edit` (GET/POST)
- `/employees/<id>/delete` (POST)

**APIs Needed for Mobile:**
```
GET  /api/v1/employees/me            # My profile
PUT  /api/v1/employees/me            # Update my profile
GET  /api/v1/employees/me/documents  # My documents
POST /api/v1/employees/me/photo      # Upload profile photo
GET  /api/v1/employees               # List employees (admin)
GET  /api/v1/employees/:id           # Get employee details (admin)
```

**Service Layer:** ✅ `EmployeeService` exists
**Repository:** ✅ Exists

---

### 4. **Attendance Module** ✅
**Current State:** GPS-based check-in/out with photos  
**Blueprint:** `app/blueprints/attendance/`  
**Models:** `Attendance`, `AttendanceLog`, `AttendancePhoto`, `GPSLog`, `OfficeSettings`

**Existing Routes:**
- `/attendance` (GET) - Attendance page
- `/attendance/checkin` (POST) - AJAX check-in
- `/attendance/checkout` (POST) - AJAX check-out
- `/attendance/upload-photo` (POST) - AJAX photo upload
- `/attendance/upload-checkout-photo` (POST)
- `/attendance/history` (GET) - Attendance history
- `/attendance/export` (POST) - Export history

**APIs Needed for Mobile:**
```
GET  /api/v1/attendance/today        # Today's attendance status
POST /api/v1/attendance/check-in     # Check in with GPS + photo
POST /api/v1/attendance/check-out    # Check out with GPS + photo
POST /api/v1/attendance/upload-photo # Upload proof photo
GET  /api/v1/attendance/history      # Attendance history (paginated)
GET  /api/v1/attendance/settings     # Office settings (GPS radius, etc.)
POST /api/v1/attendance/regularize   # Request regularization
```

**Service Layer:** ✅ `AttendanceService` exists
**Repository:** ✅ Exists

---

### 5. **Leave Module** ✅
**Current State:** Leave requests with approval workflow  
**Blueprint:** `app/blueprints/leave/`  
**Models:** `LeaveRequest`, `LeaveType`, `HalfDayRequest`, `EarlyLeaveRequest`

**Existing Routes:**
- `/leave` (GET) - My leaves
- `/leave/apply` (GET/POST) - Apply for leave
- `/leave/<id>/cancel` (POST) - Cancel leave
- `/leave/pending` (GET) - Pending requests (manager)
- `/leave/<id>/approve` (POST) - Approve (manager)
- `/leave/<id>/reject` (POST) - Reject (manager)
- `/leave/halfday/apply` (GET/POST)
- `/leave/earlyleave/apply` (GET/POST)

**APIs Needed for Mobile:**
```
GET  /api/v1/leave                   # My leave requests (paginated)
POST /api/v1/leave/apply             # Apply for leave
GET  /api/v1/leave/types             # Available leave types
GET  /api/v1/leave/balance           # Leave balance
POST /api/v1/leave/:id/cancel        # Cancel leave
GET  /api/v1/leave/approvals         # Pending approvals (manager)
POST /api/v1/leave/:id/approve       # Approve (manager)
POST /api/v1/leave/:id/reject        # Reject (manager)
POST /api/v1/leave/halfday           # Apply half-day
POST /api/v1/leave/early             # Apply early leave
```

**Service Layer:** ✅ `LeaveService` exists
**Repository:** ✅ Exists

---

### 6. **Shift Change Module** ✅
**Current State:** Shift change requests with approval  
**Blueprint:** `app/blueprints/shift_change/`  
**Models:** `ShiftChangeRequest`, `EmployeeShiftAssignment`, `Shift`

**Existing Routes:**
- `/shift-change` (GET) - Dashboard
- `/shift-change/create` (GET/POST) - Create request
- `/shift-change/my-requests` (GET) - My requests
- `/shift-change/<id>` (GET) - View request
- `/shift-change/<id>/cancel` (POST) - Cancel
- `/shift-change/approvals` (GET) - Pending approvals
- `/shift-change/shift-history` (GET) - Shift history

**APIs Needed for Mobile:**
```
GET  /api/v1/shifts/my-shift         # Current shift
GET  /api/v1/shifts/available        # Available shifts
POST /api/v1/shifts/request-change   # Request shift change
GET  /api/v1/shifts/requests         # My shift change requests
POST /api/v1/shifts/:id/cancel       # Cancel request
GET  /api/v1/shifts/approvals        # Pending approvals (manager)
POST /api/v1/shifts/:id/approve      # Approve (manager)
POST /api/v1/shifts/:id/reject       # Reject (manager)
GET  /api/v1/shifts/history          # Shift history
```

**Service Layer:** ✅ `ShiftChangeService` exists
**Repository:** ✅ Exists

---

### 7. **Payroll Module** ✅
**Current State:** Payroll processing and payslips  
**Blueprint:** `app/blueprints/payroll/`  
**Models:** `Payroll`

**Existing Routes:**
- `/payroll` (GET) - Payroll list
- `/payroll/generate` (POST) - Generate payroll
- `/payroll/<id>` (GET) - View payslip

**APIs Needed for Mobile:**
```
GET /api/v1/payroll/payslips         # My payslips (paginated)
GET /api/v1/payroll/payslips/:id     # View payslip details
GET /api/v1/payroll/latest           # Latest payslip
```

**Service Layer:** ✅ `PayrollService` exists
**Repository:** ✅ Exists

---

### 8. **Reports Module** ✅
**Current State:** Various reports generation  
**Blueprint:** `app/blueprints/reports/`

**Existing Routes:**
- `/reports` (GET) - Reports page
- `/reports/attendance` (GET)
- `/reports/leave` (GET)
- `/reports/export` (POST)

**APIs Needed for Mobile:**
```
GET /api/v1/reports/types            # Available report types
GET /api/v1/reports/attendance       # Attendance reports
GET /api/v1/reports/leave            # Leave reports
GET /api/v1/reports/payroll          # Payroll reports
```

**Service Layer:** ✅ `ReportService` exists
**Repository:** ✅ Exists

---

### 9. **Company Module** ✅
**Current State:** Company settings, shifts, holidays  
**Blueprint:** `app/blueprints/company/`  
**Models:** `Company`, `Shift`, `Holiday`

**Existing Routes:**
- `/company/settings` (GET/POST)
- `/company/shifts` (GET)
- `/company/shifts/create` (POST)
- `/company/holidays` (GET)

**APIs Needed for Mobile:**
```
GET /api/v1/company/info             # Company information
GET /api/v1/company/shifts           # Available shifts
GET /api/v1/company/holidays         # Upcoming holidays
GET /api/v1/company/announcements    # Company announcements
```

**Service Layer:** Needs creation
**Repository:** Needs creation

---

### 10. **Settings Module** ✅
**Current State:** User settings, profile, password  
**Blueprint:** `app/blueprints/settings/`

**Existing Routes:**
- `/settings/profile` (GET/POST)
- `/settings/password` (POST)
- `/settings/security` (GET)

**APIs Needed for Mobile:**
```
GET  /api/v1/settings/profile        # Get profile settings
PUT  /api/v1/settings/profile        # Update profile
PUT  /api/v1/settings/password       # Change password
GET  /api/v1/settings/preferences    # App preferences
PUT  /api/v1/settings/preferences    # Update preferences
```

**Service Layer:** Needs creation
**Repository:** Needs creation

---

### 11. **FOSS Module** ✅
**Current State:** Field operations, GPS tracking  
**Blueprint:** `app/blueprints/foss/`

**Existing Routes:**
- `/foss/history` (GET) - GPS history

**APIs Needed for Mobile:**
```
POST /api/v1/foss/location           # Track location
GET  /api/v1/foss/history            # Location history
GET  /api/v1/foss/assigned-areas     # Assigned areas
```

**Service Layer:** Needs creation
**Repository:** Needs creation

---

### 12. **Notifications Module** ✅
**Current State:** ✅ FCM notifications (already has APIs)  
**Blueprint:** `app/blueprints/notifications/`  
**Models:** `Notification`, `FCMToken`

**Existing APIs:** ✅ Already complete (from previous task)
```
GET  /api/notifications/unread-count
GET  /api/notifications/recent
POST /api/notifications/<id>/read
POST /api/notifications/<id>/clicked
POST /api/notifications/<id>/delete
POST /api/notifications/mark-all-read
POST /api/notifications/register-token
```

**Status:** ✅ **COMPLETE** - Ready for mobile

---

### 13. **Admin Module** ✅
**Current State:** Admin panel, bulk operations  
**Blueprint:** `app/blueprints/admin/`

**Existing Routes:**
- `/admin` (GET) - Admin dashboard
- `/admin/employees` (GET)
- `/admin/shift-assignment` (GET/POST)

**APIs Needed for Mobile:**
```
GET /api/v1/admin/stats              # Admin dashboard stats
GET /api/v1/admin/employees          # Employee list (admin)
POST /api/v1/admin/employees/import  # Bulk import
```

**Service Layer:** Partial
**Repository:** Partial

---

### 14. **User Module** (Core)
**Current State:** User management  
**Models:** `User`, `LoginHistory`

**APIs Needed for Mobile:**
```
GET  /api/v1/users/me                # Current user
PUT  /api/v1/users/me                # Update user
GET  /api/v1/users/login-history     # Login history
```

---

## 📊 Summary Statistics

### Modules Overview
| Module | Blueprint | Models | Service | Repository | Web Routes | API Routes | Priority |
|--------|-----------|--------|---------|------------|------------|------------|----------|
| Authentication | ✅ | ✅ | ✅ | ✅ | ✅ | ⬜ | 🔴 Critical |
| Dashboard | ✅ | N/A | ⬜ | N/A | ✅ | ⬜ | 🔴 Critical |
| Employee | ✅ | ✅ | ✅ | ✅ | ✅ | ⬜ | 🔴 Critical |
| Attendance | ✅ | ✅ | ✅ | ✅ | ✅ | ⬜ | 🔴 Critical |
| Leave | ✅ | ✅ | ✅ | ✅ | ✅ | ⬜ | 🔴 Critical |
| Shift Change | ✅ | ✅ | ✅ | ✅ | ✅ | ⬜ | 🟡 High |
| Settings | ✅ | ⬜ | ⬜ | ⬜ | ✅ | ⬜ | 🔴 Critical |
| Notifications | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ Complete |
| Payroll | ✅ | ✅ | ✅ | ✅ | ✅ | ⬜ | 🟡 High |
| Reports | ✅ | ⬜ | ✅ | ✅ | ✅ | ⬜ | 🟢 Medium |
| Company | ✅ | ✅ | ⬜ | ⬜ | ✅ | ⬜ | 🟢 Medium |
| FOSS | ✅ | ⬜ | ⬜ | ⬜ | ✅ | ⬜ | 🟢 Medium |
| Admin | ✅ | ⬜ | Partial | Partial | ✅ | ⬜ | 🟢 Medium |

### API Requirements
- **Total API Endpoints Needed:** ~60-70
- **Already Implemented:** ~10 (Notifications)
- **To Be Created:** ~50-60

### Priority Breakdown
- 🔴 **Critical (Must-have for MVP):** 6 modules
  - Authentication, Dashboard, Employee, Attendance, Leave, Settings
  - ~35-40 endpoints

- 🟡 **High (Important features):** 2 modules
  - Shift Change, Payroll
  - ~15-20 endpoints

- 🟢 **Medium (Nice to have):** 4 modules
  - Reports, Company, FOSS, Admin
  - ~10-15 endpoints

---

## 🎯 Implementation Plan

### Phase 1A: Core Infrastructure (Critical)
1. ✅ Create standardized API response format
2. ✅ Add API versioning (`/api/v1/`)
3. ✅ Create pagination utilities
4. ✅ Create filtering/sorting utilities
5. ✅ Add JWT authentication middleware
6. ✅ Create error handling

### Phase 1B: Critical APIs (Must-have)
1. Authentication APIs (6 endpoints)
2. Dashboard APIs (5 endpoints)
3. Employee APIs (6 endpoints)
4. Attendance APIs (7 endpoints)
5. Leave APIs (10 endpoints)
6. Settings APIs (5 endpoints)

**Total Critical Endpoints:** ~39

### Phase 1C: High Priority APIs
1. Shift Change APIs (8 endpoints)
2. Payroll APIs (3 endpoints)

**Total High Priority Endpoints:** ~11

### Phase 1D: Medium Priority APIs
1. Reports APIs (4 endpoints)
2. Company APIs (4 endpoints)
3. FOSS APIs (3 endpoints)
4. Admin APIs (3 endpoints)

**Total Medium Priority Endpoints:** ~14

---

## 🔧 Technical Requirements

### API Response Format
```json
{
  "success": true,
  "message": "Operation successful",
  "data": { ... },
  "errors": [],
  "meta": {
    "page": 1,
    "per_page": 20,
    "total": 100,
    "total_pages": 5
  }
}
```

### Pagination
- Query params: `?page=1&limit=20&sort=created_at&order=desc`
- Default limit: 20
- Max limit: 100

### Filtering
- Query params: `?status=approved&start_date=2024-01-01&end_date=2024-12-31`
- Support for: equals, contains, gt, lt, between

### Sorting
- Query params: `?sort=created_at&order=desc`
- Support multiple sort: `?sort=date,name&order=desc,asc`

### Authentication
- JWT token in header: `Authorization: Bearer <token>`
- Token expiry: 24 hours
- Refresh token: 30 days

### Error Codes
- 200: Success
- 201: Created
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 422: Validation Error
- 500: Server Error

---

## 📁 File Structure (To Be Created)

```
app/
├── blueprints/api/v1/
│   ├── __init__.py
│   ├── routes.py              ✅ Exists (skeleton)
│   ├── auth.py                ⬜ Create
│   ├── dashboard.py           ⬜ Create
│   ├── employees.py           ⬜ Create
│   ├── attendance.py          ⬜ Create
│   ├── leave.py               ⬜ Create
│   ├── shifts.py              ⬜ Create
│   ├── payroll.py             ⬜ Create
│   ├── reports.py             ⬜ Create
│   ├── company.py             ⬜ Create
│   ├── settings.py            ⬜ Create
│   ├── foss.py                ⬜ Create
│   └── admin.py               ⬜ Create
├── utils/
│   ├── response_utils.py      ✅ Exists
│   ├── pagination.py          ⬜ Create
│   ├── filters.py             ⬜ Create
│   └── jwt_utils.py           ⬜ Create
└── middleware/
    ├── auth_middleware.py     ⬜ Create
    └── api_middleware.py      ⬜ Create
```

---

## ✅ Task #1 Complete

**Audit Summary:**
- ✅ 14 modules identified
- ✅ 60-70 API endpoints mapped
- ✅ Priority levels assigned
- ✅ Implementation plan created
- ✅ Technical requirements defined

**Next Steps:**
- Task #2: Create standardized API response format
- Task #3: Implement Authentication APIs
- Continue with remaining modules

---

**Status:** ✅ Module Audit Complete  
**Ready for:** API Development Phase
