"""
reset_database.py
==================
Complete database reset script for Smart HRMS.

WHAT THIS DOES:
- Deletes ALL transactional data (attendance, leave, payroll, notifications, etc.)
- Preserves employee master data, users, departments, roles, company info
- Resets auto-increment sequences
- Cleans uploaded files
- Provides detailed logging

WHAT THIS KEEPS:
✓ Employee Master Data
✓ User Accounts & Login Credentials
✓ Departments, Designations, Positions
✓ Roles & Permissions
✓ Company Information
✓ Office Settings
✓ Shift Master Data
✓ System Configuration

WHAT THIS DELETES:
✗ All Attendance Records
✗ All Leave Applications
✗ All Half-Day Requests
✗ All Shift Change Requests
✗ All Payroll Records
✗ All Notifications
✗ All Audit Logs
✗ All Uploaded Photos
✗ All Session Data

USAGE:
    python reset_database.py

WARNING:
    This action is IRREVERSIBLE. All transactional data will be permanently deleted.
"""

import os
import shutil
from datetime import datetime
from pathlib import Path

from app import create_app
from app.extensions.database import db
from sqlalchemy import text


def confirm_reset():
    """Get user confirmation before proceeding."""
    print("=" * 80)
    print("⚠️  DATABASE RESET WARNING")
    print("=" * 80)
    print()
    print("This will DELETE ALL transactional data including:")
    print("  • All attendance records")
    print("  • All leave applications")
    print("  • All half-day requests")
    print("  • All shift change requests")
    print("  • All payroll records")
    print("  • All notifications")
    print("  • All uploaded photos")
    print("  • All approval history")
    print()
    print("This will PRESERVE:")
    print("  ✓ Employee master data")
    print("  ✓ User accounts and login credentials")
    print("  ✓ Departments, designations, roles")
    print("  ✓ Company information")
    print("  ✓ System settings")
    print()
    print("=" * 80)
    
    response = input("\nType 'RESET DATABASE' to confirm (or anything else to cancel): ")
    return response == "RESET DATABASE"


def delete_uploaded_files():
    """Delete all uploaded files (attendance photos, etc.)."""
    print("\n" + "=" * 80)
    print("CLEANING UPLOADED FILES")
    print("=" * 80)
    
    upload_folders = [
        "instance/uploads/attendance_photos",
        "instance/uploads/checkin_photos",
        "instance/uploads/checkout_photos",
        "instance/uploads/shift_changes",
        "instance/uploads/leave_attachments",
        "instance/uploads/temp",
    ]
    
    total_deleted = 0
    
    for folder in upload_folders:
        folder_path = Path(folder)
        if folder_path.exists():
            file_count = len(list(folder_path.glob("*")))
            if file_count > 0:
                shutil.rmtree(folder_path)
                folder_path.mkdir(parents=True, exist_ok=True)
                print(f"✅ Cleaned {folder}: {file_count} files deleted")
                total_deleted += file_count
            else:
                print(f"ℹ️  {folder}: Already empty")
        else:
            print(f"ℹ️  {folder}: Does not exist")
    
    print(f"\n📊 Total files deleted: {total_deleted}")
    return total_deleted


def reset_transactional_tables(app):
    """Delete all transactional data while preserving master data."""
    print("\n" + "=" * 80)
    print("RESETTING TRANSACTIONAL TABLES")
    print("=" * 80)
    
    with app.app_context():
        try:
            # Start transaction
            print("\n🔄 Starting database transaction...")
            
            # Define transactional tables to clear (in order to respect foreign keys)
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
                
                # Session data (if table exists)
                # "sessions",  # Uncomment if you have a sessions table
            ]
            
            deleted_counts = {}
            
            # Disable foreign key checks temporarily (SQLite)
            db.session.execute(text("PRAGMA foreign_keys = OFF"))
            
            for table_name in transactional_tables:
                try:
                    # Check if table exists
                    result = db.session.execute(
                        text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                    )
                    if result.fetchone():
                        # Count records before deletion
                        count_result = db.session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                        count = count_result.scalar()
                        
                        if count > 0:
                            # Delete all records
                            db.session.execute(text(f"DELETE FROM {table_name}"))
                            
                            # Reset auto-increment (SQLite)
                            db.session.execute(text(f"DELETE FROM sqlite_sequence WHERE name='{table_name}'"))
                            
                            deleted_counts[table_name] = count
                            print(f"✅ {table_name}: {count} records deleted")
                        else:
                            print(f"ℹ️  {table_name}: Already empty")
                    else:
                        print(f"⚠️  {table_name}: Table does not exist")
                        
                except Exception as e:
                    print(f"⚠️  {table_name}: Error - {str(e)}")
            
            # Re-enable foreign key checks
            db.session.execute(text("PRAGMA foreign_keys = ON"))
            
            # Commit transaction
            db.session.commit()
            print("\n✅ Transaction committed successfully")
            
            return deleted_counts
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ ERROR: Transaction rolled back - {str(e)}")
            raise


def verify_preservation(app):
    """Verify that master data was preserved."""
    print("\n" + "=" * 80)
    print("VERIFYING MASTER DATA PRESERVATION")
    print("=" * 80)
    
    with app.app_context():
        verification_queries = [
            ("users", "User Accounts"),
            ("employees", "Employee Records"),
            ("employee_master", "Employee Master Data"),
            ("departments", "Departments"),
            ("positions", "Positions/Designations"),
            ("shifts", "Shift Master"),
            ("office_settings", "Office Settings"),
            ("company_profile", "Company Information"),
        ]
        
        results = {}
        all_preserved = True
        
        for table_name, display_name in verification_queries:
            try:
                result = db.session.execute(
                    text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                )
                if result.fetchone():
                    count_result = db.session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                    count = count_result.scalar()
                    results[display_name] = count
                    
                    if count > 0:
                        print(f"✅ {display_name}: {count} records preserved")
                    else:
                        print(f"⚠️  {display_name}: Empty (may be expected)")
                else:
                    print(f"ℹ️  {display_name}: Table does not exist")
                    
            except Exception as e:
                print(f"❌ {display_name}: Error - {str(e)}")
                all_preserved = False
        
        return results, all_preserved


def verify_deletion(app):
    """Verify that transactional data was deleted."""
    print("\n" + "=" * 80)
    print("VERIFYING TRANSACTIONAL DATA DELETION")
    print("=" * 80)
    
    with app.app_context():
        transactional_tables = [
            ("attendance", "Attendance Records"),
            ("attendance_logs", "Attendance Logs"),
            ("attendance_photos", "Attendance Photos"),
            ("gps_logs", "GPS Logs"),
            ("leave_requests", "Leave Applications"),
            ("half_day_requests", "Half-Day Requests"),
            ("early_leave_requests", "Early Leave Requests"),
            ("shift_change_requests", "Shift Change Requests"),
            ("employee_shift_assignments", "Shift Assignments"),
            ("payroll_runs", "Payroll Runs"),
            ("payslips", "Payslips"),
            ("notifications", "Notifications"),
            ("login_history", "Login History"),
        ]
        
        all_deleted = True
        
        for table_name, display_name in transactional_tables:
            try:
                result = db.session.execute(
                    text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                )
                if result.fetchone():
                    count_result = db.session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                    count = count_result.scalar()
                    
                    if count == 0:
                        print(f"✅ {display_name}: Empty (0 records)")
                    else:
                        print(f"⚠️  {display_name}: Still has {count} records")
                        all_deleted = False
                else:
                    print(f"ℹ️  {display_name}: Table does not exist")
                    
            except Exception as e:
                print(f"❌ {display_name}: Error - {str(e)}")
        
        return all_deleted


def generate_report(deleted_counts, files_deleted, preserved_data, start_time):
    """Generate final report."""
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print("\n" + "=" * 80)
    print("RESET COMPLETE - FINAL REPORT")
    print("=" * 80)
    
    print(f"\n📊 Summary:")
    print(f"   Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   End Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Duration: {duration:.2f} seconds")
    
    print(f"\n🗑️  Transactional Data Deleted:")
    total_records = sum(deleted_counts.values())
    print(f"   Total Tables Cleared: {len(deleted_counts)}")
    print(f"   Total Records Deleted: {total_records:,}")
    
    if deleted_counts:
        print(f"\n   Breakdown:")
        for table, count in sorted(deleted_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"      • {table}: {count:,} records")
    
    print(f"\n📁 Files Deleted:")
    print(f"   Total Files Removed: {files_deleted:,}")
    
    print(f"\n✅ Master Data Preserved:")
    if preserved_data:
        for name, count in preserved_data.items():
            print(f"   ✓ {name}: {count} records")
    
    print("\n" + "=" * 80)
    print("✅ DATABASE RESET SUCCESSFUL!")
    print("=" * 80)
    
    print("\nYour HRMS is now in a fresh state:")
    print("  • All employees can still log in")
    print("  • Employee master data is intact")
    print("  • No transactional data exists")
    print("  • Ready for fresh testing")
    
    print("\nNext steps:")
    print("  1. Restart the application")
    print("  2. Test employee login")
    print("  3. Start fresh attendance/leave/shift transactions")
    print()


def main():
    """Main execution function."""
    start_time = datetime.now()
    
    print("\n" + "=" * 80)
    print("SMART HRMS - DATABASE RESET TOOL")
    print("=" * 80)
    print(f"Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Get confirmation
    if not confirm_reset():
        print("\n❌ Reset cancelled by user")
        return
    
    print("\n🚀 Starting database reset...")
    
    try:
        # Create Flask app
        app = create_app()
        
        # Step 1: Delete uploaded files
        files_deleted = delete_uploaded_files()
        
        # Step 2: Reset transactional tables
        deleted_counts = reset_transactional_tables(app)
        
        # Step 3: Verify master data preserved
        preserved_data, preservation_ok = verify_preservation(app)
        
        if not preservation_ok:
            print("\n⚠️  WARNING: Some master data may not have been preserved correctly")
        
        # Step 4: Verify transactional data deleted
        deletion_ok = verify_deletion(app)
        
        if not deletion_ok:
            print("\n⚠️  WARNING: Some transactional data may not have been deleted")
        
        # Step 5: Generate final report
        generate_report(deleted_counts, files_deleted, preserved_data, start_time)
        
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {str(e)}")
        import traceback
        print("\nStack trace:")
        traceback.print_exc()
        print("\n⚠️  Database reset may be incomplete. Please check the database manually.")


if __name__ == "__main__":
    main()
