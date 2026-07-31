# PHASE 7 BUILD ACTION PLAN - FLUTTER APP COMPILATION
**Detailed action plan to fix all compile errors and successfully build APK**

**Status:** Error Analysis Complete - Ready for Implementation  
**Date:** July 28, 2026  

---

## CRITICAL ERRORS TO FIX (18 Total)

### GROUP 1: Missing Widget Files (2 files)

#### 1.1 Create: `pending_records_indicator.dart`
**Location:** `lib/features/attendance/presentation/widgets/pending_records_indicator.dart`  
**Required by:** `check_out_screen.dart` line 15  
**Purpose:** Widget to display pending records indicator

**Implementation:**
```dart
import 'package:flutter/material.dart';

class PendingRecordsIndicator extends StatelessWidget {
  final int count;
  
  const PendingRecordsIndicator({
    Key? key,
    required this.count,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    if (count == 0) return const SizedBox.shrink();
    
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: Colors.orange.withValues(alpha: 0.2),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.orange),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(Icons.info_outline, color: Colors.orange, size: 18),
          const SizedBox(width: 8),
          Text(
            '$count pending record(s)',
            style: const TextStyle(color: Colors.orange, fontSize: 12),
          ),
        ],
      ),
    );
  }
}
```

---

#### 1.2 Create/Fix: `department_dropdown.dart`
**Location:** `lib/features/auth/presentation/widgets/department_dropdown.dart`  
**Required by:** `login_screen.dart` line 9  
**Purpose:** Dropdown widget for selecting department during login

**Implementation:**
```dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../company/presentation/providers/company_provider.dart';

class DepartmentDropdown extends ConsumerWidget {
  final String? selectedValue;
  final Function(String?) onChanged;
  final String? labelText;

  const DepartmentDropdown({
    Key? key,
    required this.selectedValue,
    required this.onChanged,
    this.labelText,
  }) : super(key: key);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final departmentsAsync = ref.watch(departmentsProvider);

    return departmentsAsync.when(
      data: (departments) => DropdownButtonFormField<String>(
        value: selectedValue,
        onChanged: onChanged,
        items: departments
            .map((dept) => DropdownMenuItem<String>(
                  value: dept.id.toString(),
                  child: Text(dept.name),
                ))
            .toList(),
        decoration: InputDecoration(
          labelText: labelText ?? 'Department',
          border: const OutlineInputBorder(),
        ),
        validator: (value) {
          if (value == null || value.isEmpty) {
            return 'Please select a department';
          }
          return null;
        },
      ),
      loading: () => const CircularProgressIndicator(),
      error: (error, stack) => Text('Error: $error'),
    );
  }
}
```

---

### GROUP 2: Add Missing Imports (1 file)

#### 2.1 Add `dart:math` import to CheckOutScreen
**File:** `lib/features/attendance/presentation/screens/check_out_screen.dart`  
**Line:** Top of file (with other imports)  
**Action:** Add this import

```dart
import 'dart:math';
```

**Fixes errors on lines:** 126-132 (all math function errors)

---

### GROUP 3: Define Missing Providers (2 files)

#### 3.1 Fix CompanyProvider
**File:** `lib/features/company/presentation/providers/company_provider.dart`  
**Error Lines:** 9, 20, 31, 42, 54, 67  
**Problem:** `companyRepositoryProvider` undefined

**Solution:** Ensure companyRepositoryProvider is defined:
```dart
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/network/dio_client.dart';
import '../repository/company_repository.dart';

// Define the provider
final companyRepositoryProvider = Provider((ref) {
  final dioClient = ref.watch(dioClientProvider);
  return CompanyRepository(dioClient);
});

// Then use it in other providers
final departmentsProvider = FutureProvider((ref) async {
  final repository = ref.watch(companyRepositoryProvider);
  final result = await repository.getDepartments();
  return result.fold(
    (failure) => throw failure,
    (departments) => departments,
  );
});
// ... etc
```

---

#### 3.2 Fix LeaveProvider
**File:** `lib/features/leave/presentation/providers/leave_provider.dart`  
**Error Lines:** Multiple undefined `leaveRepositoryProvider`  
**Problem:** `leaveRepositoryProvider` undefined

**Solution:** Ensure leaveRepositoryProvider is defined:
```dart
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/network/dio_client.dart';
import '../repository/leave_repository.dart';

// Define the provider
final leaveRepositoryProvider = Provider((ref) {
  final dioClient = ref.watch(dioClientProvider);
  return LeaveRepository(dioClient);
});

// Then use it in other providers
final leaveTypesProvider = FutureProvider((ref) async {
  final repository = ref.watch(leaveRepositoryProvider);
  final result = await repository.getLeaveTypes();
  return result.fold(
    (failure) => throw failure,
    (types) => types,
  );
});
// ... etc
```

---

## STEP-BY-STEP FIX INSTRUCTIONS

### Step 1: Create Missing Widget Files (5 min)

```bash
# Create directory if not exists
mkdir -p lib/features/attendance/presentation/widgets/
mkdir -p lib/features/auth/presentation/widgets/

# Create pending_records_indicator.dart with content above
# Create department_dropdown.dart with content above
```

### Step 2: Add Missing Import (2 min)

**File:** `lib/features/attendance/presentation/screens/check_out_screen.dart`

Find the imports section and add:
```dart
import 'dart:math';
```

### Step 3: Fix Provider Definitions (10 min)

**File:** `lib/features/company/presentation/providers/company_provider.dart`

Ensure the file has:
```dart
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/network/dio_client.dart';
import '../repository/company_repository.dart';

final companyRepositoryProvider = Provider((ref) {
  final dioClient = ref.watch(dioClientProvider);
  return CompanyRepository(dioClient);
});
```

**File:** `lib/features/leave/presentation/providers/leave_provider.dart`

Ensure the file has:
```dart
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/network/dio_client.dart';
import '../repository/leave_repository.dart';

final leaveRepositoryProvider = Provider((ref) {
  final dioClient = ref.watch(dioClientProvider);
  return LeaveRepository(dioClient);
});
```

### Step 4: Verify Fixes

```bash
cd c:\Users\durve\Downloads\HR management system\smart_hrms_mobile
flutter analyze
```

Expected output: **0 errors** ✅

### Step 5: Build Debug APK

```bash
flutter build apk --debug
```

Expected: Successfully built `build/app/outputs/flutter-apk/app-debug.apk`

### Step 6: Build Release APK

```bash
flutter build apk --release
```

Expected: Successfully built `build/app/outputs/flutter-apk/app-release.apk`

---

## OPTIONAL: Fix Linter Warnings

These are nice-to-have but not blocking:

### Fix #1: Remove Unused Fields
**File:** `lib/core/network/dio_client.dart`

```dart
// BEFORE:
final Ref _ref;
final Logger _logger;

// AFTER (remove or use them):
// Remove if not used anywhere in the file
```

### Fix #2: Fix Deprecated withOpacity
**Multiple files** - Replace pattern:

```dart
// BEFORE:
color.withOpacity(0.5)

// AFTER:
color.withValues(alpha: 0.5)
```

---

## BUILD VERIFICATION CHECKLIST

```
PRE-BUILD CHECKS:
[ ] All 5 missing file/import issues fixed
[ ] flutter analyze returns 0 errors
[ ] pubspec.yaml is valid (flutter pub get works)
[ ] All dependencies resolved

BUILD STEPS:
[ ] flutter clean (optional, removes build artifacts)
[ ] flutter pub get (ensures all packages downloaded)
[ ] flutter build apk --debug (creates debug APK)
[ ] flutter build apk --release (creates release APK)

POST-BUILD VERIFICATION:
[ ] APK files exist in build/app/outputs/flutter-apk/
[ ] APK files are > 50MB (not suspiciously small)
[ ] APK can be installed on device/emulator
[ ] App launches without crashing
[ ] Login screen displays correctly
[ ] Department dropdown works
[ ] Check-in/Check-out screens load
```

---

## EXPECTED BUILD ARTIFACTS

After successful build:

```
build/app/outputs/flutter-apk/
  ├── app-debug.apk (~80-100 MB)
  ├── app-release.apk (~50-70 MB)
  └── app-debug-symbols.dwarf (~50 MB)
```

---

## TROUBLESHOOTING

### If `flutter analyze` still shows errors:
1. Clear Flutter cache: `flutter clean`
2. Get dependencies: `flutter pub get`
3. Run: `flutter pub run build_runner build` (for code generation)
4. Run analyze again: `flutter analyze`

### If APK build fails:
1. Check Java version: `java -version` (needs Java 11+)
2. Check Android SDK: Ensure Android 34+ SDK installed
3. Clear Gradle cache: `cd android && ./gradlew clean`
4. Try again: `flutter build apk --debug`

### If app crashes on launch:
1. Check logs: `flutter logs`
2. Verify API endpoint in env/config
3. Verify Flask backend is running
4. Check network connectivity

---

## NEXT PHASE

After successful APK build:
- **PHASE 8:** Screen-by-screen verification against website
- Install APK on device
- Test all features against website
- Generate verification report

---

**Status:** Action plan ready for implementation  
**Estimated time to fix:** 30 minutes  
**Estimated build time:** 10 minutes  
**Total time to completion:** ~40 minutes

---

**Ready to proceed:** YES ✅
