# Module 1: Authentication - Complete Implementation Guide

**Status:** PHASE 3 - Module 1 Starting  
**Priority:** CRITICAL (Blocks all other modules)  
**Estimated Duration:** 2 days  
**Files to Create/Modify:** 8 files

---

## AUTHENTICATION FEATURES TO IMPLEMENT

### 1. Forgot Password Complete Flow ⚠️ CRITICAL

**Website Pattern:**
```
User on login page → Click "Forgot password?" link
  ↓
Enter Employee Code
  ↓
API validates code exists
  ↓
System sends reset token (email/display)
  ↓
User enters new password + confirm
  ↓
API validates and updates password
  ↓
Redirect to login (success)
```

**Screens to Create:**

#### Screen 1: ForgotPasswordScreen (1/2)
```
File: lib/features/auth/presentation/screens/forgot_password_screen.dart

UI:
┌─────────────────────────────────────┐
│  ← Forgot Password                  │
├─────────────────────────────────────┤
│                                     │
│  Enter your Employee Code           │
│  ┌──────────────────────────────┐   │
│  │ E-2510016                    │   │
│  └──────────────────────────────┘   │
│                                     │
│  ┌──────────────────────────────┐   │
│  │ Send Reset Link              │   │
│  └──────────────────────────────┘   │
│                                     │
│  [Loading indicator during submit]  │
│  [Error message if code invalid]    │
│  [Success: "Link sent to email"]    │
│                                     │
│  Don't have account? Register       │
│  Back to Login                      │
└─────────────────────────────────────┘

Form Fields:
- Employee Code (text input)

Buttons:
- Send Reset Link (primary)
- Back to Login (secondary)

States:
- Empty
- Loading
- Error (code not found)
- Success (link sent)
```

**Implementation:**
```dart
class ForgotPasswordScreen extends ConsumerStatefulWidget {
  @override
  ConsumerState<ForgotPasswordScreen> createState() => _ForgotPasswordScreenState();
}

class _ForgotPasswordScreenState extends ConsumerState<ForgotPasswordScreen> {
  final _codeController = TextEditingController();
  bool _isLoading = false;
  String? _error;
  bool _success = false;

  @override
  Widget build(BuildContext context) {
    // Form with employee code input
    // Submit button calls:
    //   ref.read(authRepository).forgotPassword(_codeController.text)
    // On success: show message + navigate or clear
    // On error: show error message
  }
}
```

**API Call:**
```dart
Future<Either<Failure, String>> forgotPassword(String employeeCode)
// Returns: reset token or error
// Endpoint: POST /api/v1/auth/forgot-password
// Body: { "employee_code": "E-2510016" }
// Response: { "reset_token": "abc123xyz..." }
```

---

#### Screen 2: ResetPasswordScreen (2/2)
```
File: lib/features/auth/presentation/screens/reset_password_screen.dart

UI:
┌─────────────────────────────────────┐
│  ← Set New Password                 │
├─────────────────────────────────────┤
│                                     │
│  New Password                       │
│  ┌──────────────────────────────┐   │
│  │ ••••••••••                 👁 │   │
│  └──────────────────────────────┘   │
│  [Strength bar: Red → Yellow → Green]│
│  [Strength label: "Good"]            │
│                                     │
│  Confirm Password                   │
│  ┌──────────────────────────────┐   │
│  │ ••••••••••                 👁 │   │
│  └──────────────────────────────┘   │
│                                     │
│  ┌──────────────────────────────┐   │
│  │ Reset Password               │   │
│  └──────────────────────────────┘   │
│                                     │
│  [Error if passwords don't match]   │
│  [Error if password too weak]       │
│  [Success: Redirect to login]       │
│                                     │
└─────────────────────────────────────┘

Form Fields:
- New Password (text input, masked)
- Confirm Password (text input, masked)

Password Requirements:
- Min 8 characters
- Must contain uppercase + lowercase
- Must contain digit or special char

Buttons:
- Reset Password (primary)
- Back to Login (secondary)
```

**Implementation:**
```dart
class ResetPasswordScreen extends ConsumerStatefulWidget {
  final String resetToken;
  
  @override
  ConsumerState<ResetPasswordScreen> createState() => _ResetPasswordScreenState();
}

class _ResetPasswordScreenState extends ConsumerState<ResetPasswordScreen> {
  final _passwordController = TextEditingController();
  final _confirmController = TextEditingController();
  bool _isLoading = false;
  String? _error;

  void _handleReset() async {
    // Validate passwords match
    // Call: ref.read(authRepository).resetPassword(token, password, confirm)
    // On success: Show success snackbar → Navigate to login
    // On error: Show error message
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Set New Password')),
      body: ListView(
        padding: const EdgeInsets.all(24),
        children: [
          // Password input with strength indicator
          // Confirm password input
          // Submit button
          // Error/success messages
        ],
      ),
    );
  }
}
```

**API Call:**
```dart
Future<Either<Failure, bool>> resetPassword({
  required String token,
  required String newPassword,
  required String confirmPassword,
})
// Endpoint: POST /api/v1/auth/reset-password
// Body: {
//   "reset_token": "abc123xyz...",
//   "new_password": "NewPass123!",
//   "confirm_password": "NewPass123!"
// }
// Response: { "success": true }
```

---

### 2. Employee Code Lookup (AJAX-like) ⚠️ IMPORTANT

**Website Pattern:**
```
User types employee code during registration
  ↓
After 600ms (debounce)
  ↓
Call GET /api/v1/auth/lookup-employee?code=E-2510016
  ↓
If found: Show green box with employee name
  ↓
If not found: Show error message
  ↓
Allow form submission only if lookup succeeded
```

**Where to Implement:**
```
File: lib/features/auth/presentation/screens/login_screen.dart
Location: Registration tab (tab-register panel)
Field: Employee Code input field

Enhance the existing registration form:
```

**Current Code:**
```dart
// In RegisterForm widget:
TextField(
  controller: _codeController,
  label: 'Employee Code',
  onChanged: (value) {
    _debounce(() => _lookupEmployee(value));
  },
)
```

**Add Lookup UI:**
```dart
// Show during typing:
┌──────────────────────────────────────┐
│ Employee Code                        │
│ ┌──────────────────────────┐  🔄    │  ← Spinner during loading
│ │ E-2510016                │        │
│ └──────────────────────────┘        │
│                                     │
│ ┌──────────────────────────────────┐│  ← Green box if found
│ │ ✓ Employee Name: Durvesh Parab   ││
│ └──────────────────────────────────┘│
│                                     │
│ Or error message if not found:      │
│ ┌──────────────────────────────────┐│  ← Red error
│ │ ✗ Employee code not found        ││
│ └──────────────────────────────────┘│
└──────────────────────────────────────┘
```

**Implementation:**
```dart
class RegisterForm extends ConsumerStatefulWidget {
  @override
  ConsumerState<RegisterForm> createState() => _RegisterFormState();
}

class _RegisterFormState extends ConsumerState<RegisterForm> {
  Timer? _debounceTimer;
  String? _lookupError;
  String? _employeeName;
  bool _lookupLoading = false;

  void _lookupEmployee(String code) {
    if (code.length < 3) {
      setState(() => _employeeName = null);
      return;
    }

    setState(() => _lookupLoading = true);

    ref.read(authRepository).lookupEmployee(code).then((result) {
      result.fold(
        (failure) => setState(() {
          _lookupError = 'Employee code not found';
          _employeeName = null;
          _lookupLoading = false;
        }),
        (data) => setState(() {
          _employeeName = data['name']; // Or appropriate field
          _lookupError = null;
          _lookupLoading = false;
        }),
      );
    });
  }

  @override
  Widget build(BuildContext context) {
    return Form(
      child: Column(
        children: [
          // ... other fields ...
          
          // Employee Code input with lookup
          TextFormField(
            onChanged: (value) {
              _debounceTimer?.cancel();
              _debounceTimer = Timer(
                const Duration(milliseconds: 600),
                () => _lookupEmployee(value),
              );
            },
          ),
          
          // Show lookup status
          if (_lookupLoading) ...[
            const CircularProgressIndicator(),
          ] else if (_employeeName != null) ...[
            Container(
              padding: const EdgeInsets.all(12),
              margin: const EdgeInsets.only(top: 8),
              decoration: BoxDecoration(
                color: const Color(0xFFF0FDF4), // Light green
                border: Border.all(color: const Color(0xFF16A34A)),
                borderRadius: BorderRadius.circular(4),
              ),
              child: Text(
                '✓ Employee Name: $_employeeName',
                style: const TextStyle(color: Color(0xFF166534)),
              ),
            ),
          ] else if (_lookupError != null) ...[
            Container(
              padding: const EdgeInsets.all(12),
              margin: const EdgeInsets.only(top: 8),
              decoration: BoxDecoration(
                color: const Color(0xFFFFF5F5), // Light red
                border: Border.all(color: const Color(0xFFC53030)),
                borderRadius: BorderRadius.circular(4),
              ),
              child: Text(
                '✗ $_lookupError',
                style: const TextStyle(color: Color(0xFFC53030)),
              ),
            ),
          ],
          
          // Submit button enabled only if lookup succeeded
          ElevatedButton(
            onPressed: _employeeName != null ? _handleRegister : null,
            child: const Text('Create Account'),
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _debounceTimer?.cancel();
    super.dispose();
  }
}
```

**API Call:**
```dart
Future<Either<Failure, Map<String, dynamic>>> lookupEmployee(String code)
// Endpoint: GET /api/v1/auth/lookup-employee?code=E-2510016
// Response: {
//   "found": true,
//   "name": "Durvesh Parab",
//   "employee_code": "E-2510016",
//   "department": "IT"
// }
// Or if not found:
// {
//   "found": false,
//   "message": "Employee code not found in system"
// }
```

---

### 3. Password Strength Indicator ✅ IMPORTANT

**Website Pattern:**
```
User types password during registration
  ↓
Real-time strength calculation:
  - Length ≥ 8: +1 strength
  - Length ≥ 12: +1 strength
  - Has uppercase + lowercase: +1 strength
  - Has digits + special chars: +1 strength
  ↓
Display color-coded bar:
  - 0-1 strength: Red "Too weak"
  - 1-2 strength: Orange "Weak"
  - 2-3 strength: Yellow "Fair"
  - 3-4 strength: Green "Good"
  - 4+ strength: Blue "Strong ✓"
```

**Where to Implement:**
```
File: lib/features/auth/presentation/screens/login_screen.dart
Location: Registration tab (tab-register panel)
Field: Password input field (r-pw)
```

**UI:**
```
Password
┌──────────────────────────────────────┐
│ ••••••••••                         👁 │
└──────────────────────────────────────┘
┌──────────────────────────────────────┐  ← Strength bar
│████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│
└──────────────────────────────────────┘
Good                                    ← Label + color
```

**Implementation:**
```dart
class RegisterForm extends ConsumerStatefulWidget {
  @override
  ConsumerState<RegisterForm> createState() => _RegisterFormState();
}

class _RegisterFormState extends ConsumerState<RegisterForm> {
  final _passwordController = TextEditingController();
  double _strengthScore = 0;
  String _strengthLabel = '';
  Color _strengthColor = Colors.red;

  void _updatePasswordStrength(String password) {
    if (password.isEmpty) {
      setState(() {
        _strengthScore = 0;
        _strengthLabel = '';
      });
      return;
    }

    double score = 0;

    // Length checks
    if (password.length >= 8) score++;
    if (password.length >= 12) score++;

    // Character type checks
    if (RegExp(r'[a-z]').hasMatch(password) && 
        RegExp(r'[A-Z]').hasMatch(password)) score++;

    if (RegExp(r'\d').hasMatch(password) && 
        RegExp(r'[!@#$%^&*]').hasMatch(password)) score++;

    // Map score to UI
    late String label;
    late Color color;
    switch (score.toInt()) {
      case 0:
        label = 'Too weak';
        color = Colors.red;
        break;
      case 1:
        label = 'Weak';
        color = Colors.orange;
        break;
      case 2:
        label = 'Fair';
        color = Colors.yellow[700]!;
        break;
      case 3:
        label = 'Good';
        color = Colors.green;
        break;
      case 4:
        label = 'Strong ✓';
        color = Colors.blue;
        break;
      default:
        label = '';
        color = Colors.transparent;
    }

    setState(() {
      _strengthScore = score;
      _strengthLabel = label;
      _strengthColor = color;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Form(
      child: Column(
        children: [
          // ... other fields ...
          
          // Password field with strength indicator
          TextFormField(
            controller: _passwordController,
            obscureText: true,
            onChanged: _updatePasswordStrength,
            decoration: InputDecoration(
              labelText: 'Password',
              suffixIcon: GestureDetector(
                onTap: () {
                  // Toggle password visibility
                },
                child: const Icon(Icons.visibility),
              ),
            ),
          ),
          
          const SizedBox(height: 8),
          
          // Strength bar
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: _strengthScore / 4,
              backgroundColor: Colors.grey[300],
              color: _strengthColor,
              minHeight: 4,
            ),
          ),
          
          const SizedBox(height: 4),
          
          // Strength label
          Text(
            _strengthLabel,
            style: TextStyle(
              fontSize: 12,
              color: _strengthColor,
            ),
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _passwordController.dispose();
    super.dispose();
  }
}
```

---

## REPOSITORY METHODS TO ADD/ENHANCE

**File:** `lib/features/auth/data/repository/auth_repository.dart`

```dart
// Add these methods:

Future<Either<Failure, String>> forgotPassword(String employeeCode) async {
  try {
    final response = await _client.post(
      ApiConstants.forgotPassword,
      data: {'employee_code': employeeCode.trim().toUpperCase()},
    );
    return handleResponse(response, (json) {
      return (json as Map<String, dynamic>)['reset_token'] as String? ?? '';
    });
  } on DioException catch (e) {
    return Left(dioFailure(e));
  }
}

Future<Either<Failure, bool>> resetPassword({
  required String token,
  required String newPassword,
  required String confirmPassword,
}) async {
  try {
    final response = await _client.post(
      ApiConstants.resetPassword,
      data: {
        'reset_token': token,
        'new_password': newPassword,
        'confirm_password': confirmPassword,
      },
    );
    return handleResponse(response, (_) => true);
  } on DioException catch (e) {
    return Left(dioFailure(e));
  }
}

Future<Either<Failure, Map<String, dynamic>>> lookupEmployee(String code) async {
  try {
    final response = await _client.get(
      ApiConstants.lookupEmployee,
      queryParameters: {'code': code.trim().toUpperCase()},
    );
    return handleResponse(response, (json) => json as Map<String, dynamic>);
  } on DioException catch (e) {
    return Left(dioFailure(e));
  }
}
```

---

## API ENDPOINTS TO USE

```
GET /api/v1/auth/lookup-employee?code=E-2510016
POST /api/v1/auth/forgot-password
POST /api/v1/auth/reset-password
```

**All endpoints already exist in Flask backend.**

---

## TESTING CHECKLIST

### Unit Tests
```dart
// Test password strength calculation
test('Password strength calculation', () {
  expect(calculateStrength('weak'), 0);
  expect(calculateStrength('VeryLongPassword123!'), 4);
});

// Test form validation
test('Password confirmation validation', () {
  expect(validatePasswordMatch('pass123', 'pass123'), true);
  expect(validatePasswordMatch('pass123', 'different'), false);
});
```

### Integration Tests
```dart
// Test forgot password flow
testWidgets('Forgot password complete flow', (WidgetTester tester) async {
  // 1. Navigate to forgot password screen
  // 2. Enter employee code
  // 3. Verify reset link sent message
  // 4. Navigate to reset password
  // 5. Enter new password
  // 6. Verify success + redirect to login
});

// Test employee code lookup
testWidgets('Employee code lookup', (WidgetTester tester) async {
  // 1. Type employee code in registration
  // 2. Verify lookup after debounce
  // 3. Verify employee name displayed
  // 4. Verify form enabled only when found
});
```

### Manual Tests
- [ ] Forgot password: enter valid code → see link sent
- [ ] Forgot password: enter invalid code → see error
- [ ] Reset password: enter mismatch passwords → validation error
- [ ] Reset password: weak password → strength indicator red
- [ ] Reset password: strong password → submit enabled
- [ ] Employee lookup: type code → see name after 600ms
- [ ] Employee lookup: invalid code → see error
- [ ] Password strength: updates in real-time as typing

---

## FILES TO CREATE/MODIFY

**Create:**
1. `lib/features/auth/presentation/screens/forgot_password_screen.dart` (NEW)
2. `lib/features/auth/presentation/screens/reset_password_screen.dart` (NEW)

**Modify:**
3. `lib/features/auth/presentation/screens/login_screen.dart` (enhance registration)
4. `lib/features/auth/data/repository/auth_repository.dart` (add methods)
5. `lib/core/constants/api_constants.dart` (verify endpoints)
6. `lib/features/auth/presentation/providers/auth_provider.dart` (if needed)

**Test Files:**
7. `test/features/auth/auth_test.dart` (add tests)

---

## VERIFICATION AGAINST WEBSITE

After implementation, verify:

**Screen 1: Forgot Password**
```
Website: https://hr-management-system-muqz.onrender.com/auth/forgot-password
Flutter: Matches layout, colors, buttons, validation
```

**Screen 2: Reset Password**
```
Website: https://hr-management-system-muqz.onrender.com/auth/reset-password?token=...
Flutter: Matches layout, password fields, strength indicator
```

**Screen 3: Registration with Lookup**
```
Website: https://hr-management-system-muqz.onrender.com (Register tab)
Flutter: Employee code lookup matches website, name display matches
```

---

## BUILD & TEST COMMAND

```bash
cd c:\Users\durve\Downloads\HR\ management\ system\smart_hrms_mobile

flutter clean
flutter pub get
dart run build_runner build --delete-conflicting-outputs
flutter analyze      # Must be: 0 errors
flutter test         # Must be: all pass
flutter build apk --debug
flutter build apk --release
```

---

## SUCCESS CRITERIA - MODULE 1 COMPLETE

✅ ForgotPasswordScreen created and working  
✅ ResetPasswordScreen created and working  
✅ Employee code lookup in registration working  
✅ Password strength indicator showing  
✅ All APIs called successfully  
✅ Forms validate correctly  
✅ UI matches website  
✅ All tests pass  
✅ flutter analyze = 0 errors  
✅ APK builds successfully  
✅ Manually verified against website  

---

**Next Step:** Implement these features, verify each against website, then move to Module 2 (Dashboard).

