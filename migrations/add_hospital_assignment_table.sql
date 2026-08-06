-- Migration: Create Employee Hospital Assignment Table
-- Date: 2026-08-06
-- Purpose: Store hospital assignments for each employee (support for bulk import)
-- This migration creates the employee_hospital_assignments table if it doesn't exist

CREATE TABLE IF NOT EXISTS employee_hospital_assignments (
    id SERIAL PRIMARY KEY,
    
    -- Employee foreign key
    employee_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    
    -- Hospital assignment details
    hospital_id INTEGER REFERENCES hospitals(id) ON DELETE SET NULL,
    hospital_name VARCHAR(200),
    
    -- Date range
    effective_from DATE,
    effective_until DATE,
    
    -- Audit
    notes TEXT,
    
    -- Base model fields (BaseModel)
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE,
    deleted_by INTEGER,
    
    -- Constraints
    CONSTRAINT chk_dates CHECK (effective_from IS NULL OR effective_until IS NULL OR effective_from <= effective_until),
    CONSTRAINT chk_employee_hospital CHECK (hospital_id IS NOT NULL OR hospital_name IS NOT NULL)
);

-- Create indexes for query performance
CREATE INDEX IF NOT EXISTS idx_emp_hosp_assign_employee_id 
    ON employee_hospital_assignments(employee_id);

CREATE INDEX IF NOT EXISTS idx_emp_hosp_assign_hospital_id 
    ON employee_hospital_assignments(hospital_id);

CREATE INDEX IF NOT EXISTS idx_emp_hosp_assign_hospital_name 
    ON employee_hospital_assignments(hospital_name);

CREATE INDEX IF NOT EXISTS idx_emp_hosp_assign_active 
    ON employee_hospital_assignments(effective_from, effective_until) 
    WHERE is_deleted = FALSE;

CREATE INDEX IF NOT EXISTS idx_emp_hosp_assign_deleted 
    ON employee_hospital_assignments(is_deleted);

-- Add table comment
COMMENT ON TABLE employee_hospital_assignments IS 
    'Tracks hospital assignments for each employee with date ranges';
COMMENT ON COLUMN employee_hospital_assignments.employee_id IS 
    'Reference to employees table (cascade delete)';
COMMENT ON COLUMN employee_hospital_assignments.hospital_id IS 
    'Reference to hospitals table (nullable - assignment may be by name only)';
COMMENT ON COLUMN employee_hospital_assignments.hospital_name IS 
    'Hospital name - allows assignment before hospital master entry';
COMMENT ON COLUMN employee_hospital_assignments.effective_from IS 
    'Date when assignment becomes active';
COMMENT ON COLUMN employee_hospital_assignments.effective_until IS 
    'Date when assignment ends (NULL = still active)';

-- Verify table was created
-- SELECT COUNT(*) as table_count FROM information_schema.tables 
-- WHERE table_schema = 'public' AND table_name = 'employee_hospital_assignments';
