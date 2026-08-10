from app import create_app
from app.extensions.database import db
from app.models.user import User
from datetime import date

app = create_app()

with app.app_context():
    print("Testing admin index route logic...")
    
    try:
        from app.blueprints.attendance.repository import AttendanceRepository
        from app.blueprints.employees.repository import EmployeeRepository
        from app.blueprints.leave.repository import LeaveRepository
        from app.blueprints.admin.service import AdminService
        
        _att   = AttendanceRepository()
        _emp   = EmployeeRepository()
        _leave = LeaveRepository()
        _svc   = AdminService()
        
        today = date.today()
        
        print("[OK] Repositories initialized")
        print("[OK] Getting total employees...")
        total_employees = _emp.count_total()
        print("  Total employees: {}".format(total_employees))
        
        print("[OK] Getting checked in today...")
        checked_in_today = _att.count_checked_in_today(today)
        print("  Checked in: {}".format(checked_in_today))
        
        print("[OK] Getting today's records...")
        today_records = _att.get_all_today(today)
        print("  Today's records: {}".format(len(today_records)))
        
        # Test the photo checking logic
        from app.blueprints.attendance.attendance_engine import compute_check_out_meta
        from app.models.attendance_photo import AttendancePhoto
        
        print("[OK] Testing photo checking logic on {} records...".format(len(today_records)))
        for i, att in enumerate(today_records[:3]):  # Test first 3
            try:
                photo = AttendancePhoto.query.filter_by(attendance_id=att.id).first()
                has_checkin_photo = photo and photo.image_data
                has_checkout_photo = photo and photo.checkout_image_data
                
                if not has_checkin_photo or not has_checkout_photo:
                    att.status = "pending"
                elif att.check_in_time and att.check_out_time:
                    office = _att.get_office_for_employee(_emp.get_by_id(att.employee_id))
                    if office:
                        meta = compute_check_out_meta(att, att.check_out_time, office, att.employee_id)
                        new_status = meta.get("status")
                        if new_status:
                            att.status = new_status
                
                print("  Record {}: att_id={}, status={}".format(i+1, att.id, att.status))
            except Exception as e:
                print("  Record {} ERROR: {}".format(i+1, e))
                import traceback
                traceback.print_exc()
        
        print("\n[SUCCESS] All tests passed!")
        
    except Exception as e:
        print("\n[FAILED] Error: {}".format(e))
        import traceback
        traceback.print_exc()
