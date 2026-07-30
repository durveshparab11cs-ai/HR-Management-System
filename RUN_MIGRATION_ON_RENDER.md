# Run Migration on Render - SIMPLE GUIDE

## Problem
Shift Change dashboard shows 500 error because database columns are missing.

## Solution (Choose ONE method)

---

### Method 1: Automatic Migration (EASIEST) ✅

The migration will run automatically when the app starts on Render.

**Just wait 2-3 minutes after deployment completes.**

The app now includes auto-migration code that will:
1. Check if columns exist
2. Add them if missing
3. Continue startup normally

**You don't need to do anything!**

---

### Method 2: Run Flask CLI Command (If Auto-Migration Fails)

If the automatic migration doesn't work, run this command on Render:

1. Go to Render Dashboard
2. Click on your web service
3. Click "Shell" tab (or SSH into the service)
4. Run this command:

```bash
flask migrate-shift-change
```

This will:
- Check if columns exist
- Add missing columns
- Update existing records
- Create indexes
- Show success message

---

### Method 3: Run Python Script (Alternative)

If Flask CLI doesn't work, run the Python script:

```bash
python run_migration.py
```

---

### Method 4: Manual SQL (Last Resort)

If nothing else works, connect to PostgreSQL and run:

```sql
-- Add columns
ALTER TABLE shift_change_requests 
ADD COLUMN IF NOT EXISTS reporting_manager_code VARCHAR(50);

ALTER TABLE shift_change_requests 
ADD COLUMN IF NOT EXISTS reporting_manager_name VARCHAR(200);

-- Update existing records
UPDATE shift_change_requests 
SET reporting_manager_code = 'PENDING', 
    reporting_manager_name = 'To Be Assigned'
WHERE reporting_manager_code IS NULL OR reporting_manager_code = '';

-- Set NOT NULL
ALTER TABLE shift_change_requests 
ALTER COLUMN reporting_manager_code SET NOT NULL;

-- Create index
CREATE INDEX IF NOT EXISTS idx_shift_change_requests_manager_code 
ON shift_change_requests(reporting_manager_code);
```

---

## How to Check if Migration Worked

1. Login to your HRMS system
2. Go to: **Shift Change → Dashboard**
3. If it loads without error = ✅ Migration successful!
4. If still showing 500 error = Try Method 2 or 3

---

## What Was Added

The migration adds these new columns to `shift_change_requests` table:

1. **reporting_manager_code** (VARCHAR 50, NOT NULL)
   - Stores the employee code of the reporting manager
   - Example: "E-2606003"

2. **reporting_manager_name** (VARCHAR 200, NULLABLE)
   - Stores the full name of the reporting manager  
   - Example: "Aryan Devrendra"

3. **Index on reporting_manager_code**
   - For faster queries when fetching manager's approvals

---

## After Migration

Once migration is complete:

✅ Shift Change dashboard will load  
✅ Can create requests with manager code  
✅ Manager can see approval requests  
✅ Full approval workflow active  

---

**Status:** Deployed in commit ff6c02d + auto-migration added  
**Priority:** Method 1 (Automatic) should work automatically
