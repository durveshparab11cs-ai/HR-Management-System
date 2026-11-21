"""
blueprints/admin/routes.py
============================
Admin panel routes — dashboard, office settings, user management.
"""

from datetime import date
from flask import flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.core.security import admin_required, hr_required, roles_required
from app.constants.enums import UserRole
from app.blueprints.attendance.repository import AttendanceRepository
from app.blueprints.employees.repository import EmployeeRepository
from app.blueprints.leave.repository import LeaveRepository
from .forms import OfficeSettingsForm
from .service import AdminService
from . import admin_bp

# TEMPORARY DEBUGGING ENDPOINT - Remove after role update confirmed
@admin_bp.route("/debug-users", methods=["GET"])
def debug_users():
    """Temporary endpoint to check user roles in production database."""
    from app.models.user import User
    from app.extensions.database import db
    
    try:
        user1 = User.query.filter_by(username='e_2512012').first()
        user2 = User.query.filter_by(username='e_2603025').first()
        
        return {
            "e_2512012": {
                "exists": user1 is not None,
                "role": user1.role if user1 else None,
                "email": user1.email if user1 else None
            },
            "e_2603025": {
                "exists": user2 is not None,
                "role": user2.role if user2 else None,
                "email": user2.email if user2 else None
            }
        }, 200
    except Exception as e:
        return {"error": str(e)}, 500

_att   = AttendanceRepository()
_emp   = EmployeeRepository()
_leave = LeaveRepository()
_svc   = AdminService()


@admin_bp.route("/")
@admin_bp.route("")
@login_required
@admin_required
def index():
    today = date.today()
    from datetime import datetime
    now = datetime.now()
    try:
        total_employees   = _emp.count_total()
    except Exception:
        total_employees   = 0
    try:
        checked_in_today  = _att.count_checked_in_today(today)
    except Exception:
        checked_in_today  = 0
    try:
        checked_out_today = _att.count_checked_out_today(today)
    except Exception:
        checked_out_today = 0
    try:
        late_today        = _att.count_late_today(today)
    except Exception:
        late_today        = 0
    absent_today = max(0, total_employees - checked_in_today)
    try:
        pending_leaves    = _leave.count_pending()
    except Exception:
        pending_leaves    = 0
    try:
        pending_halfdays  = _leave.count_pending_halfdays()
    except Exception:
        pending_halfdays  = 0
    try:
        pending_early     = _leave.count_pending_earlyleaves()
    except Exception:
        pending_early     = 0
    try:
        today_records     = _att.get_all_today(today)
        # Add computed status based on working hours and photo uploads
        from app.blueprints.attendance.attendance_engine import compute_check_out_meta
        from app.models.attendance_photo import AttendancePhoto
        from datetime import datetime as dt_now
        for att in today_records:
            try:
                # Check if both check-in and check-out photos are uploaded
                photo = AttendancePhoto.query.filter_by(attendance_id=att.id).first()
                has_checkin_photo = photo and photo.image_data
                has_checkout_photo = photo and photo.checkout_image_data
                
                if not has_checkin_photo or not has_checkout_photo:
                    # Missing one or both photos → PENDING
                    att.status = "pending"
                elif att.check_in_time and att.check_out_time:
                    # Both photos uploaded - compute status based on working hours
                    office = _att.get_office_for_employee(_emp.get_by_id(att.employee_id))
                    if office:
                        meta = compute_check_out_meta(att, att.check_out_time, office, att.employee_id)
                        new_status = meta.get("status")
                        if new_status:
                            att.status = new_status
            except Exception as e:
                import logging
                logging.error(f"Error computing status for att {att.id}: {e}", exc_info=True)
    except Exception as e:
        import logging
        logging.error(f"Error fetching today records: {e}", exc_info=True)
        today_records     = []
    try:
        recent_requests   = _leave.get_pending(page=1, per_page=5).items
    except Exception:
        recent_requests   = []

    # Fetch recent attendance photos for the live visual verification card
    recent_photos = []
    total_photos_count = 0
    try:
        from app.models.attendance_photo import AttendancePhoto
        from app.models.employee import Employee
        total_photos_count = AttendancePhoto.query.count()
        raw_photos = (
            AttendancePhoto.query
            .order_by(AttendancePhoto.id.desc())
            .limit(6)
            .all()
        )
        for p in raw_photos:
            emp = Employee.query.get(p.employee_id) if p.employee_id else None
            recent_photos.append({
                "id": p.id,
                "attendance_id": p.attendance_id,
                "employee_name": emp.full_name if emp else "Employee",
                "employee_code": emp.employee_code if emp else "",
                "department": emp.department if emp else "Operations",
                "image_data": p.image_data,
                "checkout_image_data": p.checkout_image_data,
                "uploaded_at": getattr(p, "uploaded_at", None),
            })
    except Exception as e:
        import logging
        logging.error(f"Error fetching recent photos for admin index: {e}")

    return render_template(
        "admin/index.html",
        title="Super Admin Operations Console",
        today=today,
        now=now,
        total_employees=total_employees,
        checked_in_today=checked_in_today,
        checked_out_today=checked_out_today,
        late_today=late_today,
        absent_today=absent_today,
        pending_leaves=pending_leaves,
        pending_halfdays=pending_halfdays,
        pending_early=pending_early,
        today_records=today_records,
        recent_requests=recent_requests,
        recent_photos=recent_photos,
        total_photos_count=total_photos_count,
    )


@admin_bp.route("/attendance-photos", methods=["GET"])
@admin_bp.route("/attendance/all", methods=["GET"])
@login_required
@admin_required
def attendance_photos():
    """
    Dedicated Attendance Photos Section:
    Displays all attendance check-in and check-out proof photos stored date-wise.
    Unified across Employee (E-prefix) and EmployeeMaster (I-prefix / imported).
    Filters:
      - date: YYYY-MM-DD (defaults to today; 'all' for all dates)
      - name: case-insensitive substring search
      - code: case-insensitive substring search
    """
    from datetime import datetime as _dt, date as _date, timedelta as _td
    from zoneinfo import ZoneInfo
    from app.models.attendance import Attendance
    from app.models.attendance_photo import AttendancePhoto
    from app.models.attendance_master import AttendanceMaster
    from app.models.attendance_master_photo import AttendanceMasterPhoto
    from app.models.employee import Employee
    from app.models.employee_master import EmployeeMaster
    from app.constants.enums import DEPARTMENT_CHOICES
    from app.extensions.database import db

    tz = ZoneInfo("Asia/Kolkata")
    today_kolkata = _dt.now(tz).date()

    def _format_ist_time(dt):
        """Format datetime into IST (Asia/Kolkata) 12-hour AM/PM string."""
        if not dt:
            return None
        if getattr(dt, "tzinfo", None) is not None:
            return dt.astimezone(tz).strftime("%I:%M %p")
        # Datetime in DB is already recorded in IST (Kolkata time)
        return dt.strftime("%I:%M %p")

    # Query params
    raw_date = request.args.get("date", "").strip()
    q_name = request.args.get("name", "").strip().lower()
    q_code = request.args.get("code", "").strip().upper()
    q_dept = request.args.get("department", "").strip()

    view_date = None
    if raw_date and raw_date != "all":
        try:
            view_date = _dt.strptime(raw_date, "%Y-%m-%d").date()
        except ValueError:
            view_date = today_kolkata
    elif raw_date == "all":
        view_date = None
    else:
        view_date = today_kolkata

    combined_items = []

    # 1. Fetch from AttendanceMaster + AttendanceMasterPhoto (Kiosk & Master 541 records)
    query_master = (
        db.session.query(AttendanceMaster, AttendanceMasterPhoto, EmployeeMaster)
        .join(EmployeeMaster, AttendanceMaster.employee_master_id == EmployeeMaster.id)
        .outerjoin(AttendanceMasterPhoto, AttendanceMaster.id == AttendanceMasterPhoto.attendance_master_id)
    )
    if view_date:
        query_master = query_master.filter(AttendanceMaster.date == view_date)
    if q_code:
        query_master = query_master.filter(EmployeeMaster.employee_code.ilike(f"%{q_code}%"))
    if q_name:
        query_master = query_master.filter(EmployeeMaster.employee_name.ilike(f"%{q_name}%"))
    if q_dept:
        query_master = query_master.filter(EmployeeMaster.department.ilike(f"%{q_dept}%"))

    for att_m, photo_m, emp_m in query_master.order_by(AttendanceMaster.date.desc(), AttendanceMaster.id.desc()).all():
        checkin_img = photo_m.image_data if photo_m else None
        checkout_img = photo_m.checkout_image_data if photo_m else None

        t_in = _format_ist_time(att_m.check_in_time)
        t_out = _format_ist_time(att_m.check_out_time)

        duration = None
        if att_m.check_in_time and att_m.check_out_time:
            diff = att_m.check_out_time - att_m.check_in_time
            secs = max(0, int(diff.total_seconds()))
            hrs = secs // 3600
            mins = (secs % 3600) // 60
            duration = f"{hrs}h {mins}m"

        combined_items.append({
            "record_id": f"master_{att_m.id}",
            "date": att_m.date,
            "date_str": att_m.date.strftime("%Y-%m-%d"),
            "date_display": att_m.date.strftime("%A, %d %B %Y"),
            "employee_code": emp_m.employee_code,
            "employee_name": emp_m.employee_name,
            "department": emp_m.department or "General",
            "location": emp_m.working_location or "Hospital Site",
            "status": att_m.status or "present",
            "check_in_time": t_in,
            "check_in_photo": checkin_img,
            "check_out_time": t_out,
            "check_out_photo": checkout_img,
            "duration": duration,
            "source": "Kiosk Terminal"
        })

    # 2. Fetch from Attendance + AttendancePhoto (Registered HR Employees)
    query_emp = (
        db.session.query(Attendance, AttendancePhoto, Employee)
        .join(Employee, Attendance.employee_id == Employee.id)
        .outerjoin(AttendancePhoto, Attendance.id == AttendancePhoto.attendance_id)
        .filter(Attendance.is_deleted == False, Employee.is_deleted == False)
    )
    if view_date:
        query_emp = query_emp.filter(Attendance.date == view_date)
    if q_code:
        query_emp = query_emp.filter(Employee.employee_code.ilike(f"%{q_code}%"))
    if q_name:
        from app.models.user import User
        query_emp = query_emp.join(User, Employee.user_id == User.id).filter(
            (User.first_name.ilike(f"%{q_name}%")) | (User.last_name.ilike(f"%{q_name}%"))
        )
    if q_dept:
        query_emp = query_emp.filter(Employee.department.ilike(f"%{q_dept}%"))

    for att, photo, emp in query_emp.order_by(Attendance.date.desc(), Attendance.id.desc()).all():
        checkin_img = photo.image_data if photo else None
        checkout_img = photo.checkout_image_data if photo else None

        t_in = _format_ist_time(att.check_in_time)
        t_out = _format_ist_time(att.check_out_time)

        duration = None
        if att.check_in_time and att.check_out_time:
            diff = att.check_out_time - att.check_in_time
            secs = max(0, int(diff.total_seconds()))
            hrs = secs // 3600
            mins = (secs % 3600) // 60
            duration = f"{hrs}h {mins}m"

        combined_items.append({
            "record_id": f"emp_{att.id}",
            "date": att.date,
            "date_str": att.date.strftime("%Y-%m-%d"),
            "date_display": att.date.strftime("%A, %d %B %Y"),
            "employee_code": emp.employee_code,
            "employee_name": emp.full_name,
            "department": emp.department or "General",
            "location": getattr(emp, "location", None) or "Hospital Site",
            "status": att.status or "present",
            "check_in_time": t_in,
            "check_in_photo": checkin_img,
            "check_out_time": t_out,
            "check_out_photo": checkout_img,
            "duration": duration,
            "source": "Office / Site"
        })

    # Sort all items date desc, then employee name
    combined_items.sort(key=lambda x: (x["date"], x["employee_name"]), reverse=True)

    # Group by date for date-wise display
    from collections import OrderedDict
    date_groups = OrderedDict()
    for item in combined_items:
        d_key = item["date_display"]
        if d_key not in date_groups:
            date_groups[d_key] = []
        date_groups[d_key].append(item)

    total_records = len(combined_items)
    with_in_photo = sum(1 for x in combined_items if x["check_in_photo"])
    with_out_photo = sum(1 for x in combined_items if x["check_out_photo"])

    return render_template(
        "admin/attendance_photos.html",
        title="Attendance Photos",
        date_groups=date_groups,
        total_records=total_records,
        with_in_photo=with_in_photo,
        with_out_photo=with_out_photo,
        selected_date=view_date.strftime("%Y-%m-%d") if view_date else "",
        q_name=q_name,
        q_code=q_code,
        q_dept=q_dept,
        department_choices=DEPARTMENT_CHOICES,
        today_str=today_kolkata.strftime("%Y-%m-%d")
    )


@admin_bp.route("/view-all-attendance")
@admin_bp.route("/all-attendance")
@login_required
@hr_required
def view_all_attendance():
    """Redirect legacy view_all_attendance endpoint to attendance_photos."""
    return redirect(url_for("admin.attendance_photos", **request.args))


@admin_bp.route("/office-settings", methods=["GET", "POST"])
@login_required
@admin_required
def office_settings():
    office = _svc.get_or_create_default_office()
    form = OfficeSettingsForm(obj=office)
    if form.validate_on_submit():
        ok, msg = _svc.update_office_settings(office.id, {
            "name":                    form.name.data,
            "address":                 form.address.data,
            "latitude":                form.latitude.data,
            "longitude":               form.longitude.data,
            "radius_metres":           form.radius_metres.data,
            "office_start_time":       form.office_start_time.data,
            "office_end_time":         form.office_end_time.data,
            "grace_period_minutes":    form.grace_period_minutes.data,
            "half_day_threshold_minutes": form.half_day_threshold_minutes.data,
            "overtime_threshold_minutes": form.overtime_threshold_minutes.data,
            "allow_remote_checkin":    form.allow_remote_checkin.data,
            "selfie_required":         form.selfie_required.data,
        })
        flash(msg, "success" if ok else "danger")
        if ok:
            return redirect(url_for("admin.office_settings"))
    return render_template(
        "admin/office_settings.html",
        title="Office Settings",
        form=form,
        office=office,
    )


@admin_bp.route("/users")
@login_required
@admin_required
def users():
    try:
        page = request.args.get("page", 1, type=int)
        search = request.args.get("q", "")
        # For admin user management, we need to bypass department filtering
        # Query directly without department constraint
        from app.models.employee import Employee
        from app.models.user import User
        from sqlalchemy import or_
        
        query = Employee.query.filter(Employee.is_deleted == False)
        
        if search:
            term = f"%{search}%"
            query = (
                query.join(User, Employee.user_id == User.id, isouter=True)
                .filter(or_(
                    Employee.employee_code.ilike(term),
                    User.first_name.ilike(term),
                    User.last_name.ilike(term),
                    User.email.ilike(term),
                    Employee.mobile.ilike(term),
                ))
            )
        
        pagination = query.order_by(Employee.employee_code.asc()).paginate(
            page=page, per_page=25, error_out=False
        )
        
        return render_template(
            "admin/users.html",
            title="User Management",
            pagination=pagination,
            employees=pagination.items,
            search=search,
        )
    except Exception as e:
        import logging
        logging.error(f"USER_MANAGEMENT_ERROR: {str(e)}", exc_info=True)
        # Return empty list on error instead of crashing
        from flask import flash
        flash(f"Error loading users: {str(e)}", "warning")
        from app.extensions.database import db
        class EmptyPagination:
            items = []
            pages = 1
            page = 1
            per_page = 25
            total = 0
        return render_template(
            "admin/users.html",
            title="User Management",
            pagination=EmptyPagination(),
            employees=[],
            search="",
        )


@admin_bp.route("/audit-logs")
@login_required
@roles_required(UserRole.SUPER_ADMIN)
def audit_logs():
    return render_template("admin/audit_logs.html", title="Audit Logs")


@admin_bp.route("/leave-types")
@login_required
@admin_required
def leave_types():
    types = _leave.get_all_types()
    return render_template("admin/leave_types.html", title="Leave Types", leave_types=types)


# ── Employee Import Module ────────────────────────────────────────────

@admin_bp.route("/import-employees", methods=["GET", "POST"])
@login_required
@admin_required
def import_employees():
    """Upload Excel and import employee master data."""
    from .employee_import import EmployeeImportService
    from app.models.employee_master import EmployeeMaster

    import_svc = EmployeeImportService()
    result     = None
    total_masters = EmployeeMaster.query.count()
    registered    = EmployeeMaster.query.filter_by(is_registered=True).count()

    if request.method == "POST":
        file = request.files.get("excel_file")
        if not file or not file.filename:
            flash("Please select a CSV or Excel file to upload.", "warning")
        elif not file.filename.lower().endswith((".xlsx", ".xls", ".csv")):
            flash("Only CSV or Excel files (.csv, .xlsx, .xls) are supported.", "danger")
        else:
            result = import_svc.import_from_source(file, imported_by=current_user.id)
            if result.get("success"):
                flash(result["message"], "success")
            else:
                flash(result["message"], "danger")
            total_masters = EmployeeMaster.query.count()
            registered    = EmployeeMaster.query.filter_by(is_registered=True).count()

    return render_template(
        "admin/import_employees.html",
        title="Import Employees",
        result=result,
        total_masters=total_masters,
        registered=registered,
    )


@admin_bp.route("/import-employees/preview", methods=["POST"])
@login_required
@admin_required
def preview_import():
    """AJAX: preview Excel without importing."""
    from .employee_import import EmployeeImportService
    import_svc = EmployeeImportService()
    file = request.files.get("excel_file")
    if not file or not file.filename:
        return jsonify(success=False, message="No file provided.")
    result = import_svc.preview(file)
    return jsonify(result)


@admin_bp.route("/employee-master")
@login_required
@admin_required
def employee_master():
    """View all employees in the master table."""
    from app.models.employee_master import EmployeeMaster
    from flask import request as _req
    
    search = _req.args.get("q", "").strip()
    status = _req.args.get("status", "")
    page   = _req.args.get("page", 1, type=int)

    q = EmployeeMaster.query
    if search:
        q = q.filter(
            EmployeeMaster.employee_code.ilike(f"%{search}%") |
            EmployeeMaster.employee_name.ilike(f"%{search}%") |
            EmployeeMaster.department.ilike(f"%{search}%")
        )
    if status == "registered":
        q = q.filter_by(is_registered=True)
    elif status == "pending":
        q = q.filter_by(is_registered=False)

    pagination = q.order_by(EmployeeMaster.employee_code).paginate(
        page=page, per_page=30, error_out=False
    )
    return render_template(
        "admin/employee_master.html",
        title="Employee Master",
        pagination=pagination,
        search=search,
        status=status,
    )


@admin_bp.route("/attendance/export")
@login_required
@admin_required
def export_daily_attendance():
    """
    Export full daily attendance for ALL employees to Excel.
    Query param: ?date=YYYY-MM-DD  (defaults to today)
    """
    import io
    from datetime import datetime as _dt
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    from flask import send_file
    from app.blueprints.attendance.repository import AttendanceRepository as AttRepo

    att_repo = AttRepo()

    date_str = request.args.get("date", "").strip()
    try:
        export_date = _dt.strptime(date_str, "%Y-%m-%d").date() if date_str else date.today()
    except ValueError:
        export_date = date.today()

    rows = att_repo.get_all_employees_attendance_for_date(export_date)

    if not rows:
        flash("No employee data available for export.", "warning")
        return redirect(url_for("admin.index"))

    # ── Build workbook ────────────────────────────────────────────────
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Daily Attendance"

    header_font  = Font(bold=True, color="FFFFFF", size=11)
    header_fill  = PatternFill(start_color="1A3C6E", end_color="1A3C6E", fill_type="solid")
    header_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
    center_align = Alignment(horizontal="center", vertical="center")
    left_align   = Alignment(horizontal="left", vertical="center")
    thin         = Side(style="thin", color="DEE2E6")
    border       = Border(left=thin, right=thin, top=thin, bottom=thin)
    alt_fill     = PatternFill(start_color="F4F6F9", end_color="F4F6F9", fill_type="solid")

    # ── Title row ─────────────────────────────────────────────────────
    ws.merge_cells("A1:L1")
    title_cell = ws["A1"]
    title_cell.value = f"Daily Attendance Report — {export_date.strftime('%d %B %Y')}"
    title_cell.font  = Font(bold=True, size=13, color="1A3C6E")
    title_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 28

    # ── Headers ───────────────────────────────────────────────────────
    headers = [
        ("#",              5),
        ("Emp Code",       12),
        ("Employee Name",  22),
        ("Department",     16),
        ("Designation",    16),
        ("Date",           12),
        ("Check In (IST)", 15),
        ("Check Out (IST)",15),
        ("Working Hours",  14),
        ("Status",         13),
        ("Late",           8),
        ("Late By (min)",  13),
    ]

    for col, (h, w) in enumerate(headers, start=1):
        cell = ws.cell(row=2, column=col, value=h)
        cell.font      = header_font
        cell.fill      = header_fill
        cell.alignment = header_align
        cell.border    = border
        ws.column_dimensions[get_column_letter(col)].width = w

    ws.row_dimensions[2].height = 24
    ws.freeze_panes = "A3"

    # ── Helpers ───────────────────────────────────────────────────────
    def to_ist(dt):
        if not dt:
            return "—"
        # Times already stored in IST (as of 2026-08-21 11:42)
        return dt.strftime("%I:%M %p")

    def fmt_hours(mins):
        if not mins:
            return "—"
        h, m = divmod(mins, 60)
        return f"{h}h {m:02d}m"

    status_colors = {
        "present":  "198754",
        "absent":   "DC3545",
        "half_day": "D97706",
        "on_leave": "0891B2",
        "holiday":  "6C757D",
        "weekend":  "ADB5BD",
    }

    # ── Data rows ─────────────────────────────────────────────────────
    summary = {"present": 0, "absent": 0, "late": 0, "on_leave": 0}

    for i, row in enumerate(rows, start=1):
        r   = i + 2
        att = row["attendance"]
        emp = row["employee"]
        usr = row["user"]
        is_alt = (i % 2 == 0)

        status_str = att.status if att else "absent"
        if status_str in summary:
            summary[status_str] += 1
        elif status_str not in summary:
            pass

        if att and att.check_in_time:
            summary["present"] = summary.get("present", 0)
        else:
            summary["absent"] = summary.get("absent", 0)

        if att and att.is_late:
            summary["late"] += 1

        row_data = [
            i,
            emp.employee_code,
            usr.full_name,
            emp.department or "—",
            emp.designation or "—",
            export_date.strftime("%d-%m-%Y"),
            to_ist(att.check_in_time) if att else "—",
            to_ist(att.check_out_time) if att else "—",
            fmt_hours(att.working_minutes) if att else "—",
            status_str.replace("_", " ").title(),
            "Yes" if (att and att.is_late) else "No",
            att.late_minutes if (att and att.is_late) else 0,
        ]

        for col, val in enumerate(row_data, start=1):
            cell = ws.cell(row=r, column=col, value=val)
            cell.border    = border
            cell.alignment = left_align if col in (3, 4, 5) else center_align
            if is_alt:
                cell.fill = alt_fill

        # Colour status
        st_cell = ws.cell(row=r, column=10)
        color   = status_colors.get(status_str, "212529")
        st_cell.font = Font(color=color, bold=True)

        # Highlight late
        if att and att.is_late:
            ws.cell(row=r, column=11).font = Font(color="D97706", bold=True)

    # ── Summary row ───────────────────────────────────────────────────
    sr = len(rows) + 3
    ws.cell(row=sr, column=1, value="SUMMARY").font = Font(bold=True, color="1A3C6E")
    summary_data = [
        ("Total Employees", len(rows), "1A3C6E"),
        ("Present",   sum(1 for r in rows if r["attendance"] and r["attendance"].check_in_time), "198754"),
        ("Absent",    sum(1 for r in rows if not r["attendance"] or not r["attendance"].check_in_time), "DC3545"),
        ("Late",      sum(1 for r in rows if r["attendance"] and r["attendance"].is_late), "D97706"),
        ("On Leave",  sum(1 for r in rows if r["attendance"] and r["attendance"].status == "on_leave"), "0891B2"),
    ]
    for col, (label, val, color) in enumerate(summary_data, start=1):
        lc = ws.cell(row=sr, column=col, value=label)
        lc.font  = Font(bold=True, color=color, size=9)
        lc.fill  = PatternFill(start_color="EFF6FF", end_color="EFF6FF", fill_type="solid")
        vc = ws.cell(row=sr + 1, column=col, value=val)
        vc.font  = Font(bold=True, color=color, size=14)
        vc.fill  = PatternFill(start_color="EFF6FF", end_color="EFF6FF", fill_type="solid")
        vc.alignment = Alignment(horizontal="center")

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    filename = f"Attendance_{export_date.strftime('%Y-%m-%d')}.xlsx"
    return send_file(
        buffer,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=filename,
    )


@admin_bp.route("/attendance/reset", methods=["POST"])
@login_required
@admin_required
def reset_attendance():
    """
    Reset ALL attendance data (development/testing only).
    Requires confirmation via JSON body: {"confirm": "DELETE ALL"}
    """
    import logging
    from app.models.attendance import Attendance
    from app.models.attendance_photo import AttendancePhoto
    from app.models.attendance_log import AttendanceLog
    from app.extensions.database import db

    logger = logging.getLogger("admin")

    data = request.get_json() or {}
    confirm = data.get("confirm", "")

    if confirm != "DELETE ALL":
        return jsonify(
            success=False,
            message="Confirmation failed. Send {\"confirm\": \"DELETE ALL\"} to proceed."
        ), 400

    try:
        # Count before deletion
        attendance_count = Attendance.query.count()
        photo_count = AttendancePhoto.query.count()
        log_count = AttendanceLog.query.count()

        logger.info(
            "ATTENDANCE_RESET_START | by_user=%s | att=%d | photos=%d | logs=%d",
            current_user.id, attendance_count, photo_count, log_count
        )

        # Delete in correct order (respect foreign keys)
        AttendanceLog.query.delete()
        AttendancePhoto.query.delete()
        Attendance.query.delete()
        db.session.commit()

        logger.info(
            "ATTENDANCE_RESET_SUCCESS | by_user=%s | deleted att=%d, photos=%d, logs=%d",
            current_user.id, attendance_count, photo_count, log_count
        )

        return jsonify(
            success=True,
            message=f"Successfully deleted {attendance_count} attendance records, {photo_count} photos, and {log_count} logs.",
            deleted={
                "attendance": attendance_count,
                "photos": photo_count,
                "logs": log_count
            }
        )

    except Exception as exc:
        db.session.rollback()
        logger.error("ATTENDANCE_RESET_FAILED | by_user=%s | error=%s", current_user.id, str(exc))
        return jsonify(
            success=False,
            message=f"Reset failed: {str(exc)}"
        ), 500


@admin_bp.route("/attendance/emergency-reset")
@login_required
@admin_required
def emergency_reset_attendance():
    """
    EMERGENCY: Delete all attendance via GET request (for immediate access).
    Can be accessed directly via browser URL.
    """
    import logging
    from app.models.attendance import Attendance
    from app.models.attendance_photo import AttendancePhoto
    from app.models.attendance_log import AttendanceLog
    from app.extensions.database import db

    logger = logging.getLogger("admin")

    try:
        # Count before deletion
        attendance_count = Attendance.query.count()
        photo_count = AttendancePhoto.query.count()
        log_count = AttendanceLog.query.count()

        logger.info(
            "EMERGENCY_ATTENDANCE_RESET | by_user=%s | att=%d | photos=%d | logs=%d",
            current_user.id, attendance_count, photo_count, log_count
        )

        # Delete in correct order
        AttendanceLog.query.delete()
        AttendancePhoto.query.delete()
        Attendance.query.delete()
        db.session.commit()

        logger.info(
            "EMERGENCY_RESET_SUCCESS | by_user=%s | deleted att=%d, photos=%d, logs=%d",
            current_user.id, attendance_count, photo_count, log_count
        )

        flash(
            f"✅ ATTENDANCE DELETED SUCCESSFULLY! "
            f"Deleted: {attendance_count} attendance records, {photo_count} photos, {log_count} logs.",
            "success"
        )
        return redirect(url_for("admin.index"))

    except Exception as exc:
        db.session.rollback()
        logger.error("EMERGENCY_RESET_FAILED | by_user=%s | error=%s", current_user.id, str(exc))
        flash(f"❌ ERROR: {str(exc)}", "danger")
        return redirect(url_for("admin.index"))


# ── Shift Assignment Routes ───────────────────────────────────────────

@admin_bp.route("/shift-assignment")
@login_required
@roles_required(UserRole.SUPER_ADMIN, UserRole.HR_MANAGER, UserRole.ADMIN)
def shift_assignment():
    """Bulk shift assignment page."""
    from .shift_assignment import assign_shifts_bulk
    return assign_shifts_bulk()


@admin_bp.route("/shift-assignment/assign", methods=["POST"])
@login_required
@roles_required(UserRole.SUPER_ADMIN, UserRole.HR_MANAGER, UserRole.ADMIN)
def assign_single_shift():
    """Assign shift to a single employee (AJAX)."""
    from .shift_assignment import assign_shift_to_employee
    return assign_shift_to_employee()


@admin_bp.route("/shift-assignment/bulk", methods=["POST"])
@login_required
@roles_required(UserRole.SUPER_ADMIN, UserRole.HR_MANAGER, UserRole.ADMIN)
def assign_bulk_shifts():
    """Bulk assign shifts (AJAX)."""
    from .shift_assignment import assign_shifts_bulk_submit
    return assign_shifts_bulk_submit()


@admin_bp.route("/shift-assignment/remove", methods=["POST"])
@login_required
@roles_required(UserRole.SUPER_ADMIN, UserRole.HR_MANAGER, UserRole.ADMIN)
def remove_shift():
    """Remove shift from employee (AJAX)."""
    from .shift_assignment import remove_shift_assignment
    return remove_shift_assignment()


@admin_bp.route("/shift-assignment/employee-info")
@login_required
@roles_required(UserRole.SUPER_ADMIN, UserRole.HR_MANAGER, UserRole.ADMIN)
def get_employee_shift():
    """Get employee shift info (AJAX)."""
    from .shift_assignment import get_employee_shift_info
    return get_employee_shift_info()


@admin_bp.route("/shift-assignment/assign-hospital", methods=["POST"])
@login_required
@roles_required(UserRole.SUPER_ADMIN, UserRole.HR_MANAGER, UserRole.ADMIN)
def assign_hospital():
    """Assign hospital to employee (AJAX)."""
    from .shift_assignment import assign_hospital_to_employee
    return assign_hospital_to_employee()


# ── Shift Import Routes ───────────────────────────────────────────

@admin_bp.route("/shift-assignment/import", methods=["GET", "POST"])
@login_required
@roles_required(UserRole.SUPER_ADMIN, UserRole.HR_MANAGER, UserRole.ADMIN)
def shift_assignment_import():
    """Import shift assignments from Excel file."""
    from .forms import ShiftImportForm
    from .shift_import import ShiftImportService
    from datetime import datetime
    from app.models.employee import Employee
    
    form = ShiftImportForm()
    import_result = None
    
    # Get all available employee codes for reference
    available_employees = Employee.query.filter_by(is_deleted=False).order_by(Employee.employee_code).all()
    employee_codes = [(emp.employee_code, emp.name) for emp in available_employees]
    
    if form.validate_on_submit():
        try:
            file = form.file.data
            effective_date = request.form.get('effective_date')
            
            service = ShiftImportService()
            import_result = service.import_from_file(
                file=file,
                effective_date=effective_date,
                assigned_by_user_id=current_user.id
            )
            
            if import_result.get('success'):
                flash(import_result.get('message', 'Import completed'), 'success')
                # After successful import, redirect to shift assignment page to see updated data
                # This ensures the page reloads with fresh data from the database
                return redirect(url_for('admin.shift_assignment'))
            else:
                flash(import_result.get('message', 'Import failed'), 'danger')
                
        except Exception as e:
            import logging
            logging.getLogger('admin').error(f"Shift import error: {str(e)}")
            flash(f'Error during import: {str(e)}', 'danger')
    
    today = date.today().isoformat()
    return render_template(
        'admin/shift_assignment_import.html',
        form=form,
        import_result=import_result,
        today=today,
        employee_codes=employee_codes
    )


@admin_bp.route("/shifts/reseed", methods=["POST"])
@login_required
@roles_required(UserRole.SUPER_ADMIN)
def reseed_shifts():
    """Reseed endpoint locked down per Zero Dummy Data policy."""
    return jsonify({
        'success': False,
        'message': 'Reseed endpoint disabled: Shifts must be configured via Settings or imported from real data per Zero Dummy Data policy.'
    }), 403


@admin_bp.route("/flow-status", methods=["GET"])
@login_required
@admin_required
def flow_status():
    """Live Flow Status pipeline for Super Admin showing real counts at every stage."""
    from datetime import date
    from app.models.company import CompanyProfile, Shift
    from app.models.hospital import Hospital
    from app.models.employee_master import EmployeeMaster
    from app.models.employee import Employee
    from app.models.user import User
    from app.models.company_holiday import CompanyHoliday
    from app.models.leave import LeaveRequest, LeaveType
    from app.models.attendance import Attendance
    from app.models.attendance_photo import AttendancePhoto
    from app.models.attendance_master_photo import AttendanceMasterPhoto
    from app.models.payroll import SalaryStructure, PayrollRun, Payslip
    from app.models.office_settings import OfficeSettings

    today = date.today()

    # Stage 1: Company Profile
    comp = CompanyProfile.query.first()
    stage1 = {
        "status": "Configured" if comp and comp.company_name else "Pending Setup",
        "company_name": comp.company_name if comp else None,
        "is_ready": bool(comp and comp.company_name)
    }

    # Stage 2: Hospitals (GPS)
    total_hospitals = Hospital.query.count()
    gps_hospitals = Hospital.query.filter(Hospital.latitude.isnot(None), Hospital.longitude.isnot(None)).count()
    stage2 = {
        "total": total_hospitals,
        "with_gps": gps_hospitals,
        "is_ready": total_hospitals > 0 and gps_hospitals == total_hospitals
    }

    # Stage 3: Shifts
    total_shifts = Shift.query.count()
    night_shifts = Shift.query.filter_by(is_night_shift=True).count()
    stage3 = {
        "total": total_shifts,
        "night_shifts": night_shifts,
        "is_ready": total_shifts > 0
    }

    # Stage 4: Holidays 2026
    total_holidays = CompanyHoliday.query.count()
    stage4 = {
        "total": total_holidays,
        "is_ready": total_holidays > 0
    }

    # Stage 5: Employee Master
    total_master = EmployeeMaster.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    hr_profiles = Employee.query.count()
    salary_structures_count = SalaryStructure.query.count()
    stage5 = {
        "master_count": total_master,
        "active_users": active_users,
        "hr_profiles": hr_profiles,
        "salary_structures": salary_structures_count,
        "target": 541,
        "is_ready": total_master >= 541 and salary_structures_count >= total_master
    }

    # Stage 6: Raw Punches (Today)
    checked_in_today = Attendance.query.filter(Attendance.date == today, Attendance.check_in_time.isnot(None)).count()
    checked_out_today = Attendance.query.filter(Attendance.date == today, Attendance.check_out_time.isnot(None)).count()
    photos_count = AttendancePhoto.query.count() + AttendanceMasterPhoto.query.count()
    stage6 = {
        "checked_in_today": checked_in_today,
        "checked_out_today": checked_out_today,
        "total_photos": photos_count,
        "date_str": today.strftime('%d %b %Y')
    }

    # Stage 7: Daily Attendance Finalization
    present_today = Attendance.query.filter(Attendance.date == today, Attendance.status == "present").count()
    late_today = Attendance.query.filter(Attendance.date == today, Attendance.is_late.is_(True)).count()
    half_day_today = Attendance.query.filter(Attendance.date == today, Attendance.is_half_day.is_(True)).count()
    partial_today = Attendance.query.filter(Attendance.date == today, Attendance.check_in_time.isnot(None), Attendance.check_out_time.is_(None)).count()
    stage7 = {
        "present": present_today,
        "late": late_today,
        "half_day": half_day_today,
        "partial_missing_out": partial_today,
    }

    # Stage 8: Leave & Comp-Off
    pending_leaves = LeaveRequest.query.filter_by(status="pending").count()
    approved_leaves_today = LeaveRequest.query.filter(
        LeaveRequest.status == "approved",
        LeaveRequest.start_date <= today,
        LeaveRequest.end_date >= today
    ).count()
    stage8 = {
        "pending_approval": pending_leaves,
        "on_leave_today": approved_leaves_today
    }

    # Stage 9: Monthly Attendance & Cut-Off
    stage9 = {
        "current_month": today.strftime("%B %Y"),
        "status": "In Progress (Finalizes at Month-End Cutoff)"
    }

    # Stage 10: Payroll Draft & Payslips
    draft_runs = PayrollRun.query.filter_by(status="draft").count()
    approved_runs = PayrollRun.query.filter_by(status="approved").count()
    paid_runs = PayrollRun.query.filter_by(status="paid").count()
    total_payslips = Payslip.query.count()
    stage10 = {
        "draft_runs": draft_runs,
        "approved_runs": approved_runs,
        "paid_runs": paid_runs,
        "total_payslips": total_payslips,
        "is_ready": approved_runs > 0 or paid_runs > 0
    }

    return render_template(
        "admin/flow_status.html",
        title="Flow Status — Operational Pipeline",
        stage1=stage1,
        stage2=stage2,
        stage3=stage3,
        stage4=stage4,
        stage5=stage5,
        stage6=stage6,
        stage7=stage7,
        stage8=stage8,
        stage9=stage9,
        stage10=stage10,
        today=today
    )


@admin_bp.route("/readiness", methods=["GET"])
@login_required
@admin_required
def data_readiness():
    """Data Readiness Dashboard tracking real enterprise dataset loading."""
    from app.models.company import CompanyProfile, Shift
    from app.models.hospital import Hospital
    from app.models.employee_master import EmployeeMaster
    from app.models.company_holiday import CompanyHoliday
    from app.models.leave import LeaveType
    from app.models.office_settings import OfficeSettings
    from app.models.office_device import OfficeDevice
    from app.models.payroll import SalaryStructure

    modules = [
        {
            "id": "company",
            "name": "Company Legal Profile",
            "required_for": "Payslips, PF/ESI Registration, Reports",
            "count": CompanyProfile.query.count(),
            "target": 1,
            "status": "Ready" if CompanyProfile.query.count() > 0 else "Missing",
            "blocking": "Official Branded Payslips, Statutory ECRs",
        },
        {
            "id": "hospitals",
            "name": "Hospitals & Geo-fencing",
            "required_for": "GPS Mobile Check-In & Geo-Fence Validation",
            "count": Hospital.query.count(),
            "target": 46,
            "status": "Ready" if Hospital.query.count() >= 46 else ("Partial" if Hospital.query.count() > 0 else "Missing"),
            "blocking": "None (46 Hospitals Seeded)",
        },
        {
            "id": "employees",
            "name": "Employee Master Registry",
            "required_for": "Authentication, Attendance, Kiosk, Leaves",
            "count": EmployeeMaster.query.count(),
            "target": 541,
            "status": "Ready" if EmployeeMaster.query.count() >= 541 else "Partial",
            "blocking": "Awaiting remaining 188 profiles to reach full 541 target",
        },
        {
            "id": "shifts",
            "name": "Shifts & Overtime Rules",
            "required_for": "Attendance Attribution & Overnight Shifts",
            "count": Shift.query.count(),
            "target": 25,
            "status": "Ready" if Shift.query.count() > 0 else "Missing",
            "blocking": "None (25 Shifts Seeded)",
        },
        {
            "id": "holidays",
            "name": "Company Holidays 2026",
            "required_for": "Comp-Off Calculations & Payable Days",
            "count": CompanyHoliday.query.count(),
            "target": 15,
            "status": "Ready" if CompanyHoliday.query.count() > 0 else "Missing",
            "blocking": "None (15 Holidays Seeded)",
        },
        {
            "id": "leave",
            "name": "Leave Policy & Quotas",
            "required_for": "Leave Applications & LOP Deductions",
            "count": LeaveType.query.count(),
            "target": 8,
            "status": "Ready" if LeaveType.query.count() > 0 else "Missing",
            "blocking": "None (CL, SL, PL, CO Active)",
        },
        {
            "id": "attendance_policy",
            "name": "Attendance & Grace Rules",
            "required_for": "Late Mark Thresholds & Nightly Finalization",
            "count": OfficeSettings.query.count(),
            "target": 1,
            "status": "Ready" if OfficeSettings.query.count() > 0 else "Missing",
            "blocking": "Automated Nightly Finalization Job",
        },
        {
            "id": "payroll_rules",
            "name": "Statutory & Tax Rules (PF/ESI/PT)",
            "required_for": "Legal Compliance & Accurate Net Pay",
            "count": 0,
            "target": 1,
            "status": "Pending Verification",
            "blocking": "Monthly Payroll Run & Bank Transfer File Generation",
        },
        {
            "id": "salary_structures",
            "name": "Employee Salary Structures",
            "required_for": "Payroll Run & Individual Payslips",
            "count": SalaryStructure.query.count(),
            "target": 541,
            "status": "Ready" if SalaryStructure.query.count() >= 541 else ("Partial" if SalaryStructure.query.count() > 0 else "Missing"),
            "blocking": "Payroll Processing Locked until structures imported",
        },
        {
            "id": "opening_balances",
            "name": "Leave & Comp-Off Opening Balances",
            "required_for": "Comp-Off Wallet & Unavailed Leave Balance",
            "count": 0,
            "target": 541,
            "status": "Missing",
            "blocking": "Opening Balance Accrual",
        },
        {
            "id": "kiosk_devices",
            "name": "Registered Kiosk Hardware",
            "required_for": "Hardware Device Lock on /kiosk",
            "count": OfficeDevice.query.count(),
            "target": 2,
            "status": "Ready" if OfficeDevice.query.count() >= 2 else "Missing",
            "blocking": "Hardware Terminal Lockout",
        },
    ]

    ready_count = sum(1 for m in modules if m["status"] == "Ready")
    readiness_percentage = round((ready_count / len(modules)) * 100)

    return render_template(
        "admin/readiness.html",
        title="Data Readiness Dashboard",
        modules=modules,
        ready_count=ready_count,
        total_modules=len(modules),
        readiness_percentage=readiness_percentage,
    )

