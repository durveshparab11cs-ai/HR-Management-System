-- IMMEDIATE FIX FOR RENDER PRODUCTION DATABASE
-- Run this if CO card still doesn't appear after redeploy

-- For PostgreSQL:
-- Step 1: Delete any duplicate/malformed CO entries
DELETE FROM leave_types 
WHERE code = 'CO' AND (name IS NULL OR name = '' OR is_active = FALSE);

-- Step 2: Verify or create CO leave type
INSERT INTO leave_types (code, name, max_days_per_year, is_paid, requires_document, color, is_active, created_at, updated_at)
SELECT 'CO', 'Comp Off', 6, true, false, '#8b5cf6', true, NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM leave_types WHERE code = 'CO' AND is_active = true);

-- Step 3: Verify it exists
SELECT id, code, name, is_active, color FROM leave_types WHERE code = 'CO' OR code = 'COMP' ORDER BY id DESC;

-- For SQLite (if using SQLite on local):
-- Step 1: Delete any duplicate/malformed CO entries
DELETE FROM leave_types 
WHERE code = 'CO' AND (name IS NULL OR name = '' OR is_active = 0);

-- Step 2: Verify or create CO leave type (SQLite)
INSERT OR IGNORE INTO leave_types (code, name, max_days_per_year, is_paid, requires_document, color, is_active)
VALUES ('CO', 'Comp Off', 6, 1, 0, '#8b5cf6', 1);

-- Step 3: Verify it exists (SQLite)
SELECT id, code, name, is_active, color FROM leave_types WHERE code = 'CO' OR code = 'COMP' ORDER BY id DESC;
