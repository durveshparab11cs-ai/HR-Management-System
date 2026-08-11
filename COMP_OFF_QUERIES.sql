-- ============================================================================
-- Comp Off Investigation Queries
-- ============================================================================
-- Database: smart_hrms_dev.db
-- Date: 11 August 2026
-- Purpose: Verify comp off records and user details
-- ============================================================================

-- ============================================================================
-- QUERY 1: Find all approved comp off records
-- ============================================================================
-- This query returns all leave requests where:
-- - Status is 'approved'
-- - Comp off work date is set (meaning it's a comp off, not regular leave)
-- ============================================================================

SELECT 
    lr.id as leave_request_id,
    lr.employee_id,
    e.employee_code,
    e.id as employee_internal_id,
    u.first_name || ' ' || u.last_name as employee_name,
    u.email,
    lr.status,
    lr.start_date,
    lr.end_date,
    lr.total_days,
    lr.comp_off_work_date,
    lr.comp_off_expiry_date,
    lr.comp_off_used_on,
    lr.comp_off_notified,
    lr.applied_on,
    CASE 
        WHEN lr.comp_off_expiry_date < DATE('now') THEN 'EXPIRED'
        WHEN lr.comp_off_used_on IS NOT NULL THEN 'USED'
        WHEN lr.comp_off_expiry_date > DATE('now') THEN 'ACTIVE'
        ELSE 'UNKNOWN'
    END as comp_off_status
FROM leave_requests lr
LEFT JOIN employees e ON lr.employee_id = e.id
LEFT JOIN users u ON e.user_id = u.id
WHERE lr.status = 'approved' 
  AND lr.comp_off_work_date IS NOT NULL
ORDER BY lr.applied_on DESC;

-- ============================================================================
-- QUERY 2: Find user Durvesh with employee details
-- ============================================================================
-- This query finds the logged-in user 'Durvesh' and his employee record
-- ============================================================================

SELECT 
    u.id as user_id,
    u.username,
    u.email,
    u.first_name,
    u.last_name,
    u.full_name = (u.first_name || ' ' || u.last_name) as full_name,
    u.role,
    u.status,
    u.is_active,
    e.id as employee_id,
    e.employee_code,
    e.department,
    e.designation,
    e.branch,
    e.office_settings_id,
    e.shift_name
FROM users u
LEFT JOIN employees e ON u.id = e.user_id
WHERE LOWER(u.first_name) LIKE '%durvesh%'
LIMIT 1;

-- ============================================================================
-- QUERY 3: Count all leave records for Durvesh (Employee ID: 3)
-- ============================================================================
-- This query counts all types of leave requests for the logged-in user
-- ============================================================================

SELECT 
    COUNT(*) as total_leave_records,
    SUM(CASE WHEN lr.comp_off_work_date IS NOT NULL THEN 1 ELSE 0 END) as comp_off_records,
    SUM(CASE WHEN lr.status = 'approved' THEN 1 ELSE 0 END) as approved_records,
    SUM(CASE WHEN lr.status = 'pending' THEN 1 ELSE 0 END) as pending_records,
    SUM(CASE WHEN lr.status = 'rejected' THEN 1 ELSE 0 END) as rejected_records
FROM leave_requests lr
WHERE lr.employee_id = 3;  -- Durvesh's Employee ID

-- ============================================================================
-- QUERY 4: All leave records for Durvesh with details
-- ============================================================================
-- This query shows all leave records (if any) for the logged-in user
-- ============================================================================

SELECT 
    lr.id,
    lt.code as leave_type_code,
    lt.name as leave_type_name,
    lr.status,
    lr.start_date,
    lr.end_date,
    lr.total_days,
    lr.reason,
    CASE WHEN lr.comp_off_work_date IS NOT NULL THEN 'YES' ELSE 'NO' END as is_comp_off,
    lr.comp_off_work_date,
    lr.comp_off_expiry_date,
    lr.comp_off_used_on,
    lr.comp_off_notified,
    lr.applied_on,
    lr.reviewed_on,
    u_reviewer.first_name || ' ' || u_reviewer.last_name as reviewed_by
FROM leave_requests lr
LEFT JOIN leave_types lt ON lr.leave_type_id = lt.id
LEFT JOIN users u_reviewer ON lr.reviewed_by = u_reviewer.id
WHERE lr.employee_id = 3  -- Durvesh's Employee ID
ORDER BY lr.applied_on DESC;

-- ============================================================================
-- QUERY 5: Comp Off Leave Type Configuration
-- ============================================================================
-- This query shows the configuration of the Comp Off leave type
-- ============================================================================

SELECT 
    id as leave_type_id,
    code,
    name,
    max_days_per_year,
    carry_forward,
    requires_document,
    is_paid,
    is_active,
    color,
    description,
    leave_order
FROM leave_types
WHERE code = 'COMP';

-- ============================================================================
-- QUERY 6: Database Schema - Verify Comp Off Columns
-- ============================================================================
-- This query checks if all comp off columns exist in leave_requests table
-- ============================================================================

PRAGMA table_info(leave_requests);
-- Look for these columns:
-- - comp_off_work_date (DATE)
-- - comp_off_expiry_date (DATE)
-- - comp_off_used_on (TIMESTAMP)
-- - comp_off_notified (BOOLEAN)

-- ============================================================================
-- QUERY 7: Statistics - Comp Off Usage
-- ============================================================================
-- This query provides statistics about comp off usage in the system
-- ============================================================================

SELECT 
    'Total Comp Off Records' as metric,
    COUNT(*) as value
FROM leave_requests
WHERE comp_off_work_date IS NOT NULL

UNION ALL

SELECT 
    'Approved Comp Off Records',
    COUNT(*)
FROM leave_requests
WHERE comp_off_work_date IS NOT NULL
  AND status = 'approved'

UNION ALL

SELECT 
    'Used Comp Off Records',
    COUNT(*)
FROM leave_requests
WHERE comp_off_work_date IS NOT NULL
  AND comp_off_used_on IS NOT NULL

UNION ALL

SELECT 
    'Unused Comp Off Records',
    COUNT(*)
FROM leave_requests
WHERE comp_off_work_date IS NOT NULL
  AND comp_off_used_on IS NULL

UNION ALL

SELECT 
    'Expired Comp Off Records',
    COUNT(*)
FROM leave_requests
WHERE comp_off_work_date IS NOT NULL
  AND comp_off_expiry_date < DATE('now')

UNION ALL

SELECT 
    'Active (Not Expired) Comp Off Records',
    COUNT(*)
FROM leave_requests
WHERE comp_off_work_date IS NOT NULL
  AND comp_off_expiry_date >= DATE('now')
  AND comp_off_used_on IS NULL;

-- ============================================================================
-- QUERY 8: Detailed Info for Each Comp Off Employee
-- ============================================================================
-- This query shows all employees with comp off records
-- ============================================================================

SELECT 
    u.id,
    u.first_name || ' ' || u.last_name as employee_name,
    u.email,
    e.employee_code,
    e.department,
    COUNT(lr.id) as comp_off_count,
    SUM(CASE WHEN lr.status = 'approved' THEN 1 ELSE 0 END) as approved_count,
    SUM(CASE WHEN lr.comp_off_used_on IS NOT NULL THEN 1 ELSE 0 END) as used_count,
    MIN(lr.comp_off_work_date) as earliest_work_date,
    MAX(lr.comp_off_expiry_date) as latest_expiry_date
FROM leave_requests lr
JOIN employees e ON lr.employee_id = e.id
JOIN users u ON e.user_id = u.id
WHERE lr.comp_off_work_date IS NOT NULL
GROUP BY lr.employee_id, u.id, u.first_name, u.last_name, u.email, e.employee_code, e.department
ORDER BY comp_off_count DESC;

-- ============================================================================
-- QUERY 9: Check Upcoming Comp Off Expiries (Next 30 days)
-- ============================================================================
-- This query helps identify comp off records that will expire soon
-- ============================================================================

SELECT 
    lr.id,
    u.first_name || ' ' || u.last_name as employee_name,
    e.employee_code,
    lr.comp_off_work_date,
    lr.comp_off_expiry_date,
    CAST((julianday(lr.comp_off_expiry_date) - julianday('now')) AS INTEGER) as days_until_expiry,
    CASE 
        WHEN (julianday(lr.comp_off_expiry_date) - julianday('now')) < 0 THEN 'EXPIRED'
        WHEN (julianday(lr.comp_off_expiry_date) - julianday('now')) <= 7 THEN 'EXPIRES SOON'
        WHEN (julianday(lr.comp_off_expiry_date) - julianday('now')) <= 30 THEN 'EXPIRES IN 30 DAYS'
        ELSE 'NOT URGENT'
    END as urgency
FROM leave_requests lr
JOIN employees e ON lr.employee_id = e.id
JOIN users u ON e.user_id = u.id
WHERE lr.comp_off_work_date IS NOT NULL
  AND lr.comp_off_used_on IS NULL
ORDER BY lr.comp_off_expiry_date ASC;

-- ============================================================================
-- QUERY 10: Rajesh Sanjay Shukla (E-2603025) - Comp Off Detail
-- ============================================================================
-- This query shows detailed information about Raj's comp off record
-- ============================================================================

SELECT 
    lr.id,
    u.first_name || ' ' || u.last_name as employee_name,
    e.employee_code,
    lt.name as leave_type,
    lr.status,
    lr.start_date,
    lr.end_date,
    lr.total_days,
    lr.reason,
    lr.applied_on,
    lr.reviewed_on,
    u_reviewer.first_name || ' ' || u_reviewer.last_name as approved_by,
    lr.comp_off_work_date as 'Day Employee Worked',
    lr.comp_off_expiry_date as 'Expiry Date (90 days later)',
    CAST((julianday(lr.comp_off_expiry_date) - julianday('now')) AS INTEGER) as 'Days Until Expiry',
    lr.comp_off_used_on as 'When Used (NULL=Not Yet Used)',
    CASE WHEN lr.comp_off_notified = 1 THEN 'Yes' ELSE 'No' END as 'HR Notified',
    lr.reporting_manager_name as 'Reporting Manager'
FROM leave_requests lr
JOIN employees e ON lr.employee_id = e.id
JOIN users u ON e.user_id = u.id
LEFT JOIN leave_types lt ON lr.leave_type_id = lt.id
LEFT JOIN users u_reviewer ON lr.reviewed_by = u_reviewer.id
WHERE e.employee_code = 'E-2603025'
  AND lr.comp_off_work_date IS NOT NULL;

-- ============================================================================
-- NOTES FOR ANALYSIS:
-- ============================================================================
-- 1. comp_off_work_date: The date on which employee worked (holiday)
-- 2. comp_off_expiry_date: 90 days after comp_off_work_date
-- 3. comp_off_used_on: When the comp off was actually taken (NULL if not used)
-- 4. comp_off_notified: Boolean flag (0 or 1) indicating HR notification
--
-- 5. Current findings:
--    - 1 approved comp off record exists (Raj - E-2603025)
--    - Work date: 2026-08-15
--    - Expiry: 2026-11-13 (90 days)
--    - Status: Not yet used (comp_off_used_on IS NULL)
--    - HR notification: Not notified (comp_off_notified = 0)
--
-- 6. Durvesh (E-2606026) status:
--    - Employee ID: 3
--    - Role: super_admin
--    - No leave records found
--    - No comp off records
--    - Department: Not set
--
-- ============================================================================
