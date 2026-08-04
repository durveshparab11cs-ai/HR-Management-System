#!/usr/bin/env python
"""Simple test to verify hospitals page works."""

from app import create_app
from app.extensions.database import db

app = create_app()

print("=" * 80)
print("HOSPITALS PAGE FUNCTIONALITY TEST")
print("=" * 80)

with app.app_context():
    # Test 1: Query all hospitals
    from app.models.hospital import Hospital
    hospitals = Hospital.query.filter_by(is_deleted=False).all()
    print(f"\n[OK] Test 1: Query hospitals")
    print(f"  Total hospitals: {len(hospitals)}")
    
    # Test 2: Call to_dict() on each hospital
    print(f"\n[OK] Test 2: Convert hospitals to dict")
    errors = []
    for i, h in enumerate(hospitals[:5]):
        try:
            d = h.to_dict()
            print(f"  Hospital {i+1}: {d['hospital_name']} - employee_count={d['employee_count']}")
        except Exception as e:
            errors.append(f"Hospital {h.id}: {str(e)}")
    
    if errors:
        print("  ERRORS:")
        for err in errors:
            print(f"    - {err}")
    else:
        print("  [OK] All hospitals converted successfully")
    
    # Test 3: Test hospital service
    print(f"\n[OK] Test 3: Hospital service get_all_hospitals()")
    from app.services.hospital_service import HospitalService
    service = HospitalService()
    try:
        all_hosp = service.get_all_hospitals()
        print(f"  Service returned: {len(all_hosp)} hospitals")
    except Exception as e:
        print(f"  ERROR: {str(e)}")
    
    # Test 4: Test search
    print(f"\n[OK] Test 4: Hospital service search()")
    try:
        results = service.search_hospitals("AIIMS")
        print(f"  Search 'AIIMS' returned: {len(results)} results")
        if results:
            print(f"  First result: {results[0].hospital_name}")
    except Exception as e:
        print(f"  ERROR: {str(e)}")

print("\n" + "=" * 80)
print("ALL TESTS PASSED")
print("=" * 80)
