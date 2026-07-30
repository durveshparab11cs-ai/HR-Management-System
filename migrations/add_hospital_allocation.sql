-- Migration: Add Hospital Master and Employee Hospital Allocation
-- Date: 2026-07-24
-- Purpose: Enable hospital-based attendance with GPS validation and flexible shifts

-- ============================================================================
-- CREATE HOSPITALS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS hospitals (
    id SERIAL PRIMARY KEY,
    
    -- Hospital identification
    hospital_code VARCHAR(50) UNIQUE,
    hospital_name VARCHAR(200) NOT NULL,
    
    -- Location details
    location VARCHAR(200),
    address VARCHAR(500),
    city VARCHAR(100),
    state VARCHAR(100),
    
    -- GPS coordinates
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    
    -- GPS validation settings
    allowed_radius_metres INTEGER NOT NULL DEFAULT 100,
    
    -- Status
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    status VARCHAR(20) NOT NULL DEFAULT 'Active',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Soft delete
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    deleted_by INTEGER,
    
    -- Indexes
    CONSTRAINT chk_latitude CHECK (latitude >= -90 AND latitude <= 90),
    CONSTRAINT chk_longitude CHECK (longitude >= -180 AND longitude <= 180),
    CONSTRAINT chk_radius CHECK (allowed_radius_metres > 0)
);

CREATE INDEX IF NOT EXISTS idx_hospitals_code ON hospitals(hospital_code);
CREATE INDEX IF NOT EXISTS idx_hospitals_name ON hospitals(hospital_name);
CREATE INDEX IF NOT EXISTS idx_hospitals_active ON hospitals(is_active);
CREATE INDEX IF NOT EXISTS idx_hospitals_deleted ON hospitals(is_deleted);

COMMENT ON TABLE hospitals IS 'Hospital master with GPS coordinates for attendance validation';
COMMENT ON COLUMN hospitals.latitude IS 'Hospital GPS latitude (-90 to 90)';
COMMENT ON COLUMN hospitals.longitude IS 'Hospital GPS longitude (-180 to 180)';
COMMENT ON COLUMN hospitals.allowed_radius_metres IS 'Allowed GPS radius for attendance in metres';

-- ============================================================================
-- EXTEND EMPLOYEES TABLE
-- ============================================================================

-- Add hospital allocation column
ALTER TABLE employees 
ADD COLUMN IF NOT EXISTS hospital_id INTEGER REFERENCES hospitals(id);

-- Add current shift information
ALTER TABLE employees 
ADD COLUMN IF NOT EXISTS current_shift VARCHAR(50);

ALTER TABLE employees 
ADD COLUMN IF NOT EXISTS shift_start_time VARCHAR(20);

ALTER TABLE employees 
ADD COLUMN IF NOT EXISTS shift_end_time VARCHAR(20);

-- Add flexible shift flag
ALTER TABLE employees 
ADD COLUMN IF NOT EXISTS is_flexible_shift INTEGER NOT NULL DEFAULT 0;

-- Add required working hours
ALTER TABLE employees 
ADD COLUMN IF NOT EXISTS required_working_hours INTEGER DEFAULT 9;

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_employees_hospital_id ON employees(hospital_id);
CREATE INDEX IF NOT EXISTS idx_employees_flexible_shift ON employees(is_flexible_shift);

COMMENT ON COLUMN employees.hospital_id IS 'Allocated hospital for GPS-based attendance';
COMMENT ON COLUMN employees.current_shift IS 'Current shift name (Morning/Evening/Night/etc)';
COMMENT ON COLUMN employees.shift_start_time IS 'Shift start time (e.g., 09:00 AM)';
COMMENT ON COLUMN employees.shift_end_time IS 'Shift end time (e.g., 06:00 PM)';
COMMENT ON COLUMN employees.is_flexible_shift IS 'Flag: 1=Flexible (9hr based), 0=Fixed shift';
COMMENT ON COLUMN employees.required_working_hours IS 'Required working hours per day (default: 9)';

-- ============================================================================
-- CREATE IMPORT AUDIT LOG TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS import_logs (
    id SERIAL PRIMARY KEY,
    
    -- Import details
    import_type VARCHAR(50) NOT NULL, -- 'hospital', 'employee_allocation'
    imported_by INTEGER NOT NULL REFERENCES users(id),
    import_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- File details
    filename VARCHAR(255),
    file_size INTEGER,
    
    -- Statistics
    total_rows INTEGER NOT NULL DEFAULT 0,
    rows_imported INTEGER NOT NULL DEFAULT 0,
    rows_updated INTEGER NOT NULL DEFAULT 0,
    rows_failed INTEGER NOT NULL DEFAULT 0,
    
    -- Specific counts
    hospitals_imported INTEGER DEFAULT 0,
    hospitals_updated INTEGER DEFAULT 0,
    employees_updated INTEGER DEFAULT 0,
    
    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'completed', -- 'completed', 'partial', 'failed'
    
    -- Error details
    error_log TEXT,
    error_details TEXT,
    
    -- Processing time
    duration_seconds FLOAT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_import_logs_type ON import_logs(import_type);
CREATE INDEX IF NOT EXISTS idx_import_logs_user ON import_logs(imported_by);
CREATE INDEX IF NOT EXISTS idx_import_logs_date ON import_logs(import_date);

COMMENT ON TABLE import_logs IS 'Audit log for Excel imports and bulk operations';

-- ============================================================================
-- SAMPLE DATA (Optional - for testing)
-- ============================================================================

-- Insert a default hospital if none exists
INSERT INTO hospitals (
    hospital_code, 
    hospital_name, 
    location, 
    latitude, 
    longitude, 
    allowed_radius_metres,
    status
)
SELECT 
    'HQ-001',
    'Head Office',
    'Pune',
    18.520430,
    73.856743,
    100,
    'Active'
WHERE NOT EXISTS (SELECT 1 FROM hospitals LIMIT 1);

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Check if tables were created successfully
-- SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name IN ('hospitals', 'import_logs');

-- Check if columns were added to employees
-- SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'employees' AND column_name IN ('hospital_id', 'current_shift', 'is_flexible_shift');

-- Check hospital count
-- SELECT COUNT(*) as hospital_count FROM hospitals;

-- ============================================================================
-- ROLLBACK (if needed)
-- ============================================================================

/*
-- To rollback this migration:

-- Drop import_logs table
DROP TABLE IF EXISTS import_logs CASCADE;

-- Remove employee columns
ALTER TABLE employees DROP COLUMN IF EXISTS required_working_hours;
ALTER TABLE employees DROP COLUMN IF EXISTS is_flexible_shift;
ALTER TABLE employees DROP COLUMN IF EXISTS shift_end_time;
ALTER TABLE employees DROP COLUMN IF EXISTS shift_start_time;
ALTER TABLE employees DROP COLUMN IF EXISTS current_shift;
ALTER TABLE employees DROP COLUMN IF EXISTS hospital_id;

-- Drop hospitals table
DROP TABLE IF EXISTS hospitals CASCADE;
*/
