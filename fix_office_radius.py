import os
from dotenv import load_dotenv
load_dotenv()
db_url = os.environ.get('DATABASE_URL', '')
if db_url.startswith('postgres://'):
    os.environ['DATABASE_URL'] = db_url.replace('postgres://', 'postgresql://', 1)

from app import create_app
from app.models.office_settings import OfficeSettings
from app.extensions.database import db

app = create_app('production')

with app.app_context():
    print("\n" + "="*60)
    print("UPDATING OFFICE SETTINGS RADIUS TO 150m")
    print("="*60 + "\n")
    
    offices = OfficeSettings.query.all()
    
    if not offices:
        print("❌ No OfficeSettings found!")
    else:
        for office in offices:
            print(f"Updating: {office.name}")
            print(f"  Old radius: {office.radius_metres}m")
            print(f"  Coordinates: {office.latitude}, {office.longitude}")
            
            office.radius_metres = 150
            db.session.commit()
            
            print(f"  ✅ NEW RADIUS: {office.radius_metres}m\n")
    
    print("="*60)
    print("After updating, your 72m GPS drift will be ACCEPTED!")
    print("="*60 + "\n")
