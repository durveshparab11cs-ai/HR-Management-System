-- Migration: Add Comp Off fields to leave_requests table
-- Date: August 10, 2026
-- Description: Add comp_off_work_date, comp_off_expiry_date, comp_off_used_on, comp_off_notified columns to track compensatory off usage

-- Add columns to leave_requests table
ALTER TABLE leave_requests ADD COLUMN comp_off_work_date DATE;
ALTER TABLE leave_requests ADD COLUMN comp_off_expiry_date DATE;
ALTER TABLE leave_requests ADD COLUMN comp_off_used_on DATETIME;
ALTER TABLE leave_requests ADD COLUMN comp_off_notified BOOLEAN NOT NULL DEFAULT 0;

-- Add leave_order column to leave_types table
ALTER TABLE leave_types ADD COLUMN leave_order INTEGER NOT NULL DEFAULT 0;

-- Create index on comp_off_expiry_date for faster filtering of unexpired comp offs
CREATE INDEX IF NOT EXISTS idx_comp_off_expiry_date ON leave_requests(comp_off_expiry_date);

-- Create index on comp_off_used_on for tracking used comp offs
CREATE INDEX IF NOT EXISTS idx_comp_off_used_on ON leave_requests(comp_off_used_on);

-- Create composite index for finding available comp offs (not expired, not used)
CREATE INDEX IF NOT EXISTS idx_comp_off_available ON leave_requests(employee_id, comp_off_expiry_date, comp_off_used_on);
