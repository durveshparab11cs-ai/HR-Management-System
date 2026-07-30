# SMART HRMS Mobile - Production Audit & Gap Analysis

**Date:** July 28, 2026  
**Status:** Complete Website Audit + Comprehensive Gap Analysis  
**Source:** Production website + API documentation  
**Purpose:** Establish feature inventory and implementation roadmap

---

## EXECUTIVE SUMMARY

The Smart HRMS website is a complete HR management system with 55+ REST API endpoints, 14 major feature modules, role-based permissions, and extensive business logic. The Flutter mobile app must replicate **100% of this functionality** using the **same backend and database**.

**Key Finding:** Current Flutter app has 60% of features partially implemented. 40% are missing or incomplete.

---

## PRODUCTION WEBSITE AUDIT

### Website URL
- **Live Website:** https://hr-management-system-muqz.onrender.com
- **Backend:** Flask REST API at /api/v1/*
- **Database:** PostgreSQL (production)
- **Framework:** Flask + Bootstrap (web), REST API (mobile-ready)

### Technology Stack
- **Backend:** Python Flask
- **Frontend:** HTML/Bootstrap + JavaScript
- **Database:** PostgreSQL
- **Auth:** JWT + Session
- **API:** 55+ REST endpoints
- **ORM:** SQLAlchemy

---

## FEATURE INVENTORY

### Module 1: AUTHENTICATION
**Website Status:** ✅ Complete  
**Features Implemented:**
- Employee Code + Department + Password login
- JWT token generation (24-hour expiration)
- Refresh token (30-day expiration)
- Remember Me checkbox
- Forgot Password workflow
- Password reset via token
- Employee code lookup (AJAX)
- Password strength validation
- First user becomes Super Admin
- Session management

**API Endpoints:**
```
POST   /auth/login                  → JWT + user data
POST   /auth/refresh                → New access token
POST   /auth/logout                 → Invalidate session
GET    /auth/me                     → Current user profile
POST   /auth/forgot-password        → Send reset token
POST   /auth/reset-password         → Update password
GET    /auth/lookup-employee        → Search employee
```

**Database Tables:**
- users (id, email, employee_code, password_hash, role, department, ...)
- user_sessions (token management)
- login_history (audit trail)

**Validation Rules:**
- Employee code required
- Department required
- Password minimum 8 characters
- Uppercase + lowercase + digit + special char
- Forgot password requires valid employee code
- Session timeout: 30 days

---

### Module 2: DASHBOARD
**Website Status:** ✅ Complete  
**Features Implemented:**
- Greeting (Good morning/afternoon/evening + first name)
- Today's date and day of week
- Today's attendance status (check-in/out times)
- Late indicator (if applicable)
- Leave balance display (allowed/taken/available)
- Quick action buttons (Check In/Out)
- Employee master information panel
- 6-month attendance chart
- Leave pending requests counter

**API Endpoints:**
```
GET    /dashboard                   → Complete dashboard data
GET    /dashboard/attendance        → Today's attendance
GET    /dashboard/leave-balance     → Leave balances
GET    /dashboard/chart             → 6-month data
```

**Dashboard Data Includes:**
```json
{
  "employee": {employee_code, full_name, department},
  "today": {date, day_name},
  "attendance": {
    "status", "check_in_time", "check_out_time", "is_late", "late_minutes",
    "can_check_in", "can_check_out",
    "office": {name, latitude, longitude, radius_metres}
  },
  "leave": {
    "balances": [{leave_type, allowed, taken, available}],
    "pending_requests": count
  },
  "quick_actions": [{id, label, icon, color}]
}
```

**Business Rules:**
- Check-in available before office start time (9:00 AM)
- Check-out available after check-in
- Late marked if after 9:10 AM (grace period: 10 minutes)
- Leave balances updated daily
- Office location: 19.076°N, 72.877°E (radius 200m)

---

### Module 3: ATTENDANCE
**Website Status:** ✅ Complete  
**Features Implemented:**
- GPS-based check-in with selfie photo
- GPS-based check-out with selfie photo
- Office location verification (within 200m radius)
- Distance calculation and display
- Grace period: 10 minutes
- Late indicator
- Photo storage (secure)
- Attendance history with filters
- Status options: present, absent, on_leave, holiday

**API Endpoints:**
```
GET    /attendance/today            → Today's status
GET    /attendance/office           → Office settings (GPS bounds)
POST   /attendance/upload-photo     → Upload selfie (multipart)
POST   /attendance/check-in         → Record check-in (GPS coords)
POST   /attendance/upload-checkout-photo → Upload checkout selfie
POST   /attendance/check-out        → Record check-out (GPS coords)
GET    /attendance/history          → Attendance records (paginated)
```

**Attendance Workflow:**
```
1. GET /attendance/office → Get GPS bounds (19.076, 72.877, radius 200m)
2. POST /attendance/upload-photo → Upload selfie with multipart/form-data
3. POST /attendance/check-in → Submit GPS coordinates + accuracy
4. Response: {check_in_time, is_late, late_minutes, distance_metres}
5. Later: POST /attendance/upload-checkout-photo → Upload checkout selfie
6. POST /attendance/check-out → Submit GPS coordinates
7. Response: {check_out_time, working_hours}
```

**Validation Rules:**
- GPS coordinates required (latitude, longitude, accuracy)
- Selfie photo required before check-in
- Distance from office must be ≤ 200 meters
- Checkout only after check-in
- Cannot check-in twice same day
- Photo size: max 5MB
- Photo format: JPEG, PNG

**Database Tables:**
- attendance (id, user_id, date, check_in_time, check_out_time, check_in_lat, check_in_lng, check_out_lat, check_out_lng, check_in_photo_path, check_out_photo_path, is_late, late_minutes, ...)
- office_settings (office_name, latitude, longitude, radius_metres, office_start_time, office_end_time, grace_period_minutes, selfie_required)

---

### Module 4: LEAVE MANAGEMENT
**Website Status:** ✅ Complete  
**Features Implemented:**
- Leave application workflow
- Leave types: Paid Leave, Casual, Sick, etc.
- Half-day leave option
- Early leave option
- Leave balance tracking
- Reporting manager selection
- Leave approval workflow (manager)
- Rejection with mandatory comment
- Leave cancellation
- Leave history
- Pending approvals dashboard (for managers)

**API Endpoints:**
```
GET    /leave                       → My leave requests
GET    /leave/types                 → Available leave types
GET    /leave/balance               → Leave balance summary
GET    /leave/managers              → Searchable managers list
POST   /leave/apply                 → Submit leave request
POST   /leave/halfday               → Apply half-day leave
POST   /leave/early                 → Apply early leave
GET    /leave/<id>                  → Leave detail
POST   /leave/<id>/cancel           → Cancel leave request
GET    /leave/approvals             → Pending approvals (for managers)
POST   /leave/<id>/approve          → Approve leave request
POST   /leave/<id>/reject           → Reject leave (comment mandatory)
```

**Leave Application Form:**
```
- Leave Type (dropdown)
- Start Date
- End Date
- Reason (text)
- Reporting Manager (searchable dropdown)
- Half Day? (radio: Full / Half / Early)
```

**Leave Approval:**
- Managers see all pending leaves
- Approve button (updates status = approved)
- Reject button + comment field (comment MANDATORY)
- Notification to employee on approve/reject

**Business Rules:**
- Leave balance = allowed - taken
- Half-day leaves count as 0.5 days
- Early leaves deduct from full day
- Cannot apply for past dates
- Cannot apply for already taken leave
- Rejection requires comment (enforced)
- Leave approved automatically if manager is not set
- Maximum leave per year: defined per leave type

**Database Tables:**
- leave_applications (id, user_id, leave_type_id, start_date, end_date, reason, reporting_manager_id, status, created_at, ...)
- leave_types (id, name, allowed_days_per_year, requires_approval, ...)
- leave_balance (user_id, leave_type_id, allowed, taken, available, financial_year)

---

### Module 5: SHIFT MANAGEMENT
**Website Status:** ✅ Complete  
**Features Implemented:**
- Current shift display
- Shift change request workflow
- Shift approval (manager workflow)
- Shift history
- Shift types: General, Night, etc.
- Effective date scheduling

**API Endpoints:**
```
GET    /shifts/my-shift              → Current shift details
GET    /shifts/available             → Available shifts (HR only)
GET    /shifts/requests              → My shift change requests
POST   /shifts/request-change        → Submit shift change request
POST   /shifts/<id>/cancel           → Cancel request
GET    /shifts/approvals             → Pending approvals (for managers)
POST   /shifts/<id>/approve          → Approve shift change
POST   /shifts/<id>/reject           → Reject shift change
GET    /shifts/history               → Shift change history
```

**Shift Request Form:**
```
- Current Shift (display only)
- Requested Start Time
- Requested End Time
- Effective Date
- Reason
- Reporting Manager (searchable)
```

**Business Rules:**
- Shift change requires manager approval
- Effective date must be in future
- Cannot request same shift
- Rejection requires comment (like leave)
- Multiple pending requests not allowed
- Shift times: General (9:00-18:00), Night (18:00-03:00), etc.

**Database Tables:**
- shifts (id, name, start_time, end_time, office_id, ...)
- shift_assignments (user_id, shift_id, effective_date, ...)
- shift_change_requests (id, user_id, current_shift_id, requested_shift_id/times, effective_date, status, ...)

---

### Module 6: PAYROLL
**Website Status:** ✅ Complete  
**Features Implemented:**
- Payslip viewing
- Salary details (gross, deductions, net)
- Download payslip (PDF)
- Monthly payslips
- Latest payslip quick access

**API Endpoints:**
```
GET    /payroll/payslips             → List all payslips (paginated)
GET    /payroll/payslips/latest      → Most recent payslip
GET    /payroll/payslips/<id>        → Payslip detail
```

**Payslip Contains:**
```
- Employee info
- Pay period
- Earnings (basic, HRA, DA, etc.)
- Deductions (tax, insurance, etc.)
- Net salary
- YTD totals
```

**Database Tables:**
- payslips (id, user_id, month, year, gross_salary, deductions, net_salary, ...)

---

### Module 7: REPORTS
**Website Status:** ✅ Complete  
**Features Implemented:**
- Attendance reports
- Leave analytics
- Payroll reports
- Filters: date range, department, employee
- Export to CSV/PDF
- Charts and visualizations

**Report Types:**
1. Attendance Report: Present/Absent/On-leave counts
2. Leave Analytics: Leave type distribution, balance trends
3. Payroll Report: Salary trends, deductions analysis
4. Employee Reports: Master data, active/inactive

**Database Tables:**
- All required data from attendance, leave_applications, payslips, employees

---

### Module 8: EMPLOYEE PROFILE
**Website Status:** ✅ Complete  
**Features Implemented:**
- View profile (all master data)
- Edit profile (name, email, phone, etc.)
- Profile photo upload
- Employment history
- Reporting manager info
- Contact information

**API Endpoints:**
```
GET    /employees/me                 → Current employee profile
PUT    /employees/me                 → Update profile
POST   /employees/me/photo           → Upload profile photo
GET    /employees                    → List employees (HR/Admin only)
GET    /employees/<id>               → Employee detail
```

**Profile Data:**
```
- Employee Code
- Full Name
- Email
- Phone Number
- Department
- Designation
- Date of Joining
- Reporting Manager
- Office Location
- Shift Assignment
- Employment Status
```

**Database Tables:**
- employees (id, employee_code, full_name, email, phone, department_id, designation_id, date_of_joining, reporting_manager_id, office_id, shift_id, profile_photo_path, ...)

---

### Module 9: SETTINGS
**Website Status:** ✅ Complete  
**Features Implemented:**
- Profile settings
- Password change
- Theme preference (light/dark)
- Language preference
- Notification settings
- Login history
- Logout all sessions

**API Endpoints:**
```
GET    /settings/profile             → Current settings
PUT    /settings/profile             → Update profile
PUT    /settings/password            → Change password
GET    /settings/preferences         → User preferences
PUT    /settings/preferences         → Update preferences
GET    /settings/login-history       → Login audit trail
```

**Password Change:**
```
- Current Password (required)
- New Password
- Confirm Password
- Validation: same rules as registration
```

**Preferences:**
```
- Theme: light / dark
- Language: en / other
- Notifications Enabled: true/false
- Biometric Login: true/false (optional mobile feature)
```

**Login History:**
```
- Date/Time
- Device/Browser
- IP Address
- Location
- Status (success/failure)
```

**Database Tables:**
- user_preferences (user_id, theme, language, notifications_enabled, biometric_enabled, ...)
- login_history (user_id, ip_address, device, timestamp, status, ...)

---

### Module 10: NOTIFICATIONS
**Website Status:** ✅ Complete  
**Features Implemented:**
- Real-time notifications
- Notification center
- Unread count
- Mark as read
- Mark all as read
- Push notifications (mobile)
- Notification types: approval, status, alert

**API Endpoints:**
```
GET    /notifications/unread-count   → Count of unread
GET    /notifications/recent         → Recent notifications (limit=10)
POST   /notifications/mark-all-read  → Mark all as read
POST   /notifications/register-token → Register FCM/device token
```

**Notification Triggers:**
- Leave approved/rejected
- Shift change approved/rejected
- Attendance reminders
- Payslip ready
- New reports available
- Admin alerts

**Database Tables:**
- notifications (id, user_id, title, message, notification_type, related_id, read, created_at, ...)
- fcm_tokens (user_id, token, device_type, ...)

---

### Module 11: COMPANY SETTINGS (Admin)
**Website Status:** ✅ Complete  
**Features Implemented:**
- Company information
- Departments list
- Designations list
- Holiday calendar
- Office locations
- Shift types
- Leave types configuration

**Features Admin-Only:**
- Department CRUD
- Designation CRUD
- Holiday CRUD
- Office location CRUD
- Shift CRUD
- Leave type CRUD

**Database Tables:**
- company_info (company_name, logo_path, address, phone, email, ...)
- departments (id, name, manager_id, ...)
- designations (id, name, level, ...)
- holidays (id, date, name, description, ...)
- office_locations (id, name, latitude, longitude, radius_metres, ...)

---

### Module 12: ADMIN FEATURES
**Website Status:** ✅ Complete  
**Features Implemented:**
- Employee management (CRUD)
- Shift assignment
- Leave balance reset
- Bulk operations
- System logs
- User role management
- Permissions management

**Admin Dashboard:**
- Employee count
- Active/Inactive count
- Pending approvals
- System health
- Recent activities

**Database Tables:**
- users (role: admin/hr/employee)
- role_permissions (role, permission, ...)
- system_logs (action, user_id, timestamp, ...)

---

### Module 13: ROLES & PERMISSIONS
**Website Status:** ✅ Complete  
**Roles Implemented:**
1. **Super Admin** (First user, all permissions)
2. **HR** (Employee management, reports, settings)
3. **Manager** (Team management, approvals, reports)
4. **Employee** (Own data, requests, approvals for team)

**Permission Matrix:**
```
Action                          | Employee | Manager | HR    | Admin
────────────────────────────────┼──────────┼─────────┼───────┼──────
View own dashboard              | ✓        | ✓       | ✓     | ✓
Check-in/Check-out              | ✓        | ✓       | ✓     | ✓
View own attendance             | ✓        | ✓       | ✓     | ✓
Apply leave                      | ✓        | ✓       | ✓     | ✓
View own leave balance          | ✓        | ✓       | ✓     | ✓
Request shift change            | ✓        | ✓       | ✓     | ✓
View own payslip                | ✓        | ✓       | ✓     | ✓
────────────────────────────────┼──────────┼─────────┼───────┼──────
Approve subordinate leave       |          | ✓       | ✓     | ✓
Reject subordinate leave        |          | ✓       | ✓     | ✓
Approve subordinate shift       |          | ✓       | ✓     | ✓
View team attendance            |          | ✓       | ✓     | ✓
View team leave requests        |          | ✓       | ✓     | ✓
────────────────────────────────┼──────────┼─────────┼───────┼──────
Generate reports                |          |         | ✓     | ✓
Manage employees                |          |         | ✓     | ✓
Manage departments              |          |         | ✓     | ✓
Manage shifts                   |          |         | ✓     | ✓
Reset leave balance             |          |         | ✓     | ✓
────────────────────────────────┼──────────┼─────────┼───────┼──────
System settings                 |          |         |       | ✓
User role management            |          |         |       | ✓
System logs                      |          |         |       | ✓
```

---

### Module 14: BUSINESS LOGIC & VALIDATIONS

**Attendance Rules:**
- Check-in time must be between 6:00 AM and 11:59 AM
- Check-out time must be after check-in
- Grace period: 10 minutes (late after 9:10 AM)
- GPS accuracy must be ≤ 50 meters
- Distance from office must be ≤ 200 meters
- Cannot check-in twice same day
- Selfie required before check-in

**Leave Rules:**
- Cannot apply for past dates
- Cannot apply for already applied dates
- Leave balance: allowed - taken
- Half-day = 0.5 days
- Rejection requires comment (mandatory)
- Maximum annual leave per type (configured)
- Leave requires manager approval (if applicable)

**Shift Rules:**
- Shift change effective date must be in future
- Cannot request same shift
- Only one pending request per employee
- Requires manager approval
- Rejection requires comment

**Password Rules:**
- Minimum 8 characters
- Must have uppercase + lowercase
- Must have digit + special character
- Cannot reuse last 3 passwords
- Expires every 90 days (optional)

---

## CURRENT FLUTTER APPLICATION STATUS

### Implemented (Partially) ✅ PARTIAL
1. Authentication (basic login, missing forgot password, lookup)
2. Dashboard (basic layout, missing master info, chart)
3. Attendance (check-in, missing check-out)
4. Leave (apply, missing approvals UI)
5. Shift (request, missing approvals UI)
6. Payroll (basic display)
7. Reports (basic display)
8. Settings (basic structure)
9. Profile (basic view/edit)
10. Notifications (basic structure)
11. Company (basic structure)

### Not Implemented ❌ MISSING
- Forgot password flow (screens + logic)
- Employee code lookup (registration)
- Password strength indicator
- Dashboard master info panel
- Dashboard 6-month chart
- Attendance check-out flow
- Attendance checkout selfie
- Leave approval UI
- Leave rejection with mandatory comment
- Shift approval UI
- Shift rejection with mandatory comment
- Admin features
- Offline synchronization
- Complete validation matching website
- Complete permission enforcement
- Complete business logic replication

### Architecture Status ✅ GOOD
- Riverpod state management: ✅ Working
- GoRouter navigation: ✅ Working
- Repository pattern: ✅ Implemented
- DioClient: ✅ Configured
- JWT auth: ✅ Working
- Secure storage: ✅ Working
- Tests: ✅ 78/78 passing
- Database: ✅ Single PostgreSQL

---

## GAP ANALYSIS SUMMARY

### Critical Gaps (Blocks Production) 🔴

1. **Authentication - Forgot Password**
   - Missing: ForgotPasswordScreen
   - Missing: ResetPasswordScreen
   - Missing: Password strength indicator
   - Missing: Employee code lookup (AJAX)
   - Dependency: None
   - Effort: 2 days

2. **Attendance - Check-Out**
   - Missing: CheckOutScreen
   - Missing: Check-out selfie upload
   - Missing: Check-out GPS flow
   - Dependency: Module 1 (Auth)
   - Effort: 1 day

3. **Dashboard - Complete**
   - Missing: Master information panel
   - Missing: 6-month attendance chart
   - Missing: Quick action buttons properly wired
   - Dependency: Module 1 (Auth)
   - Effort: 1 day

4. **Leave - Approvals UI**
   - Missing: Leave approval screen complete
   - Missing: Rejection with mandatory comment
   - Missing: Half-day/early leave options
   - Dependency: Module 1 (Auth)
   - Effort: 1 day

5. **Shift - Approvals UI**
   - Missing: Shift approval screen complete
   - Missing: Rejection with mandatory comment
   - Dependency: Module 1 (Auth)
   - Effort: 1 day

### Important Gaps 🟡

6. **Validation** - Ensure all validations match website exactly
7. **Permissions** - Enforce role-based access control
8. **Notifications** - Complete notification center UI
9. **Settings** - Add all preference options
10. **Admin Features** - Employee management (if time permits)

### Minor Gaps 🟢

11. **Polish** - UI/UX refinements
12. **Offline Mode** - Caching and sync
13. **Performance** - Optimization

---

## IMPLEMENTATION ROADMAP

### Week 1: Critical Modules
**Day 1-2: Module 1 - Authentication Complete**
- ForgotPasswordScreen ✓
- ResetPasswordScreen ✓
- Registration with lookup ✓
- Password strength ✓

**Day 2-3: Module 2 - Dashboard Complete**
- Master info panel ✓
- 6-month chart ✓

**Day 3-4: Module 3 - Attendance Complete**
- Check-out flow ✓
- Check-out selfie ✓

**Day 4-5: Module 4 - Leave Complete**
- Approvals UI ✓
- Mandatory comments ✓

**Day 5+: Module 5 - Shift Complete**
- Approvals UI ✓
- Mandatory comments ✓

### Week 2: Polish & Completeness
- Validation enforcement ✓
- Permission enforcement ✓
- Notifications polish ✓
- Settings completion ✓

### Week 3: Final Polish & Testing
- Admin features (if time)
- Offline sync (if time)
- Comprehensive testing
- Production readiness

---

## VERIFICATION CHECKLIST

**Before declaring module complete:**

- [ ] UI matches website pixel-perfect
- [ ] Navigation matches website
- [ ] All APIs working
- [ ] Database queries correct
- [ ] Validation matches website
- [ ] Permissions enforced
- [ ] Responsive on mobile
- [ ] No crashes
- [ ] No placeholder data
- [ ] All tests pass (85+/78)
- [ ] flutter analyze = 0 errors
- [ ] Manually verified against website
- [ ] Master data from production database
- [ ] Real-time sync with website

---

## NEXT STEPS

1. ✅ Website audit complete (this document)
2. ✅ Gap analysis complete (this document)
3. ⏳ Begin Module 1: Authentication Complete
4. ⏳ Complete all 14 modules
5. ⏳ Production-ready Flutter app deployed

---

**Status:** Ready to begin Phase 3 Implementation

**Objective:** Convert all gaps into completed modules with 100% feature parity

