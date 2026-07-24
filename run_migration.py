"""
Database Migration Script
Run this to add reporting_manager fields to shift_change_requests table
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app import create_app
from app.extensions.database import db

def run_migration():
    """Run the shift change manager fields migration."""
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("SHIFT CHANGE MANAGER FIELDS MIGRATION")
        print("=" * 60)
        print()
        
        try:
            # Check if columns already exist
            print("Checking if columns exist...")
            result = db.session.execute(db.text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'shift_change_requests' 
                AND column_name IN ('reporting_manager_code', 'reporting_manager_name')
            """))
            existing_columns = [row[0] for row in result]
            
            if len(existing_columns) == 2:
                print("✅ Columns already exist. Migration not needed.")
                return
            
            print(f"Found {len(existing_columns)} of 2 required columns.")
            print("Running migration...")
            print()
            
            # Step 1: Add reporting_manager_code
            if 'reporting_manager_code' not in existing_columns:
                print("Adding column: reporting_manager_code...")
                db.session.execute(db.text("""
                    ALTER TABLE shift_change_requests 
                    ADD COLUMN IF NOT EXISTS reporting_manager_code VARCHAR(50)
                """))
                db.session.commit()
                print("✅ Added reporting_manager_code")
            
            # Step 2: Add reporting_manager_name
            if 'reporting_manager_name' not in existing_columns:
                print("Adding column: reporting_manager_name...")
                db.session.execute(db.text("""
                    ALTER TABLE shift_change_requests 
                    ADD COLUMN IF NOT EXISTS reporting_manager_name VARCHAR(200)
                """))
                db.session.commit()
                print("✅ Added reporting_manager_name")
            
            # Step 3: Update existing records
            print("Updating existing records...")
            db.session.execute(db.text("""
                UPDATE shift_change_requests 
                SET reporting_manager_code = 'PENDING', 
                    reporting_manager_name = 'To Be Assigned'
                WHERE reporting_manager_code IS NULL OR reporting_manager_code = ''
            """))
            db.session.commit()
            print("✅ Updated existing records")
            
            # Step 4: Set NOT NULL constraint
            print("Setting NOT NULL constraint...")
            db.session.execute(db.text("""
                ALTER TABLE shift_change_requests 
                ALTER COLUMN reporting_manager_code SET DEFAULT ''
            """))
            db.session.execute(db.text("""
                ALTER TABLE shift_change_requests 
                ALTER COLUMN reporting_manager_code SET NOT NULL
            """))
            db.session.commit()
            print("✅ Set NOT NULL constraint")
            
            # Step 5: Create index
            print("Creating index...")
            db.session.execute(db.text("""
                CREATE INDEX IF NOT EXISTS idx_shift_change_requests_manager_code 
                ON shift_change_requests(reporting_manager_code)
            """))
            db.session.commit()
            print("✅ Created index")
            
            print()
            print("=" * 60)
            print("✅ MIGRATION COMPLETED SUCCESSFULLY")
            print("=" * 60)
            print()
            print("The shift_change_requests table now has:")
            print("  - reporting_manager_code (VARCHAR 50, NOT NULL)")
            print("  - reporting_manager_name (VARCHAR 200, NULLABLE)")
            print("  - Index on reporting_manager_code")
            print()
            
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            db.session.rollback()
            print()
            print("Migration failed. Please check the error above.")
            return False
        
        return True

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
