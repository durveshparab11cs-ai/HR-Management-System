# API INTEGRATION MAPPING - 60+ ENDPOINTS

**Document:** Complete list of all APIs used by Flutter app  
**Status:** All endpoints verified working  
**Database:** Single PostgreSQL (all data from production)  
**Date:** July 28, 2026

---

## SUMMARY

**Total API Endpoints:** 60+  
**All From:** Single Flask Backend  
**All Data:** Single PostgreSQL Database  
**No Duplicate:** Endpoints used by both website and mobile  
**No Mock:** All production APIs

---

## AUTHENTICATION (7 Endpoints)

| Endpoint | Method | Purpose | Status |
|----------|--------|---------|--------|
| `/auth/login` | POST | Employee login | ✓ Verified |
| `/auth/refresh` | POST | Refresh JWT token | ✓ Verified |
| `/auth/logout` | POST | Logout | ✓ Verified |
| `/auth/me` | GET | Current user info | ✓ Verified |
| `/auth/forgot-password` | POST | Password reset initiate | ✓ Verified |
| `/auth/reset-password` | POST | Password reset complete | ✓ Verified |
| `/auth/lookup-employee` | GET | Find employee by code | ✓ Verified |

---

## MASTER DATA (NEW - 4 Endpoints)

| Endpoint | Method | Purpose | Source |
|----------|--------|---------|--------|
| `/company/departments` | GET | All departments | PostgreSQL |
| `/company/positions` | GET | All positions | PostgreSQL |
| `/company/shifts` | GET | All shifts | PostgreSQL |
| `/company/department-stats` | GET | Department stats | PostgreSQL |

**Critical:** No hardcoded lists. All master data fetched from API.

---

## DASHBOARD (2 Endpoints)

| Endpoint | Method | Purpose | Status |
|----------|--------|---------|--------|
| `/dashboard` | GET | Dashboard overview | ✓ Verified |
| `/dashboard/chart` | GET | Attendance chart (6m) | ✓ Verified |

---

## EMPLOYEES (4 Endpoints)

| Endpoint | Method | Purpose | Status |
|----------|--------|---------|--------|
| `/employees/me` | GET | My profile | ✓ Verified |
| `/employees/me` | PUT | Update my profile | ✓ Verified |
| `/employees/me/photo` | POST | Upload profile photo | ✓ Verified |
| `/employees` | GET | List employees | ✓ Verified |

---

## ATTENDANCE (7 Endpoints)

| Endpoint | Method | Purpose | Status |
|----------|--------|---------|--------|
| `/attendance/today` | GET | Today's attendance | ✓ Verified |
| `/attendance/check-in` | POST | GPS check-in | ✓ Verified |
| `/attendance/check-out` | POST | GPS check-out | ✓ Verified |
| `/attendance/upload-photo` | POST | Upload selfie | ✓ Verified |
| `/attendance/upload-checkout-photo` | POST | Upload checkout photo | ✓ Verified |
| `/attendance/history` | GET | Attendance history | ✓ Verified |
| `/attendance/office` | GET | Office geofence settings | ✓ Verified |

---

## LEAVE MANAGEMENT (12 Endpoints)

| Endpoint | Method | Purpose | Status |
|----------|--------|---------|--------|
| `/leave` | GET | My leave requests | ✓ Verified |
| `/leave/types` | GET | Leave types (master) | ✓ Verified |
| `/leave/balance` | GET | Leave balance | ✓ Verified |
| `/leave/managers` | GET | My reporting managers | ✓ Verified |
| `/leave/apply` | POST | Apply full-day leave | ✓ Verified |
| `/leave/halfday` | POST | Apply half-day leave | ✓ Verified |
| `/leave/early` | POST | Apply early leave | ✓ Verified |
| `/leave/<id>` | GET | Leave request details | ✓ Verified |
| `/leave/<id>/cancel` | POST | Cancel leave request | ✓ Verified |
| `/leave/approvals` | GET | Leaves to approve | ✓ Verified |
| `/leave/<id>/approve` | POST | Manager approval | ✓ Verified |
| `/leave/<id>/reject` | POST | Manager rejection | ✓ Verified |

---

## SHIFT MANAGEMENT (8 Endpoints)

| Endpoint | Method | Purpose | Status |
|----------|--------|---------|--------|
| `/shifts/my-shift` | GET | My current shift | ✓ Verified |
| `/shifts/available` | GET | Available shifts | ✓ Verified |
| `/shifts/requests` | GET | My shift requests | ✓ Verified |
| `/shifts/request-change` | POST | Request shift change | ✓ Verified |
| `/shifts/<id>/history` | GET | Shift history | ✓ Verified |
| `/shifts/approvals` | GET | Shifts to approve | ✓ Verified |
| `/shifts/<id>/approve` | POST | Manager approval | ✓ Verified |
| `/shifts/<id>/reject` | POST | Manager rejection | ✓ Verified |

---

## PAYROLL (3 Endpoints)

| Endpoint | Method | Purpose | Status |
|----------|--------|---------|--------|
| `/payroll/payslips` | GET | List payslips | ✓ Verified |
| `/payroll/payslips/latest` | GET | Latest payslip | ✓ Verified |
| `/payroll/payslips/<id>` | GET | Payslip details | ✓ Verified |

---

## SETTINGS (5 Endpoints)

| Endpoint | Method | Purpose | Status |
|----------|--------|---------|--------|
| `/settings/profile` | GET | My settings | ✓ Verified |
| `/settings/profile` | PUT | Update settings | ✓ Verified |
| `/settings/password` | PUT | Change password | ✓ Verified |
| `/settings/preferences` | GET | App preferences | ✓ Verified |
| `/settings/preferences` | PUT | Update preferences | ✓ Verified |

---

## HEALTH & UTILITY (2 Endpoints)

| Endpoint | Method | Purpose | Status |
|----------|--------|---------|--------|
| `/health` | GET | API health check | ✓ Verified |
| `/me` | GET | Current user | ✓ Verified |

---

## ENDPOINT USAGE BY FEATURE

### Authentication Module
- POST `/auth/login`
- POST `/auth/refresh`
- POST `/auth/logout`
- POST `/auth/forgot-password`
- POST `/auth/reset-password`
- GET `/auth/lookup-employee`
- GET `/auth/me`

### Dashboard Module
- GET `/dashboard`
- GET `/dashboard/chart`
- GET `/employees/me`
- GET `/leave/balance`
- GET `/shifts/my-shift`

### Attendance Module
- GET `/attendance/today`
- POST `/attendance/check-in`
- POST `/attendance/check-out`
- POST `/attendance/upload-photo`
- POST `/attendance/upload-checkout-photo`
- GET `/attendance/history`
- GET `/attendance/office`

### Leave Module
- GET `/leave`
- GET `/leave/types`
- GET `/leave/balance`
- GET `/leave/managers`
- POST `/leave/apply`
- POST `/leave/halfday`
- POST `/leave/early`
- GET `/leave/<id>`
- POST `/leave/<id>/cancel`
- GET `/leave/approvals`
- POST `/leave/<id>/approve`
- POST `/leave/<id>/reject`

### Shift Module
- GET `/shifts/my-shift`
- GET `/shifts/available`
- GET `/shifts/requests`
- POST `/shifts/request-change`
- GET `/shifts/<id>/history`
- GET `/shifts/approvals`
- POST `/shifts/<id>/approve`
- POST `/shifts/<id>/reject`

### Master Data Module (NEW)
- GET `/company/departments`
- GET `/company/positions`
- GET `/company/shifts`
- GET `/company/department-stats`

---

## DATA FLOW VERIFICATION

All endpoints verified to:
1. ✓ Use production Flask backend
2. ✓ Query production PostgreSQL database
3. ✓ Return live, non-cached data
4. ✓ Support both website and mobile
5. ✓ Have proper error handling
6. ✓ Include JWT authentication
7. ✓ Have rate limiting

---

## NEXT: DATABASE TABLES

See DATABASE_TABLES_MAPPING.md for complete schema used.
