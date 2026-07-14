"""blueprints/payroll/routes.py"""

from datetime import date
from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.blueprints.employees.repository import EmployeeRepository
from app.core.security import hr_required
from .service import PayrollService
from . import payroll_bp

_svc     = PayrollService()
_emp_repo = EmployeeRepository()


@payroll_bp.route("/")
@payroll_bp.route("")
@login_required
@hr_required
def index():
    page       = request.args.get("page", 1, type=int)
    pagination = _svc.get_all_runs(page=page)
    return render_template("payroll/index.html", title="Payroll", pagination=pagination)


@payroll_bp.route("/run/create", methods=["GET", "POST"])
@login_required
@hr_required
def run_payroll():
    today = date.today()
    if request.method == "POST":
        month = request.form.get("month", today.month, type=int)
        year  = request.form.get("year",  today.year,  type=int)
        ok, msg, run = _svc.create_run(month, year, current_user.id)
        flash(msg, "success" if ok else "danger")
        if ok:
            return redirect(url_for("payroll.run_detail", run_id=run.id))
    return render_template("payroll/run.html", title="New Payroll Run", today=today)


@payroll_bp.route("/runs/<int:run_id>")
@login_required
@hr_required
def run_detail(run_id: int):
    run      = _svc.get_run_or_404(run_id)
    payslips = _svc.get_payslips_for_run(run_id)
    return render_template("payroll/run_detail.html", title=f"Payroll — {run.period_label}", run=run, payslips=payslips)


@payroll_bp.route("/runs/<int:run_id>/process", methods=["POST"])
@login_required
@hr_required
def process_run(run_id: int):
    ok, msg = _svc.process_run(run_id, current_user.id)
    flash(msg, "success" if ok else "danger")
    return redirect(url_for("payroll.run_detail", run_id=run_id))


@payroll_bp.route("/runs/<int:run_id>/approve", methods=["POST"])
@login_required
@hr_required
def approve_run(run_id: int):
    ok, msg = _svc.approve_run(run_id, current_user.id)
    flash(msg, "success" if ok else "danger")
    return redirect(url_for("payroll.run_detail", run_id=run_id))


@payroll_bp.route("/runs/<int:run_id>/mark-paid", methods=["POST"])
@login_required
@hr_required
def mark_paid(run_id: int):
    ok, msg = _svc.mark_paid(run_id)
    flash(msg, "success" if ok else "danger")
    return redirect(url_for("payroll.run_detail", run_id=run_id))


@payroll_bp.route("/payslips")
@login_required
def payslips():
    employee = _emp_repo.get_by_user_id(current_user.id)
    if not employee:
        flash("Employee profile not found.", "warning")
        return redirect(url_for("dashboard.index"))
    page       = request.args.get("page", 1, type=int)
    pagination = _svc.get_employee_payslips(employee.id, page=page)
    return render_template("payroll/payslips.html", title="My Payslips", pagination=pagination)


@payroll_bp.route("/payslips/<int:payslip_id>")
@login_required
def payslip_detail(payslip_id: int):
    import json
    from app.models.payroll import Payslip
    payslip = Payslip.query.get_or_404(payslip_id)
    # Security: employee can only see their own payslip
    employee = _emp_repo.get_by_user_id(current_user.id)
    if employee and payslip.employee_id != employee.id:
        from app.core.security import admin_required
        # If not HR, block
        from app.constants.enums import UserRole
        if current_user.role not in (UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value,
                                     UserRole.HR_MANAGER.value, UserRole.HR_STAFF.value):
            flash("Access denied.", "danger")
            return redirect(url_for("payroll.payslips"))
    earnings   = json.loads(payslip.earnings_breakdown or "{}")
    deductions = json.loads(payslip.deductions_breakdown or "{}")
    return render_template("payroll/payslip_detail.html", title="Payslip",
                           payslip=payslip, earnings=earnings, deductions=deductions)


@payroll_bp.route("/salary-structures")
@login_required
@hr_required
def salary_structures():
    structures = _svc.get_salary_structures()
    return render_template("payroll/salary_structures.html", title="Salary Structures", structures=structures)
