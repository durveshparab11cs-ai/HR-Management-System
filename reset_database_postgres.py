"""
reset_database_postgres.py
===========================
Database reset script optimized for PostgreSQL production environment.

USAGE:
    python reset_database_postgres.py
"""

import os
import shutil
from datetime import datetime
from pathlib import Path

from app import create_app
from app.extensions.database import db
from sqlalchemy import text


def confirm_reset():
    """Get user confirmation."""
    print("=" * 80)
    print("⚠️  POSTGRESQL DATABASE RESET WARNING")
    print("=" * 80)
    print()
    print("This will DELETE ALL transactional data")
    print("This will PRESERVE all employee master data")
    print()
    
    response = input("Type 'RESET DATABASE' to confirm: ")
    return response == "RESET DATABASE"


def reset_transactional_tables_postgres(app):
    """PostgreSQL-specific reset with proper sequence handling."""
    print("\n" + "=" * 80)
    print("RESETTING TRANSACTIONAL TABLES (PostgreSQL)")
    print("=" * 80)
    
    with app.app_context():
        try:
            print("\n🔄 Starting transaction...")
            
            # Transactional tables (in dependency order)
            transactional_tables = [
                # Attendance related
                "gps_logs",
                "attendance_photos",
                "attendance_logs",
                "attendance",
                
                # Leave related
                "early_leave_requests",
                "half_day_requests",
                "leave_requests",
                "leave_balances",
                
                # Shift change related
                "shift_change_requests",
                "employee_shift_assignments",
                
                # Payroll related
                "payslips",
                "payroll_runs",
                
                # Notifications and logs
                "notifications",
                "login_history",
            ]
            
            deleted_counts = {}
            
            for table_name in transactional_tables:
                try:
                    # Check if table exists
                    result = db.session.execute(text(
                        f"SELECT to_regclass('public.{table_name}')"
                    ))
                    if result.scalar():
                        # Count before deletion
                        count_result = db.session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                        count = count_result.scalar()
                        
                        if count > 0:
                            # Truncate with CASCADE (handles foreign keys)
                            db.session.execute(text(f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE"))
                            deleted_counts[table_name] = count
                            print(f"✅ {table_name}: {count} records deleted")
                        else:
                            print(f"ℹ️  {table_name}: Already empty")
                    else:
                        print(f"ℹ️  {table_name}: Table does not exist")
                        
                except Exception as e:
                    print(f"⚠️  {table_name}: Error - {str(e)}")
            
            # Commit
            db.session.commit()
            print("\n✅ Transaction committed")
            
            return deleted_counts
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ ERROR: Rolled back - {str(e)}")
            raise


def verify_postgres(app):
    """PostgreSQL-specific verification."""
    print("\n" + "=" * 80)
    print("VERIFICATION")
    print("=" * 80)
    
    with app.app_context():
        # Verify master data
        print("\n✅ Master Data Preserved:")
        master_tables = [
            "users",
            "employees",
            "employee_master",
            "departments",
            "positions",
            "shifts",
            "office_settings",
        ]
        
        preserved = {}
        for table in master_tables:
            try:
                result = db.session.execute(text(
                    f"SELECT to_regclass('public.{table}')"
                ))
                if result.scalar():
                    count = db.session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                    preserved[table] = count
                    print(f"   ✓ {table}: {count} records")
            except Exception as e:
                print(f"   ⚠️  {table}: {str(e)}")
        
        # Verify deletion
        print("\n✅ Transactional Data Deleted:")
        transactional_tables = [
            "attendance",
            "leave_requests",
            "shift_change_requests",
            "notifications",
            "payroll_runs",
        ]
        
        all_empty = True
        for table in transactional_tables:
            try:
                result = db.session.execute(text(
                    f"SELECT to_regclass('public.{table}')"
                ))
                if result.scalar():
                    count = db.session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                    if count == 0:
                        print(f"   ✓ {table}: Empty")
                    else:
                        print(f"   ⚠️  {table}: Still has {count} records")
                        all_empty = False
            except Exception as e:
                print(f"   ⚠️  {table}: {str(e)}")
        
        return preserved, all_empty


def main():
    """Main execution for PostgreSQL."""
    print("\n" + "=" * 80)
    print("SMART HRMS - POSTGRESQL DATABASE RESET")
    print("=" * 80)
    
    if not confirm_reset():
        print("\n❌ Cancelled")
        return
    
    try:
        app = create_app()
        
        # Check if using PostgreSQL
        with app.app_context():
            db_url = str(db.engine.url)
            if 'postgresql' not in db_url.lower():
                print("\n⚠️  WARNING: This script is for PostgreSQL")
                print(f"   Current database: {db_url}")
                response = input("\nContinue anyway? (yes/no): ")
                if response.lower() != 'yes':
                    return
        
        # Reset tables
        deleted_counts = reset_transactional_tables_postgres(app)
        
        # Verify
        preserved, all_empty = verify_postgres(app)
        
        # Report
        print("\n" + "=" * 80)
        print("✅ RESET COMPLETE")
        print("=" * 80)
        
        total_deleted = sum(deleted_counts.values())
        print(f"\nRecords deleted: {total_deleted:,}")
        print(f"Tables cleared: {len(deleted_counts)}")
        print(f"Master records preserved: {sum(preserved.values())}")
        
        if all_empty:
            print("\n✅ All transactional tables are empty")
        else:
            print("\n⚠️  Some transactional data may remain")
        
        print("\n🎉 Database reset successful!")
        print("   Ready for fresh testing")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
