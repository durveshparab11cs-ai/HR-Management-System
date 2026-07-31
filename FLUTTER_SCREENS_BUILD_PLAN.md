# FLUTTER SCREENS BUILD PLAN - PHASE 5
**Complete screen development roadmap to match website**

**Status:** Planning & Analysis  
**Date:** July 28, 2026  
**Target:** 100% feature parity with website  

---

## EXECUTIVE SUMMARY

**Current State:**
- ✅ 26 screen files exist
- ✅ Core architecture: Riverpod + GoRouter + Clean Architecture
- ⚠️ 40% incomplete (partial implementations)
- ❌ 30% missing entirely (employee management, admin, auth flows)

**Scope for PHASE 5:**
- Complete 12 incomplete screens
- Build 15 missing screens
- Verify 26 screens working correctly
- **Total: 53 screens** (30+ from website mapping)

---

## MODULE BREAKDOWN & PRIORITIES

### PRIORITY 1: AUTHENTICATION (CRITICAL - 4 screens)

**Website requires:** Login, Register, Forgot Password, Reset Password

#### Current Status:
- ✅ Login Screen (195 lines) - COMPLETE
  - Email/code + password
  - Department dropdown
  - Remember me checkbox
  - Biometric option
  - Proper validation

- ✅ Register Tab (in LoginScreen) - PARTIAL
  - Employee code lookup
  - Name input
  - Password strength validator
  - Confirm password
  - Needs: Full page separation, API call

- ❌ Forgot Password Screen - MISSING
  - Email/code input field
  - Email verification flow
  - Token sent message

- ❌ Reset Password Screen - MISSING
  - Token input field
  - New password input
  - Confirm password input
  - Submit button

**Build Priority:** HIGH  
**Effort:** 2 screens × 150 lines = 300 lines  
**Timeline:** 4 hours

**Required Endpoints:**
- POST /api/v1/auth/forgot-password
- POST /api/v1/auth/reset-password

---

### PRIORITY 2: EMPLOYEE MANAGEMENT (CRITICAL - 7 screens)

**Website requires:** List, Create, Edit, Detail, Profile, Reset Password, Login History

**Current Status:**
- ❌ Employee List Screen - MISSING
- ❌ Employee Create Screen - MISSING
- ❌ Employee Edit Screen - MISSING
- ❌ Employee Detail Screen - MISSING
- ❌ Employee Profile Screen - MISSING
- ❌ Reset Employee Password Screen - MISSING
- ❌ Employee Login History Screen - MISSING

**Build Priority:** CRITICAL  
**Effort:** 7 screens × 200 lines = 1,400 lines  
**Timeline:** 12 hours

**Required Endpoints:**
- GET /api/v1/employees (list with search/filter)
- POST /api/v1/employees (create)
- GET /api/v1/employees/{id} (detail)
- PUT /api/v1/employees/{id} (edit)
- DELETE /api/v1/employees/{id} (delete)
- POST /api/v1/employees/{id}/reset-password (reset pwd)
- GET /api/v1/employees/{id}/login-history (login audit)

**Features per Screen:**
1. **Employee List** (180 lines)
   - Search by name/code
   - Filter by department
   - Filter by branch
   - Filter by status (active/inactive)
   - Sort by name/code/date_joined
   - Create button
   - Tap to view detail

2. **Employee Create** (220 lines)
   - Employee code input (unique check)
   - First name + Last name inputs
   - Email input
   - Mobile input
   - Department dropdown (from API)
   - Position dropdown (from API)
   - Branch input
   - Date joined picker
   - Employment type radio (full-time, part-time, contract, intern)
   - Manager lookup (autocomplete)
   - Photo upload
   - Submit + Cancel buttons

3. **Employee Edit** (220 lines)
   - Load current data
   - Edit all fields (except code)
   - Save + Cancel buttons
   - Delete button (confirmation)
   - Validation same as Create

4. **Employee Detail** (180 lines)
   - Read-only view of all fields
   - Actions: Edit, Reset Password, Login History, Delete
   - Display attendance summary
   - Display leave balance
   - Display current shift
   - Display reporting manager

5. **Employee Profile** (140 lines)
   - My own employee profile (read-only)
   - View current position
   - View department
   - View manager
   - View join date
   - Edit own details button
   - View my login history

6. **Reset Password** (120 lines)
   - Modal/bottom sheet
   - Employee code display (read-only)
   - Email display (read-only)
   - New password input
   - Confirm password input
   - Strength indicator
   - Reset button
   - Success/error message

7. **Login History** (150 lines)
   - Table with: Timestamp, IP, Device, Success/Failure
   - Pagination
   - Search by date range
   - Export button

---

### PRIORITY 3: ATTENDANCE (INTERMEDIATE - 3 screens)

**Website requires:** Check-in, Check-out, History, Export

**Current Status:**
- ✅ Check-in Screen (385 lines) - COMPLETE
  - GPS location
  - Camera photo
  - Geofence validation
  - Office settings integration

- ⚠️ Check-out Screen - MISSING (separate from check-in)
  - Similar to check-in
  - Shows morning check-in time
  - Validates location again

- ⚠️ Attendance History - PARTIAL (needs completion)
  - Filter by date range
  - Show status badge
  - Show working hours
  - Show late/early indicators
  - Export to CSV/PDF

- ⚠️ Office Settings - PARTIAL (view/edit settings)
  - GPS coordinates display
  - Geofence radius setter
  - Grace period display
  - Office hours display

**Build Priority:** HIGH  
**Effort:** 3 screens × 180 lines = 540 lines  
**Timeline:** 6 hours

**Required Endpoints:**
- POST /api/v1/attendance/check-in
- POST /api/v1/attendance/check-out
- GET /api/v1/attendance/history
- GET /api/v1/settings/office (already exists)
- PUT /api/v1/settings/office (if allowing edits)

---

### PRIORITY 4: LEAVE MANAGEMENT (HIGH - 5 screens)

**Website requires:** Apply, History, Approvals, Detail, Balance

**Current Status:**
- ✅ Apply Leave Screen (288 lines) - COMPLETE
  - Full-day leave
  - Half-day leave
  - Early leave
  - Date pickers
  - Manager lookup
  - Form validation

- ⚠️ Leave History - PARTIAL
  - List all leave requests
  - Filter by status (pending, approved, rejected)
  - Filter by leave type
  - Sort by date
  - Show approval status
  - Cancel button if pending

- ❌ Leave Approvals - MISSING (Manager view)
  - Show all pending leave requests from team
  - Approve button
  - Reject button with remarks
  - Comment field
  - Details of applicant

- ⚠️ Leave Detail - PARTIAL
  - Show full leave request details
  - Show approval history
  - Show reviewer comments
  - Show dates/days
  - Show leave type
  - Cancel if pending

- ⚠️ Leave Balance - PARTIAL
  - Show balance for each leave type
  - Show used/remaining
  - Show annual entitlement
  - Show carry-forward available

**Build Priority:** HIGH  
**Effort:** 5 screens × 160 lines = 800 lines  
**Timeline:** 8 hours

**Required Endpoints:**
- GET /api/v1/leave (my requests)
- POST /api/v1/leave (apply)
- GET /api/v1/leave/balance
- GET /api/v1/leave/approvals (manager)
- POST /api/v1/leave/{id}/approve (manager)
- POST /api/v1/leave/{id}/reject (manager)
- GET /api/v1/leave/{id}
- POST /api/v1/leave/{id}/cancel

---

### PRIORITY 5: SHIFT MANAGEMENT (HIGH - 4 screens)

**Website requires:** Current Shift, Request Change, Approvals, History, Calendar

**Current Status:**
- ⚠️ Current Shift - PARTIAL
  - Show current shift (name, time, grace period)
  - Show office location
  - Show working hours

- ⚠️ Request Change - PARTIAL
  - Current shift display (read-only)
  - Available shifts dropdown
  - Effective date picker
  - Reason textarea
  - Document upload
  - Submit button

- ❌ Shift Approvals - MISSING (Manager view)
  - List pending shift change requests
  - Show requester details
  - Show current vs requested shift
  - Approve button
  - Reject button with remarks

- ⚠️ Shift History - PARTIAL
  - Show all shift changes (past and pending)
  - Sort by effective date
  - Show status (pending, approved, rejected)
  - Show previous shift info

**Build Priority:** HIGH  
**Effort:** 4 screens × 150 lines = 600 lines  
**Timeline:** 7 hours

**Required Endpoints:**
- GET /api/v1/shift/my-shift
- GET /api/v1/shift/available
- POST /api/v1/shift/change-request
- GET /api/v1/shift/history
- GET /api/v1/shift/approvals (manager)
- POST /api/v1/shift/{id}/approve (manager)
- POST /api/v1/shift/{id}/reject (manager)

---

### PRIORITY 6: PAYROLL (MEDIUM - 3 screens)

**Website requires:** View Payslips, Payslip Detail, Payroll Runs (HR), Salary Structures

**Current Status:**
- ⚠️ Payslip List - PARTIAL
  - Show all payslips (paginated)
  - Sort by month (recent first)
  - Show basic info (month, net salary, status)
  - Tap to view detail
  - Download button

- ⚠️ Payslip Detail - PARTIAL
  - Show payslip details
  - Earnings breakdown
  - Deductions breakdown
  - Taxes applied
  - Net salary calculation
  - Download PDF button

- ❌ Payroll Runs (HR only) - MISSING
  - List of payroll runs (paginated)
  - Filter by status (draft, processing, approved, paid)
  - Create new run
  - View run details
  - Approve run
  - Mark as paid

**Build Priority:** MEDIUM  
**Effort:** 3 screens × 140 lines = 420 lines  
**Timeline:** 5 hours

**Required Endpoints:**
- GET /api/v1/payroll/payslips
- GET /api/v1/payroll/payslips/{id}
- GET /api/v1/payroll/runs (HR only)
- GET /api/v1/payroll/runs/{id} (HR only)
- POST /api/v1/payroll/runs (HR only)

---

### PRIORITY 7: REPORTS (MEDIUM - 3 screens)

**Website requires:** Attendance Report, Leave Report, Employee Report

**Current Status:**
- ⚠️ Attendance Report - PARTIAL
  - Date range picker
  - Department filter
  - Show table: Employee, Present, Absent, Leave, Days, %
  - Sort by name/percentage
  - Export CSV/PDF

- ⚠️ Leave Report - PARTIAL
  - Date range picker
  - Leave type filter
  - Status filter
  - Show table: Employee, Leave Type, Days, Status, Approver
  - Export

- ⚠️ Employee Report - PARTIAL
  - Department filter
  - Designation filter
  - Status filter (active/inactive)
  - Show table: Employee Code, Name, Dept, Designation, Join Date
  - Export

**Build Priority:** MEDIUM  
**Effort:** 3 screens × 130 lines = 390 lines  
**Timeline:** 4 hours

**Required Endpoints:**
- GET /api/v1/reports/attendance
- GET /api/v1/reports/leave
- GET /api/v1/reports/employees

---

### PRIORITY 8: DASHBOARD (LOW - 1 screen)

**Website requires:** Master info, Attendance status, Leave balance, Shift display, Charts

**Current Status:**
- ⚠️ Dashboard Home - PARTIAL (86 lines)
  - Master info panel (name, code, department)
  - Today's attendance status
  - Leave balance summary
  - Current shift display
  - Attendance chart (optional, low priority)
  - Quick action buttons

**Build Priority:** LOW (Nice-to-have)  
**Effort:** 1 screen × 200 lines = 200 lines  
**Timeline:** 2 hours

**Required Endpoints:**
- GET /api/v1/dashboard/master-info
- GET /api/v1/attendance/today
- GET /api/v1/leave/balance
- GET /api/v1/shift/my-shift
- GET /api/v1/dashboard/stats (optional)

---

### PRIORITY 9: SETTINGS & PROFILE (LOW - 2 screens)

**Website requires:** My Profile, Security Settings

**Current Status:**
- ⚠️ My Profile - PARTIAL
  - Edit own employee details
  - Photo upload
  - Contact info
  - Personal info
  - Save/Cancel buttons

- ⚠️ Settings - PARTIAL
  - Change password
  - Notification preferences
  - Language selection
  - Theme selection (light/dark)
  - Logout button

**Build Priority:** LOW  
**Effort:** 2 screens × 120 lines = 240 lines  
**Timeline:** 2 hours

---

### PRIORITY 10: NOTIFICATIONS (LOW - 1 screen)

**Website requires:** Notification inbox, Mark as read, Delete

**Current Status:**
- ⚠️ Notifications List - PARTIAL
  - Show all notifications (recent first)
  - Filter by type (leave, attendance, payroll, shift)
  - Mark as read/unread
  - Delete button
  - Tap to navigate to related screen
  - Unread count badge

**Build Priority:** LOW  
**Effort:** 1 screen × 140 lines = 140 lines  
**Timeline:** 1.5 hours

---

### PRIORITY 11: ADMIN FEATURES (NOT FOR MOBILE)

**Status:** NOT REQUIRED for mobile version

**Reason:** Admin features (office settings, hospital management, shift assignment, employee import) are backend operations typically done on desktop.

**Mobile-only admin screens needed:** None (HR/Admin use desktop)

---

## IMPLEMENTATION ROADMAP

### Week 1: CRITICAL (Authentication + Employee Management)
```
Day 1-2: Authentication (4 screens)
  - Forgot Password screen (1.5 hours)
  - Reset Password screen (1.5 hours)
  - Register screen extraction (1 hour)
  - Testing & integration (1 hour)

Day 3-4: Employee Management (7 screens)
  - Employee List screen (2 hours)
  - Employee Create screen (3 hours)
  - Employee Edit screen (2.5 hours)
  - Employee Detail screen (2 hours)
  - Testing (1 hour)

Day 5: Employee Management cont'd
  - Employee Profile (1.5 hours)
  - Reset Password modal (1.5 hours)
  - Login History screen (1.5 hours)
```

### Week 2: HIGH PRIORITY (Attendance + Leave + Shift)
```
Day 1: Attendance (3 screens)
  - Check-out screen (1.5 hours)
  - Attendance History completion (2 hours)
  - Office Settings view (1 hour)

Day 2-3: Leave Management (5 screens)
  - Leave History completion (1.5 hours)
  - Leave Approvals screen (2 hours)
  - Leave Detail completion (1 hour)
  - Leave Balance display (1 hour)
  - Testing (1.5 hours)

Day 4-5: Shift Management (4 screens)
  - Current Shift display (1 hour)
  - Request Change completion (1.5 hours)
  - Shift Approvals screen (2 hours)
  - Shift History completion (1.5 hour)
  - Testing (1 hour)
```

### Week 3: MEDIUM + LOW PRIORITY
```
Day 1-2: Payroll (3 screens)
  - Payslip List (1.5 hours)
  - Payslip Detail (1.5 hours)
  - Payroll Runs (HR) (1.5 hours)
  - Testing (1 hour)

Day 3-4: Reports (3 screens)
  - Attendance Report (1.5 hours)
  - Leave Report (1.5 hours)
  - Employee Report (1.5 hours)
  - Testing (1 hour)

Day 5: Dashboard + Notifications
  - Dashboard completion (2 hours)
  - Notifications completion (1.5 hours)
  - Settings/Profile completion (1 hour)
  - Testing (0.5 hours)
```

---

## SCREEN BUILD CHECKLIST

### Must Build (Critical)
- [ ] Forgot Password Screen
- [ ] Reset Password Screen
- [ ] Employee List Screen
- [ ] Employee Create Screen
- [ ] Employee Edit Screen
- [ ] Employee Detail Screen
- [ ] Employee Profile Screen
- [ ] Reset Password Modal
- [ ] Login History Screen
- [ ] Check-out Screen
- [ ] Leave Approvals Screen
- [ ] Shift Approvals Screen

### Must Complete (Partial)
- [ ] Register Screen (separate from Login)
- [ ] Attendance History Screen
- [ ] Leave History Screen
- [ ] Leave Balance Display
- [ ] Shift Current Display
- [ ] Request Shift Change Screen
- [ ] Shift History Screen
- [ ] Payslip List Screen
- [ ] Payslip Detail Screen
- [ ] Attendance Report Screen
- [ ] Leave Report Screen
- [ ] Employee Report Screen
- [ ] Dashboard Screen
- [ ] Settings Screen
- [ ] Notifications Screen

### Already Complete ✅
- [x] Login Screen
- [x] Check-in Screen

---

## ARCHITECTURE STANDARDS

**Framework:** Flutter with Riverpod state management  
**Navigation:** GoRouter  
**Form Validation:** Form widgets with proper validators  
**Error Handling:** SnackBar + dialog overlays  
**Loading:** Proper loading indicators  
**Offline Support:** Connectivity detection  
**API Integration:** Proper error handling for API calls  
**Responsive Design:** Mobile-first, adapt to tablets  

---

## VALIDATION REQUIREMENTS

### Form Validation
- Email: Must be valid email format
- Password: Min 8 chars, 1 uppercase, 1 digit, 1 special
- Employee Code: Alphanumeric, unique check via API
- Phone: Valid format
- Date: Must be valid date
- Required fields: Cannot be empty

### Date Range Validation
- Start date must be ≤ end date
- Future dates: Cannot apply leave in past
- Leave overlap: Cannot apply overlapping leave

### API Response Validation
- All API responses must be 200 OK
- Error responses must show user-friendly messages
- Timeout handling (5 seconds default)
- Retry logic for failed requests

---

## TESTING CHECKLIST

### Unit Tests
- [ ] All form validators work correctly
- [ ] Date calculations correct
- [ ] Leave balance calculations correct
- [ ] Distance calculations (GPS) correct

### Integration Tests
- [ ] Login flow works end-to-end
- [ ] Leave application flow works
- [ ] Attendance check-in/out flow works
- [ ] Employee CRUD operations work
- [ ] Approval workflows work

### Manual Tests
- [ ] All screens load without errors
- [ ] All buttons are clickable
- [ ] All forms validate correctly
- [ ] All API calls return correct data
- [ ] Error messages display properly
- [ ] Offline mode handles gracefully

---

## ESTIMATED TIMELINE

**Total Screens to Build/Complete:** 27 screens  
**Average per Screen:** 2-3 hours  
**Estimated Total Time:** 65-80 hours  
**With testing/debugging:** ~100 hours

**Realistic Timeline:** 3 weeks (80 hours @ 8 hrs/day)

---

## NEXT STEPS

1. Start with PRIORITY 1 (Authentication) - 4 screens
2. Then PRIORITY 2 (Employee Management) - 7 screens
3. Follow priorities 3-11 in order
4. Each screen should:
   - Match website exact layout
   - Use correct API endpoints
   - Include proper error handling
   - Include loading states
   - Include form validation
   - Include user feedback (success/error)

---

**PHASE 5 Ready to Begin** ✅

**Files Modified:** None (yet - starting implementation)  
**Next Action:** Begin building screens in priority order
