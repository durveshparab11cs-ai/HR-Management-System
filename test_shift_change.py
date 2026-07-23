"""Test Shift Change Module"""
from app import create_app
from app.extensions.database import db

app = create_app()

with app.app_context():
    print("=" * 70)
    print("SHIFT CHANGE MODULE TEST")
    print("=" * 70)
    print()
    
    # Test 1: Check if tables exist
    print("1. Checking database tables...")
    tables = list(db.metadata.tables.keys())
    print(f"   Total tables: {len(tables)}")
    
    shift_tables = [t for t in tables if 'shift' in t.lower()]
    print(f"   Shift-related tables: {shift_tables}")
    
    if 'employee_shift_assignments' in tables:
        print("   ✅ employee_shift_assignments table exists")
    else:
        print("   ❌ employee_shift_assignments table NOT found")
    
    if 'shift_change_requests' in tables:
        print("   ✅ shift_change_requests table exists")
    else:
        print("   ❌ shift_change_requests table NOT found")
    
    print()
    
    # Test 2: Import models
    print("2. Importing models...")
    try:
        from app.models import EmployeeShiftAssignment, ShiftChangeRequest
        print("   ✅ Models imported successfully")
        print(f"   - EmployeeShiftAssignment: {EmployeeShiftAssignment.__tablename__}")
        print(f"   - ShiftChangeRequest: {ShiftChangeRequest.__tablename__}")
    except Exception as e:
        print(f"   ❌ Error importing models: {e}")
    
    print()
    
    # Test 3: Check if blueprint is registered
    print("3. Checking blueprints...")
    blueprints = list(app.blueprints.keys())
    print(f"   Total blueprints: {len(blueprints)}")
    
    if 'shift_change' in blueprints:
        print("   ✅ shift_change blueprint registered")
    else:
        print("   ❌ shift_change blueprint NOT registered")
    
    print()
    
    # Test 4: Check if routes exist
    print("4. Checking routes...")
    shift_routes = [rule for rule in app.url_map.iter_rules() if 'shift' in rule.endpoint]
    print(f"   Shift-related routes: {len(shift_routes)}")
    for route in shift_routes[:5]:
        print(f"   - {route.endpoint}: {route.rule}")
    if len(shift_routes) > 5:
        print(f"   ... and {len(shift_routes) - 5} more")
    
    print()
    
    # Test 5: Check existing Shift model from company
    print("5. Checking Shift model...")
    try:
        from app.models.company import Shift
        shifts = Shift.query.all()
        print(f"   ✅ Shift model accessible")
        print(f"   - Total shifts in database: {len(shifts)}")
        for shift in shifts:
            print(f"     • {shift.name} ({shift.code}): {shift.start_time} - {shift.end_time}")
    except Exception as e:
        print(f"   ❌ Error accessing Shift model: {e}")
    
    print()
    
    # Test 6: Test service layer
    print("6. Testing service layer...")
    try:
        from app.blueprints.shift_change.service import ShiftChangeService
        service = ShiftChangeService()
        print("   ✅ ShiftChangeService instantiated")
    except Exception as e:
        print(f"   ❌ Error instantiating service: {e}")
    
    print()
    print("=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)
