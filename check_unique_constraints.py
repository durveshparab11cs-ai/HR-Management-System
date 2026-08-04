#!/usr/bin/env python
"""Check unique constraints on attendance table."""

from app import create_app
from app.extensions.database import db
from sqlalchemy import inspect

app = create_app()

with app.app_context():
    insp = inspect(db.engine)
    
    # Get indexes on attendance table
    print("Attendance table indexes:")
    for idx in insp.get_indexes('attendance'):
        print(f"  Index: {idx['name']}")
        print(f"    Columns: {idx['column_names']}")
        print(f"    Unique: {idx['unique']}")
        print()
    
    # Get constraints
    print("\nAttendance table constraints:")
    for constraint in insp.get_unique_constraints('attendance'):
        print(f"  Constraint: {constraint['name']}")
        print(f"    Columns: {constraint['column_names']}")
        print()
    
    # Get primary key
    print("\nAttendance table primary key:")
    pk = insp.get_pk_constraint('attendance')
    print(f"  Columns: {pk['constrained_columns']}")

print("\nDone")
