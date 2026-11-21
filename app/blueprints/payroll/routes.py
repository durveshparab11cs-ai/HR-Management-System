"""blueprints/payroll/routes.py"""

import time
from datetime import date
from flask import flash, redirect, render_template, request, session, url_for, send_file, jsonify
from flask_login import current_user, login_required

from app.blueprints.employees.repository import EmployeeRepository
from app.constants.enums import UserRole
from app.core.security import hr_required, admin_required
from .service import PayrollService
from . import payroll_bp

_svc     = PayrollService()
_emp_repo = EmployeeRepository()


@payroll_bp.before_request
def check_payroll_step_up():
    """Enforce Super Admin / Payroll Admin role check and 15-min step-up password confirmation."""
    if not (current_user and current_user.is_authenticated):
        return  # Handled by @login_required

    # Role restriction: Super Admin or Admin only
    allowed_roles = (UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value)
    if current_user.role not in allowed_roles:
        flash("Access Denied: Only Super Admin and Payroll Admin can access the Payroll Vault.", "danger")
        return redirect(url_for("dashboard.index"))

    # Skip step-up check for verification endpoint and static files
    if request.endpoint in ("payroll.verify_access", "payroll.static"):
        return

    # 15-minute step-up timeout check
    unlocked_at = session.get("payroll_unlocked_at", 0)
    if time.time() - unlocked_at > 900:
        return redirect(url_for("payroll.verify_access", next=request.url))


@payroll_bp.route("/verify-access", methods=["GET", "POST"])
@login_required
def verify_access():
    """Step-up authentication password verification before granting access to Payroll."""
    next_url = request.args.get("next") or request.form.get("next") or url_for("payroll.index")

    if request.method == "POST":
        pwd = request.form.get("password", "")
        if current_user.check_password(pwd):
            session["payroll_unlocked_at"] = time.time()
            return redirect(next_url)
        else:
            flash("Incorrect password. Payroll authorization failed.", "danger")

    return render_template("payroll/step_up.html", next_url=next_url)


@payroll_bp.route("/")
@payroll_bp.route("")
@login_required
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


@payroll_bp.route("/runs/<int:run_id>/delete", methods=["POST"])
@login_required
@hr_required
def delete_run(run_id: int):
    """Delete a payroll run and its associated payslips."""
    from app.models.payroll import PayrollRun, Payslip
    from app.extensions.database import db
    run = db.session.get(PayrollRun, run_id)
    if not run:
        flash("Payroll run not found.", "danger")
        return redirect(url_for("payroll.index"))
    
    label = run.period_label
    Payslip.query.filter_by(run_id=run.id).delete()
    db.session.delete(run)
    db.session.commit()
    flash(f"Payroll run '{label}' and its payslips have been removed.", "info")
    return redirect(url_for("payroll.index"))



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


# ── Employee Salary Master Excel Import ──────────────────────────────
@payroll_bp.route("/import-salaries", methods=["GET", "POST"])
@login_required
@hr_required
def import_salaries():
    """Import employee salary structure (code, name, salary amount, pf, tds, pt)."""
    from .salary_import import SalaryImportService
    from app.models.payroll import EmployeeSalaryMaster
    from app.extensions.database import db
    from sqlalchemy import func

    svc = SalaryImportService()
    result = None

    if request.method == "POST":
        file = request.files.get("excel_file")
        if not file or not file.filename:
            flash("Please choose an Excel (.xlsx, .xls) or CSV file.", "warning")
        elif not file.filename.lower().endswith((".xlsx", ".xls", ".csv")):
            flash("Only Excel (.xlsx, .xls) or CSV files are supported.", "danger")
        else:
            result = svc.import_file(file)
            if result.get("success"):
                flash(
                    f"Successfully processed {result.get('total', 0)} records! "
                    f"Imported: {result.get('imported', 0)} new, "
                    f"Updated: {result.get('updated', 0)} existing.",
                    "success"
                )
            else:
                flash(f"Import failed: {result.get('error', 'Unknown error')}", "danger")

    # Fetch records and summary metrics
    search_q = request.args.get("q", "").strip()
    query = EmployeeSalaryMaster.query.filter_by(is_active=True)
    if search_q:
        query = query.filter(
            (EmployeeSalaryMaster.employee_code.ilike(f"%{search_q}%")) |
            (EmployeeSalaryMaster.employee_name.ilike(f"%{search_q}%"))
        )

    page = request.args.get("page", 1, type=int)
    records_pagination = query.order_by(EmployeeSalaryMaster.employee_code.asc()).paginate(
        page=page, per_page=15, error_out=False
    )

    total_records = EmployeeSalaryMaster.query.filter_by(is_active=True).count()
    stats = db.session.query(
        func.coalesce(func.sum(EmployeeSalaryMaster.salary_amount), 0.0),
        func.coalesce(func.sum(EmployeeSalaryMaster.pf_amount), 0.0),
        func.coalesce(func.sum(EmployeeSalaryMaster.tds_amount), 0.0),
        func.coalesce(func.sum(EmployeeSalaryMaster.pt_amount), 0.0),
        func.coalesce(func.sum(EmployeeSalaryMaster.net_salary), 0.0),
    ).filter(EmployeeSalaryMaster.is_active == True).first()

    total_gross = float(stats[0]) if stats else 0.0
    total_pf    = float(stats[1]) if stats else 0.0
    total_tds   = float(stats[2]) if stats else 0.0
    total_pt    = float(stats[3]) if stats else 0.0
    total_net   = float(stats[4]) if stats else 0.0

    return render_template(
        "payroll/import_salaries.html",
        title="Import Employee Salaries",
        result=result,
        pagination=records_pagination,
        search_q=search_q,
        total_records=total_records,
        total_gross=total_gross,
        total_pf=total_pf,
        total_tds=total_tds,
        total_pt=total_pt,
        total_net=total_net,
    )


@payroll_bp.route("/import-salaries/sample", methods=["GET"])
@login_required
@hr_required
def sample_salary_template():
    """Download pre-formatted sample Excel file for salary import."""
    from .salary_import import SalaryImportService
    buf = SalaryImportService.generate_sample_template()
    return send_file(
        buf,
        as_attachment=True,
        download_name="salary_master_import_template.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@payroll_bp.route("/import-salaries/preview", methods=["POST"])
@login_required
@hr_required
def preview_salaries():
    """AJAX preview of first 15 rows before submitting."""
    from .salary_import import SalaryImportService
    svc = SalaryImportService()
    file = request.files.get("excel_file")
    if not file or not file.filename:
        return jsonify({"success": False, "error": "No file uploaded"}), 400
    res = svc.preview(file)
    return jsonify(res)


@payroll_bp.route("/import-salaries/delete/<int:record_id>", methods=["POST"])
@login_required
@hr_required
def delete_salary_record(record_id: int):
    """Remove an employee salary master record."""
    from app.models.payroll import EmployeeSalaryMaster
    from app.extensions.database import db
    record = EmployeeSalaryMaster.query.get_or_404(record_id)
    emp_code = record.employee_code
    db.session.delete(record)
    db.session.commit()
    flash(f"Salary master record for {emp_code} removed.", "info")
    return redirect(url_for("payroll.import_salaries"))

