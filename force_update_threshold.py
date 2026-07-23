"""Force update half_day_threshold to 300 minutes"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app import create_app
from app.extensions.database import db
from app.models.office_settings import OfficeSettings

app = create_app()

with app.app_context():
    offices = OfficeSettings.query.all()
    
    for office in offices:
        print(f"Updating {office.name}: {office.half_day_threshold_minutes} → 300")
        office.half_day_threshold_minutes = 300
        db.session.add(office)
    
    db.session.commit()
    
    print("\n✅ Updated successfully!")
    
    for office in OfficeSettings.query.all():
        print(f"{office.name}: {office.half_day_threshold_minutes} minutes = {office.half_day_threshold_minutes / 60:.1f} hours")
