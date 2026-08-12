#!/usr/bin/env python
"""
set_super_admin.py
===================
Script to set a user as SUPER_ADMIN.

Usage:
    python set_super_admin.py <username>

Example:
    python set_super_admin.py e2606026
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from app.models.user import User
from app.extensions.database import db

def main():
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        print(__doc__)
        return

    username = sys.argv[1]
    app = create_app()

    with app.app_context():
        # Find user
        user = User.query.filter_by(username=username).first()
        
        if not user:
            print(f"❌ User '{username}' not found")
            return

        old_role = user.role
        user.role = "super_admin"
        
        db.session.commit()
        
        print(f"✅ User updated successfully!")
        print(f"   Username: {user.username}")
        print(f"   Email: {user.email}")
        print(f"   Old Role: {old_role}")
        print(f"   New Role: {user.role}")

if __name__ == "__main__":
    main()
