#!/usr/bin/env python3
"""
Run Comp Off Migration

This script applies the comp_off migration to add the new columns to the database.
Usage: python run_comp_off_migration.py
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app import create_app
from app.extensions.database import db
import sqlalchemy as sa


def run_migration():
    """Run the comp_off migration."""
    app = create_app()
    
    with app.app_context():
        try:
            print("🔄 Starting Comp Off Migration...")
            print("=" * 60)
            
            # Read the migration SQL file
            migration_file = project_root / "migrations" / "add_comp_off_fields.sql"
            if not migration_file.exists():
                print(f"❌ Migration file not found: {migration_file}")
                return False
            
            with open(migration_file, 'r') as f:
                sql_statements = f.read()
            
            # Execute the migration
            print(f"📝 Executing migration from {migration_file.name}...")
            
            # Split by semicolon and execute each statement
            statements = [stmt.strip() for stmt in sql_statements.split(';') if stmt.strip()]
            
            for i, statement in enumerate(statements, 1):
                if statement.startswith('--'):
                    # Skip comments
                    continue
                try:
                    print(f"   [{i}/{len(statements)}] Executing: {statement[:50]}...")
                    db.session.execute(sa.text(statement))
                except Exception as col_err:
                    # Column might already exist
                    if "duplicate column" in str(col_err).lower() or "already exists" in str(col_err).lower():
                        print(f"   ⚠️  Column already exists (skipping)")
                    else:
                        raise
            
            db.session.commit()
            print("✅ Migration completed successfully!")
            print("=" * 60)
            
            # Verify the new columns exist
            print("\n🔍 Verifying new columns...")
            
            inspector = sa.inspect(db.engine)
            
            # Check leave_requests columns
            lr_columns = [col['name'] for col in inspector.get_columns('leave_requests')]
            expected_cols = ['comp_off_work_date', 'comp_off_expiry_date', 'comp_off_used_on', 'comp_off_notified']
            
            missing_cols = []
            for col in expected_cols:
                if col in lr_columns:
                    print(f"   ✅ {col}: OK")
                else:
                    print(f"   ❌ {col}: MISSING")
                    missing_cols.append(col)
            
            # Check leave_types columns
            lt_columns = [col['name'] for col in inspector.get_columns('leave_types')]
            if 'leave_order' in lt_columns:
                print(f"   ✅ leave_order: OK")
            else:
                print(f"   ❌ leave_order: MISSING")
                missing_cols.append('leave_order')
            
            if missing_cols:
                print(f"\n⚠️  Some columns are still missing: {missing_cols}")
                print("This might be due to database locking. Try again or check database manually.")
                return False
            
            print("\n✅ All columns verified successfully!")
            print("=" * 60)
            print("\n🎉 Comp Off Migration Complete!")
            print("\nNext steps:")
            print("  1. Restart your application")
            print("  2. Test the Leave page with 4 leave types")
            print("  3. Verify Comp Off functionality")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Migration failed: {e}")
            print(f"Error type: {type(e).__name__}")
            db.session.rollback()
            return False


if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
