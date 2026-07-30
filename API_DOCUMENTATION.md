
# Smart HRMS REST API Documentation

**Version:** 1.0.0
**Base URL:** `https://your-app.onrender.com/api/v1`
**Authentication:** Bearer JWT token

---

## Standard Response Format

```json
{ "success": true, "message": "...", "data": { } }
```

Paginated list:
```json
{ "success": true, "data": [ ], "meta": { "page": 1, "per_page": 20, "total": 100, "pages": 5, "has_next": true } }
```

Error:
```json
{ "success": false, "error": { "code": "VALIDATION_ERROR", "message": "...", "details": { "field": "error text" } } }
```

All protected endpoints require:
```
Authorization: Bearer <access_token>
```

---

## Endpoint Index

| Module | Method | Endpoint | Auth Required |
|--------|--------|----------|---------------|
| System | GET | `/health` | No |
| Auth | POST | `/auth/login` | No |
| Auth | POST | `/auth/refresh` | No |
| Auth | POST | `/auth/logout` | Yes |
| Auth | GET | `/auth/me` | Yes |
| Auth | POST | `/auth/forgot-password` | No |
| Auth | POST | `/auth/reset-password` | No |
| Auth | GET | `/auth/lookup-employee?code=` | No |
| Dashboard | GET | `/dashboard` | Yes |
| Dashboard | GET | `/dashboard/attendance` | Yes |
| Dashboard | GET | `/dashboard/leave-balance` | Yes |
| Dashboard | GET | `/dashboard/chart` | Yes |
| Employee | GET | `/employees/me` | Yes |
| Employee | PUT | `/employees/me` | Yes |
| Employee | POST | `/employees/me/photo` | Yes |
| Employee | GET | `/employees` | Admin/HR |
| Employee | GET | `/employees/<id>` | Admin/HR |
| Attendance | GET | `/attendance/today` | Yes |
| Attendance | POST | `/attendance/check-in` | Yes |
| Attendance | POST | `/attendance/check-out` | Yes |
| Attendance | POST | `/attendance/upload-photo` | Yes |
| Attendance | POST | `/attendance/upload-checkout-photo` | Yes |
| Attendance | GET | `/attendance/history` | Yes |
| Attendance | GET | `/attendance/office` | Yes |
| Leave | GET | `/leave` | Yes |
| Leave | GET | `/leave/types` | Yes |
| Leave | GET | `/leave/balance` | Yes |
| Leave | GET | `/leave/managers` | Yes |
| Leave | POST | `/leave/apply` | Yes |
| Leave | POST | `/leave/halfday` | Yes |
| Leave | POST | `/leave/early` | Yes |
| Leave | GET | `/leave/<id>` | Yes |
| Leave | POST | `/leave/<id>/cancel` | Yes |
| Leave | GET | `/leave/approvals` | Yes |
| Leave | POST | `/leave/<id>/approve` | Yes |
| Leave | POST | `/leave/<id>/reject` | Yes |
| Settings | GET | `/settings/profile` | Yes |
| Settings | PUT | `/settings/profile` | Yes |
| Settings | PUT | `/settings/password` | Yes |
| Settings | GET | `/settings/preferences` | Yes |
| Settings | PUT | `/settings/preferences` | Yes |
| Settings | GET | `/settings/login-history` | Yes |
| Payroll | GET | `/payroll/payslips` | Yes |
| Payroll | GET | `/payroll/payslips/latest` | Yes |
| Payroll | GET | `/payroll/payslips/<id>` | Yes |
| Shifts | GET | `/shifts/my-shift` | Yes |
| Shifts | GET | `/shifts/available` | Yes |
| Shifts | GET | `/shifts/requests` | Yes |
| Shifts | POST | `/shifts/request-change` | Yes |
| Shifts | POST | `/shifts/<id>/cancel` | Yes |
| Shifts | GET | `/shifts/approvals` | Yes |
| Shifts | POST | `/shifts/<id>/approve` | Yes |
| Shifts | POST | `/shifts/<id>/reject` | Yes |
| Shifts | GET | `/shifts/history` | Yes |
| Notifications | GET | `/notifications/unread-count` | Yes |
| Notifications | GET | `/notifications/recent?limit=10` | Yes |
| Notifications | POST | `/notifications/mark-all-read` | Yes |
| Notifications | POST | `/notifications/register-token` | Yes |

---

## Authentication

### POST /auth/login

Request:
```json
{ "employee_code": "E-2510016", "password": "password123", "department": "IT" }
```

Response:
```json
{
  "success": true, "message": "Login successful",
  "data": {
    "access_token": "eyJ0eXAiOiJKV1Q...",
    "refresh_token": "eyJ0eXAiOiJKV1Q...",
    "token_type": "Bearer", "expires_in": 86400,
    "user": {
      "id": 1, "email": "user@example.com", "full_name": "Durvesh Parab",
      "employee_code": "E-2510016", "role": "employee",
      "department": "IT", "designation": "Software Engineer",
      "is_admin": false, "profile_photo": null
    }
  }
}
```

### POST /auth/refresh
Request: `{ "refresh_token": "eyJ0..." }`
Response: `{ "data": { "access_token": "...", "expires_in": 86400 } }`

### GET /auth/me
Response:
```json
{
  "data": {
    "id": 1, "full_name": "Durvesh Parab", "employee_code": "E-2510016",
    "department": "IT", "role": "employee",
    "employee_details": { "date_of_joining": "2024-01-15", "mobile": "+91-9876543210", "shift_name": "General" }
  }
}
```

---

## Dashboard

### GET /dashboard
Returns complete home screen data in one request.

Response:
```json
{
  "data": {
    "employee": { "employee_code": "E-2510016", "full_name": "Durvesh Parab", "department": "IT" },
    "today": { "date": "2026-07-25", "day_name": "Saturday" },
    "attendance": {
      "today": { "status": "present", "check_in_time": "09:12", "is_late": true, "late_minutes": 12 },
      "can_check_in": false, "can_check_out": true,
      "office": { "name": "Main Office", "radius_metres": 200, "latitude": 19.076, "longitude": 72.877 }
    },
    "leave": {
      "balances": [{ "leave_type": "Paid Leave", "allowed": 6, "taken": 2, "available": 4 }],
      "pending_requests": 1
    },
    "quick_actions": [
      { "id": "check_out", "label": "Check Out", "icon": "logout", "color": "warning" }
    ]
  }
}
```

### GET /dashboard/chart
Returns 6-month attendance data for bar/line charts.
```json
{
  "data": {
    "labels": ["Feb '26", "Mar '26", "Apr '26", "May '26", "Jun '26", "Jul '26"],
    "datasets": { "present": [22,20,23,21,22,15], "absent": [1,0,0,1,0,0], "on_leave": [0,2,0,0,1,2] }
  }
}
```

---

## Attendance

### Attendance Flow (Mobile)
```
Step 1: GET  /attendance/office          → Get GPS center + radius
Step 2: POST /attendance/upload-photo    → Upload selfie (multipart)
Step 3: POST /attendance/check-in        → Submit GPS coordinates
Step 4: POST /attendance/upload-checkout-photo → Upload checkout selfie
Step 5: POST /attendance/check-out       → Submit GPS coordinates
```

### POST /attendance/upload-photo
```
Content-Type: multipart/form-data
photo: <image file>
```

### POST /attendance/check-in
```json
{ "latitude": "19.0760", "longitude": "72.8777", "accuracy": "15.5" }
```
Success response:
```json
{ "data": { "check_in_time": "09:12", "is_late": true, "late_minutes": 12, "distance_metres": 45.2 }, "message": "Check-in recorded at 09:12 IST." }
```
Error when outside radius:
```json
{ "success": false, "error": { "code": "CHECKIN_FAILED", "message": "You are 350m away from office. Maximum allowed: 200m." } }
```

### GET /attendance/history
Query params: `page`, `per_page`, `start_date`, `end_date`, `status`
```
status options: present | absent | on_leave | holiday
```

### GET /attendance/office
```json
{
  "data": {
    "latitude": 19.076, "longitude": 72.877, "radius_metres": 200,
    "office_start_time": "09:00", "office_end_time": "18:00",
    "grace_period_minutes": 10, "selfie_required": true
  }
}
```

---

## Leave

### POST /leave/apply
```json
{
  "leave_type_id": 2, "start_date": "2026-08-01", "end_date": "2026-08-03",
  "reason": "Family function", "reporting_manager_name": "Tejas Ashok Jadhav"
}
```

### POST /leave/<id>/reject
Rejection reason is **mandatory**:
```json
{ "comment": "Cannot approve - project deadline" }
```

### GET /leave/approvals
Returns leave requests where current employee is the reporting manager.

---

## Settings

### PUT /settings/password
```json
{ "current_password": "oldpass", "new_password": "newpass123", "confirm_password": "newpass123" }
```

### PUT /settings/preferences
```json
{ "theme": "dark", "language": "en", "notifications_enabled": true, "biometric_login": false }
```

---

## Shifts

### POST /shifts/request-change
```json
{
  "current_shift_id": 1, "requested_start_time": "08:00", "requested_end_time": "17:00",
  "effective_date": "2026-08-01", "reason": "Personal preference",
  "reporting_manager_code": "E-2510001"
}
```

---

## Pagination Parameters

All list endpoints support these query parameters:

| Param | Default | Description |
|-------|---------|-------------|
| `page` | 1 | Page number |
| `per_page` | 20 | Records per page (max 100) |
| `sort` | `id` | Sort field |
| `order` | `desc` | `asc` or `desc` |
| `start_date` | — | `YYYY-MM-DD` |
| `end_date` | — | `YYYY-MM-DD` |
| `status` | — | Filter by status |
| `search` | — | Full-text search |

---

## Error Codes

| Code | HTTP | Description |
|------|------|-------------|
| `UNAUTHORIZED` | 401 | Token missing or expired |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource does not exist |
| `PROFILE_NOT_FOUND` | 404 | Employee profile not linked |
| `VALIDATION_ERROR` | 422 | Field-level validation failed |
| `CHECKIN_FAILED` | 400 | GPS check failed or duplicate |
| `PHOTO_REQUIRED` | 400 | Selfie must be uploaded first |
| `LEAVE_APPLICATION_FAILED` | 400 | Leave validation failed |
| `PASSWORD_RESET_FAILED` | 400 | Invalid employee code or token |
| `UPDATE_FAILED` | 500 | Database write error |

---

## Flutter Integration Guide

### Base Setup
```dart
class ApiConstants {
  static const String baseUrl = 'https://your-app.onrender.com/api/v1';
  static const int connectTimeoutSeconds = 30;
}
```

### Token Refresh Interceptor (Dio)
```dart
// On 401 response:
// 1. Call POST /auth/refresh with stored refresh_token
// 2. Store new access_token
// 3. Retry failed request
// 4. If refresh fails → navigate to login screen
```

### Attendance Check-in Flow
```dart
// 1. Request location permission
// 2. GET /attendance/office  → store office lat/lng/radius
// 3. Get device GPS location
// 4. Upload selfie: POST /attendance/upload-photo (multipart)
// 5. Submit: POST /attendance/check-in with lat/lng/accuracy
```

### File Upload Pattern
```dart
FormData formData = FormData.fromMap({
  'photo': await MultipartFile.fromFile(imagePath, filename: 'photo.jpg'),
});
await dio.post('/attendance/upload-photo', data: formData);
```

---

## Phase 1 Summary

**Total Endpoints Created:** 55+
**New Files:** 10 Python files, 2 utility files
**Dependencies Added:** PyJWT==2.9.0

All existing website routes continue working unchanged.
Website: `/dashboard`, `/attendance`, `/leave` etc. → HTML responses
Mobile API: `/api/v1/dashboard`, `/api/v1/attendance` etc. → JSON responses
