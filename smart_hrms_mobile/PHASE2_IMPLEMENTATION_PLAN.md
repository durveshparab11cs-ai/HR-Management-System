# Smart HRMS Mobile - Phase 2 Implementation Plan

**Target:** Website Feature Parity  
**Duration:** 1 Week  
**Status:** READY TO START

---

## CRITICAL FEATURES TO IMPLEMENT

### Feature 1: Authentication - Forgot Password Flow
**Website:** Login page has "Forgot password?" link  
**Current Status:** Link exists but UI incomplete  
**Priority:** CRITICAL

**Tasks:**
- [ ] Create `ForgotPasswordScreen` UI matching website
- [ ] POST /auth/forgot-password endpoint call
- [ ] Reset token verification
- [ ] New password entry form
- [ ] POST /auth/reset-password endpoint call
- [ ] Success/error messaging

**Files to Create/Modify:**
- `lib/features/auth/presentation/screens/forgot_password_screen.dart` ✓ EXISTS - NEEDS UI
- `lib/features/auth/presentation/providers/forgot_password_provider.dart` - CREATE
- `lib/features/auth/data/repository/auth_repository.dart` - ADD METHODS

---

### Feature 2: Authentication - Employee Code Lookup
**Website:** Registration form looks up employee name via AJAX as user types  
**Current Status:** NOT IMPLEMENTED  
**Priority:** CRITICAL

**Tasks:**
- [ ] Create lookup endpoint call in AuthRepository
- [ ] Add debounced search to registration form
- [ ] Display employee name in green box (matching website)
- [ ] Show error if employee not found
- [ ] Prevent form submission if lookup failed

**Files to Modify:**
- `lib/features/auth/data/repository/auth_repository.dart` - ADD lookupEmployee()
- `lib/features/auth/presentation/screens/login_screen.dart` - ADD lookup widget

---

### Feature 3: Attendance - Check-Out Flow + Selfie
**Website:** Complete checkout requires selfie upload + GPS  
**Current Status:** Check-in works, checkout NOT IMPLEMENTED  
**Priority:** CRITICAL

**Tasks:**
- [ ] Add checkout button to dashboard
- [ ] Reuse check-in selfie flow for checkout
- [ ] Upload checkout selfie: POST /attendance/upload-checkout-photo
- [ ] Record check-out: POST /attendance/check-out with GPS
- [ ] Show working hours on dashboard

**Files to Create/Modify:**
- `lib/features/attendance/presentation/screens/check_out_screen.dart` - CREATE
- `lib/features/attendance/data/repository/attendance_repository.dart` - ADD checkOut()
- `lib/features/dashboard/presentation/screens/home_screen.dart` - ADD checkout button

---

### Feature 4: Dashboard - Master Information Panel
**Website:** Shows employee master data (department, designation, DOJ, manager, location, etc.)  
**Current Status:** Card exists but no data  
**Priority:** CRITICAL

**Tasks:**
- [ ] Call GET /employees/me to fetch master info
- [ ] Display all fields matching website exactly:
  - Employee Code, Name, Department, Designation
  - Date of Joining, Official Email, Phone Number
  - Reporting Manager Code & Name
  - Location, Employment Status
- [ ] Format dates as "DD MMM YYYY"
- [ ] Use proper typography matching website

**Files to Modify:**
- `lib/features/dashboard/data/models/dashboard_model.dart` - ADD master info fields
- `lib/features/dashboard/presentation/screens/home_screen.dart` - ADD panel

---

### Feature 5: Dashboard - 6-Month Attendance Chart
**Website:** Bar/line chart showing 6 months of attendance (present/absent/on_leave)  
**Current Status:** NOT VISUALIZED  
**Priority:** IMPORTANT

**Tasks:**
- [ ] Call GET /dashboard/chart to fetch data
- [ ] Add chart package (fl_chart already in pubspec)
- [ ] Create BarChart widget showing months on X-axis
- [ ] Display present (green), absent (red), on_leave (yellow)
- [ ] Add legend and labels

**Files to Create/Modify:**
- `lib/features/dashboard/presentation/widgets/attendance_chart.dart` - CREATE
- `lib/features/dashboard/presentation/screens/home_screen.dart` - ADD chart

---

### Feature 6: Leave - Approvals UI Complete
**Website:** Manager sees leave requests, can approve/reject  
**Current Status:** PARTIAL - needs full approval/rejection flow  
**Priority:** CRITICAL

**Tasks:**
- [ ] Create detailed leave approval card showing:
  - Employee name, employee code
  - Leave type, date range, duration
  - Reason
  - Reporting manager
- [ ] Add approve button
- [ ] Add reject button with comment field
- [ ] **Make comment MANDATORY for rejection** (match website rule)
- [ ] Show success/error after action
- [ ] Refresh list after approval/rejection

**Files to Create/Modify:**
- `lib/features/leave/presentation/screens/leave_approvals_screen.dart` - COMPLETE
- `lib/features/leave/data/repository/leave_repository.dart` - ADD methods

---

### Feature 7: Shift - Approvals UI Complete
**Website:** Manager sees shift change requests, can approve/reject  
**Current Status:** PARTIAL  
**Priority:** CRITICAL

**Tasks:**
- [ ] Create detailed shift approval card showing:
  - Employee name, employee code
  - Current shift, requested shift
  - Effective date, reason
- [ ] Add approve button
- [ ] Add reject button with comment field
- [ ] Make comment MANDATORY for rejection
- [ ] Refresh list after action

**Files to Create/Modify:**
- `lib/features/shift/presentation/screens/shift_approvals_screen.dart` - COMPLETE
- `lib/features/shift/data/repository/shift_repository.dart` - ADD methods

---

### Feature 8: Leave - Half-Day and Early Leave Options
**Website:** Leave form has options for half-day and early leave  
**Current Status:** NOT IMPLEMENTED  
**Priority:** IMPORTANT

**Tasks:**
- [ ] Add radio buttons to leave form: Full Day / Half Day / Early Leave
- [ ] Adjust date pickers based on selection
- [ ] Call appropriate endpoints:
  - Full Day: POST /leave/apply
  - Half Day: POST /leave/halfday
  - Early: POST /leave/early
- [ ] Validate requests before submission

**Files to Modify:**
- `lib/features/leave/presentation/screens/apply_leave_screen.dart` - ADD options

---

### Feature 9: Password Strength Indicator
**Website:** Registration shows password strength as user types  
**Current Status:** NOT IMPLEMENTED  
**Priority:** IMPORTANT

**Tasks:**
- [ ] Add strength bar to password field
- [ ] Calculate strength based on:
  - Length ≥ 8: +1
  - Length ≥ 12: +1
  - Has uppercase + lowercase: +1
  - Has digits + special chars: +1
- [ ] Display color-coded bar: Red (weak) → Yellow (fair) → Green (strong)
- [ ] Show strength label

**Files to Modify:**
- `lib/features/auth/presentation/screens/login_screen.dart` - ADD widget

---

### Feature 10: Settings - Preferences (Theme, Language, Biometric)
**Website:** Settings has preferences for theme, language, notifications, biometric  
**Current Status:** Screen exists but NOT FUNCTIONAL  
**Priority:** IMPORTANT

**Tasks:**
- [ ] Add theme toggle (light/dark)
- [ ] Add language selector (if backend supports)
- [ ] Add notification toggle
- [ ] Add biometric login toggle (optional)
- [ ] Call PUT /settings/preferences to save
- [ ] Load saved preferences on app start

**Files to Create/Modify:**
- `lib/features/settings/presentation/screens/settings_screen.dart` - ADD toggles
- `lib/features/settings/data/models/preferences_model.dart` - CREATE
- `lib/core/providers/settings_provider.dart` - CREATE

---

### Feature 11: Settings - Login History
**Website:** Settings shows past login sessions  
**Current Status:** NOT IMPLEMENTED  
**Priority:** NICE-TO-HAVE

**Tasks:**
- [ ] Call GET /settings/login-history
- [ ] Display list of past logins:
  - Date/time, Device, IP address, Location
- [ ] Add log out from other sessions option

**Files to Create:**
- `lib/features/settings/presentation/screens/login_history_screen.dart` - CREATE

---

### Feature 12: Company - Holiday Calendar
**Website:** Admin can view company holidays  
**Current Status:** NOT IMPLEMENTED  
**Priority:** IMPORTANT

**Tasks:**
- [ ] Create Holiday Calendar screen
- [ ] Fetch holidays from backend
- [ ] Display as calendar view
- [ ] Show holiday names and dates
- [ ] Integration with attendance (mark as holiday)

**Files to Create:**
- `lib/features/company/presentation/screens/holiday_calendar_screen.dart` - CREATE

---

## IMPLEMENTATION ORDER

### Week 1, Day 1-2: Critical Auth
1. Forgot Password Flow (Feature 1)
2. Employee Code Lookup (Feature 2)
3. Password Strength Indicator (Feature 9)

### Week 1, Day 2-3: Critical Attendance
4. Check-Out Flow + Selfie (Feature 3)

### Week 1, Day 3-4: Dashboard
5. Master Information Panel (Feature 4)
6. Attendance Chart (Feature 5)

### Week 1, Day 4-5: Approvals
7. Leave Approvals Complete (Feature 6)
8. Shift Approvals Complete (Feature 7)

### Week 1, Day 5+: Polish
9. Half-Day/Early Leave (Feature 8)
10. Settings Preferences (Feature 10)
11. Holiday Calendar (Feature 12)
12. Login History (Feature 11) - If time permits

---

## QUALITY CHECKLIST

For each feature implemented:
- [ ] UI matches website exactly
- [ ] All validations match website
- [ ] Error messages match website
- [ ] API calls use correct endpoints
- [ ] Loading states shown
- [ ] Success/error messages shown
- [ ] Responsive on mobile
- [ ] Tests pass: `flutter test`
- [ ] No warnings: `flutter analyze`
- [ ] Builds successfully: `flutter build apk --debug`

---

## BUILD VERIFICATION

After each feature:
```bash
flutter clean
flutter pub get
dart run build_runner build --delete-conflicting-outputs
flutter analyze        # 0 errors
flutter test           # all pass
flutter build apk --debug
```

---

## SUCCESS CRITERIA

✓ All 11 feature modules working  
✓ Website and Flutter app have feature parity  
✓ UI matches website exactly  
✓ All backend APIs called correctly  
✓ All validations enforced  
✓ No crashes or errors  
✓ All tests pass  
✓ APK builds successfully  

