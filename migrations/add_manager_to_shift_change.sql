-- Migration: Add reporting manager fields to shift_change_requests table
-- Date: 2026-07-24
-- Purpose: Match leave approval system - employees enter manager code

-- Add reporting_manager_code column
ALTER TABLE shift_change_requests 
ADD COLUMN IF NOT EXISTS reporting_manager_code VARCHAR(50) NOT NULL DEFAULT '';

-- Add reporting_manager_name column
ALTER TABLE shift_change_requests 
ADD COLUMN IF NOT EXISTS reporting_manager_name VARCHAR(200);

-- Create index on reporting_manager_code for faster lookups
CREATE INDEX IF NOT EXISTS idx_shift_change_requests_manager_code 
ON shift_change_requests(reporting_manager_code);

-- Update existing records (if any) with a placeholder
UPDATE shift_change_requests 
SET reporting_manager_code = 'PENDING', 
    reporting_manager_name = 'To Be Assigned'
WHERE reporting_manager_code = '' OR reporting_manager_code IS NULL;

-- Add comment
COMMENT ON COLUMN shift_change_requests.reporting_manager_code IS 'Employee code of reporting manager who will approve/reject';
COMMENT ON COLUMN shift_change_requests.reporting_manager_name IS 'Full name of reporting manager for display';
