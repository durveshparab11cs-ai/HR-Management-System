-- ============================================================================
-- DELETE ALL ATTENDANCE DATA - DIRECT SQL SCRIPT
-- ============================================================================
-- Run this in Render PostgreSQL Console to immediately delete all attendance
--
-- HOW TO USE:
-- 1. Go to Render Dashboard: https://dashboard.render.com
-- 2. Click on your PostgreSQL database (not the web service)
-- 3. Click "Connect" → "External Connection"
-- 4. Use the PSQL command shown, or use TablePlus/DBeaver
-- 5. Paste this entire script and execute
-- ============================================================================

-- Show current counts
SELECT 
    'BEFORE DELETE' as status,
    (SELECT COUNT(*) FROM attendance WHERE is_deleted = false) as attendance_records,
    (SELECT COUNT(*) FROM attendance_photos) as photo_records,
    (SELECT COUNT(*) FROM attendance_logs) as log_records;

-- Delete in correct order (respect foreign keys)

-- Step 1: Delete attendance logs
DELETE FROM attendance_logs;

-- Step 2: Delete attendance photos
DELETE FROM attendance_photos;

-- Step 3: Delete attendance records
DELETE FROM attendance WHERE is_deleted = false;

-- Show final counts
SELECT 
    'AFTER DELETE' as status,
    (SELECT COUNT(*) FROM attendance WHERE is_deleted = false) as attendance_records,
    (SELECT COUNT(*) FROM attendance_photos) as photo_records,
    (SELECT COUNT(*) FROM attendance_logs) as log_records;

-- Verify all deleted
SELECT CASE 
    WHEN (SELECT COUNT(*) FROM attendance WHERE is_deleted = false) = 0 
         AND (SELECT COUNT(*) FROM attendance_photos) = 0 
         AND (SELECT COUNT(*) FROM attendance_logs) = 0
    THEN '✅ SUCCESS: All attendance data deleted'
    ELSE '❌ ERROR: Some records remain'
END as result;
