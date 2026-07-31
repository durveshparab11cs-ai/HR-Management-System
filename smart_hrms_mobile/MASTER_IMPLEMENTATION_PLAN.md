# Smart HRMS Mobile - Master Implementation Plan

**Goal:** Build official mobile version of Smart HRMS website  
**Status:** PHASE 1 COMPLETE → PHASE 2 STARTING  
**Architecture:** One Backend, One Database, One Source of Truth  
**Date:** July 28, 2026

---

## PHASE 1 RESULTS - WEBSITE AUDIT COMPLETE ✅

### Website Analysis Summary

**Source:** https://hr-management-system-muqz.onrender.com  
**Framework:** Flask + Bootstrap  
**Database:** PostgreSQL  
**Auth:** JWT + Session  

### Modules Identified (14 Total)

| # | Module | Website Status | API Endpoints | Flutter Status |
|---|--------|----------------|---------------|-----------------|
| 1 | **Authentication** | ✅ Complete | 7 endpoints | 60% (missing forgotpass, lookup) |
| 2 | **Dashboard** | ✅ Complete | 4 endpoints | 40% (missing charts, master info) |
| 3 | **Attendance** | ✅ Complete | 6 endpoints | 60% (missing checkout flow) |
| 4 | **Leave** | ✅ Complete | 11 endpoints | 50% (missing approvals UI) |
| 5 | **Shift** | ✅ Complete | 8 endpoints | 60% (missing approvals UI) |
| 6 | **Payroll** | ✅ Complete | 3 endpoints | 90% (mostly done) |
| 7 | **Reports** | ✅ Complete | 5 endpoints | 70% (UI needs polish) |
| 8 | **Settings** | ✅ Complete | 4 endpoints | 50% (missing preferences) |
| 9 | **Profile** | ✅ Complete | 3 endpoints | 70% (mostly done) |
| 10 | **Notifications** | ✅ Complete | 4 endpoints | 70% (UI incomplete) |
| 11 | **Company** | ✅ Complete | 3 endpoints | 80% (missing holidays) |
| 12 | **Employee** | ✅ Complete | 3 endpoints | 60% |
| 13 | **Admin** | ✅ Complete | 5+ endpoints | 0% (not started) |
| 14 | **Offline Sync** | ⏳ Later | — | 0% (Phase 3+) |

**Total APIs:** 55+  
**Total Screens:** 25+  
**Total Forms:** 15+  

---

## PHASE 2 - GAP ANALYSIS COMPLETE

### Critical Gaps to Close (Priority Order)

#### 🔴 CRITICAL (Blocks Production)

1. **Authentication - Forgot Password Flow**
   - Website: ✅ Complete (2-step reset)
   - Flutter: ❌ Missing UI
   - Action: Create screens + use existing API

2. **Attendance - Check-Out Flow**
   - Website: ✅ Complete (GPS + selfie + logout)
   - Flutter: ❌ Missing check-out
   - Action: Implement full checkout flow

3. **Dashboard - Master Information Panel**
   - Website: ✅ Complete (employee details card)
   - Flutter: ❌ Not showing data
   - Action: Fetch and display master info

4. **Leave - Approvals UI**
   - Website: ✅ Complete (manager approval workflow)
   - Flutter: ❌ Screen exists but incomplete
   - Action: Complete approval/rejection UI

5. **Shift - Approvals UI**
   - Website: ✅ Complete (manager approval workflow)
   - Flutter: ❌ Screen exists but incomplete
   - Action: Complete approval/rejection UI

#### 🟡 IMPORTANT (Improves UX)

6. **Dashboard - Attendance Chart** (6-month visualization)
7. **Leave - Half-day/Early Leave** options
8. **Settings - Preferences** (theme, language, biometric)
9. **Company - Holiday Calendar** display
10. **Employee Code Lookup** (AJAX-like during registration)

#### 🟢 NICE-TO-HAVE

11. **Admin Dashboard** (if time permits)
12. **Offline Mode** (Phase 3+)
13. **Login History** (settings)
14. **Emergency Contacts** (profile)

---

## PHASE 3 - IMPLEMENTATION ROADMAP

### Sprint Breakdown (Week 1)

**Day 1-2: Critical Authentication Fixes**
```
Priority 1: Forgot Password Complete Flow
  - Create ForgotPasswordScreen
  - Create ResetPasswordScreen
  - Use POST /api/v1/auth/forgot-password
  - Use POST /api/v1/auth/reset-password
  - Match website UI/UX exactly
  
Priority 2: Employee Code Lookup
  - Add live search during registration
  - Call GET /api/v1/auth/lookup-employee
  - Display employee name (green box, match website)
  - Show error if not found
  
Priority 3: Password Strength Indicator
  - Add to registration password field
  - Color-coded bar (red→yellow→green)
  - Real-time feedback
```

**Day 2-3: Critical Attendance Fix**
```
Priority 1: Complete Check-Out Flow
  - Create CheckOutScreen
  - Upload checkout selfie: POST /api/v1/attendance/upload-checkout-photo
  - Submit check-out: POST /api/v1/attendance/check-out {lat,lng}
  - Show working hours on dashboard
  - Match website checkout experience
```

**Day 3-4: Dashboard Polish**
```
Priority 1: Master Information Panel
  - Fetch: GET /api/v1/employees/me
  - Display all fields:
    - Code, Name, Department, Designation
    - DOJ, Email, Phone, Manager, Location
  - Format dates as "DD MMM YYYY"
  - Match website card layout
  
Priority 2: 6-Month Attendance Chart
  - Fetch: GET /api/v1/dashboard/chart
  - Create bar chart (fl_chart)
  - Show: present (green), absent (red), on_leave (yellow)
  - Legend + labels
```

**Day 4-5: Approval Workflows**
```
Priority 1: Leave Approvals Complete
  - Show all pending leave requests
  - Display: employee, dates, reason
  - Approve button → POST /api/v1/leave/{id}/approve
  - Reject button → POST /api/v1/leave/{id}/reject
  - Reject requires MANDATORY comment
  - Refresh list after action
  
Priority 2: Shift Approvals Complete
  - Show all pending shift requests
  - Display: employee, current/requested shift, dates
  - Approve/Reject same pattern
  - Mandatory comment on reject
```

**Day 5+: Enhancements (If Time)**
```
- Leave half-day/early options
- Settings preferences
- Holiday calendar
- Login history
- Polish animations
```

---

## DETAILED IMPLEMENTATION CHECKLIST

### Module 1: Authentication ✅ PARTIAL → COMPLETE

**Screens to Complete:**
- [ ] Forgot Password Screen (1 screen)
- [ ] Reset Password Screen (1 screen)
- [ ] Registration with lookup (enhance existing)

**APIs to Use:**
- [ ] POST /api/v1/auth/forgot-password
- [ ] POST /api/v1/auth/reset-password
- [ ] GET /api/v1/auth/lookup-employee

**Database Tables:**
- users (no schema changes needed)

**UI Components:**
- [ ] Password reset form
- [ ] Employee name display box
- [ ] Password strength indicator
- [ ] Form validation matching website

**Tests:**
- [ ] Unit tests for form validation
- [ ] Integration test: forgot password flow
- [ ] Integration test: lookup employee
- [ ] flutter test (all 78+ tests pass)

---

### Module 2: Dashboard ✅ PARTIAL → COMPLETE

**Screens to Complete:**
- [ ] Dashboard with master info panel
- [ ] Dashboard with 6-month chart

**APIs to Use:**
- [ ] GET /api/v1/dashboard (get all data)
- [ ] GET /api/v1/employees/me (master info)
- [ ] GET /api/v1/dashboard/chart (attendance history)

**Database Tables:**
- employees, attendance, leave_applications

**UI Components:**
- [ ] Master information card panel
- [ ] Bar chart with 6 months
- [ ] Color-coded attendance data
- [ ] Responsive layout for mobile

**Tests:**
- [ ] Verify all fields displayed
- [ ] Chart renders correctly
- [ ] Data matches website
- [ ] Responsive on different screen sizes

---

### Module 3: Attendance ✅ PARTIAL → COMPLETE

**Screens to Complete:**
- [ ] Check-Out Screen (new)
- [ ] Enhanced Check-In with GPS

**APIs to Use:**
- [ ] GET /api/v1/attendance/office (bounds)
- [ ] POST /api/v1/attendance/upload-photo (check-in selfie)
- [ ] POST /api/v1/attendance/check-in (GPS)
- [ ] POST /api/v1/attendance/upload-checkout-photo (checkout selfie)
- [ ] POST /api/v1/attendance/check-out (checkout GPS)

**Database Tables:**
- attendance, office_settings

**UI Components:**
- [ ] Checkout selfie capture
- [ ] GPS distance verification
- [ ] Working hours display
- [ ] Error messages matching website

**Tests:**
- [ ] Check-in + check-out workflow
- [ ] GPS validation
- [ ] Photo upload
- [ ] Distance calculation
- [ ] Distance error handling

---

### Module 4: Leave ✅ PARTIAL → COMPLETE

**Screens to Complete:**
- [ ] Leave Approvals (complete UI)
- [ ] Add half-day option
- [ ] Add early leave option

**APIs to Use:**
- [ ] GET /api/v1/leave/approvals
- [ ] POST /api/v1/leave/{id}/approve
- [ ] POST /api/v1/leave/{id}/reject (mandatory comment)
- [ ] POST /api/v1/leave/halfday
- [ ] POST /api/v1/leave/early

**Database Tables:**
- leave_applications, leave_types

**UI Components:**
- [ ] Approval card (pending leaves)
- [ ] Approve/Reject buttons
- [ ] Comment field (mandatory for reject)
- [ ] Half-day/Early radio buttons on form

**Tests:**
- [ ] Approval workflow
- [ ] Mandatory comment validation
- [ ] Half-day leave creation
- [ ] Early leave creation
- [ ] List refresh after action

---

### Module 5: Shift ✅ PARTIAL → COMPLETE

**Screens to Complete:**
- [ ] Shift Approvals (complete UI)

**APIs to Use:**
- [ ] GET /api/v1/shifts/approvals
- [ ] POST /api/v1/shifts/{id}/approve
- [ ] POST /api/v1/shifts/{id}/reject (mandatory comment)

**Database Tables:**
- shifts, shift_assignments

**UI Components:**
- [ ] Approval card (pending shifts)
- [ ] Approve/Reject buttons
- [ ] Comment field
- [ ] Current/Requested shift display

**Tests:**
- [ ] Approval workflow
- [ ] Comment validation
- [ ] List refresh

---

### Module 6-14: Ensure Completeness

| Module | Status | Action |
|--------|--------|--------|
| Payroll | 90% | Test all features, ensure API working |
| Reports | 70% | UI polish, verify data matches website |
| Settings | 50% | Add preferences, password change |
| Profile | 70% | Verify all fields, photo upload |
| Notifications | 70% | Notification center UI |
| Company | 80% | Add holiday calendar |
| Employee | 60% | Ensure master data display |
| Admin | 0% | If time permits, implement dashboard |

---

## BUILD VERIFICATION AFTER EACH PHASE

```bash
# After every feature completion
flutter clean
flutter pub get
dart run build_runner build --delete-conflicting-outputs
flutter analyze           # Must be: 0 errors
flutter test             # Must be: 78+ tests pass
flutter build apk --debug
flutter build apk --release
```

---

## TESTING STRATEGY

### Unit Tests
- Form validation
- Business logic
- API error handling
- JWT token refresh

### Widget Tests
- Screen UI rendering
- Button interactions
- Form submission
- List loading/empty states

### Integration Tests
- End-to-end workflows
- API integration
- Database consistency
- Navigation flows

### Manual Tests
- Compare with website side-by-side
- Test on real device (phone)
- GPS functionality
- Photo upload/capture
- Network error handling

---

## SUCCESS CRITERIA

A module is COMPLETE when:
✅ UI matches website pixel-perfect  
✅ Navigation matches website  
✅ Uses production API (/api/v1/*)  
✅ Uses production PostgreSQL  
✅ CRUD operations work  
✅ Validation matches website exactly  
✅ Permissions honored  
✅ Responsive on mobile  
✅ No crashes or exceptions  
✅ No placeholder or fake data  
✅ All tests pass  
✅ flutter analyze = 0 errors  
✅ Manually verified against website  

---

## FINAL COMPLETION CRITERIA

Project is COMPLETE when:

1. ✅ All 14 modules implemented
2. ✅ 100% feature parity with website
3. ✅ All 55+ API endpoints working
4. ✅ All validations match website
5. ✅ All permissions enforced
6. ✅ All dashboards showing
7. ✅ All reports working
8. ✅ Offline mode (Phase 3+)
9. ✅ All tests pass (100+)
10. ✅ flutter build apk succeeds
11. ✅ flutter analyze = 0 errors
12. ✅ Manual verification complete
13. ✅ No crashes on device
14. ✅ Production-ready

**When all criteria met = Ready for Production Deployment**

---

## FILES TO MODIFY (Expected)

**Auth Module:**
- lib/features/auth/presentation/screens/forgot_password_screen.dart (create)
- lib/features/auth/presentation/screens/reset_password_screen.dart (create)
- lib/features/auth/presentation/providers/auth_provider.dart (enhance)
- lib/features/auth/data/repository/auth_repository.dart (add methods)

**Dashboard Module:**
- lib/features/dashboard/presentation/screens/home_screen.dart (enhance)
- lib/features/dashboard/data/models/dashboard_model.dart (add fields)
- lib/features/dashboard/presentation/widgets/attendance_chart.dart (create)

**Attendance Module:**
- lib/features/attendance/presentation/screens/check_out_screen.dart (create)
- lib/features/attendance/data/repository/attendance_repository.dart (add checkout)

**Leave Module:**
- lib/features/leave/presentation/screens/leave_approvals_screen.dart (complete)
- lib/features/leave/presentation/screens/apply_leave_screen.dart (add options)
- lib/features/leave/data/repository/leave_repository.dart (enhance)

**Shift Module:**
- lib/features/shift/presentation/screens/shift_approvals_screen.dart (complete)
- lib/features/shift/data/repository/shift_repository.dart (enhance)

[And more as implementation progresses...]

---

## TIMELINE

**Week 1 (Starting Now):**
- Day 1-2: Auth + Forgot Password
- Day 2-3: Attendance Check-Out
- Day 3-4: Dashboard Master Info + Chart
- Day 4-5: Leave/Shift Approvals
- Day 5: Enhancements + Testing

**Week 2:**
- Polish all modules
- Add missing features
- Performance optimization
- Comprehensive testing

**Week 3:**
- Admin features (if time)
- Offline sync (Phase 3+)
- Final testing
- Production readiness

---

## NEXT ACTION

**START MODULE 1: AUTHENTICATION COMPLETE**

Current work:
1. Create ForgotPasswordScreen
2. Create ResetPasswordScreen  
3. Add Employee Code lookup
4. Add password strength indicator
5. Verify all UIs match website
6. Test authentication flow end-to-end

Estimated completion: 2 days

---

**Document Generated:** July 28, 2026  
**Architect:** Lead Flutter Engineer  
**Status:** Ready for Phase 3 Implementation

