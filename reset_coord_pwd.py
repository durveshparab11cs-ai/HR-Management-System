import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensions import db
from app.models.user import User

print("Connecting to database...")
app = create_app('production')

with app.app_context():
    print("Finding coordinator user...")
    coordinator = User.query.filter_by(username='coordinator_kiosk').first()
    
    if not coordinator:
        print("ERROR: coordinator_kiosk user not found!")
        sys.exit(1)
    
    print(f"Found user: {coordinator.username}")
    print(f"Current role: {coordinator.role}")
    
    # New password
    new_password = "SmartHRMS@Coordinator2026"
    
    print(f"Setting new password...")
    coordinator.set_password(new_password)
    db.session.commit()
    
    print("\n" + "="*60)
    print("SUCCESS! Coordinator password has been reset")
    print("="*60)
    print(f"Username: coordinator_kiosk")
    print(f"New Password: {new_password}")
    print(f"Login URL: https://smarthrms.online/auth/login")
    print("="*60)
