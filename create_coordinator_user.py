#!/usr/bin/env python3
"""
Script to create a dedicated Coordinator Portal user account.

This user will be used to access the kiosk for recording employee attendance.
Regular employees will NOT be able to check in/out from their own portals.
"""

import sys
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.employee import Employee
from app.constants.enums import UserRole, UserStatus

def create_coordinator_user():
    """Create or update the coordinator user account."""
    
    app = create_app('production')
    
    with app.app_context():
        # Check if coordinator user already exists
        coordinator = User.query.filter_by(username='coordinator_kiosk').first()
        
        if coordinator:
            print(f"✓ Coordinator user already exists: {coordinator.username}")
            print(f"  Name: {coordinator.full_name}")
            print(f"  Role: {coordinator.role}")
            print(f"  Email: {coordinator.email}")
            return coordinator
        
        # Create new coordinator user
        print("Creating new Coordinator Portal user...")
        
        coordinator = User(
            username='coordinator_kiosk',
            email='coordinator@smarthrms.local',
            first_name='Coordinator',
            last_name='Portal',
            role=UserRole.SUPER_ADMIN.value,  # Give admin permissions to manage attendance
            status=UserStatus.ACTIVE.value,
        )
        
        # Set password: "CoordinatorPortal@2026"
        coordinator.set_password('CoordinatorPortal@2026')
        
        db.session.add(coordinator)
        db.session.commit()
        
        print(f"✓ Coordinator user created successfully!")
        print(f"\n{'='*60}")
        print(f"COORDINATOR LOGIN CREDENTIALS")
        print(f"{'='*60}")
        print(f"Username: coordinator_kiosk")
        print(f"Password: CoordinatorPortal@2026")
        print(f"Role:     Super Admin (can access all attendance)")
        print(f"URL:      https://smarthrms.online/coordinator/")
        print(f"{'='*60}\n")
        
        return coordinator

if __name__ == '__main__':
    try:
        create_coordinator_user()
        print("✓ Setup complete!")
        sys.exit(0)
    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        sys.exit(1)
