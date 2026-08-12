import os
from dotenv import load_dotenv
load_dotenv()
db_url = os.environ.get('DATABASE_URL', '')
if db_url.startswith('postgres://'):
    os.environ['DATABASE_URL'] = db_url.replace('postgres://', 'postgresql://', 1)

from app import create_app
from app.models.office_settings import OfficeSettings

app = create_app('production')
with app.app_context():
    offices = OfficeSettings.query.all()
    print(f"\nOfficeSettings records ({len(offices)}):\n")
    for office in offices:
        print(f"ID: {office.id}, Name: {office.name}")
        print(f"  Radius: {office.radius_metres}m")
        print(f"  Lat/Lng: {office.latitude}, {office.longitude}\n")
