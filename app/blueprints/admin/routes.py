"""
blueprints/admin/routes.py
============================
Admin panel routes — dashboard, office settings, user management.
"""

from datetime import date
from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.core.security import admin_required, roles_required
from app.constants.enums import UserRole
from app.blueprints.attendance.repository import AttendanceRepository
from app.blueprints.employees.repository import EmployeeRepository
from app.blueprints.leave.repository import LeaveRepository
from .forms import OfficeSettingsForm
from .service import AdminService
from . import admin_bp

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
    total_employees   = _emp.count_total()
    checked_in_today  = _att.count_checked_in_today(today)
    checked_out_today = _att.count_checked_out_today(today)
    late_today        = _att.count_late_today(today)
    absent_today      = total_employees - checked_in_today
    pending_leaves    = _leave.count_pending()
    pending_halfdays  = _leave.count_pending_halfdays()
    pending_early     = _leave.count_pending_earlyleaves()
    today_records     = _att.get_all_today(today)
    recent_requests   = _leave.get_pending(page=1, per_page=5).items

    return render_template(
        "admin/index.html",
        title="Admin Dashboard",
        today=today,
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
    )


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
    page = request.args.get("page", 1, type=int)
    search = request.args.get("q", "")
    pagination = _emp.get_all(page=page, per_page=25, search=search)
    return render_template(
        "admin/users.html",
        title="User Management",
        pagination=pagination,
        employees=pagination.items,
        search=search,
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
