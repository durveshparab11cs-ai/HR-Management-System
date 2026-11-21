
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
    from app.models.employee_master import EmployeeMaster
    
    # HARDCODED: E-2606026 (Durvesh Parab) is always super admin portal
    if current_user.username == 'e2606026':
        from flask import redirect, url_for
        return redirect(url_for("admin.index"), code=302)
    
    # DIRECT CHECK - if role is admin-level, MUST go to /admin/
    # This is a failsafe redirect
    if current_user.role in ('super_admin', 'admin', 'hr_manager', 'hr_staff'):
        # Force redirect to admin dashboard
        from flask import redirect, url_for
        return redirect(url_for("admin.index"), code=302)

    employee = _emp.get_by_user_id(current_user.id)
    today    = date.today()
    today_att = None
    office    = None
    balances  = []
    employee_master = None
    attendance_chart_data = _build_attendance_chart_data([])
    department_chart_data = {"labels": [], "values": []}
    monthly_salary_records = []
    
    if employee:
        try:
            today_att = _att.get_today(employee.id, today)
        except Exception:  # noqa: BLE001
            today_att = None
        try:
            office = _att.get_office_for_employee(employee)
        except Exception:  # noqa: BLE001
            office = None
        try:
            balances = _lsvc.get_balance(employee.id)
        except Exception:  # noqa: BLE001
            balances = []
        try:
            # Fetch employee master data by employee code
            employee_master = EmployeeMaster.query.filter_by(
                employee_code=employee.employee_code
            ).first()
        except Exception:  # noqa: BLE001
            employee_master = None
        try:
            months_data = _build_attendance_chart_data_for_employee(employee.id)
            attendance_chart_data = months_data
        except Exception:  # noqa: BLE001
            pass
        try:
            monthly_salary_records = _get_employee_salary_and_absence_breakdown(employee, num_months=6)
        except Exception as exc:  # noqa: BLE001
            import logging
            logging.getLogger(__name__).warning("Failed to calculate monthly salary breakdown: %s", exc)
            monthly_salary_records = []

    return render_template(
        "dashboard/index.html",
        title="Dashboard",
        employee=employee,
        employee_master=employee_master,
        today_att=today_att,
        today=today,
        office=office,
        balances=balances,
        attendance_chart_data=attendance_chart_data,
        department_chart_data=department_chart_data,
        monthly_salary_records=monthly_salary_records,
    )


def _get_employee_salary_and_absence_breakdown(employee, num_months: int = 6) -> list:
    """
    Build month-wise salary credit, attendance, and absent-days breakdown.
    For each month (past months + current month):
    - Reads EmployeeSalaryMaster for base CTC/Gross, PF, TDS, PT
    - Checks for finalized Payslip from payroll runs if available
    - Queries Attendance records for present, half_day, late marks, and absent records
    - Checks approved LeaveRequest for paid leaves (CL, SL, PL, CO)
    - Pinpoints the exact calendar dates of absence
    - Calculates per-day deduction rate and exact salary credited
    """
    import calendar
    from datetime import date, timedelta
    from sqlalchemy import extract
    from app.models.payroll import EmployeeSalaryMaster, Payslip, PayrollRun
    from app.models.attendance import Attendance
    from app.models.leave import LeaveRequest

    today = date.today()
    results = []

    # Get employee salary master if uploaded
    salary_master = EmployeeSalaryMaster.query.filter_by(
        employee_code=employee.employee_code, is_active=True
    ).first()

    has_salary_master = salary_master is not None
    base_gross = float(salary_master.salary_amount) if salary_master else 0.0
    base_pf = float(salary_master.pf_amount) if salary_master else 0.0
    base_tds = float(salary_master.tds_amount) if salary_master else 0.0
    base_pt = float(salary_master.pt_amount) if salary_master else 0.0

    for i in range(num_months):
        m = today.month - i
        y = today.year
        while m <= 0:
            m += 12
            y -= 1

        days_in_month = calendar.monthrange(y, m)[1]
        month_label = date(y, m, 1).strftime("%B %Y")
        month_short = date(y, m, 1).strftime("%b '%y")
        month_tab_id = f"m_{y}_{m}"
        is_current_month = (y == today.year and m == today.month)

        # Check if finalized payslip exists
        payslip = (
            Payslip.query.join(PayrollRun, PayrollRun.id == Payslip.run_id)
            .filter(
                Payslip.employee_id == employee.id,
                PayrollRun.year == y,
                PayrollRun.month == m,
            )
            .first()
        )

        # Query attendance records in this month
        att_records = Attendance.query.filter(
            Attendance.employee_id == employee.id,
            Attendance.is_deleted == False,
            extract("year", Attendance.date) == y,
            extract("month", Attendance.date) == m,
        ).all()

        # ZERO DUMMY DATA: If not current month and no records exist in DB, skip this month
        if not is_current_month and payslip is None and len(att_records) == 0:
            continue

        att_by_date = {a.date: a for a in att_records}

        # Query approved leaves in this month
        approved_leaves = LeaveRequest.query.filter(
            LeaveRequest.employee_id == employee.id,
            LeaveRequest.status == "approved",
            LeaveRequest.start_date <= date(y, m, days_in_month),
            LeaveRequest.end_date >= date(y, m, 1),
        ).all()
        approved_leave_dates = set()
        for lr in approved_leaves:
            cur = max(lr.start_date, date(y, m, 1))
            end_d = min(lr.end_date, date(y, m, days_in_month))
            while cur <= end_d:
                approved_leave_dates.add(cur)
                cur += timedelta(days=1)

        eval_end_day = today.day if is_current_month else days_in_month

        present_count = 0
        leave_count = 0
        absent_dates = []
        half_day_dates = []
        late_count = 0
        total_working_days = 0

        for day in range(1, days_in_month + 1):
            cur_date = date(y, m, day)
            is_weekend = (cur_date.weekday() >= 5)  # Sat=5, Sun=6
            if not is_weekend:
                total_working_days += 1

            if day <= eval_end_day:
                att = att_by_date.get(cur_date)
                if att and att.status == "present":
                    present_count += 1
                    if att.is_late:
                        late_count += 1
                elif att and att.status == "on_leave":
                    leave_count += 1
                elif cur_date in approved_leave_dates:
                    leave_count += 1
                elif att and (att.status == "half_day" or att.is_half_day):
                    present_count += 0.5
                    half_day_dates.append({
                        "date_str": cur_date.strftime("%d %b %Y (%a)"),
                        "type": "Half Day",
                        "badge": "Half Day",
                    })
                elif att and att.status == "absent":
                    absent_dates.append({
                        "date_str": cur_date.strftime("%d %b %Y (%a)"),
                        "type": "Full Day Absent",
                        "badge": "Marked Absent",
                    })
                elif not is_weekend and att is not None and att.status == "absent":
                    absent_dates.append({
                        "date_str": cur_date.strftime("%d %b %Y (%a)"),
                        "type": "Full Day Absent",
                        "badge": "Absent",
                    })

        late_half_days = late_count // 3
        daily_rate = round(base_gross / days_in_month, 2) if (has_salary_master and days_in_month > 0) else 0.0

        if payslip:
            gross = float(payslip.gross_salary)
            net_salary = float(payslip.net_salary)
            tot_ded = float(payslip.total_deductions)
            days_absent_count = payslip.days_absent
            days_present_count = payslip.days_present
            status_text = "Credited to Bank Account"
            status_class = "success"
            is_finalized = True
            absence_deduction = max(0.0, round(daily_rate * days_absent_count, 2))
            pf = base_pf
            tds = base_tds
            pt = base_pt
        elif has_salary_master:
            gross = base_gross
            days_absent_count = len(absent_dates)
            days_present_count = present_count
            total_absent_units = days_absent_count + (len(half_day_dates) * 0.5) + (late_half_days * 0.5)
            absence_deduction = round(daily_rate * total_absent_units, 2)

            pf = base_pf
            tds = base_tds
            pt = base_pt
            tot_ded = round(absence_deduction + pf + tds + pt, 2)
            net_salary = max(0.0, round(gross - tot_ded, 2))

            if is_current_month:
                status_text = "Estimated Net (Month-to-Date)"
                status_class = "primary"
                is_finalized = False
            else:
                status_text = "Processed / Take-Home"
                status_class = "info"
                is_finalized = True
        else:
            # ZERO DUMMY DATA: Salary master not yet uploaded by HR
            gross = 0.0
            days_absent_count = len(absent_dates)
            days_present_count = present_count
            absence_deduction = 0.0
            pf = 0.0
            tds = 0.0
            pt = 0.0
            tot_ded = 0.0
            net_salary = 0.0
            status_text = "Salary Master Pending Upload"
            status_class = "secondary"
            is_finalized = False

        results.append({
            "year": y,
            "month": m,
            "month_label": month_label,
            "month_short": month_short,
            "month_tab_id": month_tab_id,
            "is_current": is_current_month,
            "is_finalized": is_finalized,
            "has_salary_master": has_salary_master,
            "days_in_month": days_in_month,
            "working_days": total_working_days,
            "days_present": days_present_count,
            "leave_days": leave_count,
            "days_absent": days_absent_count,
            "absent_dates": absent_dates,
            "half_day_dates": half_day_dates,
            "late_count": late_count,
            "late_half_days": late_half_days,
            "daily_rate": daily_rate,
            "gross_salary": gross,
            "absence_deduction": absence_deduction,
            "pf_amount": pf,
            "tds_amount": tds,
            "pt_amount": pt,
            "total_deductions": tot_ded,
            "net_salary": net_salary,
            "status_text": status_text,
            "status_class": status_class,
        })

    return results


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
