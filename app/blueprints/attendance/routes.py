"""
attendance/routes.py
======================
Attendance routes — thin HTTP layer only.
"""

import os
from datetime import date
from flask import flash, jsonify, redirect, render_template, request, url_for, send_from_directory, abort
from flask_login import current_user, login_required

from app.blueprints.employees.repository import EmployeeRepository
from app.core.security import hr_required
from .forms import OfficeSettingsForm
from .office_settings_service import OfficeSettingsService
from .repository import AttendanceRepository
from .service import AttendanceService
from . import attendance_bp

_svc      = AttendanceService()
_repo     = AttendanceRepository()
_emp_repo = EmployeeRepository()
_office_svc = OfficeSettingsService()


# ── Employee attendance dashboard ────────────────────────────────────

@attendance_bp.route("/gps-test")
@login_required
def gps_test():
    """GPS diagnostic page — helps identify why geolocation is blocked."""
    return render_template("attendance/gps_test.html", title="GPS Test")


@attendance_bp.route("/")
@login_required
def index():
    employee = _emp_repo.get_by_user_id(current_user.id)
    if not employee:
        flash("Employee profile not found. Contact HR.", "warning")
        return redirect(url_for("dashboard.index"))

    status = _svc.get_today_status(employee)
    page   = request.args.get("page", 1, type=int)
    history = _repo.get_history(employee.id, page=page, per_page=30)
    office = status.get("office")

    return render_template(
        "attendance/dashboard.html",
        title="Attendance",
        employee=employee,
        status=status,
        history=history,
        office=office,
    )


# ── Check In (AJAX) ──────────────────────────────────────────────────

@attendance_bp.route("/checkin", methods=["POST"])
@login_required
def checkin():
    employee = _emp_repo.get_by_user_id(current_user.id)
    if not employee:
        return jsonify(success=False, message="Employee profile not found."), 400

    lat = request.form.get("latitude", "")
    lon = request.form.get("longitude", "")
    acc = request.form.get("accuracy", "")

    ok, message, attendance, gps_detail = _svc.check_in(employee, lat, lon, acc)
    if ok:
        return jsonify(
            success=True,
            message=message,
            time=attendance.check_in_time.strftime("%H:%M"),
            is_late=attendance.is_late,
            late_minutes=attendance.late_minutes or 0,
            gps=gps_detail,
        )
    return jsonify(success=False, message=message, gps=gps_detail), 400


# ── Check Out (AJAX) ─────────────────────────────────────────────────

@attendance_bp.route("/checkout", methods=["POST"])
@login_required
def checkout():
    employee = _emp_repo.get_by_user_id(current_user.id)
    if not employee:
        return jsonify(success=False, message="Employee profile not found."), 400

    lat = request.form.get("latitude", "")
    lon = request.form.get("longitude", "")
    acc = request.form.get("accuracy", "")

    ok, message, attendance, gps_detail = _svc.check_out(employee, lat, lon, acc)
    if ok:
        return jsonify(
            success=True,
            message=message,
            time=attendance.check_out_time.strftime("%H:%M"),
            working=attendance.working_hours_display,
            overtime_minutes=attendance.overtime_minutes or 0,
            gps=gps_detail,
        )
    return jsonify(success=False, message=message, gps=gps_detail), 400


# ── Photo Upload (AJAX) ──────────────────────────────────────────────

@attendance_bp.route("/upload-photo", methods=["POST"])
@login_required
def upload_photo():
    employee = _emp_repo.get_by_user_id(current_user.id)
    if not employee:
        return jsonify(success=False, message="Employee profile not found."), 400

    file = request.files.get("photo")
    if not file:
        return jsonify(success=False, message="No file received."), 400

    ok, message, photo_url = _svc.upload_photo(employee, file)
    if ok:
        return jsonify(success=True, message=message, photo_url=photo_url)
    return jsonify(success=False, message=message), 400


# ── Attendance history ────────────────────────────────────────────────

@attendance_bp.route("/history")
@login_required
def history():
    employee = _emp_repo.get_by_user_id(current_user.id)
    if not employee:
        flash("Employee profile not found.", "warning")
        return redirect(url_for("dashboard.index"))

    page       = request.args.get("page",       1,  type=int)
    start_date = request.args.get("start_date", "").strip()
    end_date   = request.args.get("end_date",   "").strip()
    status     = request.args.get("status",     "").strip()

    # Parse date strings
    from datetime import datetime as _dt
    parsed_start = None
    parsed_end   = None
    try:
        if start_date:
            parsed_start = _dt.strptime(start_date, "%Y-%m-%d").date()
        if end_date:
            parsed_end = _dt.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        parsed_start = parsed_end = None

    pagination = _repo.get_history_with_photos(
        employee.id,
        start_date=parsed_start,
        end_date=parsed_end,
        status=status,
        page=page,
        per_page=30,
    )

    return render_template(
        "attendance/history.html",
        title="Attendance History",
        employee=employee,
        pagination=pagination,
        start_date=start_date,
        end_date=end_date,
        status=status,
    )


# ── Export Attendance History to Excel ───────────────────────────────

@attendance_bp.route("/history/export")
@login_required
def export_history():
    """
    Export attendance history to Excel (.xlsx).
    Respects the same filters as the history page.
    Uses openpyxl — no temp file written to disk.
    """
    import io
    from datetime import datetime as _dt
    import openpyxl
    from openpyxl.styles import (
        Font, PatternFill, Alignment, Border, Side
    )
    from openpyxl.utils import get_column_letter
    from flask import send_file

    employee = _emp_repo.get_by_user_id(current_user.id)
    if not employee:
        return jsonify(success=False, message="Employee profile not found."), 400

    # Parse filters (same as history route)
    start_date = request.args.get("start_date", "").strip()
    end_date   = request.args.get("end_date",   "").strip()
    status     = request.args.get("status",     "").strip()

    parsed_start = None
    parsed_end   = None
    try:
        if start_date:
            parsed_start = _dt.strptime(start_date, "%Y-%m-%d").date()
        if end_date:
            parsed_end = _dt.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        pass

    # Fetch all matching records (no pagination)
    records = _repo.get_history_all_filtered(
        employee.id,
        start_date=parsed_start,
        end_date=parsed_end,
        status=status,
    )

    if not records:
        return jsonify(
            success=False,
            message="No attendance records available for export."
        ), 404

    # ── Build Excel workbook ──────────────────────────────────────────
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Attendance History"

    # Styles
    header_font    = Font(bold=True, color="FFFFFF", size=11)
    header_fill    = PatternFill(start_color="1A3C6E", end_color="1A3C6E", fill_type="solid")
    header_align   = Alignment(horizontal="center", vertical="center", wrap_text=True)
    center_align   = Alignment(horizontal="center", vertical="center")
    thin_border    = Border(
        left=Side(style="thin", color="DEE2E6"),
        right=Side(style="thin", color="DEE2E6"),
        top=Side(style="thin", color="DEE2E6"),
        bottom=Side(style="thin", color="DEE2E6"),
    )
    alt_fill = PatternFill(start_color="F4F6F9", end_color="F4F6F9", fill_type="solid")

    # ── Headers ───────────────────────────────────────────────────────
    headers = [
        ("Employee ID",      14),
        ("Employee Name",    22),
        ("Date",             14),
        ("Day",              10),
        ("Check In (IST)",   16),
        ("Check Out (IST)",  16),
        ("Working Hours",    14),
        ("Overtime",         12),
        ("Status",           14),
        ("Late",             10),
        ("Late By (min)",    13),
        ("Remarks",          20),
    ]

    for col_idx, (header_text, col_width) in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col_idx, value=header_text)
        cell.font    = header_font
        cell.fill    = header_fill
        cell.alignment = header_align
        cell.border  = thin_border
        ws.column_dimensions[get_column_letter(col_idx)].width = col_width

    ws.row_dimensions[1].height = 28

    # Freeze header row
    ws.freeze_panes = "A2"

    # ── Data rows ─────────────────────────────────────────────────────
    def to_ist(dt):
        """Convert naive UTC datetime to IST string HH:MM AM/PM."""
        if not dt:
            return "—"
        # IST = UTC + 5:30
        from datetime import timedelta
        ist = dt + timedelta(hours=5, minutes=30)
        return ist.strftime("%I:%M %p")

    def fmt_date(d):
        return d.strftime("%d-%m-%Y") if d else "—"

    def fmt_hours(minutes):
        if not minutes:
            return "—"
        h, m = divmod(minutes, 60)
        return f"{h}h {m:02d}m"

    def fmt_overtime(minutes):
        if not minutes:
            return "—"
        h, m = divmod(minutes, 60)
        return f"+{h}h {m:02d}m" if h else f"+{m}m"

    def fmt_status(status_str):
        return status_str.replace("_", " ").title() if status_str else "—"

    for row_idx, att in enumerate(records, start=2):
        is_alt = (row_idx % 2 == 0)
        row_fill = alt_fill if is_alt else None

        row_data = [
            att.employee.employee_code,
            att.employee.full_name,
            fmt_date(att.date),
            att.date.strftime("%A") if att.date else "—",
            to_ist(att.check_in_time),
            to_ist(att.check_out_time),
            fmt_hours(att.working_minutes),
            fmt_overtime(att.overtime_minutes),
            fmt_status(att.status),
            "Yes" if att.is_late else "No",
            att.late_minutes if att.is_late else 0,
            "Half Day" if att.is_half_day else (
                "Early Leave" if att.is_early_leave else ""
            ),
        ]

        for col_idx, value in enumerate(row_data, start=1):
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.border    = thin_border
            cell.alignment = center_align if col_idx not in (2,) else Alignment(vertical="center")
            if row_fill:
                cell.fill = row_fill

        # Highlight late rows
        if att.is_late:
            ws.cell(row=row_idx, column=10).font = Font(color="D97706", bold=True)

        # Colour status cell
        status_colors = {
            "present":   "198754",
            "absent":    "DC3545",
            "half_day":  "FFC107",
            "on_leave":  "0DCAF0",
            "holiday":   "6C757D",
            "weekend":   "ADB5BD",
        }
        color = status_colors.get(att.status, "212529")
        ws.cell(row=row_idx, column=9).font = Font(color=color, bold=True)

    # ── Summary row ───────────────────────────────────────────────────
    total_row = len(records) + 2
    ws.cell(row=total_row, column=1, value="TOTAL").font = Font(bold=True, color="1A3C6E")
    ws.cell(row=total_row, column=1).fill = PatternFill(
        start_color="EFF6FF", end_color="EFF6FF", fill_type="solid"
    )
    ws.cell(row=total_row, column=7,
            value=fmt_hours(sum(r.working_minutes or 0 for r in records))
    ).font = Font(bold=True, color="198754")

    # ── Save to in-memory buffer ──────────────────────────────────────
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    filename = f"Attendance_History_{_dt.now().strftime('%Y-%m-%d')}.xlsx"

    return send_file(
        buffer,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=filename,
    )


# ── Office Settings (HR / Admin only) ────────────────────────────────

@attendance_bp.route("/settings", methods=["GET", "POST"])
@login_required
@hr_required
def settings():
    office = _office_svc.get_or_create_default()
    form   = OfficeSettingsForm(obj=office)

    if form.validate_on_submit():
        ok, msg = _office_svc.update(
            office_id=office.id,
            data={
                "name":                       form.name.data,
                "address":                    form.address.data,
                "latitude":                   form.latitude.data,
                "longitude":                  form.longitude.data,
                "radius_metres":              form.radius_metres.data,
                "office_start_time":          form.office_start_time.data,
                "office_end_time":            form.office_end_time.data,
                "grace_period_minutes":       form.grace_period_minutes.data,
                "half_day_threshold_minutes": form.half_day_threshold_minutes.data,
                "overtime_threshold_minutes": form.overtime_threshold_minutes.data,
                "allow_remote_checkin":       form.allow_remote_checkin.data,
                "selfie_required":            form.selfie_required.data,
            },
            updated_by=current_user.id,
        )
        flash(msg, "success" if ok else "danger")
        if ok:
            return redirect(url_for("attendance.settings"))

    return render_template(
        "attendance/settings.html",
        title="Attendance Settings",
        form=form,
        office=office,
    )


# ── Serve attendance proof photos ────────────────────────────────────

@attendance_bp.route("/photo/<path:filename>")
@login_required
def serve_photo(filename):
    """
    Serve an attendance proof photo from the uploads folder.
    Only the employee who owns the photo or HR/Admin can view it.
    """
    from flask import current_app  # noqa: PLC0415
    upload_folder = current_app.config.get("UPLOAD_FOLDER", "./instance/uploads")
    # Security: prevent directory traversal
    safe_name = os.path.normpath(filename)
    if safe_name.startswith(".."):
        abort(403)
    try:
        return send_from_directory(upload_folder, safe_name)
    except Exception:
        abort(404)
