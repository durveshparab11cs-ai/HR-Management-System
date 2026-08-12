#!/usr/bin/env python3
"""
Fix Head office GPS allowed radius to 150 meters to account for GPS accuracy.
Run this once to update the existing hospital record.
"""

import os
import sys
from pathlib import Path

# Set environment
os.environ['FLASK_ENV'] = 'production'
sys.path.insert(0, str(Path.cwd()))

# Load environment
from dotenv import load_dotenv
load_dotenv()

# Fix database URL
db_url = os.environ.get('DATABASE_URL', '')
if db_url.startswith('postgres://'):
    os.environ['DATABASE_URL'] = db_url.replace('postgres://', 'postgresql://', 1)

from app import create_app
from app.models.hospital import Hospital
from app.extensions.database import db

app = create_app('production')

with app.app_context():
    print("\nUpdating Head office GPS radius...")
    
    # Find Head office
    head_office = Hospital.query.filter_by(hospital_name='Head office').first()
    
    if head_office:
        old_radius = head_office.allowed_radius_metres
        head_office.allowed_radius_metres = 150
        db.session.commit()
        
        print(f"✅ Head office updated:")
        print(f"   Location: {head_office.hospital_name}")
        print(f"   Coordinates: {head_office.latitude}, {head_office.longitude}")
        print(f"   Old radius: {old_radius}m")
        print(f"   New radius: {head_office.allowed_radius_metres}m")
        print(f"\n   GPS accuracy accounts for ±72m satellite drift")
        print(f"   150m radius allows comfortable check-in")
    else:
        print("❌ Head office hospital not found in database")
        print("   Make sure app started and seeded hospitals first")

print()
