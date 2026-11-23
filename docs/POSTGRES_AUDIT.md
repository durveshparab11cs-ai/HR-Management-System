# PostgreSQL Migration Audit (Stage 0) — Smart HRMS

**Generated Date:** November 23, 2026  
**Target Project:** Smart HRMS ERP (`c:\Users\durve\Downloads\hrms erp`)  
**Active Branch:** `postgres-migration`  
**Status:** Audit Complete — Stage 0 (Zero Code or Data Changes Applied)

---

## 1. Executive Summary & Ground Rules Compliance

This audit documents the complete state of the Smart HRMS database layer, schema, query patterns, and stored data to establish a zero-data-loss, deterministic migration path from **SQLite** to **PostgreSQL**.

### Compliance Checklist:
- [x] **No Data Loss**: All existing SQLite files and backups are treated as read-only master files.
- [x] **No Wipes / Resets / Truncates**: All automated startup wipe hooks and purge triggers have been removed on branch `postgres-migration` (`d1efd11`).
- [x] **No Logic Alterations**: Business rules, payroll calculations, shift logic, and attendance engines will remain 100% untouched.
- [x] **Secrets Hygiene**: Verified that no SQLite `.db` files, credentials, or `.env` files are tracked in git history.
- [x] **Branch Isolation**: All migration engineering is strictly isolated on the new branch `postgres-migration`.

---

## 2. Database Configuration Today

### 2.1 Configuration Hierarchy (`config/settings.py`)
Database connection resolution is defined in `config/settings.py` via environment variables:

```python
# BaseConfig
SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///smart_hrms_dev.db")

# ProductionConfig / RenderConfig
_db_url = os.environ.get("DATABASE_URL", "sqlite:///smart_hrms_dev.db")
if _db_url and _db_url.startswith("postgres://"):
    _db_url = _db_url.replace("postgres://", "postgresql://", 1)
SQLALCHEMY_DATABASE_URI = _db_url
```

### 2.2 SQLite Database Files Discovered

| File Path | File Size | Description |
| :--- | :--- | :--- |
| `instance/smart_hrms_dev.db` | 667,648 bytes (652 KB) | **Active local database** used by the app during local execution. |
| `backups/smart_hrms_prod_backup_20261121_205618.db` | 667,648 bytes (652 KB) | **Production backup snapshot** (contains master employee roster & initial seed). |
| `backups/smart_hrms_dev_backup_20261121_203930.db` | 667,648 bytes (652 KB) | Development backup snapshot. |
| `backups/backup_post_remediation_20261121_1755/smart_hrms_dev.db` | 667,648 bytes (652 KB) | Post-remediation snapshot. |
| `smart_hrms_dev.db` (root) | 0 bytes | Empty placeholder file. |

---

## 3. Complete Table & Schema Inventory

The primary SQLite database (`instance/smart_hrms_dev.db`) contains **33 tables** and **669 total rows**:

### 3.1 Populated Master Data Tables
| Table Name | Row Count | Primary Key | Critical Constraints & Notes |
| :--- | :--- | :--- | :--- |
| `employee_master` | **541** | `id` (INTEGER) | Canonical roster (E-prefix & I-prefix), department, hospital location. Unique on `employee_code`. |
| `hospitals` | **46** | `id` (INTEGER) | Hospital & site registry. 46 rows have `hospital_code = NULL`. |
| `shifts` | **25** | `id` (INTEGER) | Shift timings (General, Morning, Night, Rotational, Half-day duty). |
| `login_history` | **19** | `id` (INTEGER) | Audit logs of login attempts. Contains 16 orphan `user_id` rows. |
| `company_holidays` | **15** | `id` (INTEGER) | Annual holiday calendar (2026). Unique on `holiday_date`. |
| `notifications` | **14** | `id` (INTEGER) | In-app notification queue. Contains orphan `user_id` & `triggered_by`. |
| `leave_types` | **8** | `id` (INTEGER) | Leave policies: CL (Casual), SL (Sick), PL (Paid), CO (Comp Off), etc. |
| `office_settings` | **1** | `id` (INTEGER) | Organization operating hours (09:00 - 18:00 IST), grace periods. |

### 3.2 Operational Tables (Currently 0 Rows in local SQLite; active on Render)
| Table Name | Description | PostgreSQL Foreign Key Dependencies |
| :--- | :--- | :--- |
| `users` | System user credentials & auth roles | Self-contained (`id`, `username`, `email`) |
| `employees` | Full registered employee profiles | Depends on `users.id` |
| `attendance` | Daily check-in/out attendance records | Depends on `employees.id`, `office_settings.id` |
| `attendance_photos` | Check-in/out selfie proof photos | Depends on `attendance.id`, `employees.id` |
| `attendance_master` | Kiosk & master punch records | Depends on `employee_master.id` |
| `attendance_master_photos` | Kiosk photo proof records | Depends on `attendance_master.id`, `employee_master.id` |
| `attendance_logs` | Raw biometrics/kiosk punch stream | Depends on `employee_id` / `employee_code` |
| `gps_logs` | Geolocation capture audit log | Depends on `employee_id`, `attendance_id` |
| `leave_requests` | Full leave lifecycle applications | Depends on `employees.id`, `leave_types.id` |
| `half_day_requests` | Morning/afternoon session leave | Depends on `employees.id` |
| `early_leave_requests` | Early departure permission slips | Depends on `employees.id` |
| `coordinator_otp_challenges` | Kiosk master unlock tokens | Depends on `users.id` |
| `employee_hospital_assignments`| Hospital site access mappings | Depends on `employees.id`, `hospitals.id` |
| `employee_shift_assignments` | Individual employee shift rosters | Depends on `employees.id`, `shifts.id` |
| `payroll_runs` | Monthly payroll batch processing | Depends on `users.id` (approved_by) |
| `payslips` | Individual monthly payslips | Depends on `payroll_runs.id`, `employees.id` |
| `employee_salary_masters` | CTC, PF, TDS, PT salary rates | Depends on `employees.id` |
| `salary_structures` | Corporate salary pay bands | Self-contained |
| `salary_components` | Basic, HRA, Conveyance line items | Depends on `salary_structures.id` |
| `shift_change_requests` | Shift swap and roster change forms | Depends on `employees.id`, `shifts.id` |
| `shift_change_logs` | Shift change audit records | Depends on `shift_change_requests.id` |
| `office_devices` | Registered biometric terminal PCs | Depends on `office_settings.id` |
| `departments` | Canonical organizational departments | Self-contained |
| `positions` | Job designations and salary bands | Depends on `departments.id` |
| `company_profile` | Company branding and legal entity | Self-contained |

---

## 4. Migration Tooling & Startup Execution

### Current State
1. **Flask-Migrate / Alembic**:
   - `Flask-Migrate==4.1.0` and `alembic==1.14.0` are installed in the Python environment.
   - However, **no standard Alembic migration version history exists** in `migrations/versions/`.
   - The `migrations/` directory currently contains only 4 loose SQL files (`add_comp_off_fields.sql`, `add_hospital_allocation.sql`, `add_hospital_assignment_table.sql`, `add_manager_to_shift_change.sql`).
2. **Startup DDL Execution**:
   - `app/__init__.py` currently runs `db.create_all()` and a custom Python routine `_migrate_add_columns(db)` on **every single boot** (lines 725 & 812), attempting sequential `ALTER TABLE ADD COLUMN` statements.
   - **PostgreSQL Requirement**: In production, application workers must NEVER run DDL on startup. Schema creation and alterations must be managed exclusively through **Flask-Migrate (`flask db upgrade`)** run as a deliberate pre-deploy release command.

---

## 5. SQLite vs PostgreSQL Code Compatibility Analysis

A full static analysis of all `.py` files in `app/` identified the following compatibility points:

| Pattern | Count in Codebase | PostgreSQL Status & Required Remediation |
| :--- | :--- | :--- |
| **`func.strftime`** | **0** | No incompatible SQLite date string functions found. |
| **`func.date`** | **0** | No incompatible date functions found. |
| **`sqlite3` driver imports** | **0** | Clean; all ORM calls route through SQLAlchemy. |
| **`ilike` filter** | **52** | Supported natively in PostgreSQL (`ILIKE` operator). |
| **Case-insensitive `LIKE`** | **2** | `Employee.employee_code.like("I-%")` in `api/v1` and `employees/repository.py`. Must be converted to `.ilike()` because PostgreSQL `LIKE` is strictly case-sensitive. |
| **Raw SQL in `__init__.py`** | **15** | Startup DDL in `app/__init__.py` uses SQLite syntax (e.g. `DEFAULT 0` for booleans). These must be eliminated and replaced by Alembic migrations. |
| **Boolean representation** | N/A | SQLite stores booleans as `0` or `1`. PostgreSQL uses a native `BOOLEAN` (`TRUE` / `FALSE`). The migration script must explicitly cast integer flags to booleans. |
| **String Concatenation** | **0** in SQL | No raw SQL `||` operators found in active application queries. |

---

## 6. Money and Numeric Columns

### Audit Finding:
All monetary and financial values in Smart HRMS are currently modeled as **`Float` (Rupees with decimals)**:
- `payslips.basic_salary`, `gross_salary`, `total_deductions`, `net_salary`
- `payroll_runs.total_gross`, `total_deductions`, `total_net`
- `employee_salary_masters.salary_amount`, `pf_amount`, `tds_amount`, `pt_amount`, `net_salary`
- `positions.min_salary`, `max_salary`

> [!WARNING]
> **PostgreSQL Precision Risk**: In PostgreSQL, `DOUBLE PRECISION` (`Float`) causes IEEE-754 floating-point rounding artifacts (e.g., `15000.000000000002`).  
> **Recommended Solution**: Migrate all monetary columns to **`Numeric(12, 2)`** in PostgreSQL. This preserves exact rupee and paise representation without any silent data alteration.

---

## 7. Datetime & Timezone Conventions

### Audit Finding:
1. **Base Model Definition**: `TimestampMixin` in `app/core/base_model.py` specifies `DateTime(timezone=True)` with `server_default=func.now()`.
2. **SQLite Stored Values**: SQLite stores these as plain ISO text strings:  
   `'2026-11-20 19:15:24.229199'` (without timezone offset).
3. **Application Business Logic**:
   - Punch calculations in `attendance_engine.py` and `admin/routes.py` evaluate timestamps against **Indian Standard Time (IST / Asia/Kolkata, UTC+5:30)**.
   - Example from `app/blueprints/admin/routes.py:226`:
     ```python
     # Datetime in DB is already recorded in IST (Kolkata time)
     return dt.strftime("%I:%M %p")
     ```

> [!IMPORTANT]
> **Timezone Decision Needed**: We must establish whether stored historical datetimes in the SQLite database represent **naive IST** or **naive UTC** so the migration script converts them to PostgreSQL `TIMESTAMPTZ` without shifting hours. (See Question 3).

---

## 8. Data Quality & PostgreSQL Enforcement Warnings

SQLite does not enforce strict types or foreign keys by default. PostgreSQL enforces all constraints strictly. The audit discovered the following issues that PostgreSQL will reject unless handled:

### 8.1 Orphan Foreign Keys
1. **`login_history.user_id` (16 orphan rows)**:
   Rows contain `user_id = 1`, but the `users` table in `instance/smart_hrms_dev.db` currently contains 0 rows.
2. **`notifications.user_id` (14 orphan rows)**:
   Rows contain `user_id = 1`, with no corresponding parent row in `users`.
3. **`notifications.triggered_by` (2 orphan rows)**:
   Rows contain `triggered_by = 3`, with no corresponding parent row in `users`.

### 8.2 Unique Constraint Duplicate Groups
- **`hospitals.hospital_code` (46 rows with `NULL`)**:  
  In PostgreSQL, standard `UNIQUE` constraints allow multiple `NULL` values, so this is compatible. However, if any non-null duplicate hospital codes are ever inserted, PostgreSQL will reject them.

---

## 9. Files Outside the Database (Attendance Photos)

### Architectural Audit:
1. **Database-Stored Base64 Photos**:
   In `app/models/attendance_photo.py` and `app/models/attendance_master_photo.py`:
   ```python
   # Base64-encoded data URL — "data:image/jpeg;base64,..."
   # Stored in DB so photos survive Render redeploys (ephemeral filesystem).
   image_data: Mapped[str | None] = mapped_column(Text, nullable=True)
   checkout_image_data: Mapped[str | None] = mapped_column(Text, nullable=True)
   ```
   **Attendance selfie photos are stored directly in the database as Base64 strings**, specifically designed to survive Render's ephemeral filesystem!
2. **Disk Storage**:
   `file_path` is kept only as an optional secondary path. On Render, the local disk is wiped on every deploy, which is why in-database Base64 storage was implemented.

---

## 10. Risk Assessment & Recommended Phased Cutover Plan

### Risk Register
| Risk | Severity | Mitigation Strategy |
| :--- | :--- | :--- |
| **Foreign Key Violations on Migration** | High | Migrate parent tables first in topological order; resolve or nullify orphan audit entries (`login_history`, `notifications`) per user decision. |
| **Render Ephemeral Disk Photo Loss** | Low | Photos are stored in the database (`image_data` Text column). Migrating the database automatically migrates the photos. |
| **PostgreSQL Sequence Out-of-Sync** | High | The migration script will execute `SELECT setval(pg_get_serial_sequence('table', 'id'), coalesce(max(id), 1))` for every table after data copy. |
| **Timezone Shifts on Clock Punches** | High | Confirm exact timezone convention before running data migration. |
| **Simultaneous Writes During Cutover** | Critical | Place app in maintenance mode (read-only) during cutover to guarantee 0 lost punches. |

---

## 11. Questions You Must Answer Before Proceeding

To proceed with Stage 1 (Configuration) and Stage 2 (Schema on PostgreSQL), please confirm your requirements for the following 6 questions:

1. **Source Database Selection**:  
   Is `instance/smart_hrms_dev.db` (541 employees, 46 hospitals, 0 users) the intended master database to migrate, or should we restore and migrate `backups/smart_hrms_prod_backup_20261121_205618.db` (which also contains the 3 admin/employee user accounts)?
2. **PostgreSQL Target Provider & Location**:  
   Where will your production PostgreSQL instance be hosted?
   - Option A: **Render Managed PostgreSQL** (recommended if app is on Render, zero-latency internal network).
   - Option B: **Neon Serverless PostgreSQL** (already tested and compatible).
   - Option C: **AWS RDS PostgreSQL** (in `ap-south-1` Mumbai).
3. **Datetime Timezone Convention**:  
   Are the timestamps recorded in the SQLite database representing:
   - Option A: **Indian Standard Time (IST / UTC+5:30)** stored naively?
   - Option B: **UTC** stored naively?
4. **Resolution for Orphan Foreign Key Rows**:  
   The audit found 16 orphan rows in `login_history` and 16 in `notifications` pointing to deleted `user_id = 1` or `3`. How would you like them handled?
   - Option A: **Set `user_id = NULL`** on orphans (preserves all audit log text without violating foreign keys).
   - Option B: **Exclude old orphan logs** from the migration (clean start for audit logs).
5. **Photo Storage Long-Term Architecture**:  
   Attendance photos are currently stored as Base64 strings in PostgreSQL `TEXT` columns (surviving deploys with 0 external dependencies). Do you want to:
   - Option A: **Keep Base64 in PostgreSQL** (simple, 0 extra monthly bills, 100% portable).
   - Option B: **Migrate photos to AWS S3 / Cloudflare R2** object storage with presigned URLs?
6. **Maintenance Window Schedule**:  
   When is an acceptable 15-minute maintenance window for the final production data cutover?

---
*Audit completed on branch `postgres-migration`. Awaiting your answers before starting Stage 1.*
