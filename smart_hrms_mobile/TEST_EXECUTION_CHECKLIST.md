# Test Execution Checklist - Phase 4 Task 9

## Pre-Test Setup

### Environment Verification
- [ ] Flutter SDK installed (3.19.0+)
- [ ] Dart SDK available
- [ ] Android SDK configured
- [ ] Xcode installed (macOS only)
- [ ] Git repository cloned
- [ ] Dependencies installed (`flutter pub get`)

### Repository Configuration
- [ ] `.github/workflows/` directory exists
- [ ] `test/` directory structure created
- [ ] `scripts/check_coverage.py` available
- [ ] `.gitignore` includes test artifacts
- [ ] Secrets configured in GitHub

### Local Environment
```bash
# Verify Flutter setup
flutter doctor

# Verify Dart
dart --version

# Clean build
flutter clean
flutter pub get
```

---

## Unit Test Execution

### Leave Module Tests
**File**: `test/features/leave/data/`
```bash
flutter test test/features/leave/data/models/leave_model_test.dart
flutter test test/features/leave/data/repository/leave_repository_test.dart
```
- [ ] Models: LeaveRequest, LeaveApproval
- [ ] Repository: applyLeave, getLeaveRequests, approveLeave
- [ ] Error handling, pagination, status validation
- [ ] Expected: 25+ test cases, all passing

### Shift Module Tests
**File**: `test/features/shift/data/`
```bash
flutter test test/features/shift/data/models/shift_model_test.dart
flutter test test/features/shift/data/repository/shift_repository_test.dart
```
- [ ] Models: Shift, ShiftChangeRequest, ShiftHistory
- [ ] Repository: getMyShift, requestShiftChange, approveShiftChange
- [ ] Status transitions, change request workflow
- [ ] Expected: 28+ test cases, all passing

### Payroll Module Tests
**File**: `test/features/payroll/data/`
```bash
flutter test test/features/payroll/data/models/payroll_model_test.dart
flutter test test/features/payroll/data/repository/payroll_repository_test.dart
```
- [ ] Models: SalarySlip, PayrollSummary
- [ ] Repository: getPayslips, downloadPayslip, sharePayslip
- [ ] Salary calculations, tax calculations
- [ ] Expected: 22+ test cases, all passing

### Reports Module Tests
**File**: `test/features/reports/data/`
```bash
flutter test test/features/reports/data/models/report_model_test.dart
flutter test test/features/reports/data/repository/report_repository_test.dart
```
- [ ] Models: AttendanceReport, LeaveAnalytics, PayrollReport
- [ ] Repository: getDashboardSummary, getAttendanceReport
- [ ] Report generation, export functionality
- [ ] Expected: 20+ test cases, all passing

### Attendance Module Tests
**File**: `test/features/attendance/data/`
```bash
flutter test test/features/attendance/data/models/attendance_model_test.dart
flutter test test/features/attendance/data/repository/attendance_repository_test.dart
```
- [ ] Models: Attendance, CheckInCheckOut, GeoLocation
- [ ] Repository: checkIn, checkOut, getTodayAttendance
- [ ] Geofence validation, location handling
- [ ] Expected: 25+ test cases, all passing

### Run All Unit Tests
```bash
flutter test test/features/ --no-pub
```
- [ ] Leave module: 25+ passing
- [ ] Shift module: 28+ passing
- [ ] Payroll module: 22+ passing
- [ ] Reports module: 20+ passing
- [ ] Attendance module: 25+ passing
- [ ] **Total**: 150+ tests passing
- [ ] **Expected Duration**: 2-3 minutes

---

## Widget Test Execution

### CheckInScreen Tests
**File**: `test/features/attendance/presentation/screens/check_in_screen_test.dart`
```bash
flutter test test/features/attendance/presentation/screens/check_in_screen_test.dart
```
- [ ] Widget rendering
- [ ] Button interactions
- [ ] Loading states
- [ ] Error message display
- [ ] Expected: 12+ tests passing

### LeaveListScreen Tests
**File**: `test/features/leave/presentation/screens/leave_list_screen_test.dart`
```bash
flutter test test/features/leave/presentation/screens/leave_list_screen_test.dart
```
- [ ] List display
- [ ] FAB functionality
- [ ] Filtering options
- [ ] Navigation
- [ ] Expected: 15+ tests passing

### MyShiftScreen Tests
**File**: `test/features/shift/presentation/screens/my_shift_screen_test.dart`
```bash
flutter test test/features/shift/presentation/screens/my_shift_screen_test.dart
```
- [ ] Shift card display
- [ ] Timing information
- [ ] Change request button
- [ ] History section
- [ ] Expected: 16+ tests passing

### PayrollListScreen Tests
**File**: `test/features/payroll/presentation/screens/payroll_list_screen_test.dart`
```bash
flutter test test/features/payroll/presentation/screens/payroll_list_screen_test.dart
```
- [ ] Payslip list display
- [ ] Amount display
- [ ] Status badges
- [ ] Pagination
- [ ] Expected: 18+ tests passing

### ReportsDashboardScreen Tests
**File**: `test/features/reports/presentation/screens/reports_dashboard_screen_test.dart`
```bash
flutter test test/features/reports/presentation/screens/reports_dashboard_screen_test.dart
```
- [ ] Summary cards
- [ ] Report options
- [ ] Date range picker
- [ ] Navigation
- [ ] Expected: 14+ tests passing

### Run All Widget Tests
```bash
flutter test test/features/*/presentation/screens/
```
- [ ] All screens rendering correctly
- [ ] Interactions working
- [ ] Navigation functional
- [ ] **Total**: 75+ tests passing
- [ ] **Expected Duration**: 3-4 minutes

---

## Security Test Execution

### Authentication Security Tests
**File**: `test/security/auth_security_test.dart`
```bash
flutter test test/security/auth_security_test.dart
```
- [ ] Token storage in secure storage
- [ ] Password not stored
- [ ] Brute force prevention
- [ ] Rate limiting
- [ ] Session management
- [ ] **Tests**: 30+ passing

### Data Encryption Tests
**File**: `test/security/data_encryption_test.dart`
```bash
flutter test test/security/data_encryption_test.dart
```
- [ ] Encryption/decryption
- [ ] Token encryption
- [ ] Personal data protection
- [ ] HMAC verification
- [ ] Tamper detection
- [ ] **Tests**: 28+ passing

### Input Validation Tests
**File**: `test/security/input_validation_test.dart`
```bash
flutter test test/security/input_validation_test.dart
```
- [ ] Email validation
- [ ] Password strength
- [ ] XSS prevention
- [ ] SQL injection prevention
- [ ] Command injection prevention
- [ ] **Tests**: 27+ passing

### Run All Security Tests
```bash
flutter test test/security/
```
- [ ] All security tests passing
- [ ] No vulnerabilities found
- [ ] **Total**: 85+ tests passing
- [ ] **Expected Duration**: 1-2 minutes

---

## Offline Functionality Tests

### Run Offline Tests
**File**: `test/offline/offline_functionality_test.dart`
```bash
flutter test test/offline/offline_functionality_test.dart
```
- [ ] Attendance data caching
- [ ] Leave data caching
- [ ] Shift data caching
- [ ] Payroll data caching
- [ ] Sync queue management
- [ ] Cache expiry handling
- [ ] Data consistency
- [ ] **Tests**: 45+ passing
- [ ] **Expected Duration**: 1-2 minutes

---

## GPS & Location Tests

### Run GPS Tests
**File**: `test/gps/location_service_test.dart`
```bash
flutter test test/gps/location_service_test.dart
```
- [ ] Permission handling
- [ ] Location retrieval
- [ ] Geofencing
- [ ] Accuracy validation
- [ ] Background tracking
- [ ] Privacy protection
- [ ] **Tests**: 35+ passing
- [ ] **Expected Duration**: 1-2 minutes

---

## Coverage Report Generation

### Generate Coverage
```bash
flutter test --coverage --no-pub
```
- [ ] LCOV file generated at `coverage/lcov.info`
- [ ] Coverage report created

### Check Coverage Threshold
```bash
python3 scripts/check_coverage.py --threshold 75
```
- [ ] Output shows coverage percentage
- [ ] Coverage >= 75% (Target: Pass)
- [ ] All modules above threshold

### View HTML Coverage Report
```bash
# macOS
open coverage/index.html

# Linux
xdg-open coverage/index.html

# Windows
start coverage\index.html
```
- [ ] HTML report opens
- [ ] Coverage visualization clear
- [ ] Drill-down into modules possible
- [ ] Line-by-line coverage visible

### Coverage Breakdown Verification
- [ ] Leave module: 82% coverage
- [ ] Shift module: 78% coverage
- [ ] Payroll module: 75% coverage
- [ ] Reports module: 76% coverage
- [ ] Attendance module: 79% coverage
- [ ] Security module: 90% coverage
- [ ] Offline module: 88% coverage
- [ ] GPS module: 85% coverage
- [ ] **Overall**: 80% minimum

---

## Code Analysis

### Run Static Analysis
```bash
flutter analyze
```
- [ ] No errors reported
- [ ] No critical warnings
- [ ] Code follows conventions

### Check Code Format
```bash
dart format --set-exit-if-changed .
```
- [ ] All files properly formatted
- [ ] No formatting issues

---

## CI/CD Pipeline Verification

### Configure GitHub Secrets
GitHub Settings > Secrets > Actions:
- [ ] `SLACK_WEBHOOK` - Slack notification URL
- [ ] `FIREBASE_PROJECT_ID` - Firebase project
- [ ] `FIREBASE_ANDROID_APP_ID` - Android app ID
- [ ] `FIREBASE_TOKEN` - Firebase CLI token
- [ ] `KEYSTORE_PROPERTIES` - Android keystore config
- [ ] `RELEASE_KEYSTORE` - Keystore file (base64)

### Test Workflow Execution
```bash
# Manually trigger test workflow
gh workflow run test.yml

# Monitor execution
gh run list
gh run view <run-id>
```
- [ ] Workflow triggers successfully
- [ ] All jobs run
- [ ] Tests execute in CI environment
- [ ] Coverage report generated
- [ ] Slack notification sent

### Build Workflow Verification
```bash
# Check build workflow exists
gh workflow list
```
- [ ] Build workflow available
- [ ] Triggers on tags
- [ ] Manual dispatch available

---

## Local Build Verification

### Build APK
```bash
flutter build apk --release
```
- [ ] APK builds successfully
- [ ] Output: `build/app/outputs/apk/release/app-release.apk`
- [ ] APK size < 100MB
- [ ] Duration: 5-8 minutes

### Build App Bundle
```bash
flutter build appbundle --release
```
- [ ] App Bundle builds successfully
- [ ] Output: `build/app/outputs/bundle/release/app-release.aab`
- [ ] Bundle size acceptable

---

## Integration Testing (Optional)

### Build Debug APK for Testing
```bash
flutter build apk --debug
```
- [ ] Debug APK builds
- [ ] Can be deployed to emulator/device

### Deploy to Emulator
```bash
# Start emulator
emulator -avd <device-name>

# Install APK
adb install build/app/outputs/apk/debug/app-debug.apk

# Run app
adb shell am start -n com.example.smart_hrms/.MainActivity
```
- [ ] App installs on emulator
- [ ] App launches without crashes
- [ ] Basic functionality works

---

## Test Results Documentation

### Create Test Summary
```
Total Test Cases Run:     1,200+
Unit Tests:               150+  ✅ Pass
Widget Tests:             75+   ✅ Pass
Security Tests:           85+   ✅ Pass
Offline Tests:            45+   ✅ Pass
GPS Tests:                35+   ✅ Pass

Code Coverage:            80% (Target: 75%) ✅
Static Analysis:          Pass ✅
Code Format:              Pass ✅

Build Artifacts:
- APK Size:              65-85 MB (Target: < 100MB) ✅
- Build Duration:        5-8 minutes

CI/CD Pipeline:           Operational ✅
```

### Document Test Failures (if any)
- [ ] Identify failing test
- [ ] Analyze root cause
- [ ] Fix code or test
- [ ] Re-run tests
- [ ] Verify fix

---

## Final Verification Checklist

### Before Marking Complete
- [ ] All 150+ unit tests passing
- [ ] All 75+ widget tests passing
- [ ] All 85+ security tests passing
- [ ] All 45+ offline tests passing
- [ ] All 35+ GPS tests passing
- [ ] Code coverage >= 75%
- [ ] Static analysis passing
- [ ] Code formatting correct
- [ ] APK builds successfully
- [ ] APK size < 100MB
- [ ] GitHub workflows configured
- [ ] All secrets configured
- [ ] CI/CD pipeline tested
- [ ] Slack notifications working
- [ ] Documentation complete

### Sign-Off
- [ ] All tests passing
- [ ] Coverage adequate
- [ ] Ready for production
- [ ] Documentation reviewed
- [ ] Team approval obtained

---

## Quick Reference Commands

```bash
# Install dependencies
flutter pub get

# Run all tests
flutter test

# Run with coverage
flutter test --coverage

# Check coverage
python3 scripts/check_coverage.py --threshold 75

# Code analysis
flutter analyze

# Code format
dart format .

# Build APK
flutter build apk --release

# Build App Bundle
flutter build appbundle --release

# Check CI/CD workflows
gh workflow list

# Trigger test workflow
gh workflow run test.yml

# View test results
gh run list
```

---

## Support Resources

- **Flutter Testing**: https://flutter.dev/docs/testing
- **GitHub Actions**: https://docs.github.com/en/actions
- **Mockito**: https://pub.dev/packages/mockito
- **Codecov**: https://codecov.io
- **Firebase**: https://firebase.google.com/docs

---

**Document Version**: 1.0  
**Last Updated**: July 2024  
**Status**: Final
