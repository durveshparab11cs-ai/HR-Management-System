#!/usr/bin/env python3
"""
Script to reset the Coordinator Portal password.
This is a one-time password reset script.
"""

import sys
from app import create_app
from app.extensions import db
from app.models.user import User

def reset_coordinator_password(new_password):
    """Reset the coordinator user password."""
    
    app = create_app('production')
    
    with app.app_context():
        # Find coordinator user
        coordinator = User.query.filter_by(username='coordinator_kiosk').first()
        
        if not coordinator:
            print(f"✗ ERROR: Coordinator user 'coordinator_kiosk' not found!")
            print(f"  Run: python create_coordinator_user.py first")
            return False
        
        # Reset password
        coordinator.set_password(new_password)
        db.session.commit()
        
        print(f"{'='*60}")
        print(f"✓ COORDINATOR PASSWORD RESET SUCCESSFUL!")
        print(f"{'='*60}")
        print(f"Username: coordinator_kiosk")
        print(f"New Password: {new_password}")
        print(f"Role: {coordinator.role}")
        print(f"URL: https://smarthrms.online/coordinator/")
        print(f"{'='*60}\n")
        
        return True

if __name__ == '__main__':
    # Set your new password here
    NEW_PASSWORD = "SmartHRMS@Coordinator2026"
    
    try:
        success = reset_coordinator_password(NEW_PASSWORD)
        if success:
            print("✓ Password reset complete!")
            print(f"\nIMPORTANT: Store this password securely.")
            print(f"Update the login page template if needed.")
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
