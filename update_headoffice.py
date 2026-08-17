#!/usr/bin/env python3
import os, sys
from pathlib import Path
os.environ['FLASK_ENV'] = 'production'
sys.path.insert(0, str(Path.cwd()))
from dotenv import load_dotenv
load_dotenv()
db_url = os.environ.get('DATABASE_URL', '')
if db_url.startswith('postgres://'):
    os.environ['DATABASE_URL'] = db_url.replace('postgres://', 'postgresql://', 1)
from app import create_app
from app.models.hospital import Hospital
from app.extensions.database import db

app = create_app('production')
with app.app_context():
    print("\n" + "="*60)
    print("UPDATING HEAD OFFICE GPS RADIUS TO 150m")
    print("="*60 + "\n")
    ho = Hospital.query.filter_by(hospital_name='Head office').first()
    if ho:
        print(f"✅ Found: {ho.hospital_name}")
        print(f"   Coordinates: {ho.latitude}, {ho.longitude}")
        print(f"   Current radius: {ho.allowed_radius_metres}m")
        ho.allowed_radius_metres = 150
        db.session.commit()
        print(f"   ✅ NEW RADIUS: {ho.allowed_radius_metres}m")
        print(f"\n   Your distance: 72m < Allowed: 150m ✅")
    else:
        print("❌ Head office NOT found")
    print("\n" + "="*60 + "\n")
