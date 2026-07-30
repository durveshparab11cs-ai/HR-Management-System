# Fix Shift Change 500 Error

## Problem
The shift change dashboard is showing "500 Internal Server Error"

## Most Likely Cause
The database migration for the new manager approval fields was **NOT** run on the production database.

## Solution

### Step 1: Check if Migration Was Run

Connect to your production database and check if the columns exist:

```sql
-- Connect to your database
psql $DATABASE_URL

-- Check if the columns exist
\d shift_change_requests

-- Look for these columns:
-- reporting_manager_code
-- reporting_manager_name
```

### Step 2: Run the Migration

If the columns are missing, run the migration:

```bash
# Option A: From local machine (if you have access to production DB)
psql $DATABASE_URL < migrations/add_manager_to_shift_change.sql

# Option B: On Render
# 1. Go to Render Dashboard
# 2. Click on your database
# 3. Click "Connect" → "External Connection"
# 4. Copy the psql command
# 5. Run the migration SQL
```

### Step 3: Run Migration SQL Manually

If you can't run the file, copy and paste this SQL directly:

```sql
-- Add manager approval fields to shift_change_requests table
ALTER TABLE shift_change_requests 
ADD COLUMN IF NOT EXISTS reporting_manager_code VARCHAR(50);

ALTER TABLE shift_change_requests 
ADD COLUMN IF NOT EXISTS reporting_manager_name VARCHAR(200);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_shift_change_manager_code 
ON shift_change_requests(reporting_manager_code);

-- Update existing records with a default manager code
-- Replace 'E-DEFAULT' with an actual manager code from your system
UPDATE shift_change_requests 
SET reporting_manager_code = 'E-DEFAULT'
WHERE reporting_manager_code IS NULL;

-- Make the column NOT NULL after updating
ALTER TABLE shift_change_requests 
ALTER COLUMN reporting_manager_code SET NOT NULL;

-- Verify the changes
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'shift_change_requests' 
AND column_name IN ('reporting_manager_code', 'reporting_manager_name');
```

### Step 4: Restart Application on Render

After running the migration:

1. Go to Render Dashboard
2. Select your web service (HR Management System)
3. Click "Manual Deploy" → "Deploy latest commit"
4. Wait 2-3 minutes for deployment

### Step 5: Verify Fix

1. Login to your application
2. Navigate to: **Shift Change → Dashboard**
3. Should load without 500 error

## Alternative Quick Fix (If Migration Fails)

If you can't run the migration right now, temporarily revert the changes:

```bash
cd "c:\Users\durve\Downloads\HR management system\smart_hrms"
git revert HEAD
git push origin main
```

This will remove the manager approval feature temporarily until you can run the migration.

## Status After Fix

✅ Dashboard loads  
✅ Can view shift history  
✅ Can create requests with manager code  
✅ Manager can see approvals  

## Need Help?

If the error persists after migration:

1. Check Render logs for the actual error message
2. Look for Python traceback
3. Share the error message for specific help

---

**Deployed:** Commit ff6c02d (with better error handling)  
**Migration File:** `migrations/add_manager_to_shift_change.sql`
