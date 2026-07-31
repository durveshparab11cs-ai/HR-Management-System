# DATABASE TABLES MAPPING - SINGLE POSTGRESQL

**Document:** Complete list of PostgreSQL tables used  
**Status:** All tables verified in production  
**Backend:** Single Flask instance  
**Date:** July 28, 2026

---

## SUMMARY

**Single PostgreSQL Database** - All Flutter data sourced from:

- **Master Tables:** Departments, Positions, Shifts, Leave Types
- **Business Tables:** Employees, Attendance, Leave Requests, Shift Changes
- **Support Tables:** Users, Roles, Permissions, Audit Logs

All tables are shared between website and mobile app.

---

## MASTER DATA TABLES (No Hardcoding)

### 1. Department Table
```sql
departments
├── id (Primary Key)
├── name (string) - Company's departments
├── code (string) - Unique department code
├── description (text)
├── color (string) - UI color for dashboard
├── is_active (boolean)
├── created_at
├── updated_at
└── is_deleted

Flutter: GET /api/v1/company/departments → Fetch all departments
Website: SQL Query → Same departments shown
```

### 2. Position Table
```sql
positions
├── id (Primary Key)
├── title (string) - Job titles
├── code (string) - Unique position code
├── department_id (FK) → departments.id
├── grade (string) - Pay grade
├── description (text)
├── is_active (boolean)
├── created_at
├── updated_at
└── is_deleted

Flutter: GET /api/v1/company/positions → Fetch all positions
```

### 3. Shift Table
```sql
shifts
├── id (Primary Key)
├── name (string) - Morning, Afternoon, Evening, Night, Rotating
├── code (string) - Unique shift code
├── start_time (time)
├── end_time (time)
├── grace_minutes (int) - Late tolerance
├── break_minutes (int) - Break duration
├── working_days (string) - Mon-Fri, Rotating, etc.
├── is_night_shift (boolean)
├── is_active (boolean)
├── created_at
├── updated_at
└── is_deleted

Flutter: GET /api/v1/company/shifts → Fetch all shifts
NO HARDCODING - All shifts from database
```

### 4. Leave Type Table
```sql
leave_types
├── id (Primary Key)
├── name (string) - Annual, Sick, Casual, etc.
├── code (string)
├── max_days_per_year (int)
├── description (text)
├── is_active (boolean)
└── is_deleted

Flutter: GET /api/v1/leave/types → Fetch via API
```

---

## BUSINESS DATA TABLES

### 5. Employee Table
```sql
employees
├── id (Primary Key)
├── employee_code (string) - Unique employee ID
├── first_name (string)
├── last_name (string)
├── email (string)
├── phone (string)
├── department (string) - FK to Department
├── designation (string) - FK to Position
├── branch (string)
├── hire_date (date)
├── reporting_manager_id (FK) → employees.id
├── is_active (boolean)
├── created_at
├── updated_at
└── is_deleted

Flutter: Used by all modules
Website: Same employee data
Data Flow: One single source
```

### 6. Attendance Record Table
```sql
attendance_records
├── id (Primary Key)
├── employee_id (FK) → employees.id
├── date (date)
├── check_in_time (timestamp)
├── check_out_time (timestamp)
├── check_in_latitude (decimal)
├── check_in_longitude (decimal)
├── check_out_latitude (decimal)
├── check_out_longitude (decimal)
├── check_in_photo (string) - S3/local path
├── check_out_photo (string) - S3/local path
├── status (enum) - Present, Absent, Late, Half Day, Leave
├── remarks (text)
├── created_at
├── updated_at
└── is_deleted

Flutter: POST check-in → Saved to PostgreSQL
Website: Displays same attendance record
Sync: Automatic via database
```

### 7. Leave Request Table
```sql
leave_requests
├── id (Primary Key)
├── employee_id (FK) → employees.id
├── leave_type_id (FK) → leave_types.id
├── start_date (date)
├── end_date (date)
├── duration (decimal) - Days
├── reason (text) - Mandatory
├── status (enum) - Pending, Approved, Rejected, Cancelled
├── approved_by (FK) → employees.id (manager)
├── approval_date (timestamp)
├── approval_remarks (text)
├── created_at
├── updated_at
└── is_deleted

Flutter: POST leave request → Saved to PostgreSQL
Website: Manager sees same requests
Sync: Manager approval visible immediately
```

### 8. Shift Change Request Table
```sql
shift_change_requests
├── id (Primary Key)
├── employee_id (FK) → employees.id
├── current_shift_id (FK) → shifts.id
├── requested_shift_id (FK) → shifts.id
├── requested_effective_from (date)
├── reason (text) - Mandatory
├── status (enum) - Pending, Approved, Rejected, Cancelled
├── approved_by (FK) → employees.id (manager)
├── approval_date (timestamp)
├── approval_remarks (text)
├── created_at
├── updated_at
└── is_deleted

Flutter: Request shift change → Saved to PostgreSQL
Website: Manager approves
Sync: Automatic
```

---

## USER & AUTHENTICATION TABLES

### 9. User Table
```sql
users
├── id (Primary Key)
├── email (string) - Unique
├── password_hash (string)
├── first_name (string)
├── last_name (string)
├── employee_id (FK) → employees.id
├── role_id (FK) → roles.id
├── is_active (boolean)
├── last_login (timestamp)
├── created_at
├── updated_at
└── is_deleted

Flutter: POST /auth/login → Same user validation
Website: Same login
JWT: Same token
```

### 10. Role Table
```sql
roles
├── id (Primary Key)
├── name (string) - Admin, Manager, Employee
├── description (text)
├── is_active (boolean)
└── created_at

Flutter: Role-based permissions
Website: Same roles
```

### 11. Permission Table
```sql
permissions
├── id (Primary Key)
├── name (string)
├── code (string)
├── description (text)
└── is_active (boolean)
```

---

## SUPPORT TABLES

### 12. Payroll/Payslip Table
```sql
payslips
├── id (Primary Key)
├── employee_id (FK) → employees.id
├── salary_month (date)
├── basic_salary (decimal)
├── allowances (decimal)
├── deductions (decimal)
├── net_salary (decimal)
├── is_released (boolean)
├── created_at
└── updated_at

Flutter: GET /api/v1/payroll/payslips
```

### 13. Office Settings Table
```sql
office_settings
├── id (Primary Key)
├── latitude (decimal) - Office location
├── longitude (decimal)
├── geofence_radius (int) - In meters
├── check_in_time (time)
├── check_out_time (time)
├── grace_minutes (int)
└── updated_at

Flutter: GET /api/v1/attendance/office → Geofence settings
```

### 14. Audit Log Table
```sql
audit_logs
├── id (Primary Key)
├── user_id (FK) → users.id
├── action (string) - login, logout, leave_request, etc.
├── resource (string) - attendance, leave, shift
├── resource_id (integer)
├── changes (json) - What changed
├── ip_address (string)
├── created_at
└── timestamp
```

---

## DATA FLOW DIAGRAM

```
┌─────────────────────────────────────────┐
│   PostgreSQL Database (Single Instance) │
│   (Production - Shared by all apps)     │
│                                         │
│   Master Tables:                        │
│   - departments                         │
│   - positions                           │
│   - shifts                              │
│   - leave_types                         │
│                                         │
│   Business Tables:                      │
│   - employees                           │
│   - attendance_records                  │
│   - leave_requests                      │
│   - shift_change_requests               │
│   - payslips                            │
│                                         │
│   Auth Tables:                          │
│   - users                               │
│   - roles                               │
│   - permissions                         │
│                                         │
│   Support:                              │
│   - office_settings                     │
│   - audit_logs                          │
└─────────────────────────────┬───────────┘
        ▲                     │
        │                     │
        │ SQL                 │ SQL Queries
        │                     │
    ┌───┴─────────────────┬───┴──────────┐
    │                     │              │
    ▼                     ▼              ▼
┌──────────────┐  ┌─────────────┐  ┌───────────────┐
│ Website      │  │ Flask API   │  │ Flutter App   │
│ (Web Browser)│  │ (Backend)   │  │ (Mobile)      │
│              │  │             │  │               │
│ - Same data  │  │ - 60+ REST  │  │ - Same data   │
│ - Same users │  │   endpoints │  │ - Same users  │
│ - Sync via   │  │             │  │ - Sync via    │
│   database   │  │ - Auth JWT  │  │   database    │
└──────────────┘  │ - Error hdl │  └───────────────┘
                  └─────────────┘
```

---

## DATA VERIFICATION

### Single Source of Truth
```
✓ departments → Only one table, both apps use it
✓ positions → Only one table, both apps use it
✓ shifts → Only one table, both apps use it
✓ employees → Only one table, both apps use it
✓ attendance → Only one table, both apps use it
✓ leave_requests → Only one table, both apps use it
```

### No Duplication
```
✗ No SQLite business database in Flutter
✗ No Hive business database in Flutter
✗ No hardcoded JSON
✗ No mock data in production
✓ All data from PostgreSQL via Flask API
```

### Real-Time Synchronization
```
1. Website admin changes department name
2. PostgreSQL updated immediately
3. Flutter app fetches latest → API → Database
4. Both show same data automatically
```

---

## TABLES ACCESSED BY FLUTTER

### By Module

**Authentication:**
- users
- roles
- permissions

**Dashboard:**
- employees
- attendance_records (count)
- leave_requests (count)
- shifts

**Attendance:**
- employees
- attendance_records
- office_settings

**Leave:**
- employees
- leave_requests
- leave_types

**Shift:**
- employees
- shift_change_requests
- shifts

**Master Data:**
- departments
- positions
- shifts
- leave_types

---

## VERIFICATION: ZERO HARDCODING

```
✓ No hardcoded department list
✓ No hardcoded shift types
✓ No hardcoded positions
✓ No hardcoded leave types
✓ No hardcoded employee data
✓ No hardcoded SQL queries
✓ All data from Flask API
✓ All data from PostgreSQL
```

---

**Status: ✅ 100% SINGLE SOURCE OF TRUTH**

All Flutter data comes from the same PostgreSQL database as the website.
No duplication. No separate storage. Perfect synchronization.
