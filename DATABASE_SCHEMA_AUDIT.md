# DATABASE SCHEMA AUDIT
**PHASE 3 - Complete PostgreSQL Database Documentation**

**Status:** ✅ COMPLETE  
**Date:** July 28, 2026  
**Database:** PostgreSQL (Single instance - shared by website and mobile app)  
**ORM:** SQLAlchemy 2.x  

---

## EXECUTIVE SUMMARY

**20 Core Tables** across 6 functional domains:

1. **Authentication & Users** (3 tables) - Users, LoginHistory, FCMToken
2. **Employee Management** (6 tables) - Employee, EmployeeMaster, EmployeeShiftAssignment, Department, Position, Shift
3. **Attendance Tracking** (5 tables) - Attendance, AttendancePhoto, AttendanceLog, GPSLog
4. **Leave Management** (3 tables) - LeaveType, LeaveRequest, HalfDayRequest, EarlyLeaveRequest (4 total)
5. **Shift Management** (2 tables) - ShiftChangeRequest, ShiftChangeLog
6. **Payroll & Finance** (4 tables) - SalaryStructure, SalaryComponent, PayrollRun, Payslip
7. **Company Master** (3 tables) - CompanyProfile, OfficeSettings, Notification

---

## TABLE DETAILS

### DOMAIN 1: AUTHENTICATION & USERS

#### 1. `users` (BaseModel)
**Primary Table for authentication and user accounts**

| Column | Type | Constraints | Purpose |
|--------|------|-----------|---------|
| id | Integer | PK, auto-increment | Unique identifier |
| email | String(254) | UNIQUE, indexed | Login credential, unique per system |
| first_name | String(100) | NOT NULL | User's first name |
| last_name | String(100) | NOT NULL | User's last name |
| password_hash | String(255) | NOT NULL | bcrypt hashed password |
| role | String(30) | NOT NULL, default="employee", indexed | UserRole enum: admin, hr, manager, employee |
| is_active | Boolean | NOT NULL, default=True | Account status |
| is_locked | Boolean | NOT NULL, default=False | Account locked after failed login attempts |
| failed_login_attempts | Integer | default=0 | Counter for brute force protection |
| last_login_at | DateTime | nullable | Last successful login timestamp |
| created_at | DateTime | default=utcnow | Account creation timestamp |
| updated_at | DateTime | nullable | Last modification timestamp |

**Key Relationships:**
- 1-to-1 with Employee (backref: employee)
- 1-to-many with LoginHistory (backref: login_history)
- 1-to-many with Notification
- 1-to-many with FCMToken

**Business Rules:**
- Every authenticated user must have a unique email
- Role determines access level: admin > hr > manager > employee
- Account locks after N failed attempts (configurable)
- Password must meet strength requirements (via validator)
- At least one admin must exist in system

---

#### 2. `login_history` (db.Model)
**Security audit table - logs every authentication attempt**

| Column | Type | Constraints | Purpose |
|--------|------|-----------|---------|
| id | Integer | PK, auto-increment | Unique identifier |
| user_id | Integer | FK→users.id, nullable, indexed | User who attempted login |
| email_attempted | String(254) | NOT NULL, indexed | Email used in login attempt |
| success | Boolean | NOT NULL, default=False | Success/failure flag |
| ip_address | String(45) | nullable | IPv4/IPv6 address of attempt |
| user_agent | String(255) | nullable | Browser/client identifier |
| failure_reason | String(100) | nullable | Reason if failed (invalid_creds, account_locked, etc.) |
| timestamp | DateTime | NOT NULL, default=utcnow | When attempt occurred |

**Key Relationships:**
- Many-to-one with User

**Business Rules:**
- EVERY login attempt (success OR failure) is logged
- Records retained for compliance/audit trail
- Used to detect suspicious account activity
- Failure reasons help identify attack patterns

---

#### 3. `fcm_tokens` (db.Model)
**Firebase Cloud Messaging tokens for push notifications**

| Column | Type | Constraints | Purpose |
|--------|------|-----------|---------|
| id | Integer | PK, auto-increment | Unique identifier |
| user_id | Integer | FK→users.id, indexed | Token belongs to this user |
| employee_code | String(50) | nullable, indexed | Denormalized for quick lookup |
| token | String(500) | UNIQUE | FCM token from Firebase |
| device_type | String(50) | nullable | chrome, firefox, safari, edge, android, ios |
| user_agent | String(500) | nullable | Full browser/device identifier |
| is_active | Boolean | NOT NULL, default=True | Token active/revoked status |
| created_at | DateTime | default=utcnow | Token registration timestamp |
| last_used_at | DateTime | default=utcnow | Last successful push delivery |

**Key Relationships:**
- Many-to-one with User

**Business Rules:**
- Each device registers one FCM token per session
- Tokens can expire or be revoked
- Multiple tokens per user (different devices/browsers) allowed
- Used exclusively for server→client push notifications



---

### DOMAIN 2: EMPLOYEE MANAGEMENT

#### 4. `employees` (BaseModel)
**Primary HR profile table - HR data separate from User authentication**

| Column | Type | Constraints | Purpose |
|--------|------|-----------|---------|
| id | Integer | PK, auto-increment | Unique identifier |
| user_id | Integer | FK→users.id, UNIQUE, indexed | 1-to-1 link with User account |
| employee_code | String(20) | UNIQUE, indexed | HR system employee ID |
| date_of_birth | Date | nullable | Employee's birth date |
| gender | String(20) | nullable | M / F / Other |
| nationality | String(50) | nullable | Country of citizenship |
| national_id | String(50) | nullable | Passport / National ID number |
| personal_email | String(254) | nullable | Personal email address |
| mobile | String(20) | nullable | Mobile phone number |
| address | Text | nullable | Residential address |
| emergency_contact_name | String(100) | nullable | Emergency contact name |
| emergency_contact_phone | String(20) | nullable | Emergency contact phone |
| department | String(100) | nullable, indexed | Department name (denormalized) |
| designation | String(100) | nullable | Job title / position |
| branch | String(100) | nullable, indexed | Branch / office location name |
| employment_type | String(30) | default="full_time" | full_time \| part_time \| contract \| intern |
| date_joined | Date | nullable | Employment start date |
| date_of_leaving | Date | nullable | Termination date (if left) |
| probation_end_date | Date | nullable | End of probation period |
| shift_name | String(50) | nullable | Current shift name |
| office_settings_id | Integer | FK→office_settings.id, nullable | Office location reference |
| manager_id | Integer | FK→employees.id, nullable | Direct manager's employee ID |
| profile_photo | String(255) | nullable | Photo file path |
| created_at | DateTime | default=utcnow | Record creation timestamp |
| updated_at | DateTime | nullable | Last modification timestamp |

**Key Relationships:**
- 1-to-1 with User (backref: employee)
- 1-to-many with Attendance (backref: attendance_records)
- 1-to-many with LeaveRequest
- Self-referential manager (backref: subordinates)
- Many-to-one with OfficeSettings
- 1-to-many with ShiftChangeRequest
- 1-to-many with ShiftChangeLog

**Business Rules:**
- employee_code must be unique across organization
- user_id must be unique (one User = one Employee)
- Every employee MUST have a manager (except top-level executives)
- Employment type determines leave policies
- Denormalized fields (department, designation, branch) updated by FOSS during imports

---

#### 5. `employee_master` (BaseModel)
**Staging table for bulk employee imports**

| Column | Type | Constraints | Purpose |
|--------|------|-----------|---------|
| id | Integer | PK, auto-increment | Unique identifier |
| employee_code | String(20) | NOT NULL, indexed | HR code from source system |
| first_name | String(100) | NOT NULL | First name |
| last_name | String(100) | NOT NULL | Last name |
| email | String(254) | NOT NULL | Email address |
| department | String(100) | nullable | Department assignment |
| designation | String(100) | nullable | Position/title |
| date_joined | Date | nullable | Employment start date |
| employment_type | String(30) | default="full_time" | Employment type |
| manager_employee_code | String(20) | nullable | Manager's employee code (for linking) |
| shift_name | String(50) | nullable | Assigned shift |
| import_batch_id | String(50) | indexed | Batch identifier for tracking |
| processed | Boolean | default=False | Whether imported into Employee table |
| processed_at | DateTime | nullable | When successfully imported |
| error_message | Text | nullable | Error message if import failed |
| raw_data | Text | nullable | Original row data (JSON) |
| created_at | DateTime | default=utcnow | Import request timestamp |
| updated_at | DateTime | nullable | Last modification timestamp |

**Business Rules:**
- Used for bulk employee imports from external systems
- Records must be validated before processing
- Links to actual employees via employee_code lookup
- Audit trail of all import attempts maintained

---

#### 6. `departments` (BaseModel)
**Company departments (Engineering, HR, Finance, etc.)**

| Column | Type | Constraints | Purpose |
|--------|------|-----------|---------|
| id | Integer | PK, auto-increment | Unique identifier |
| name | String(100) | UNIQUE, NOT NULL | Department name |
| code | String(20) | UNIQUE, NOT NULL, indexed | Short code for reports (ENG, HR, FIN) |
| description | Text | nullable | Department description/purpose |
| head_employee_id | Integer | FK→employees.id, nullable | Department head (Employee) |
| parent_department_id | Integer | FK→departments.id, nullable | Parent department (for hierarchies) |
| is_active | Boolean | default=True | Active/archived status |
| color | String(7) | default="#1a3c6e" | UI color code (hex) |
| created_at | DateTime | default=utcnow | Record creation timestamp |
| updated_at | DateTime | nullable | Last modification timestamp |

**Key Relationships:**
- 1-to-many with Employee (denormalized as department.name)
- Many-to-one with Employee (head_employee_id)
- Self-referential parent_department_id (hierarchical departments)
- API endpoint: GET /api/v1/master/departments

**Business Rules:**
- Department names must be unique
- Department codes must be unique (used in reports)
- Department head is an optional Employee reference
- Support hierarchical departments (sub-departments)

---

#### 7. `positions` (BaseModel)
**Job positions / designations**

| Column | Type | Constraints | Purpose |
|--------|------|-----------|---------|
| id | Integer | PK, auto-increment | Unique identifier |
| title | String(100) | NOT NULL | Position title (Senior Engineer, Manager) |
| code | String(20) | UNIQUE, NOT NULL | Short code |
| department_id | Integer | FK→departments.id, nullable | Department this position belongs to |
| grade | String(20) | nullable | Salary grade / level |
| min_salary | Float | nullable | Minimum salary range |
| max_salary | Float | nullable | Maximum salary range |
| description | Text | nullable | Position description |
| is_active | Boolean | default=True | Active/archived status |
| created_at | DateTime | default=utcnow | Record creation timestamp |
| updated_at | DateTime | nullable | Last modification timestamp |

**Key Relationships:**
- Many-to-one with Department
- API endpoint: GET /api/v1/master/positions

**Business Rules:**
- Position titles must be unique within department
- Codes must be unique globally
- Salary ranges inform payroll calculations
- Positions are master data (created by admin/HR)

---

#### 8. `shifts` (BaseModel)
**Work shift schedules (9-5, 10-6, 24/7 rotations, etc.)**

| Column | Type | Constraints | Purpose |
|--------|------|-----------|---------|
| id | Integer | PK, auto-increment | Unique identifier |
| name | String(100) | NOT NULL | Shift name (Morning, Evening, Night) |
| code | String(20) | UNIQUE, NOT NULL | Short code |
| start_time | Time | default="09:00" | Shift start time |
| end_time | Time | default="18:00" | Shift end time |
| grace_minutes | Integer | default=10 | Grace period for late arrivals |
| break_minutes | Integer | default=60 | Lunch/break duration |
| working_days | String(20) | default="Mon-Fri" | Days worked (Mon-Fri, Sun-Thu, etc.) |
| is_night_shift | Boolean | default=False | Night shift flag (affects overtime) |
| is_active | Boolean | default=True | Active/archived status |
| description | Text | nullable | Shift description |
| created_at | DateTime | default=utcnow | Record creation timestamp |
| updated_at | DateTime | nullable | Last modification timestamp |

**Key Relationships:**
- 1-to-many with Employee (denormalized as shift_name)
- 1-to-many with ShiftChangeRequest (current_shift, requested_shift)
- 1-to-many with EmployeeShiftAssignment
- API endpoint: GET /api/v1/master/shifts

**Business Rules:**
- Shift code must be unique
- start_time < end_time (within same day or next day for night shifts)
- working_days defines which days shift is active
- Grace period applied to check-in time for lateness calculation
- Break time deducted from total working hours



---

### DOMAIN 3: ATTENDANCE TRACKING

#### 9. `attendance` (BaseModel)
**Core attendance record - one row per employee per day**

| Column | Type | Constraints | Purpose |
|--------|------|-----------|---------|
| id | Integer | PK, auto-increment | Unique identifier |
| employee_id | Integer | FK→employees.id, indexed | Employee |
| date | Date | indexed | Attendance date |
| check_in_time | DateTime | nullable | Check-in timestamp |
| check_in_latitude | Float | nullable | GPS latitude at check-in |
| check_in_longitude | Float | nullable | GPS longitude at check-in |
| check_in_accuracy | Float | nullable | GPS accuracy (metres) |
| check_in_distance_metres | Float | nullable | Distance from office geofence |
| check_in_ip | String(45) | nullable | IP address at check-in |
| check_in_device | String(255) | nullable | Device/browser identifier |
| check_in_selfie | String(255) | nullable | (DEPRECATED - use AttendancePhoto) |
| check_out_time | DateTime | nullable | Check-out timestamp |
| check_out_latitude | Float | nullable | GPS latitude at check-out |
| check_out_longitude | Float | nullable | GPS longitude at check-out |
| check_out_accuracy | Float | nullable | GPS accuracy (metres) at check-out |
| check_out_distance_metres | Float | nullable | Distance from office at check-out |
| working_minutes | Integer | nullable | Calculated working minutes |
| overtime_minutes | Integer | nullable | Minutes beyond scheduled shift |
| late_minutes | Integer | nullable | Minutes late from shift start |
| is_late | Boolean | default=False | Late flag |
| is_half_day | Boolean | default=False | Half-day flag |
| is_early_leave | Boolean | default=False | Early leave flag |
| status | String(30) | indexed, default="present" | present \| absent \| half_day \| on_leave \| holiday \| weekend \| wfh |
| is_regularised | Boolean | default=False | Whether absent/late was regularised |
| regularised_by | Integer | FK→users.id, nullable | User who regularised |
| regularisation_reason | String(255) | nullable | Reason for regularisation |
| created_at | DateTime | default=utcnow | Record creation timestamp |
| updated_at | DateTime | nullable | Last modification timestamp |

**Key Relationships:**
- Many-to-one with Employee
- 1-to-1 with AttendancePhoto (if photo exists)
- 1-to-many with AttendanceLog (audit trail)

**Business Rules:**
- Unique constraint: (employee_id, date) - one record per employee per day
- Status computed from check-in, check-out, and leave records
- Lateness calculated: late_minutes = (check_in_time - shift_start_time)
- Early leave calculated: leaves before shift_end_time
- Half-day: working_minutes < threshold (default 300 mins / 5 hours)
- Overtime: working_minutes > scheduled shift duration
- Regularisation: HR can mark absent/late as approved (LOP, regularisation, etc.)

---

#### 10. `attendance_photos` (db.Model)
**Photo proof records from GPS check-ins**

| Column | Type | Constraints | Purpose |
|--------|------|-----------|---------|
| id | Integer | PK, auto-increment | Unique identifier |
| attendance_id | Integer | FK→attendance.id, UNIQUE, indexed | Links to Attendance record |
| employee_id | Integer | FK→employees.id, indexed | Employee (denormalized) |
| file_path | String(255) | default="" | File system path (legacy) |
| original_filename | String(255) | nullable | Original filename from upload |
| file_size_bytes | Integer | nullable | File size |
| mime_type | String(50) | nullable | Image MIME type (image/jpeg) |
| image_data | Text | nullable | Base64-encoded image data URL |
| checkout_image_data | Text | nullable | Base64-encoded check-out photo |
| uploaded_at | DateTime | default=utcnow | Photo upload timestamp |
| ip_address | String(45) | nullable | IP address of uploader |

**Key Relationships:**
- 1-to-1 with Attendance

**Business Rules:**
- Photo stored as base64 in DB (survives deployment ephemerality)
- Unique constraint ensures one photo per attendance record
- Photos are visual proof only - NOT used for biometric verification
- Both check-in and check-out photos supported

---

#### 11. `attendance_logs` (BaseModel)
**Immutable audit trail of attendance state changes**

| Column | Type | Constraints | Purpose |
|--------|------|-----------|---------|
| id | Integer | PK, auto-increment | Unique identifier |
| attendance_id | Integer | FK→attendance.id, indexed | Attendance record being tracked |
| employee_id | Integer | FK→employees.id, indexed | Employee |
| event_type | String(50) | indexed | check_in \| check_out \| regularisation \| status_change |
| old_value | Text | nullable | Previous state (JSON) |
| new_value | Text | nullable | New state (JSON) |
| changed_by_user_id | Integer | FK→users.id, nullable | User who made change |
| ip_address | String(45) | nullable | IP address of change |
| created_at | DateTime | default=utcnow | Change timestamp |

**Business Rules:**
- Immutable log of every state change
- Enables audit trail and compliance reporting
- Captures user who made each change (auto-filled for check-in/out)

---

#### 12. `gps_logs` (db.Model)
**Raw GPS data points from every check-in/check-out attempt**

| Column | Type | Constraints | Purpose |
|--------|------|-----------|---------|
| id | Integer | PK, auto-increment | Unique identifier |
| user_id | Integer | FK→users.id, indexed | User who submitted data |
| employee_id | Integer | FK→employees.id, nullable | Employee (denormalized) |
| latitude | Float | nullable | GPS latitude |
| longitude | Float | nullable | GPS longitude |
| accuracy_metres | Float | nullable | GPS accuracy radius |
| distance_from_office | Float | nullable | Calculated distance from office |
| action | String(30) | check_in \| check_out | Type of action |
| ip_address | String(45) | nullable | Client IP address |
| timestamp | DateTime | default=utcnow | GPS data timestamp |

**Business Rules:**
- Records EVERY GPS attempt regardless of success/failure
- Used for security auditing and location history
- High-frequency log - can grow large (one row per attempt)



---

### DOMAIN 4: LEAVE MANAGEMENT

#### 13. `leave_types` (db.Model)
**Configurable leave types (Casual, Sick, Paid, LOP, CompOff, etc.)**

| Column | Type | Constraints | Purpose |
|--------|------|-----------|---------|
| id | Integer | PK, auto-increment | Unique identifier |
| name | String(50) | UNIQUE, NOT NULL | Leave type name (Casual, Sick) |
| code | String(10) | UNIQUE, NOT NULL | Short code |
| max_days_per_year | Integer | default=12 | Annual entitlement |
| carry_forward | Boolean | default=False | Whether unused days carry to next year |
| requires_document | Boolean | default=False | Medical certificate required |
| is_paid | Boolean | default=True | Whether leave is paid or LOP |
| is_active | Boolean | default=True | Active/archived status |
| color | String(7) | default="#1a3c6e" | UI color code |
| description | Text | nullable | Description |
| created_at | DateTime | default=utcnow | Record creation timestamp |
| updated_at | DateTime | nullable | Last modification timestamp |

**Key Relationships:**
- 1-to-many with LeaveRequest

**Business Rules:**
- Leave type names must be unique
- max_days_per_year defines annual quota
- carry_forward determines whether unused days roll over
- requires_document triggers attachment validation
- is_paid affects salary calculation

---

#### 14. `leave_requests` (BaseModel)
**Employee leave applications with approval workflow**

| Column | Type | Constraints | Purpose |
|--------|------|-----------|---------|
| id | Integer | PK, auto-increment | Unique identifier |
| employee_id | Integer | FK→employees.id, indexed | Employee applying |
| leave_type_id | Integer | FK→leave_types.id | Type of leave |
| start_date | Date | NOT NULL | First day of leave |
| end_date | Date | NOT NULL | Last day of leave |
| total_days | Float | default=1 | Days applied for (can be 0.5 for half-day) |
| reason | Text | NOT NULL | Reason for leave |
| attachment | String(255) | nullable | Medical certificate file path |
| status | String(20) | indexed, default="pending" | pending \| approved \| rejected \| cancelled \| withdrawn |
| applied_on | DateTime | default=utcnow | Application submission date |
| reviewed_by | Integer | FK→users.id, nullable | Approver user ID |
| reviewed_on | DateTime | nullable | Approval/rejection date |
| reviewer_comment | Text | nullable | Approver's comment |
| reporting_manager_code | String(30) | indexed, nullable | Manager's employee code (for routing) |
| reporting_manager_name | String(200) | nullable | Manager's name (denormalized) |
| created_at | DateTime | default=utcnow | Record creation timestamp |
| updated_at | DateTime | nullable | Last modification timestamp |

**Key Relationships:**
- Many-to-one with Employee
- Many-to-one with LeaveType
- Many-to-one with User (reviewed_by)

**Business Rules:**
- start_date ≤ end_date
- total_days calculated from date range minus weekends/holidays
- Overlapping leave applications not allowed
- Approval workflow: Employee → Manager → HR
- Deduction from leave balance on approval
- Can be cancelled by employee if pending
- Requires document attachment for sick leave

---

#### 15. `half_day_requests` (BaseModel)
**Half-day work requests (morning or afternoon)**

| Column | Type | Constraints | Purpose |
|--------|------|-----------|---------|
| id | Integer | PK, auto-increment | Unique identifier |
| employee_id | Integer | FK→employees.id, indexed | Employee applying |
| date | Date | NOT NULL | Date of half-day |
| half_type | String(10) | morning \| afternoon | Which half |
| reason | Text | NOT NULL | Reason for half-day |
| status | String(20) | indexed, default="pending" | pending \| approved \| rejected |
| applied_on | DateTime | default=utcnow | Application date |
| reviewed_by | Integer | FK→users.id, nullable | Approver user ID |
| reviewed_on | DateTime | nullable | Approval/rejection date |
| reviewer_comment | Text | nullable | Approver's comment |
| reporting_manager_code | String(30) | indexed, nullable | Manager's code |
| reporting_manager_name | String(200) | nullable | Manager's name |
| created_at | DateTime | default=utcnow | Record creation timestamp |
| updated_at | DateTime | nullable | Last modification timestamp |

**Key Relationships:**
- Many-to-one with Employee
- Many-to-one with User

**Business Rules:**
- Only one half-day per date
- Morning: before noon, Afternoon: after noon
- Treated as 0.5 day deduction from leave balance
- Must match attendance check-in/out

---

#### 16. `early_leave_requests` (BaseModel)
**Early leave requests - leave before shift end time**

| Column | Type | Constraints | Purpose |
|--------|------|-----------|---------|
| id | Integer | PK, auto-increment | Unique identifier |
| employee_id | Integer | FK→employees.id, indexed | Employee applying |
| date | Date | NOT NULL | Date of early leave |
| requested_leave_time | Time | NOT NULL | Time to leave at |
| reason | Text | NOT NULL | Reason for early leave |
| status | String(20) | indexed, default="pending" | pending \| approved \| rejected |
| applied_on | DateTime | default=utcnow | Application date |
| reviewed_by | Integer | FK→users.id, nullable | Approver user ID |
| reviewed_on | DateTime | nullable | Approval/rejection date |
| reviewer_comment | Text | nullable | Approver's comment |
| reporting_manager_code | String(30) | indexed, nullable | Manager's code |
| reporting_manager_name | String(200) | nullable | Manager's name |
| created_at | DateTime | default=utcnow | Record creation timestamp |
| updated_at | DateTime | nullable | Last modification timestamp |

**Key Relationships:**
- Many-to-one with Employee
- Many-to-one with User

**Business Rules:**
- requested_leave_time must be before shift end time
- Early leave deduction calculated from shift end - leave time
- Marked in attendance as is_early_leave = True



---

### DOMAIN 5: SHIFT MANAGEMENT

#### 17. `shift_change_requests` (BaseModel)
**Employee shift change requests with approval workflow**

| Column | Type | Constraints | Purpose |
|--------|------|-----------|---------|
| id | Integer | PK, auto-increment | Unique identifier |
| employee_id | Integer | FK→employees.id, indexed | Employee requesting change |
| current_shift_id | Integer | FK→shifts.id | Current shift |
| requested_shift_id | Integer | FK→shifts.id, nullable | Requested shift |
| requested_start_time | Time | NOT NULL | Custom start time (if no shift match) |
| requested_end_time | Time | NOT NULL | Custom end time (if no shift match) |
| effective_date | Date | indexed | When change should take effect |
| reason | Text | NOT NULL | Reason for change |
| attachment_path | String(500) | nullable | Supporting document |
| remarks | Text | nullable | Additional remarks |
| reporting_manager_code | String(50) | indexed | Manager's code |
| reporting_manager_name | String(200) | nullable | Manager's name |
| status | String(20) | indexed, default="pending" | pending \| approved \| rejected \| cancelled \| expired \| returned |
| current_approver_level | String(50) | nullable | Current approval stage |
| current_approver_id | Integer | FK→users.id, nullable | Current approver user |
| approved_by | Integer | FK→users.id, nullable | User who approved |
| approved_date | DateTime | nullable | Approval timestamp |
| approval_remarks | Text | nullable | Approver's remarks |
| rejected_by | Integer | FK→users.id, nullable | User who rejected |
| rejected_date | DateTime | nullable | Rejection timestamp |
| rejection_reason | Text | nullable | Rejection reason |
| submitted_date | DateTime | default=utcnow | Application submission date |
| created_at | DateTime | default=utcnow | Record creation timestamp |
| updated_at | DateTime | nullable | Last modification timestamp |

**Key Relationships:**
- Many-to-one with Employee
- Many-to-one with Shift (current_shift, requested_shift)
- Many-to-one with User (approver, approved_by, rejected_by)
- 1-to-1 with EmployeeShiftAssignment (if approved)

**Business Rules:**
- current_shift_id is employee's current shift
- requested_shift_id or custom times must be provided
- effective_date must be in future
- Multi-level approval workflow possible
- On approval, creates EmployeeShiftAssignment record
- Automatic expiry if not acted upon within N days

---

#### 18. `shift_change_logs` (db.Model)
**Immutable audit log of all shift and office location changes**

| Column | Type | Constraints | Purpose |
|--------|------|-----------|---------|
| id | Integer | PK, auto-increment | Unique identifier |
| employee_id | Integer | FK→employees.id, indexed | Employee affected |
| changed_by_user_id | Integer | FK→users.id | User who made change (admin/HR) |
| old_shift_name | String(100) | nullable | Previous shift name |
| new_shift_name | String(100) | nullable | New shift name |
| old_start_time | String(8) | nullable | Previous start time (HH:MM format) |
| new_start_time | String(8) | nullable | New start time |
| old_end_time | String(8) | nullable | Previous end time |
| new_end_time | String(8) | nullable | New end time |
| old_grace_minutes | Integer | nullable | Previous grace period |
| new_grace_minutes | Integer | nullable | New grace period |
| old_office_name | String(100) | nullable | Previous office location |
| new_office_name | String(100) | nullable | New office location |
| old_latitude | String(20) | nullable | Previous office latitude |
| new_latitude | String(20) | nullable | New office latitude |
| old_longitude | String(20) | nullable | Previous office longitude |
| new_longitude | String(20) | nullable | New office longitude |
| old_radius | Integer | nullable | Previous geofence radius (metres) |
| new_radius | Integer | nullable | New geofence radius |
| change_type | String(20) | shift \| location \| both | Type of change |
| reason | Text | nullable | Change reason |
| effective_date | String(12) | nullable | When change took effect |
| changed_at | DateTime | default=utcnow | When change was made |

**Business Rules:**
- Immutable - never updated or deleted
- Enables audit trail of all position/location changes
- Tracks before/after state
- Used for compliance and employee verification



#### 19. `employee_shift_assignments` (BaseModel)
**Historical tracking of employee shift assignments over time**

| Column | Type | Constraints | Purpose |
|--------|------|-----------|---------|
| id | Integer | PK, auto-increment | Unique identifier |
| employee_id | Integer | FK→employees.id, indexed | Employee |
| shift_id | Integer | FK→shifts.id | Assigned shift |
| effective_from | Date | indexed | Start date of assignment |
| effective_until | Date | indexed, nullable | End date of assignment (NULL = current) |
| assigned_by | Integer | FK→users.id | User who made assignment |
| assigned_date | DateTime | default=utcnow | Assignment date |
| shift_change_request_id | Integer | FK→shift_change_requests.id, nullable | Source request (if from approval) |
| reason | Text | nullable | Reason for assignment |
| remarks | Text | nullable | Additional remarks |
| previous_shift_id | Integer | FK→shifts.id, nullable | Previous shift (for audit) |
| created_at | DateTime | default=utcnow | Record creation timestamp |
| updated_at | DateTime | nullable | Last modification timestamp |

**Key Relationships:**
- Many-to-one with Employee
- Many-to-one with Shift (current and previous)
- Many-to-one with ShiftChangeRequest (if created from approval)

**Business Rules:**
- Maintains complete history of shift assignments
- effective_until = NULL means currently active
- Linked to ShiftChangeRequest when created from approval
- Can be created directly by HR/admin
- Tracks who made the assignment and when

---

### DOMAIN 6: PAYROLL & FINANCE

#### 20. `salary_structures` (BaseModel)
**Templates defining salary components for grades/roles**

| Column | Type | Constraints | Purpose |
|--------|------|-----------|---------|
| id | Integer | PK, auto-increment | Unique identifier |
| name | String(100) | UNIQUE, NOT NULL | Structure name |
| code | String(20) | UNIQUE, NOT NULL | Short code |
| description | Text | nullable | Structure description |
| is_active | Boolean | default=True | Active/archived status |
| created_at | DateTime | default=utcnow | Record creation timestamp |
| updated_at | DateTime | nullable | Last modification timestamp |

**Key Relationships:**
- 1-to-many with SalaryComponent (backref: components)

**Business Rules:**
- Codes must be unique (used in reports)
- Templates used to generate payslips
- Can be archived but not deleted (audit trail)

---

#### 21. `salary_components` (BaseModel)
**Individual earnings or deductions within a salary structure**

| Column | Type | Constraints | Purpose |
|--------|------|-----------|---------|
| id | Integer | PK, auto-increment | Unique identifier |
| structure_id | Integer | FK→salary_structures.id, indexed | Parent structure |
| name | String(100) | NOT NULL | Component name (Basic, HRA, etc.) |
| component_type | String(20) | earning \| deduction \| tax \| reimbursement | Type |
| calculation_type | String(20) | fixed \| %_basic \| %_gross | Calculation method |
| value | Float | default=0.0 | Value (amount or percentage) |
| is_taxable | Boolean | default=True | Whether subject to income tax |
| sequence | Integer | default=1 | Display/calculation order |
| created_at | DateTime | default=utcnow | Record creation timestamp |
| updated_at | DateTime | nullable | Last modification timestamp |

**Business Rules:**
- Fixed: use value as-is
- %_basic: value is percentage of basic salary
- %_gross: value is percentage of total earnings
- Earnings added to total, deductions subtracted
- Components processed in sequence order
- Taxable components included in income tax calculation

---

#### 22. `payroll_runs` (BaseModel)
**Monthly payroll processing runs**

| Column | Type | Constraints | Purpose |
|--------|------|-----------|---------|
| id | Integer | PK, auto-increment | Unique identifier |
| month | Integer | 1-12 | Month number |
| year | Integer | 2020+ | Year |
| period_label | String(20) | "July 2026" format | Human-readable label |
| status | String(20) | indexed, default="draft" | draft \| processing \| processed \| approved \| paid \| cancelled |
| total_gross | Float | default=0.0 | Total gross salary for all employees |
| total_deductions | Float | default=0.0 | Total deductions |
| total_net | Float | default=0.0 | Total net salary to be paid |
| employee_count | Integer | default=0 | Number of employees in this run |
| notes | Text | nullable | Processing notes |
| approved_by | Integer | FK→users.id, nullable | User who approved |
| approved_on | DateTime | nullable | Approval timestamp |
| created_at | DateTime | default=utcnow | Run creation timestamp |
| updated_at | DateTime | nullable | Last modification timestamp |

**Key Relationships:**
- 1-to-many with Payslip (backref: payslips)

**Business Rules:**
- One run per month per year
- Status workflow: draft → processing → processed → approved → paid
- Cannot modify once approved
- totals auto-calculated from linked payslips
- HR can cancel and restart

---

#### 23. `payslips` (BaseModel)
**Individual employee payslips for a payroll run**

| Column | Type | Constraints | Purpose |
|--------|------|-----------|---------|
| id | Integer | PK, auto-increment | Unique identifier |
| run_id | Integer | FK→payroll_runs.id, indexed | Parent payroll run |
| employee_id | Integer | FK→employees.id, indexed | Employee |
| basic_salary | Float | default=0.0 | Base salary amount |
| gross_salary | Float | default=0.0 | Total earnings (basic + add-ons) |
| total_deductions | Float | default=0.0 | Total deductions |
| net_salary | Float | default=0.0 | Amount to be paid (gross - deductions) |
| working_days | Integer | default=0 | Total working days in month |
| days_present | Integer | default=0 | Days employee was present |
| days_absent | Integer | default=0 | Days employee was absent |
| leave_days | Integer | default=0 | Days on approved leave |
| earnings_breakdown | Text | nullable | JSON: {component: amount, ...} |
| deductions_breakdown | Text | nullable | JSON: {component: amount, ...} |
| status | String(20) | default="draft" | draft \| final \| paid |
| notes | Text | nullable | Payslip notes |
| created_at | DateTime | default=utcnow | Record creation timestamp |
| updated_at | DateTime | nullable | Last modification timestamp |

**Key Relationships:**
- Many-to-one with PayrollRun
- Many-to-one with Employee

**Business Rules:**
- net_salary = gross_salary - total_deductions
- Working hours/days fetched from Attendance records
- Earnings and deductions stored as JSON breakdown
- Calculated based on SalaryStructure assigned to employee
- Readonly once run is finalized

---

### DOMAIN 7: COMPANY MASTER DATA

#### 24. `company_profile` (BaseModel)
**Singleton company settings table (always id=1)**

| Column | Type | Constraints | Purpose |
|--------|------|-----------|---------|
| id | Integer | PK | Always 1 (singleton) |
| name | String(200) | default="My Company" | Company legal name |
| logo | String(255) | nullable | Logo file path |
| industry | String(100) | nullable | Industry sector |
| website | String(255) | nullable | Company website URL |
| phone | String(30) | nullable | Main phone number |
| email | String(254) | nullable | Support email |
| address | Text | nullable | Registered address |
| city | String(100) | nullable | City |
| state | String(100) | nullable | State/Province |
| country | String(100) | default="India" | Country |
| pin_code | String(20) | nullable | Postal code |
| gstin | String(30) | nullable | GST ID (India) |
| pan | String(20) | nullable | PAN (India) |
| founded_year | Integer | nullable | Founding year |
| employee_count | Integer | default=0 | Current headcount |
| description | Text | nullable | Company description |
| timezone | String(50) | default="Asia/Kolkata" | Server timezone |
| currency | String(10) | default="INR" | Operating currency |
| currency_symbol | String(5) | default="₹" | Currency symbol |
| created_at | DateTime | default=utcnow | Record creation timestamp |
| updated_at | DateTime | nullable | Last modification timestamp |

**Business Rules:**
- Single row (id always = 1)
- Global settings for entire system
- Used in reports, exports, and display
- Timezone used for all datetime calculations

---

#### 25. `office_settings` (BaseModel)
**Branch/office location configuration including GPS geofence**

| Column | Type | Constraints | Purpose |
|--------|------|-----------|---------|
| id | Integer | PK, auto-increment | Unique identifier |
| name | String(100) | default="Head Office" | Office/branch name |
| address | Text | nullable | Office address |
| is_default | Boolean | default=True | Whether this is default office |
| latitude | Float | default=18.520430 | Office GPS latitude |
| longitude | Float | default=73.856743 | Office GPS longitude |
| radius_metres | Integer | default=100 | Geofence radius (metres) |
| min_gps_accuracy_metres | Integer | default=50 | Minimum GPS accuracy required |
| office_start_time | Time | default=09:00 | Office opening time |
| office_end_time | Time | default=18:00 | Office closing time |
| grace_period_minutes | Integer | default=10 | Grace period for late attendance |
| half_day_threshold_minutes | Integer | default=300 | Minutes below = half day (300 = 5 hrs) |
| overtime_threshold_minutes | Integer | default=30 | Minutes over shift = overtime |
| allow_remote_checkin | Boolean | default=False | Whether remote check-in allowed |
| selfie_required | Boolean | default=False | Whether selfie photo required |
| auto_checkout_enabled | Boolean | default=False | Auto-checkout at end time |
| auto_checkout_time | Time | nullable | Auto-checkout time (if enabled) |
| created_at | DateTime | default=utcnow | Record creation timestamp |
| updated_at | DateTime | nullable | Last modification timestamp |

**Business Rules:**
- One default office (is_default = True) for employees with no explicit assignment
- GPS radius defines geofence for attendance
- Latitude/longitude: office location center point
- min_gps_accuracy: browser GPS must be this accurate to allow check-in
- Policies (grace, thresholds) applied per office
- API endpoint: GET /api/v1/master/office-settings



#### 26. `notifications` (db.Model)
**In-app notification records for users**

| Column | Type | Constraints | Purpose |
|--------|------|-----------|---------|
| id | Integer | PK, auto-increment | Unique identifier |
| user_id | Integer | FK→users.id, indexed | Recipient user |
| employee_code | String(50) | indexed, nullable | Employee code (denormalized) |
| employee_name | String(200) | nullable | Employee name (denormalized) |
| title | String(255) | NOT NULL | Notification title |
| message | Text | NOT NULL | Message body |
| module | String(50) | indexed, default="info" | Module category |
| category | String(50) | default="info" | Sub-category (info, success, warning, danger, leave, attendance, payroll, system) |
| reference_id | Integer | nullable | ID of related record (leave_id, attendance_id, etc.) |
| action_url | String(500) | nullable | Deep link to action |
| action_label | String(100) | nullable | Button label |
| is_read | Boolean | indexed, default=False | Read status |
| read_at | DateTime | nullable | When read |
| clicked_at | DateTime | nullable | When action clicked |
| created_at | DateTime | indexed, default=utcnow | Notification creation timestamp |
| triggered_by | Integer | FK→users.id, nullable | User who triggered notification |

**Key Relationships:**
- Many-to-one with User (recipient)
- Many-to-one with User (triggered_by - optional)

**Business Rules:**
- Each notification is per-user (no cross-system broadcast)
- Modules: leave, attendance, payroll, shift, company, reports, settings, foss, admin
- reference_id links to source record for context
- action_url enables deep linking (navigate to specific record in app)
- is_read tracks user engagement

---

### INDEXES & QUERY OPTIMIZATION

**Key Indexes Defined:**

| Table | Columns | Purpose |
|-------|---------|---------|
| users | email, role | Authentication lookup, role-based filtering |
| employees | user_id, employee_code, department, branch, manager_id | Fast employee lookup |
| attendance | employee_id, date, status | Daily attendance queries |
| leave_requests | employee_id, status, start_date | Leave balance queries |
| shift_change_requests | employee_id, status, effective_date | Active request filtering |
| payslips | run_id, employee_id, status | Payroll report queries |
| notifications | user_id, is_read, created_at | User inbox queries |
| login_history | user_id, timestamp, email_attempted | Security audits |
| gps_logs | user_id, employee_id, timestamp | Location tracking |

---

## RELATIONSHIPS DIAGRAM

```
┌─ AUTHENTICATION ──────────────────────────────────
│
│  User (users)
│    ├─ 1-to-1 → Employee
│    ├─ 1-to-many → LoginHistory
│    ├─ 1-to-many → FCMToken
│    └─ 1-to-many → Notification
│
├─ EMPLOYEE MANAGEMENT ─────────────────────────────
│
│  Employee (employees)
│    ├─ Many-to-one ← User
│    ├─ 1-to-many → Attendance
│    ├─ 1-to-many → LeaveRequest
│    ├─ 1-to-many → ShiftChangeRequest
│    ├─ Self-ref → Manager (many-to-one)
│    ├─ 1-to-many → EmployeeShiftAssignment
│    └─ Many-to-one → OfficeSettings
│
│  Department (departments)
│    └─ Many-to-one ← Employee (denormalized)
│
│  Position (positions)
│    └─ Many-to-one → Department
│
│  Shift (shifts)
│    ├─ 1-to-many ← Employee (denormalized as shift_name)
│    ├─ 1-to-many → ShiftChangeRequest
│    ├─ 1-to-many → EmployeeShiftAssignment
│    └─ 1-to-many → ShiftChangeLog
│
├─ ATTENDANCE TRACKING ─────────────────────────────
│
│  Attendance (attendance)
│    ├─ Many-to-one → Employee
│    ├─ 1-to-1 → AttendancePhoto
│    └─ 1-to-many → AttendanceLog
│
│  AttendancePhoto (attendance_photos)
│    └─ 1-to-1 → Attendance
│
│  AttendanceLog (attendance_logs)
│    └─ Many-to-one → Attendance
│
│  GPSLog (gps_logs)
│    ├─ Many-to-one → User
│    └─ Many-to-one → Employee
│
├─ LEAVE MANAGEMENT ────────────────────────────────
│
│  LeaveType (leave_types)
│    └─ 1-to-many ← LeaveRequest
│
│  LeaveRequest (leave_requests)
│    ├─ Many-to-one → Employee
│    ├─ Many-to-one → LeaveType
│    └─ Many-to-one → User (reviewed_by)
│
│  HalfDayRequest (half_day_requests)
│    ├─ Many-to-one → Employee
│    └─ Many-to-one → User (reviewed_by)
│
│  EarlyLeaveRequest (early_leave_requests)
│    ├─ Many-to-one → Employee
│    └─ Many-to-one → User (reviewed_by)
│
├─ SHIFT MANAGEMENT ────────────────────────────────
│
│  ShiftChangeRequest (shift_change_requests)
│    ├─ Many-to-one → Employee
│    ├─ Many-to-one → Shift (current, requested)
│    ├─ Many-to-one → User (approver)
│    └─ 1-to-1 → EmployeeShiftAssignment (if approved)
│
│  EmployeeShiftAssignment (employee_shift_assignments)
│    ├─ Many-to-one → Employee
│    ├─ Many-to-one → Shift
│    ├─ Many-to-one → User (assigned_by)
│    └─ Many-to-one → ShiftChangeRequest
│
│  ShiftChangeLog (shift_change_logs)
│    ├─ Many-to-one → Employee
│    └─ Many-to-one → User (changed_by)
│
├─ PAYROLL & FINANCE ───────────────────────────────
│
│  SalaryStructure (salary_structures)
│    └─ 1-to-many → SalaryComponent
│
│  SalaryComponent (salary_components)
│    └─ Many-to-one → SalaryStructure
│
│  PayrollRun (payroll_runs)
│    ├─ 1-to-many → Payslip
│    └─ Many-to-one → User (approved_by)
│
│  Payslip (payslips)
│    ├─ Many-to-one → PayrollRun
│    └─ Many-to-one → Employee
│
└─ COMPANY MASTER ──────────────────────────────────

   CompanyProfile (company_profile)
   OfficeSettings (office_settings)
   Notification (notifications)
```

---

## KEY BUSINESS RULES BY DOMAIN

### Authentication
- Every user must have unique email
- Password policy: minimum 8 chars, 1 uppercase, 1 digit, 1 special
- Account locks after 5 failed login attempts
- Failed login attempts reset after 24 hours
- Login history retained indefinitely (compliance)

### Employee Management
- One employee = one user (1-to-1 relationship)
- Employee code must be globally unique
- Manager hierarchy enforced (non-cyclical)
- Department and designation denormalized from master data
- Employment type determines leave policies and benefits

### Attendance
- One attendance record per employee per day
- Status: present, absent, half_day, on_leave, holiday, weekend, wfh
- Lateness calculated: check_in_time - shift_start_time
- Half-day: working_minutes < half_day_threshold (default 300 min)
- Overtime: working_minutes > scheduled shift
- GPS accuracy minimum: 50 metres
- Photos stored as base64 (ephemeral filesystem tolerance)

### Leave
- Leave balance calculated from LeaveType.max_days_per_year
- Cannot apply for overlapping dates
- Approval workflow: Employee → Manager → HR
- Medical certificate required for sick leave
- Leave deducted on approval (not on application)
- Half-day = 0.5 day deduction

### Shift Management
- Grace period applied to attendance calculation
- Shift change requires approval workflow
- Effective date must be in future
- Multiple shifts per employee (historical tracking)
- Changes logged for audit trail

### Payroll
- One payroll run per month per year
- Status workflow: draft → processing → processed → approved → paid
- Payslip calculated from SalaryStructure assigned to employee
- Components include: Basic, HRA, Conveyance, Allowances, Deductions, Tax
- Net salary = Gross salary - Total deductions
- Working days fetched from Attendance records

### Notifications
- Per-user inbox (not system-wide broadcast)
- Categories: leave, attendance, payroll, shift, company, reports, settings, foss, admin
- Reference ID links to source record
- Deep action links for navigation
- Read status tracked for engagement metrics

---

## DATABASE INTEGRITY CONSTRAINTS

**Foreign Key Constraints:**
- All foreign keys configured with CASCADE or RESTRICT (prevents orphaned records)
- Referential integrity enforced at DB level

**Unique Constraints:**
- users.email
- employees.user_id (1-to-1)
- employees.employee_code
- departments.name, departments.code
- positions.code
- shifts.code
- leave_types.name, leave_types.code
- salary_structures.name, salary_structures.code
- attendance_photos.attendance_id (1-to-1)
- fcm_tokens.token

**Indexes:**
- All foreign keys indexed for join performance
- Status columns indexed (frequent WHERE clauses)
- Date columns indexed (range queries)
- user_id and employee_id indexed universally
- Composite indexes on (employee_id, date) for attendance queries

---

## DATA CONSISTENCY RULES

1. **Attendance & Leave Overlap:**
   - If attendance.status = "on_leave", LeaveRequest must exist for that date
   - LeaveRequest.status must be "approved"

2. **Employee & User:**
   - Every Employee must have linked User
   - Every User with role != "admin" should have linked Employee
   - Email in both User and Employee must match

3. **Shift & Office:**
   - Employee has office_settings_id OR inherits from default office
   - OfficeSettings.is_default = True must exist exactly once

4. **Manager Hierarchy:**
   - Employee.manager_id cannot create cycles
   - Manager must be active employee

5. **Payroll Processing:**
   - Employee must exist before adding to PayrollRun
   - All Attendance records for month must exist before finalizing run

---

## AUDIT & COMPLIANCE

**Tables with Immutable Logs:**
- LoginHistory - every authentication attempt
- AttendanceLog - every attendance state change
- ShiftChangeLog - every shift/location change
- GPS Logs - every geolocation data point

**Retention Policy:**
- LoginHistory: indefinite (compliance requirement)
- AttendanceLog: indefinite
- ShiftChangeLog: indefinite
- GPS Logs: 90 days rolling (high-volume, temporary)
- Notifications: 30 days rolling (automatic cleanup)

**Audit Trail:**
- User WHO made each change tracked
- Timestamp of each change tracked
- IP address of change (where applicable)
- Before/after state stored (in logs table)

---

## MIGRATION & DEPLOYMENT NOTES

- All models inherit from `BaseModel` which adds: id (PK), created_at, updated_at
- TimeZone: Use `DateTime(timezone=True)` for all timestamps
- ORM: SQLAlchemy 2.x with type hints (Mapped[])
- Migrations: Use Alembic for schema changes
- Foreign key constraints: Cascade delete carefully (retention requirements)

---

**PHASE 3 COMPLETE** ✅

**Total Tables Audited:** 20 core tables + 6 supporting tables = 26 tables  
**Total Relationships:** 50+ documented  
**Total Columns:** 300+ analyzed  
**Data Consistency Rules:** 5 major rules enforced  

**Next Phase:** PHASE 4 - Remove all hardcoded/mock data from Flutter app
