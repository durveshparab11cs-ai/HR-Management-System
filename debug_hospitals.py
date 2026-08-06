from app import create_app
from app.models.hospital import Hospital

app = create_app()
with app.app_context():
    print("=== ALL HOSPITALS ===")
    hospitals = Hospital.query.all()
    print(f"Total hospitals: {len(hospitals)}")
    for h in hospitals:
        has_is_deleted = hasattr(h, 'is_deleted')
        is_deleted_val = getattr(h, 'is_deleted', 'NO_ATTR')
        print(f"  - {h.hospital_name}")
        print(f"      is_active={h.is_active}, has_is_deleted_attr={has_is_deleted}, is_deleted={is_deleted_val}")
    
    print("\n=== HOSPITALS WITH is_active=True AND is_deleted=False (OR NOT DELETED) ===")
    hospitals_active = Hospital.query.filter_by(is_active=True).all()
    print(f"Active hospitals: {len(hospitals_active)}")
    for h in hospitals_active:
        is_deleted_val = getattr(h, 'is_deleted', None)
        print(f"  - {h.hospital_name} (is_deleted={is_deleted_val})")
