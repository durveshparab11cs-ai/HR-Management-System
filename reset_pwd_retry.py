import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensions import db
from app.models.user import User

MAX_RETRIES = 3
RETRY_DELAY = 5

for attempt in range(1, MAX_RETRIES + 1):
    try:
        print(f"Attempt {attempt}/{MAX_RETRIES}: Connecting to database...")
        app = create_app('production')
        
        with app.app_context():
            print("Finding coordinator user...")
            coordinator = User.query.filter_by(username='coordinator_kiosk').first()
            
            if not coordinator:
                print("ERROR: coordinator_kiosk user not found!")
                sys.exit(1)
            
            print(f"Found user: {coordinator.username}")
            
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
            print(f"Coordinator Portal: https://smarthrms.online/coordinator/")
            print("="*60)
            print("\nIMPORTANT: Update the login page template with new password!")
            sys.exit(0)
            
    except Exception as e:
        print(f"Attempt {attempt} failed: {str(e)[:100]}")
        if attempt < MAX_RETRIES:
            print(f"Retrying in {RETRY_DELAY} seconds...")
            time.sleep(RETRY_DELAY)
        else:
            print("\nAll retries failed. Database connection issues.")
            sys.exit(1)
