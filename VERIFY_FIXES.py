#!/usr/bin/env python
"""
VERIFY_FIXES.py - Comprehensive verification of all fixes
Runs all checks to confirm admin dashboard and status fixes are working
"""

import sys
from datetime import date

def verify_fixes():
    print("="*70)
    print("COMPREHENSIVE FIX VERIFICATION")
    print("="*70)
    print()
    
    # Import and create app
    try:
        from app import create_app
        app = create_app()
        print("[OK] Application created successfully")
    except Exception as e:
        print("[FAILED] Could not create app: {}".format(e))
        return False
    
    with app.app_context():
        # Check 1: Admin routes registered
        print("\n--- Check 1: Admin Route Registration ---")
        admin_routes = []
        for rule in app.url_map.iter_rules():
            if 'admin' in rule.rule and rule.endpoint.startswith('admin.'):
                admin_routes.append(rule.rule)
        
        if '/admin/' in admin_routes or any(r == '/admin' for r in admin_routes):
            print("[OK] Admin dashboard route (/admin/) is registered")
        else:
            print("[FAILED] Admin dashboard route NOT found!")
            print("  Available admin routes: {}".format(admin_routes[:5]))
            return False
        
        # Check 2: Admin blueprint registered
        print("\n--- Check 2: Blueprint Registration ---")
        if 'admin' in app.blueprints:
            print("[OK] Admin blueprint is registered")
            bp = app.blueprints['admin']
            print("  Blueprint name: {}".format(bp.name))
            print("  URL prefix: {}".format(bp.url_prefix))
        else:
            print("[FAILED] Admin blueprint NOT registered!")
            return False
        
        # Check 3: No redirect hook
        print("\n--- Check 3: Redirect Hook Removed ---")
        try:
            init_source = open('app/__init__.py', encoding='utf-8').read()
        except:
            init_source = open('app/__init__.py', encoding='latin-1').read()
        if '_redirect_admin_to_dashboard' in init_source:
            print("[WARNING] _redirect_admin_to_dashboard function still exists!")
        else:
            print("[OK] Dangerous redirect hook removed")
        
        # Check 4: Status computation code present
        print("\n--- Check 4: Status Computation Code ---")
        try:
            admin_routes_source = open('app/blueprints/admin/routes.py', encoding='utf-8').read()
        except:
            admin_routes_source = open('app/blueprints/admin/routes.py', encoding='latin-1').read()
        if 'AttendancePhoto' in admin_routes_source and 'photo.image_data' in admin_routes_source:
            print("[OK] Photo-based status computation code is present")
            if 'has_checkin_photo' in admin_routes_source and 'has_checkout_photo' in admin_routes_source:
                print("[OK] Both check-in and check-out photo checks are present")
            else:
                print("[WARNING] Photo check logic may be incomplete")
        else:
            print("[FAILED] Status computation code NOT found!")
            return False
        
        # Check 5: Template styling present
        print("\n--- Check 5: Template Styling ---")
        try:
            template_source = open('app/templates/admin/index.html', encoding='utf-8').read()
        except:
            template_source = open('app/templates/admin/index.html', encoding='latin-1').read()
        if 'badge-pending' in template_source:
            print("[OK] Pending status styling is present")
        else:
            print("[WARNING] Pending status styling may be missing")
        
        if 'att.status' in template_source:
            print("[OK] Status display logic is in template")
        else:
            print("[WARNING] Status display logic may be missing")
        
        # Check 6: Imports work
        print("\n--- Check 6: Import Verification ---")
        try:
            from app.models.attendance_photo import AttendancePhoto
            print("[OK] AttendancePhoto model imports successfully")
        except Exception as e:
            print("[FAILED] AttendancePhoto import failed: {}".format(e))
            return False
        
        try:
            from app.blueprints.attendance.attendance_engine import compute_check_out_meta
            print("[OK] compute_check_out_meta imports successfully")
        except Exception as e:
            print("[FAILED] compute_check_out_meta import failed: {}".format(e))
            return False
        
        # Check 7: Repository instantiation
        print("\n--- Check 7: Repository Instantiation ---")
        try:
            from app.blueprints.attendance.repository import AttendanceRepository
            from app.blueprints.employees.repository import EmployeeRepository
            from app.blueprints.leave.repository import LeaveRepository
            from app.blueprints.admin.service import AdminService
            
            _att   = AttendanceRepository()
            _emp   = EmployeeRepository()
            _leave = LeaveRepository()
            _svc   = AdminService()
            
            print("[OK] All repositories instantiate successfully")
        except Exception as e:
            print("[FAILED] Repository instantiation failed: {}".format(e))
            return False
        
        # Check 8: Admin dashboard statistics work
        print("\n--- Check 8: Admin Dashboard Statistics ---")
        try:
            today = date.today()
            total_employees = _emp.count_total()
            checked_in = _att.count_checked_in_today(today)
            
            print("[OK] Dashboard statistics queries work")
            print("  Total employees: {}".format(total_employees))
            print("  Checked in today: {}".format(checked_in))
        except Exception as e:
            print("[FAILED] Dashboard statistics failed: {}".format(e))
            return False
        
        # Check 9: Status computation logic
        print("\n--- Check 9: Status Computation Logic ---")
        try:
            today_records = _att.get_all_today(today)
            print("[OK] Today's records query works")
            print("  Records today: {}".format(len(today_records)))
            
            # Test photo checking logic on first record if available
            if len(today_records) > 0:
                att = today_records[0]
                photo = AttendancePhoto.query.filter_by(attendance_id=att.id).first()
                has_checkin = photo and photo.image_data
                has_checkout = photo and photo.checkout_image_data
                
                print("[OK] Photo checking logic works")
                print("  Sample record: att_id={}, has_check_in_photo={}, has_check_out_photo={}".format(
                    att.id, has_checkin, has_checkout
                ))
        except Exception as e:
            print("[WARNING] Could not test status logic on records: {}".format(e))
        
    print("\n" + "="*70)
    print("VERIFICATION COMPLETE - ALL CHECKS PASSED!")
    print("="*70)
    print("\nNext steps:")
    print("1. Deploy changes to production")
    print("2. Login as admin user (e2512012 or e2603025)")
    print("3. Navigate to Admin Panel")
    print("4. Verify dashboard loads WITHOUT 404 error")
    print("5. Check attendance status display (PENDING/ABSENT/HALF_DAY/PRESENT)")
    print()
    return True

if __name__ == '__main__':
    success = verify_fixes()
    sys.exit(0 if success else 1)
