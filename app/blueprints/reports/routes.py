"""blueprints/reports/routes.py"""

from datetime import date, datetime
from flask import flash, redirect, render_template, request, send_file, url_for
from flask_login import current_user, login_required

from app.core.security import manager_required
from app.constants.limits import Limits
from app.extensions.limiter import limiter
from .service import ReportService
from . import reports_bp

_svc = ReportService()


@reports_bp.route("/")
@reports_bp.route("")
@login_required
@manager_required
def index():
    stats = _svc.employee_stats()
    today = date.today()
    daily = _svc.daily_attendance(today)
    return render_template("reports/index.html", title="Reports", stats=stats, daily=daily, today=today)


@reports_bp.route("/attendance")
@login_required
@manager_required
def attendance_report():
    start_str = request.args.get("start", date.today().replace(day=1).isoformat())
    end_str   = request.args.get("end",   date.today().isoformat())
    department = request.args.get("dept", "")
    try:
        start = date.fromisoformat(start_str)
        end   = date.fromisoformat(end_str)
    except ValueError:
        start = date.today().replace(day=1)
        end   = date.today()
    data  = _svc.attendance_summary(start, end, department=department)
    depts = _svc.get_departments()
    return render_template(
        "reports/attendance.html", title="Attendance Report",
        data=data, start=start, end=end, department=department, departments=depts,
    )


@reports_bp.route("/leave")
@login_required
@manager_required
def leave_report():
    year = request.args.get("year", date.today().year, type=int)
    data = _svc.leave_summary(year)
    return render_template("reports/leave.html", title="Leave Report", data=data, year=year)


@reports_bp.route("/employees")
@login_required
@manager_required
def employee_report():
    stats    = _svc.employee_stats()
    employees = _svc.get_all_employees_simple()
    return render_template("reports/employees.html", title="Employee Report", stats=stats, employees=employees)


@reports_bp.route("/export/<report_type>/<fmt>")
@login_required
@manager_required
@limiter.limit(Limits.RateLimit.EXPORT)
def export(report_type: str, fmt: str):
    """Export report as CSV, Excel or PDF."""
    from app.utils.export_utils import export_to_csv, export_to_excel, export_to_pdf, stream_file_response
    start_str = request.args.get("start", date.today().replace(day=1).isoformat())
    end_str   = request.args.get("end",   date.today().isoformat())
    try:
        start = date.fromisoformat(start_str)
        end   = date.fromisoformat(end_str)
    except ValueError:
        start = date.today().replace(day=1)
        end   = date.today()

    if report_type == "attendance":
        data    = _svc.attendance_summary(start, end)
        headers = ["Code","Name","Department","Present","Absent","Half Day","On Leave","Late Days","Total Hours"]
        rows    = [
            [r["employee"].employee_code, r["user"].full_name,
             r["employee"].department or "—",
             r["present"], r["absent"], r["half_day"],
             r["on_leave"], r["late_days"], r["total_hours"]]
            for r in data
        ]
        title = f"Attendance Report ({start} to {end})"
    elif report_type == "leave":
        year = request.args.get("year", date.today().year, type=int)
        data    = _svc.leave_summary(year)
        headers = ["Code","Name","Total Requests","Approved Days","Pending","Rejected"]
        rows    = [
            [r["employee"].employee_code, r["user"].full_name,
             r["total_requests"], r["approved_days"], r["pending_count"], r["rejected_count"]]
            for r in data
        ]
        title = f"Leave Report {year}"
    elif report_type == "employees":
        data    = _svc.get_all_employees_simple()
        headers = ["Code","Name","Email","Department","Designation","Employment Type"]
        rows    = [
            [e.employee_code, u.full_name, u.email,
             e.department or "—", e.designation or "—",
             e.employment_type.replace("_"," ").title()]
            for e, u in data
        ]
        title = "Employee Report"
    else:
        flash("Unknown report type.", "danger")
        return redirect(url_for("reports.index"))

    if fmt == "csv":
        file_bytes, mime, fname = export_to_csv(headers, rows, report_type)
    elif fmt == "xlsx":
        file_bytes, mime, fname = export_to_excel(headers, rows, sheet_name=title[:31], filename=report_type)
    elif fmt == "pdf":
        file_bytes, mime, fname = export_to_pdf(title, headers, rows, filename=report_type)
    else:
        flash("Invalid export format.", "danger")
        return redirect(url_for("reports.index"))

    return stream_file_response(file_bytes, mime, fname)
