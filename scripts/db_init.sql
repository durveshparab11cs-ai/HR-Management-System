-- ===========================================================================
-- Smart HRMS — PostgreSQL Database Initialization Script
-- ===========================================================================
-- Run once on a fresh PostgreSQL server before the first Flask-Migrate run.
-- This script creates the database, user, and grants privileges.
--
-- Usage (as postgres superuser):
--   psql -U postgres -f scripts/db_init.sql
-- ===========================================================================

-- Create the application database user
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'hrms_user') THEN
        CREATE ROLE hrms_user WITH LOGIN PASSWORD 'change_this_password_immediately';
    END IF;
END
$$;

-- Create the production database
SELECT 'CREATE DATABASE smart_hrms_db OWNER hrms_user ENCODING ''UTF8'' LC_COLLATE ''en_US.UTF-8'' LC_CTYPE ''en_US.UTF-8'' TEMPLATE template0'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'smart_hrms_db')\gexec

-- Grant all privileges on the database to the application user
GRANT ALL PRIVILEGES ON DATABASE smart_hrms_db TO hrms_user;

-- Connect to the new database and set default privileges
\connect smart_hrms_db

GRANT ALL ON SCHEMA public TO hrms_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES    TO hrms_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO hrms_user;

-- Enable UUID extension (used for future UUID primary keys if needed)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pg_trgm for efficient ILIKE / full-text search on employee names
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Confirmation
SELECT 'Database smart_hrms_db initialized successfully.' AS status;
