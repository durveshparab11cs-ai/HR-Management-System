from app import create_app
from app.models.hospital import Hospital

app = create_app()
with app.app_context():
    hospitals = Hospital.query.filter_by(is_active=True, is_deleted=False).order_by(Hospital.hospital_name).all()
    
    print("=== HOSPITALS IN DATABASE ===\n")
    for i, h in enumerate(hospitals, 1):
        print(f"{i:2d}. {h.hospital_name}")
