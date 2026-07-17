"""
blueprints/foss/routes.py
===========================
FOSS Shift & Office Location Management.

Only FOSS department employees and Admins may access these routes.
"""

import logging
from datetime import datetime

from flask import abort, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.blueprints.employees.repository import EmployeeRepository
from app.constants.enums import UserRole
from app.models.employee import Employee
from app.models.notification import Notification
from app.models.office_settings import OfficeSettings
from app.models.shift_change_log import ShiftChangeLog
from app.models.user import User
from sqlalchemy import or_
from . import foss_bp

logger = logging.getLogger(__name__)
_emp_repo = EmployeeRepository()


def _foss_required():
    """Abort 403 if not FOSS dept or Admin."""
    from flask import session  # noqa: PLC0415
    if not current_user.is_authenticated:
        abort(403)
    role = getattr(current_user, "role", "")
    if role in (UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value):
        return  # Admin always allowed
    dept = session.get("login_department", "")
    if not dept:
        emp = getattr(current_user, "employee", None)
        dept = (emp.department or "") if emp else ""
    if dept != "FOSS":
        abort(403)


# ── Index / Search ────────────────────────────────────────────────────

@foss_bp.route("/")
@login_required
def index():
    _foss_required()
    return render_template("foss/index.html", title="FOSS — Shift & Location Management")


@foss_bp.route("/search")
@login_required
def search():
    _foss_required()
    q = request.args.get("q", "").strip()
    employees = []
    if q:
        employees = (
            db.session.query(Employee, User)
            .join(User, Employee.user_id == User.id)
            .filter(
                Employee.is_deleted == False,
                or_(
                    Employee.employee_code.ilike(f"%{q}%"),
                    User.first_name.ilike(f"%{q}%"),
                    User.last_name.ilike(f"%{q}%"),
                ),
            )
            .limit(20)
            .all()
        )
    results = []
    for emp, usr in employees:
        office = None
        if emp.office_settings_id:
            office = OfficeSettings.query.get(emp.office_settings_id)
        if not office:
            office = OfficeSettings.query.filter_by(is_default=True, is_deleted=False).first()
        results.append({
            "id":           emp.id,
            "code":         emp.employee_code,
            "name":         usr.full_name,
            "department":   emp.department or "—",
            "shift_name":   emp.shift_name or "—",
            "office_name":  office.name if office else "—",
            "office_lat":   office.latitude if office else None,
            "office_lon":   office.longitude if office else None,
            "radius":       office.radius_metres if office else None,
            "start_time":   office.office_start_time.strftime("%H:%M") if office else "—",
            "end_time":     office.office_end_time.strftime("%H:%M") if office else "—",
            "grace_min":    office.grace_period_minutes if office else None,
            "office_id":    office.id if office else None,
        })
    return jsonify(employees=results)


# ── Employee detail ───────────────────────────────────────────────────

@foss_bp.route("/employee/<int:emp_id>")
@login_required
def employee_detail(emp_id: int):
    _foss_required()
    emp = Employee.query.filter_by(id=emp_id, is_deleted=False).first_or_404()
    office = None
    if emp.office_settings_id:
        office = OfficeSettings.query.get(emp.office_settings_id)
    if not office:
        office = OfficeSettings.query.filter_by(is_default=True, is_deleted=False).first()
    all_offices = OfficeSettings.query.filter_by(is_deleted=False).order_by(OfficeSettings.name).all()
    history = (
        ShiftChangeLog.query
        .filter_by(employee_id=emp_id)
        .order_by(ShiftChangeLog.changed_at.desc())
        .limit(20)
        .all()
    )
    return render_template(
        "foss/employee.html",
        title=f"Manage — {emp.full_name}",
        employee=emp,
        office=office,
        all_offices=all_offices,
        history=history,
    )


# ── Save shift changes ────────────────────────────────────────────────

@foss_bp.route("/employee/<int:emp_id>/save-shift", methods=["POST"])
@login_required
def save_shift(emp_id: int):
    _foss_required()
    emp = Employee.query.filter_by(id=emp_id, is_deleted=False).first_or_404()

    shift_name      = request.form.get("shift_name", "").strip()
    start_time_str  = request.form.get("start_time", "").strip()   # HH:MM
    end_time_str    = request.form.get("end_time", "").strip()
    grace_str       = request.form.get("grace_minutes", "").strip()
    reason          = request.form.get("reason", "").strip()
    effective_date  = request.form.get("effective_date", "").strip()

    if not (shift_name and start_time_str and end_time_str):
        flash("Shift name, start time, and end time are required.", "danger")
        return redirect(url_for("foss.employee_detail", emp_id=emp_id))

    # Get current office to update timing
    office = None
    if emp.office_settings_id:
        office = OfficeSettings.query.get(emp.office_settings_id)
    if not office:
        office = OfficeSettings.query.filter_by(is_default=True, is_deleted=False).first()

    import datetime as _dt  # noqa: PLC0415

    try:
        new_start = _dt.time(*map(int, start_time_str.split(":")))
        new_end   = _dt.time(*map(int, end_time_str.split(":")))
        new_grace = int(grace_str) if grace_str.isdigit() else (office.grace_period_minutes if office else 15)
    except (ValueError, AttributeError):
        flash("Invalid time format.", "danger")
        return redirect(url_for("foss.employee_detail", emp_id=emp_id))

    # Log the change
    old_shift = emp.shift_name or ""
    log = ShiftChangeLog(
        employee_id=emp_id,
        changed_by_user_id=current_user.id,
        change_type="shift",
        old_shift_name=old_shift,
        new_shift_name=shift_name,
        old_start_time=office.office_start_time.strftime("%H:%M") if office else None,
        new_start_time=start_time_str,
        old_end_time=office.office_end_time.strftime("%H:%M") if office else None,
        new_end_time=end_time_str,
        old_grace_minutes=office.grace_period_minutes if office else None,
        new_grace_minutes=new_grace,
        reason=reason,
        effective_date=effective_date,
    )
    db.session.add(log)

    # Update employee's shift name
    emp.shift_name = shift_name

    # Update office settings timing (if employee has own office, update it;
    # otherwise create a dedicated OfficeSettings record for this employee)
    if office and office.is_default:
        # Create a personal copy so we don't affect all employees using default
        personal_office = OfficeSettings(
            name=f"{emp.employee_code} — {shift_name}",
            latitude=office.latitude,
            longitude=office.longitude,
            radius_metres=office.radius_metres,
            office_start_time=new_start,
            office_end_time=new_end,
            grace_period_minutes=new_grace,
            is_default=False,
        )
        db.session.add(personal_office)
        db.session.flush()
        emp.office_settings_id = personal_office.id
    elif office:
        office.office_start_time = new_start
        office.office_end_time = new_end
        office.grace_period_minutes = new_grace
        office.name = f"{emp.employee_code} — {shift_name}"

    # Notify employee
    _notify(emp, "shift", shift_name, start_time_str, end_time_str, new_grace)

    db.session.commit()
    logger.info("SHIFT_CHANGED | emp=%s | by=%s | shift=%s", emp_id, current_user.id, shift_name)
    flash(f"Shift updated to '{shift_name}' for {emp.full_name}.", "success")
    return redirect(url_for("foss.employee_detail", emp_id=emp_id))


# ── Save office location changes ──────────────────────────────────────

@foss_bp.route("/employee/<int:emp_id>/save-location", methods=["POST"])
@login_required
def save_location(emp_id: int):
    _foss_required()
    emp = Employee.query.filter_by(id=emp_id, is_deleted=False).first_or_404()

    office_name = request.form.get("office_name", "").strip()
    lat_str     = request.form.get("latitude", "").strip()
    lon_str     = request.form.get("longitude", "").strip()
    radius_str  = request.form.get("radius", "").strip()
    address     = request.form.get("address", "").strip()
    reason      = request.form.get("reason", "").strip()

    try:
        new_lat    = float(lat_str)
        new_lon    = float(lon_str)
        new_radius = int(radius_str)
    except ValueError:
        flash("Invalid latitude, longitude, or radius.", "danger")
        return redirect(url_for("foss.employee_detail", emp_id=emp_id))

    if not (-90 <= new_lat <= 90) or not (-180 <= new_lon <= 180):
        flash("Coordinates out of range.", "danger")
        return redirect(url_for("foss.employee_detail", emp_id=emp_id))

    # Get current office
    office = None
    if emp.office_settings_id:
        office = OfficeSettings.query.get(emp.office_settings_id)
    default_office = OfficeSettings.query.filter_by(is_default=True, is_deleted=False).first()

    log = ShiftChangeLog(
        employee_id=emp_id,
        changed_by_user_id=current_user.id,
        change_type="location",
        old_office_name=office.name if office else (default_office.name if default_office else ""),
        new_office_name=office_name,
        old_latitude=str(office.latitude) if office else (str(default_office.latitude) if default_office else ""),
        new_latitude=str(new_lat),
        old_longitude=str(office.longitude) if office else (str(default_office.longitude) if default_office else ""),
        new_longitude=str(new_lon),
        old_radius=office.radius_metres if office else (default_office.radius_metres if default_office else None),
        new_radius=new_radius,
        reason=reason,
    )
    db.session.add(log)

    if office and not office.is_default:
        # Update existing personal office
        office.name = office_name
        office.latitude = new_lat
        office.longitude = new_lon
        office.radius_metres = new_radius
        if address:
            office.address = address
    else:
        # Create personal office record
        src = office or default_office
        personal_office = OfficeSettings(
            name=office_name,
            latitude=new_lat,
            longitude=new_lon,
            radius_metres=new_radius,
            office_start_time=src.office_start_time if src else None,
            office_end_time=src.office_end_time if src else None,
            grace_period_minutes=src.grace_period_minutes if src else 15,
            is_default=False,
            address=address or None,
        )
        db.session.add(personal_office)
        db.session.flush()
        emp.office_settings_id = personal_office.id

    _notify_location(emp, office_name, new_lat, new_lon, new_radius)
    db.session.commit()
    logger.info("LOCATION_CHANGED | emp=%s | by=%s | office=%s", emp_id, current_user.id, office_name)
    flash(f"Office location updated to '{office_name}' for {emp.full_name}.", "success")
    return redirect(url_for("foss.employee_detail", emp_id=emp_id))


# ── Change history ────────────────────────────────────────────────────

@foss_bp.route("/history")
@login_required
def history():
    _foss_required()
    logs = (
        ShiftChangeLog.query
        .order_by(ShiftChangeLog.changed_at.desc())
        .limit(100)
        .all()
    )
    return render_template("foss/history.html", title="Change History", logs=logs)


# ── Internal notification helpers ─────────────────────────────────────

def _notify(emp, change_type, shift_name, start, end, grace):
    try:
        msg = (
            f"Your shift has been updated to '{shift_name}' "
            f"({start}–{end}, {grace} min grace)."
        )
        notif = Notification(
            user_id=emp.user_id,
            title="Shift Updated",
            message=msg,
            category="attendance",
            triggered_by=current_user.id,
        )
        db.session.add(notif)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Notification failed: %s", exc)


def _notify_location(emp, office_name, lat, lon, radius):
    try:
        msg = (
            f"Your office location has been updated to '{office_name}' "
            f"(GPS radius: {radius}m)."
        )
        notif = Notification(
            user_id=emp.user_id,
            title="Office Location Updated",
            message=msg,
            category="info",
            triggered_by=current_user.id,
        )
        db.session.add(notif)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Location notification failed: %s", exc)
