# FLUTTER API INTEGRATION MAPPING - PHASE 5
**Screen-by-screen API endpoint mapping for implementation**

**Date:** July 28, 2026  
**Status:** Reference guide for developers  

---

## AUTHENTICATION SCREENS

### 1. Login Screen
**File:** `lib/features/auth/presentation/screens/login_screen.dart`  
**Status:** ✅ COMPLETE

**API Endpoints Used:**
```
POST /api/v1/auth/login
  Request: {email, password, department}
  Response: {access_token, user_id, user_role, expires_in}

GET /api/v1/master/departments
  Response: [{id, name, code}]
  (for department dropdown)
```

---

### 2. Register Screen
**File:** `lib/features/auth/presentation/screens/register_screen.dart`  
**Status:** ❌ MISSING - Extract from LoginScreen tab

**API Endpoints:**
```
POST /api/v1/auth/register
  Request: {email, first_name, last_name, password, employee_code}
  Response: {message, user_id}

GET /api/v1/auth/lookup-employee?code=XXX
  Response: {employee_code, first_name, last_name}
  (for auto-lookup on code entry)
```

---

### 3. Forgot Password Screen
**File:** `lib/features/auth/presentation/screens/forgot_password_screen.dart`  
**Status:** ❌ MISSING

**API Endpoints:**
```
POST /api/v1/auth/forgot-password
  Request: {email}
  Response: {message: "Reset link sent to email"}
```

---

### 4. Reset Password Screen
**File:** `lib/features/auth/presentation/screens/reset_password_screen.dart`  
**Status:** ❌ MISSING

**API Endpoints:**
```
POST /api/v1/auth/reset-password
  Request: {token, new_password}
  Response: {message: "Password reset successfully"}
  (token passed as route parameter)
```

---

## EMPLOYEE MANAGEMENT SCREENS

### 5. Employee List Screen
**File:** `lib/features/employee/presentation/screens/employee_list_screen.dart`  
**Status:** ❌ MISSING

**API Endpoints:**
```
GET /api/v1/employees
  Query Params: ?page=1&limit=20&search=name&department=X&branch=Y&status=active
  Response: {data: [{id, employee_code, first_name, last_name, email, department, status}], total, page}

GET /api/v1/master/departments
  Response: [{id, name, code}]
  (for filter dropdown)
```

---

### 6. Employee Create Screen
**File:** `lib/features/employee/presentation/screens/employee_create_screen.dart`  
**Status:** ❌ MISSING

**API Endpoints:**
```
POST /api/v1/employees
  Request: {
    employee_code, first_name, last_name, email, mobile, department_id, position_id,
    branch, employment_type, date_joined, manager_id, personal_email, address
  }
  Response: {id, employee_code}

GET /api/v1/master/departments
  Response: [{id, name}]

GET /api/v1/master/positions
  Response: [{id, title, department_id}]

GET /api/v1/employees?search=X
  Response: [{id, employee_code, first_name, last_name}]
  (for manager lookup autocomplete)
```

---

### 7. Employee Edit Screen
**File:** `lib/features/employee/presentation/screens/employee_edit_screen.dart`  
**Status:** ❌ MISSING

**API Endpoints:**
```
GET /api/v1/employees/{id}
  Response: {id, employee_code, first_name, last_name, email, mobile, ... all fields}

PUT /api/v1/employees/{id}
  Request: {first_name, last_name, email, mobile, department_id, position_id, ... editable fields}
  Response: {message: "Employee updated"}
  NOTE: employee_code cannot be edited

GET /api/v1/master/departments
  Response: [{id, name}]

GET /api/v1/master/positions
  Response: [{id, title, department_id}]
```

---

### 8. Employee Detail Screen
**File:** `lib/features/employee/presentation/screens/employee_detail_screen.dart`  
**Status:** ❌ MISSING

**API Endpoints:**
```
GET /api/v1/employees/{id}
  Response: {id, employee_code, first_name, last_name, email, mobile, department, position, date_joined, manager_id, ...}

GET /api/v1/employees/{id}/login-history
  Response: [{timestamp, ip, device, success}]
  (for quick summary)

DELETE /api/v1/employees/{id}
  Response: {message: "Employee deleted"}
  (for delete action)

GET /api/v1/attendance/summary?employee_id=X
  Response: {present, absent, leave, ...}
  (for summary card)
```

---

### 9. Employee Profile Screen
**File:** `lib/features/profile/presentation/screens/my_profile_screen.dart`  
**Status:** ⚠️ PARTIAL

**API Endpoints:**
```
GET /api/v1/auth/me
  Response: {id, email, first_name, last_name, employee: {employee_code, department, position, manager_id}}

PUT /api/v1/auth/me
  Request: {first_name, last_name, email, mobile, personal_email, address}
  Response: {message: "Profile updated"}

GET /api/v1/employees/{id}/login-history?limit=5
  Response: [{timestamp, ip, device, success, failure_reason}]
```

---

### 10. Reset Employee Password (Modal)
**File:** `lib/features/employee/presentation/widgets/reset_password_modal.dart`  
**Status:** ❌ MISSING

**API Endpoints:**
```
POST /api/v1/employees/{id}/reset-password
  Request: {new_password}
  Response: {message: "Password reset successfully", temporary_password}
```

---

### 11. Login History Screen
**File:** `lib/features/employee/presentation/screens/login_history_screen.dart`  
**Status:** ❌ MISSING

**API Endpoints:**
```
GET /api/v1/employees/{id}/login-history?page=1&limit=20
  Response: {data: [{timestamp, ip, user_agent, success, failure_reason}], total, page}

GET /api/v1/employees/{id}/login-history/export
  Response: CSV file
  (for export button)
```

---

## ATTENDANCE SCREENS

### 12. Check-in Screen
**File:** `lib/features/attendance/presentation/screens/check_in_screen.dart`  
**Status:** ✅ COMPLETE

**API Endpoints:**
```
POST /api/v1/attendance/check-in
  Request: {latitude, longitude, accuracy, photo_data}
  Response: {attendance_id, check_in_time, distance_from_office}

GET /api/v1/settings/office
  Response: {latitude, longitude, radius_metres, min_gps_accuracy_metres}
  (for geofence validation)

GET /api/v1/attendance/today
  Response: {has_checked_in, check_in_time}
  (to determine check-in vs check-out)
```

---

### 13. Check-out Screen
**File:** `lib/features/attendance/presentation/screens/check_out_screen.dart`  
**Status:** ❌ MISSING

**API Endpoints:**
```
POST /api/v1/attendance/check-out
  Request: {attendance_id, latitude, longitude, accuracy, photo_data}
  Response: {attendance_id, check_out_time, working_hours}

GET /api/v1/attendance/today
  Response: {check_in_time, has_checked_out}

GET /api/v1/settings/office
  Response: {latitude, longitude, radius_metres}
```

---

### 14. Attendance History Screen
**File:** `lib/features/attendance/presentation/screens/attendance_history_screen.dart`  
**Status:** ⚠️ PARTIAL

**API Endpoints:**
```
GET /api/v1/attendance/history?start_date=X&end_date=Y&page=1&limit=20
  Response: {data: [{date, check_in_time, check_out_time, working_hours, status, is_late}], total}

GET /api/v1/attendance/history/export?start_date=X&end_date=Y
  Response: CSV file
```

---

## LEAVE MANAGEMENT SCREENS

### 15. Apply Leave Screen
**File:** `lib/features/leave/presentation/screens/apply_leave_screen.dart`  
**Status:** ✅ COMPLETE

**API Endpoints:**
```
POST /api/v1/leave/apply
  Request: {leave_type_id, start_date, end_date, reason}
  Response: {leave_request_id}

POST /api/v1/leave/halfday
  Request: {leave_type_id, date, half_type: "morning"|"afternoon", reason}
  Response: {half_day_request_id}

POST /api/v1/leave/early
  Request: {date, requested_leave_time: "HH:MM", reason}
  Response: {early_leave_request_id}

GET /api/v1/master/leave-types
  Response: [{id, name, code, max_days_per_year, is_paid}]

GET /api/v1/leave/balance
  Response: [{leave_type_id, leave_type_name, balance, used, available}]
```

---

### 16. Leave History Screen
**File:** `lib/features/leave/presentation/screens/leave_history_screen.dart`  
**Status:** ⚠️ PARTIAL

**API Endpoints:**
```
GET /api/v1/leave?status=X&leave_type_id=Y&page=1&limit=20
  Query Params: ?status=pending|approved|rejected&leave_type_id=X
  Response: {data: [{id, leave_type, start_date, end_date, status, approved_by}], total}

POST /api/v1/leave/{id}/cancel
  Response: {message: "Leave cancelled"}
  (only if status == "pending")

GET /api/v1/master/leave-types
  Response: [{id, name, code}]
```

---

### 17. Leave Approvals Screen (Manager)
**File:** `lib/features/leave/presentation/screens/leave_approvals_screen.dart`  
**Status:** ❌ MISSING

**API Endpoints:**
```
GET /api/v1/leave/approvals?page=1&limit=20
  Response: {data: [{id, employee_name, leave_type, start_date, end_date, days, reason, status}], total}

POST /api/v1/leave/{id}/approve
  Request: {remarks}
  Response: {message: "Leave approved"}

POST /api/v1/leave/{id}/reject
  Request: {reason}
  Response: {message: "Leave rejected"}

GET /api/v1/leave/{id}
  Response: {id, employee_name, leave_type, dates, reason, ...}
```

---

### 18. Leave Balance Display
**File:** `lib/features/leave/presentation/screens/leave_balance_screen.dart`  
**Status:** ⚠️ PARTIAL

**API Endpoints:**
```
GET /api/v1/leave/balance
  Response: {data: [{leave_type_id, leave_type_name, max_days, used_days, balance_days, carry_forward}]}
```

---

## SHIFT MANAGEMENT SCREENS

### 19. Current Shift Display
**File:** `lib/features/shift/presentation/screens/current_shift_screen.dart`  
**Status:** ⚠️ PARTIAL

**API Endpoints:**
```
GET /api/v1/shift/my-shift
  Response: {shift_id, shift_name, start_time, end_time, working_hours, grace_minutes, office_location}

GET /api/v1/settings/office
  Response: {name, address, latitude, longitude, office_start_time, office_end_time}
```

---

### 20. Request Shift Change Screen
**File:** `lib/features/shift/presentation/screens/request_shift_change_screen.dart`  
**Status:** ⚠️ PARTIAL

**API Endpoints:**
```
GET /api/v1/shift/my-shift
  Response: {shift_id, shift_name, start_time, end_time}
  (current shift - read only)

GET /api/v1/shift/available
  Response: [{shift_id, shift_name, start_time, end_time, description}]
  (for dropdown)

POST /api/v1/shift/change-request
  Request: {current_shift_id, requested_shift_id, effective_date, reason}
  Response: {shift_change_request_id}
```

---

### 21. Shift Approvals Screen (Manager)
**File:** `lib/features/shift/presentation/screens/shift_approvals_screen.dart`  
**Status:** ❌ MISSING

**API Endpoints:**
```
GET /api/v1/shift/approvals?page=1&limit=20
  Response: {data: [{id, employee_name, current_shift, requested_shift, effective_date, reason, status}], total}

POST /api/v1/shift/{id}/approve
  Request: {remarks}
  Response: {message: "Shift change approved"}

POST /api/v1/shift/{id}/reject
  Request: {reason}
  Response: {message: "Shift change rejected"}

GET /api/v1/shift/{id}
  Response: {id, employee_name, current_shift, requested_shift, effective_date, reason}
```

---

### 22. Shift History Screen
**File:** `lib/features/shift/presentation/screens/shift_history_screen.dart`  
**Status:** ⚠️ PARTIAL

**API Endpoints:**
```
GET /api/v1/shift/history?page=1&limit=20
  Response: {data: [{id, shift_name, effective_from, effective_until, status}], total}

GET /api/v1/shift/change-requests?page=1&limit=20
  Response: {data: [{id, requested_shift, effective_date, status, approved_date}], total}
```

---

## PAYROLL SCREENS

### 23. Payslip List Screen
**File:** `lib/features/payroll/presentation/screens/payslip_list_screen.dart`  
**Status:** ⚠️ PARTIAL

**API Endpoints:**
```
GET /api/v1/payroll/payslips?page=1&limit=12
  Response: {data: [{id, month, year, net_salary, status, generated_at}], total}

GET /api/v1/payroll/payslips/{id}/download
  Response: PDF file
```

---

### 24. Payslip Detail Screen
**File:** `lib/features/payroll/presentation/screens/payslip_detail_screen.dart`  
**Status:** ⚠️ PARTIAL

**API Endpoints:**
```
GET /api/v1/payroll/payslips/{id}
  Response: {id, month, year, basic_salary, gross_salary, deductions, net_salary, earnings: [...], deductions: [...]}

GET /api/v1/payroll/payslips/{id}/download
  Response: PDF file
```

---

### 25. Payroll Runs (HR Only)
**File:** `lib/features/payroll/presentation/screens/payroll_runs_screen.dart`  
**Status:** ❌ MISSING

**API Endpoints:**
```
GET /api/v1/payroll/runs?status=X&page=1&limit=20
  Response: {data: [{id, month, year, period_label, status, total_gross, total_net, employee_count}], total}

POST /api/v1/payroll/runs
  Request: {month, year}
  Response: {payroll_run_id}

GET /api/v1/payroll/runs/{id}
  Response: {id, month, year, status, total_gross, total_net, payslips: [...]}

POST /api/v1/payroll/runs/{id}/approve
  Response: {message: "Payroll run approved"}

POST /api/v1/payroll/runs/{id}/process
  Response: {message: "Payroll run processed"}
```

---

## REPORTING SCREENS

### 26. Attendance Report
**File:** `lib/features/reports/presentation/screens/attendance_report_screen.dart`  
**Status:** ⚠️ PARTIAL

**API Endpoints:**
```
GET /api/v1/reports/attendance?start_date=X&end_date=Y&department_id=Z
  Response: {data: [{employee_code, employee_name, days_present, days_absent, days_leave, percentage}]}

GET /api/v1/reports/attendance/export?start_date=X&end_date=Y&format=csv|pdf
  Response: CSV/PDF file

GET /api/v1/master/departments
  Response: [{id, name}]
```

---

### 27. Leave Report
**File:** `lib/features/reports/presentation/screens/leave_report_screen.dart`  
**Status:** ⚠️ PARTIAL

**API Endpoints:**
```
GET /api/v1/reports/leave?start_date=X&end_date=Y&leave_type_id=Z&status=W
  Response: {data: [{employee_code, employee_name, leave_type, days, status, approver_name}]}

GET /api/v1/reports/leave/export?start_date=X&end_date=Y&format=csv|pdf
  Response: CSV/PDF file

GET /api/v1/master/leave-types
  Response: [{id, name, code}]
```

---

### 28. Employee Report
**File:** `lib/features/reports/presentation/screens/employee_report_screen.dart`  
**Status:** ⚠️ PARTIAL

**API Endpoints:**
```
GET /api/v1/reports/employees?department_id=X&status=Y
  Response: {data: [{employee_code, employee_name, department, position, date_joined, status}]}

GET /api/v1/reports/employees/export?format=csv|pdf
  Response: CSV/PDF file

GET /api/v1/master/departments
  Response: [{id, name}]
```

---

## DASHBOARD & NOTIFICATIONS

### 29. Dashboard Screen
**File:** `lib/features/dashboard/presentation/screens/home_screen.dart`  
**Status:** ⚠️ PARTIAL

**API Endpoints:**
```
GET /api/v1/auth/me
  Response: {id, email, first_name, last_name}

GET /api/v1/employees/me
  Response: {employee_code, department, position, manager_id}

GET /api/v1/attendance/today
  Response: {has_checked_in, has_checked_out, check_in_time, check_out_time}

GET /api/v1/leave/balance
  Response: [{leave_type_name, balance, used, available}]

GET /api/v1/shift/my-shift
  Response: {shift_name, start_time, end_time}

GET /api/v1/dashboard/stats
  Response: {pending_approvals, pending_leaves, attendance_this_month}
```

---

### 30. Notifications Screen
**File:** `lib/features/notifications/presentation/screens/notifications_screen.dart`  
**Status:** ⚠️ PARTIAL

**API Endpoints:**
```
GET /api/v1/notifications?page=1&limit=20&is_read=false
  Response: {data: [{id, title, message, module, is_read, created_at}], total}

PUT /api/v1/notifications/{id}/read
  Response: {message: "Marked as read"}

DELETE /api/v1/notifications/{id}
  Response: {message: "Notification deleted"}

POST /api/v1/notifications/{id}/action
  Response: (navigation payload)
```

---

## SETTINGS & PROFILE

### 31. Settings Screen
**File:** `lib/features/settings/presentation/screens/settings_screen.dart`  
**Status:** ⚠️ PARTIAL

**API Endpoints:**
```
PUT /api/v1/auth/change-password
  Request: {current_password, new_password}
  Response: {message: "Password changed"}

POST /api/v1/auth/logout
  Response: {message: "Logged out"}
```

---

## MASTER DATA ENDPOINTS (Used by Multiple Screens)

These are called by multiple screens for dropdowns and filters:

```
GET /api/v1/master/departments
  Used by: Login, Employee List, Employee Create, Reports
  Response: [{id, name, code, color}]

GET /api/v1/master/positions
  Used by: Employee Create, Employee Edit
  Response: [{id, title, code, department_id, grade, min_salary, max_salary}]

GET /api/v1/master/shifts
  Used by: Request Shift Change, Shift Approvals
  Response: [{id, name, code, start_time, end_time, working_hours}]

GET /api/v1/master/leave-types
  Used by: Apply Leave, Leave History, Leave Reports
  Response: [{id, name, code, max_days_per_year, is_paid, carry_forward}]

GET /api/v1/settings/office
  Used by: Check-in, Check-out, Dashboard
  Response: [{id, name, latitude, longitude, radius_metres, office_start_time, office_end_time}]
```

---

**END OF MAPPING** ✅

**Total Screens:** 31  
**API Endpoints Referenced:** 56+ (all covered in BACKEND_API_AUDIT.md)  
**Status:** All endpoints exist and working ✅
