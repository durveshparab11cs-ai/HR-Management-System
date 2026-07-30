# Smart HRMS Mobile - Website Feature Parity Analysis

**Source of Truth:** https://hr-management-system-muqz.onrender.com  
**Date:** July 28, 2026  
**Status:** PHASE 1 - Feature Inventory Complete

---

## WEBSITE FEATURE INVENTORY

### 1. AUTHENTICATION MODULE
**Website Features:**
- ✓ Sign In (Employee Code + Department + Password)
- ✓ Remember Me option
- ✓ Forgot Password flow
- ✓ Register (Employee Code, Employee Name, Password, Re-enter Password)
- ✓ Employee Code lookup via AJAX
- ✓ Password strength indicator
- ✓ Auto-focus first field
- ✓ First user becomes Super Admin, others register as Employee

**Backend APIs:**
```
POST /api/v1/auth/login               → JWT tokens + user data
POST /api/v1/auth/refresh              → Refresh expired tokens
POST /api/v1/auth/logout               → Invalidate session
GET  /api/v1/auth/me                   → Current user profile
POST /api/v1/auth/forgot-password      → Request password reset
POST /api/v1/auth/reset-password       → Complete password reset
GET  /api/v1/auth/lookup-employee      → Search employee by code
```

**Flutter Status:**
- ✓ Basic login implemented
- ✓ Auth provider with Riverpod
- ✓ JWT token management
- ? Password strength indicator - NOT YET
- ? Employee lookup - NOT YET
- ? Forgot password UI - NEEDS COMPLETION
- ? Remember me - NEEDS VERIFICATION

---

### 2. DASHBOARD MODULE
**Website Features:**
- ✓ Greeting (Good morning/afternoon/evening, user first name)
- ✓ Today's date and day name
- ✓ Quick action button (Check In / Check Out / View Attendance)
- ✓ Four status cards:
  1. Check In time (with late indicator if applicable)
  2. Check Out time (with hours worked)
  3. Leave Balance (Casual days left)
  4. Employee Code + Department
- ✓ Employee Master Information panel:
  - Employee Code, Name, Department, Designation
  - Date of Joining, Official Email, Phone Number
  - Reporting Manager Code & Name
  - Location, Employment Status
- ✓ 6-month attendance chart (present/absent/on_leave)

**Backend APIs:**
```
GET /api/v1/dashboard                  → Complete home screen data
GET /api/v1/dashboard/attendance       → Today's attendance stats
GET /api/v1/dashboard/leave-balance    → Leave balance summary
GET /api/v1/dashboard/chart            → 6-month attendance data
```

**Flutter Status:**
- ✓ Dashboard screen exists
- ✓ Basic card layout
- ? Master info panel - NEEDS DATA
- ? 6-month chart - NOT VISUALIZED
- ? Quick actions - NEEDS IMPLEMENTATION

---

### 3. ATTENDANCE MODULE
**Website Features:**
- ✓ GPS-based check-in/check-out
- ✓ Selfie photo capture (check-in & check-out)
- ✓ Office location verification (latitude, longitude, radius)
- ✓ Distance calculation (shows meters away from office)
- ✓ Grace period check (10 minutes)
- ✓ Late indicator
- ✓ Attendance history with filters:
  - Status filter (present/absent/on_leave/holiday)
  - Date range filter
  - Pagination

**Workflow:**
1. GET /attendance/office → Get GPS bounds
2. POST /attendance/upload-photo → Upload selfie
3. POST /attendance/check-in → Submit GPS + lat/long
4. (Later) POST /attendance/upload-checkout-photo → Checkout selfie
5. (Later) POST /attendance/check-out → Submit GPS

**Backend APIs:**
```
GET  /api/v1/attendance/today           → Today's status
GET  /api/v1/attendance/office          → Office location bounds
POST /api/v1/attendance/upload-photo    → Upload selfie (multipart)
POST /api/v1/attendance/check-in        → Record check-in with GPS
POST /api/v1/attendance/upload-checkout-photo → Upload checkout selfie
POST /api/v1/attendance/check-out       → Record check-out with GPS
GET  /api/v1/attendance/history         → List attendance records (paginated)
```

**Flutter Status:**
- ✓ Check-in screen with GPS
- ✓ Selfie photo capture
- ✓ Distance calculation
- ? Checkout flow - NEEDS IMPLEMENTATION
- ? Checkout selfie - NEEDS IMPLEMENTATION
- ✓ Attendance history list
- ? History filters - NEEDS UI

---

### 4. LEAVE MODULE
**Website Features:**
- ✓ Apply for leave (Select leave type, date range, reason, reporting manager)
- ✓ Leave types list (Paid Leave, Casual, etc.)
- ✓ Leave balance display (Allowed, Taken, Available)
- ✓ Half-day leave option
- ✓ Early leave option
- ✓ Cancel leave request
- ✓ Leave approvals dashboard (for managers)
- ✓ Approval workflow: Approve / Reject with mandatory comment
- ✓ Leave history with filters

**Managers can:**
- View leave requests assigned to them
- Approve with optional comment
- **Reject with MANDATORY comment** (enforced)

**Backend APIs:**
```
GET  /api/v1/leave                      → My leave requests
GET  /api/v1/leave/types                → Available leave types
GET  /api/v1/leave/balance              → Leave balance summary
GET  /api/v1/leave/managers             → Searchable reporting managers list
POST /api/v1/leave/apply                → Submit leave request
POST /api/v1/leave/halfday              → Apply half-day leave
POST /api/v1/leave/early                → Apply early leave
GET  /api/v1/leave/<id>                 → Get leave detail
POST /api/v1/leave/<id>/cancel          → Cancel leave request
GET  /api/v1/leave/approvals            → Leave requests pending my approval
POST /api/v1/leave/<id>/approve         → Approve leave (optional comment)
POST /api/v1/leave/<id>/reject          → Reject leave (**mandatory comment**)
```

**Flutter Status:**
- ✓ Leave apply screen
- ✓ Leave list screen
- ? Half-day option - NOT IMPLEMENTED
- ? Early leave option - NOT IMPLEMENTED
- ? Leave approvals - NOT FULLY IMPLEMENTED
- ✓ Reject with comment - MUST VERIFY MANDATORY

---

### 5. SHIFT MODULE
**Website Features:**
- ✓ View my current shift
- ✓ View available shifts (HR only)
- ✓ Request shift change:
  - Current shift ID
  - Requested start time
  - Requested end time
  - Effective date
  - Reason
  - Reporting manager selection
- ✓ Cancel shift change request
- ✓ Shift change approvals (for managers)
- ✓ Shift history

**Backend APIs:**
```
GET  /api/v1/shifts/my-shift             → Current shift details
GET  /api/v1/shifts/available            → All available shifts (HR)
GET  /api/v1/shifts/requests             → My shift change requests
POST /api/v1/shifts/request-change       → Submit shift change request
POST /api/v1/shifts/<id>/cancel          → Cancel request
GET  /api/v1/shifts/approvals            → Requests pending my approval
POST /api/v1/shifts/<id>/approve         → Approve shift change
POST /api/v1/shifts/<id>/reject          → Reject shift change
GET  /api/v1/shifts/history              → Shift change history
```

**Flutter Status:**
- ✓ Shift view screen
- ✓ Shift change request screen
- ✓ Shift approvals screen
- ✓ Shift history screen
- ? Reject with comment - VERIFY MANDATORY
- ? Effective date picker - VERIFY PRESENT

---

### 6. PAYROLL MODULE
**Website Features:**
- ✓ View payslips list
- ✓ Filter payslips by date
- ✓ View payslip detail (Earnings, Deductions, Net Salary)
- ✓ Download payslip (PDF)

**Backend APIs:**
```
GET /api/v1/payroll/payslips             → List all payslips (paginated)
GET /api/v1/payroll/payslips/latest      → Most recent payslip
GET /api/v1/payroll/payslips/<id>        → Payslip detail
```

**Flutter Status:**
- ✓ Payroll list screen
- ✓ Payslip detail screen
- ? PDF download - NEEDS VERIFICATION

---

### 7. REPORTS MODULE
**Website Features:**
- ✓ Dashboard with summary cards
- ✓ Attendance Report (with charts)
- ✓ Leave Analytics (leave taken vs available)
- ✓ Payroll Report (salary trends)
- ✓ Export to CSV/PDF

**Flutter Status:**
- ✓ Reports dashboard screen
- ✓ Attendance report screen
- ✓ Leave analytics screen
- ✓ Payroll report screen
- ? Export functionality - NOT IMPLEMENTED (mobile alternative: share as image)

---

### 8. SETTINGS MODULE
**Website Features:**
- ✓ Profile settings (Edit name, email, phone)
- ✓ Password change (Current password required)
- ✓ Preferences (Theme, Language, Notifications, Biometric)
- ✓ Login history

**Backend APIs:**
```
GET  /api/v1/settings/profile            → Current profile
PUT  /api/v1/settings/profile            → Update profile
PUT  /api/v1/settings/password           → Change password
GET  /api/v1/settings/preferences        → User preferences
PUT  /api/v1/settings/preferences        → Update preferences
GET  /api/v1/settings/login-history      → Login audit trail
```

**Flutter Status:**
- ✓ Settings screen
- ✓ Change password screen
- ? Profile edit - PARTIAL
- ? Preferences (theme, language, biometric) - PARTIAL
- ? Login history - NOT IMPLEMENTED

---

### 9. PROFILE MODULE
**Website Features:**
- ✓ View profile (same as dashboard master info, more detailed)
- ✓ Edit profile photo
- ✓ Edit name, email, phone, address
- ✓ View employment history
- ✓ Emergency contacts

**Backend APIs:**
```
GET  /api/v1/employees/me                → Current employee profile
PUT  /api/v1/employees/me                → Update profile
POST /api/v1/employees/me/photo          → Upload profile photo
GET  /api/v1/employees                   → List all employees (Admin/HR)
GET  /api/v1/employees/<id>              → Employee detail
```

**Flutter Status:**
- ✓ Profile screen
- ✓ Edit profile screen
- ✓ Photo upload
- ? Emergency contacts - NOT IMPLEMENTED

---

### 10. NOTIFICATIONS MODULE
**Website Features:**
- ✓ Real-time notifications
- ✓ Notification center (list of recent notifications)
- ✓ Mark as read / Mark all as read
- ✓ Push notifications (if mobile)
- ✓ Unread count badge

**Backend APIs:**
```
GET  /api/v1/notifications/unread-count  → Count of unread
GET  /api/v1/notifications/recent        → Recent notifications (paginated)
POST /api/v1/notifications/mark-all-read → Mark all as read
POST /api/v1/notifications/register-token → Register FCM/device token
```

**Flutter Status:**
- ✓ Notifications service (Workmanager)
- ✓ FCM integration
- ✓ Push notifications
- ? Notification center UI - PARTIAL
- ? Mark as read - NEEDS VERIFICATION

---

### 11. COMPANY MODULE
**Website Features:**
- ✓ Company information (Admin only)
- ✓ Departments list
- ✓ Designations list
- ✓ Holiday calendar
- ✓ Office locations

**Flutter Status:**
- ✓ Company info screen
- ✓ Departments screen
- ✓ Designations screen
- ? Holiday calendar - NOT IMPLEMENTED

---

## DESIGN SYSTEM PARITY

**Website Design:**
- Color scheme: Blue primary (#4f9cf9), orange accents (#f90, #e77600), dark backgrounds
- Typography: Inter font family
- Components: Cards with shadows, rounded corners
- Icons: Bootstrap Icons (bi-*)
- Responsive: Mobile-friendly Bootstrap grid

**Flutter Status:**
- ✓ AppTheme defined
- ✓ Primary colors match
- ? Mobile-optimized layouts - PARTIAL

---

## MISSING FEATURES IN FLUTTER

### Critical (Must Have)
1. **Attendance Checkout Selfie** - Selfie upload for checkout
2. **Attendance Checkout** - Complete check-out workflow
3. **Leave Approvals** - Full approval/rejection UI
4. **Shift Approvals** - Full approval/rejection UI
5. **Password Strength Indicator** - Visual feedback during registration
6. **Employee Code Lookup** - AJAX-like live search
7. **Forgot Password Flow** - Complete UI
8. **Holiday Calendar** - Company holidays display

### Important (Should Have)
1. **Half-day Leave** - Leave type selection
2. **Early Leave** - Leave type selection
3. **Login History** - Past login sessions
4. **Emergency Contacts** - Profile data
5. **Preferences** - Theme, language, biometric
6. **Leave Balance Charts** - Visual representation

### Nice-to-Have (Could Have)
1. **Export Reports** - Share as image/PDF
2. **Offline Sync** - Cache data locally
3. **Biometric Login** - Fingerprint/Face ID (optional mobile feature)
4. **Dark Theme** - Theme preference
5. **Localization** - Multiple languages

---

## MIGRATION PRIORITY

### Phase 2 (Week 1)
- [ ] Authentication complete (forgot password, lookup)
- [ ] Dashboard full (master info, charts)
- [ ] Attendance checkout flow
- [ ] Leave approvals UI

### Phase 3 (Week 2)
- [ ] Shift approvals UI
- [ ] Holiday calendar
- [ ] Settings (preferences, login history)
- [ ] Half-day/early leave options

### Phase 4 (Week 3)
- [ ] Polish UI to match website exactly
- [ ] Add missing validations
- [ ] Offline sync implementation
- [ ] Testing and fixes

---

## ARCHITECTURE COMPLIANCE

✓ Riverpod providers maintained  
✓ GoRouter navigation intact  
✓ Repository pattern used  
✓ Clean architecture layers  
✓ Feature-first folder structure  
✓ Dependency injection working  
✓ Backend API reuse  

---

## NEXT STEP

**Phase 2 starts:** Implement missing features in priority order, ensuring every Flutter screen matches the website exactly.

