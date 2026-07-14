"""
blueprints/dashboard/routes.py
================================
Dashboard — post-login landing page.
Admins redirect to /admin/. Employees see their personal dashboard.
All data passed to the template comes from real database queries only.
No placeholder or dummy values are used.
"""

from datetime import date, datetime, timezone
from flask import redirect, render_template, url_for
from flask_login import current_user, login_required

from app.blueprints.attendance.repository import AttendanceRepository
from app.blueprints.employees.repository import EmployeeRepository
from app.blueprints.leave.repository import LeaveRepository
from app.blueprints.leave.service import LeaveService
from . import dashboard_bp

_emp   = EmployeeRepository()
_att   = AttendanceRepository()
_leave = LeaveRepository()
_lsvc  = LeaveService()


@dashboard_bp.route("/")
@dashboard_bp.route("")
@login_required
def index():
    from app.constants.enums import UserRole
    if current_user.role in (
        UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value,
        UserRole.HR_MANAGER.value, UserRole.HR_STAFF.value,
    ):
        return redirect(url_for("admin.index"))

    employee = _emp.get_by_user_id(current_user.id)
    today    = date.today()
    today_att = None
    office    = None
    balances  = []
    attendance_chart_data = _build_attendance_chart_data([])
    department_chart_data = {"labels": [], "values": []}

    if employee:
        today_att = _att.get_today(employee.id, today)
        office    = _att.get_office_for_employee(employee)
        balances  = _lsvc.get_balance(employee.id)

        # Build real 6-month attendance chart data
        months_data = _build_attendance_chart_data_for_employee(employee.id)
        attendance_chart_data = months_data

    return render_template(
        "dashboard/index.html",
        title="Dashboard",
        employee=employee,
        today_att=today_att,
        today=today,
        office=office,
        balances=balances,
        attendance_chart_data=attendance_chart_data,
        department_chart_data=department_chart_data,
    )


def _build_attendance_chart_data_for_employee(employee_id: int) -> dict:
    """
    Build 6-month attendance summary for Chart.js.
    Uses real attendance records only.
    """
    from datetime import timedelta
    from sqlalchemy import extract, func
    from app.extensions.database import db
    from app.models.attendance import Attendance

    labels   = []
    present  = []
    absent   = []
    on_leave = []

    today = date.today()
    for i in range(5, -1, -1):
        # Calculate year/month for i months ago
        month = today.month - i
        year  = today.year
        while month <= 0:
            month += 12
            year  -= 1

        label = datetime(year, month, 1).strftime("%b '%y")
        labels.append(label)

        base_q = db.session.query(func.count(Attendance.id)).filter(
            Attendance.employee_id == employee_id,
            Attendance.is_deleted == False,
            extract("year", Attendance.date) == year,
            extract("month", Attendance.date) == month,
        )
        present.append(int(base_q.filter(Attendance.status == "present").scalar() or 0))
        absent.append(int(base_q.filter(Attendance.status == "absent").scalar() or 0))
        on_leave.append(int(base_q.filter(Attendance.status == "on_leave").scalar() or 0))

    return {"labels": labels, "present": present, "absent": absent, "on_leave": on_leave}


def _build_attendance_chart_data(records: list) -> dict:
    """Empty chart data structure used as fallback."""
    return {"labels": [], "present": [], "absent": [], "on_leave": []}
