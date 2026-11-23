# Smart HRMS ERP — PostgreSQL Production Cutover Runbook

This document defines the step-by-step procedures for switching the production **Smart HRMS ERP** on Render from SQLite to **Render Managed PostgreSQL** with **zero data loss**, full rollback safety, and continuous operational integrity.

---

## Pre-Flight Checklist
- [x] Full database audit completed ([`docs/POSTGRES_AUDIT.md`](file:///c:/Users/durve/Downloads/hrms%20erp/docs/POSTGRES_AUDIT.md))
- [x] Automatic wipe/reset triggers permanently eliminated on `postgres-migration`
- [x] PostgreSQL driver `psycopg2-binary==2.9.10` pinned
- [x] Dynamic connection pool tuning & SSL enforcement configured
- [x] Zero-data-loss migration script tested ([`scripts/migrate_sqlite_to_postgres.py`](file:///c:/Users/durve/Downloads/hrms%20erp/scripts/migrate_sqlite_to_postgres.py))
- [ ] Render PostgreSQL instance provisioned

---

## 1. Cutover Timeline & Schedule

Total estimated maintenance window: **10 – 15 minutes** (Recommended off-peak: 10:00 PM – 11:00 PM IST or Sunday).

| Phase | Step | Owner | Est. Time |
| :--- | :--- | :---: | :---: |
| **Phase 1** | Disable Auto-Deploy on Render | Admin / Dev | 1 min |
| **Phase 2** | Take Snapshot of Production SQLite & Photos | System | 2 mins |
| **Phase 3** | Run Migration Script to PostgreSQL | System | 3 mins |
| **Phase 4** | Verify Row Counts & Checksums | System / QA | 2 mins |
| **Phase 5** | Update `DATABASE_URL` on Render Web Service | Admin | 1 min |
| **Phase 6** | Deploy `postgres-migration` Branch | Render | 3 mins |
| **Phase 7** | Post-Cutover Smoke Tests | QA / HR | 3 mins |
| **Total** | | | **~15 mins** |

---

## 2. Step-by-Step Execution Guide

### Step 1: Disable Auto-Deploy on Render (1 min)
1. Open Render Dashboard → Select Web Service **`SMART-HRMS-ERP`**.
2. Go to **Settings** → **Build & Deploy**.
3. Toggle **Auto-Deploy** to **"No"** (or OFF).
*Reason: Prevents accidental redeployments during data transfer.*

### Step 2: Snapshot Production SQLite (2 mins)
In Render Shell (or SSH):
```bash
cp instance/smart_hrms_dev.db backups/smart_hrms_pre_cutover_$(date +%Y%m%d_%H%M%S).db
```
*Note: SQLite is treated as strictly read-only.*

### Step 3: Run Zero-Data-Loss Migration (3 mins)
Execute the migration tool against your PostgreSQL database:

```bash
# 1. Dry run to validate all 541 employees, shifts, and hospitals
python scripts/migrate_sqlite_to_postgres.py --source instance/smart_hrms_dev.db --target "$DATABASE_URL" --dry-run

# 2. Live execution into PostgreSQL
python scripts/migrate_sqlite_to_postgres.py --source instance/smart_hrms_dev.db --target "$DATABASE_URL" --execute
```

Review `migration_reports/summary.md` to confirm:
- 541/541 Employee Master records migrated.
- 46/46 Hospitals migrated.
- 25/25 Shift Types migrated.
- Sequences properly set.

### Step 4: Verify Row Counts & Constraints (2 mins)
Run verification check:
```bash
python scripts/print_audit_summary.py
```
Ensure 0 rejected records in `migration_reports/`.

### Step 5: Update `DATABASE_URL` in Render Environment (1 min)
1. Render Dashboard → **SMART-HRMS-ERP** → **Environment**.
2. Set `DATABASE_URL` to the Render PostgreSQL **Internal Connection String**:
   `postgresql://hrms_user:<password>@dpg-...-a:5432/smart_hrms_db`
3. Click **Save Changes**.

### Step 6: Deploy `postgres-migration` (3 mins)
1. In Render Dashboard, click **Manual Deploy** → **Deploy latest commit** (from branch `postgres-migration`).
2. Monitor build logs: verify clean boot and database connectivity.

### Step 7: Post-Cutover Verification (3 mins)
Perform immediate live smoke test:
1. **Login**: Login with admin credentials at `/auth/login`.
2. **Kiosk Punch**: Visit `/auth/kiosk`, unlock with Master Password, execute check-in with selfie capture.
3. **Admin Attendance**: Check `/admin/attendance/all` — verify attendance record and photo appear immediately.
4. **Leave Management**: Visit `/leave` — verify balance cards load without errors.
5. **Payroll**: Visit `/payroll` — generate test payslip draft.
6. **Excel Export**: Export employee master list.

---

## 3. Instant Rollback Plan (If Needed)

Because SQLite is **never written to or deleted** during migration, rolling back takes **under 60 seconds**:

1. In Render Dashboard → **Environment**:
   - Change `DATABASE_URL` back to: `sqlite:///smart_hrms_dev.db`
2. Click **Save Changes** and **Manual Deploy**.
3. The service immediately resumes reading from the intact SQLite database with zero data loss.
