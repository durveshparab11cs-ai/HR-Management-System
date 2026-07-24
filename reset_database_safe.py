"""
reset_database_safe.py
=======================
SAFE database reset with automatic backup.

This version creates a backup before resetting, allowing recovery if needed.

USAGE:
    python reset_database_safe.py
"""

import os
import shutil
from datetime import datetime
from pathlib import Path

from reset_database import (
    delete_uploaded_files,
    reset_transactional_tables,
    verify_preservation,
    verify_deletion,
    generate_report
)
from app import create_app


def create_backup():
    """Create backup of database and uploads before reset."""
    print("\n" + "=" * 80)
    print("CREATING BACKUP")
    print("=" * 80)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = Path(f"backups/reset_backup_{timestamp}")
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n📁 Backup location: {backup_dir}")
    
    # Backup database
    db_file = Path("instance/smart_hrms.db")
    if db_file.exists():
        shutil.copy2(db_file, backup_dir / "smart_hrms.db")
        db_size = db_file.stat().st_size / (1024 * 1024)  # MB
        print(f"✅ Database backed up ({db_size:.2f} MB)")
    else:
        print("⚠️  Database file not found")
    
    # Backup uploads folder
    uploads_dir = Path("instance/uploads")
    if uploads_dir.exists():
        shutil.copytree(uploads_dir, backup_dir / "uploads", dirs_exist_ok=True)
        file_count = len(list((backup_dir / "uploads").rglob("*")))
        print(f"✅ Uploads folder backed up ({file_count} files)")
    else:
        print("ℹ️  Uploads folder not found")
    
    # Create backup info file
    info_file = backup_dir / "backup_info.txt"
    with open(info_file, "w") as f:
        f.write(f"Smart HRMS Database Backup\n")
        f.write(f"Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Purpose: Pre-reset backup\n")
        f.write(f"\nRestore Instructions:\n")
        f.write(f"1. Stop the application\n")
        f.write(f"2. Copy smart_hrms.db to instance/\n")
        f.write(f"3. Copy uploads/ contents to instance/uploads/\n")
        f.write(f"4. Restart the application\n")
    
    print(f"✅ Backup info saved: {info_file}")
    print(f"\n📦 Backup complete: {backup_dir}")
    
    return backup_dir


def main():
    """Main execution with backup."""
    start_time = datetime.now()
    
    print("\n" + "=" * 80)
    print("SMART HRMS - SAFE DATABASE RESET TOOL (WITH BACKUP)")
    print("=" * 80)
    print(f"Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Confirmation
    print("\n⚠️  This will:")
    print("  1. Create a backup of your current database")
    print("  2. Delete all transactional data")
    print("  3. Preserve employee master data")
    print()
    
    response = input("Type 'YES' to proceed with safe reset: ")
    if response != "YES":
        print("\n❌ Reset cancelled")
        return
    
    try:
        # Step 1: Create backup
        backup_dir = create_backup()
        
        # Step 2: Proceed with reset
        app = create_app()
        
        # Step 3: Delete files
        files_deleted = delete_uploaded_files()
        
        # Step 4: Reset database
        deleted_counts = reset_transactional_tables(app)
        
        # Step 5: Verify
        preserved_data, preservation_ok = verify_preservation(app)
        deletion_ok = verify_deletion(app)
        
        # Step 6: Report
        generate_report(deleted_counts, files_deleted, preserved_data, start_time)
        
        print(f"\n💾 Backup available at: {backup_dir}")
        print("   (Keep this backup for recovery if needed)")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        print(f"\n💾 Your backup is safe at: {backup_dir}")
        print("   You can restore from this backup if needed")


if __name__ == "__main__":
    main()
