#!/usr/bin/env python
"""Debug script to test hospitals endpoint."""

from app import create_app
from app.models.hospital import Hospital
from app.extensions.database import db
from sqlalchemy import inspect

app = create_app()

with app.app_context():
    print("=" * 80)
    print("HOSPITALS DEBUG TEST")
    print("=" * 80)
    
    # Check if table exists
    insp = inspect(db.engine)
    tables = insp.get_table_names()
    print(f"\n1. Hospitals table exists: {'hospitals' in tables}")
    
    # Try to query hospitals
    try:
        hospitals = Hospital.query.filter_by(is_deleted=False).all()
        print(f"2. Hospitals count: {len(hospitals)}")
        
        if hospitals:
            h = hospitals[0]
            print(f"3. First hospital ID: {h.id}")
            print(f"4. First hospital name: {h.hospital_name}")
            
            # Try to_dict()
            try:
                d = h.to_dict()
                print(f"5. to_dict() SUCCESS: {d.get('hospital_name')}")
            except AttributeError as e:
                print(f"5. to_dict() FAILED with AttributeError: {str(e)}")
            except Exception as e:
                print(f"5. to_dict() FAILED with {type(e).__name__}: {str(e)}")
        else:
            print("3. No hospitals found in database")
    except Exception as e:
        print(f"2. Error querying hospitals: {type(e).__name__}: {str(e)}")
    
    # Try to access the route
    print("\n6. Testing HTTP GET /admin/hospitals")
    with app.test_client() as client:
        try:
            response = client.get('/admin/hospitals', follow_redirects=False)
            print(f"   Status: {response.status_code}")
            if response.status_code != 302:
                data = response.get_data(as_text=True)
                if 'AttributeError' in data or 'error' in data.lower():
                    print(f"   ERROR in response: {data[:500]}")
        except Exception as e:
            print(f"   Exception: {type(e).__name__}: {str(e)}")

print("\nDone.")
