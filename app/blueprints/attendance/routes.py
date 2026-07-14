"""
attendance/routes.py
======================
Attendance routes — thin HTTP layer only.

Rules:
    - No business logic here.
    - Every route delegates to AttendanceService or OfficeSettingsService.
    - JSON endpoints return structured responses.
    - HTML endpoints render templates.
"""

from datetime import date
from flask import flash, jsonify, redirect, render_template, request, url_for
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
    page       = request.args.get("page", 1, type=int)
    pagination = _repo.get_history(employee.id, page=page, per_page=30)
    return render_template(
        "attendance/history.html",
        title="Attendance History",
        employee=employee,
        pagination=pagination,
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
