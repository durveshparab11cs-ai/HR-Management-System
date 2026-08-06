from app import create_app
from app.models.hospital import Hospital
from app.extensions.database import db

app = create_app()
with app.app_context():
    # Missing hospitals from the Excel file
    missing_hospitals = [
        {
            'hospital_name': 'Claim Team',
            'latitude': 0.0,
            'longitude': 0.0,
            'allowed_radius_metres': 100,
        },
        {
            'hospital_name': 'Project Office',
            'latitude': 0.0,
            'longitude': 0.0,
            'allowed_radius_metres': 100,
        },
        {
            'hospital_name': 'Despande Hospital',
            'latitude': 0.0,
            'longitude': 0.0,
            'allowed_radius_metres': 100,
        },
        {
            'hospital_name': 'Trauma Hospital',
            'latitude': 0.0,
            'longitude': 0.0,
            'allowed_radius_metres': 100,
        },
    ]
    
    added_count = 0
    for hospital_data in missing_hospitals:
        # Check if already exists
        existing = Hospital.query.filter_by(hospital_name=hospital_data['hospital_name']).first()
        if not existing:
            hospital = Hospital(**hospital_data)
            db.session.add(hospital)
            added_count += 1
            print(f"[+] Added: {hospital_data['hospital_name']}")
        else:
            print(f"[-] Already exists: {hospital_data['hospital_name']}")
    
    db.session.commit()
    print(f"\n[SUCCESS] Total added: {added_count}")
