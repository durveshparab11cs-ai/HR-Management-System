"""
blueprints/employees/routes.py
================================
Employee management routes — thin, delegates to EmployeeService.
"""

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.core.security import hr_required
from .forms import CreateEmployeeForm, EditEmployeeForm, ResetPasswordForm
from .service import EmployeeService
from .repository import EmployeeRepository
from . import employees_bp

_svc = EmployeeService()
_repo = EmployeeRepository()


@employees_bp.route("/")
@login_required
@hr_required
def index():
    from app.core.dept_filter import get_dept_filter  # noqa: PLC0415
    page = request.args.get("page", 1, type=int)
    search = request.args.get("q", "")
    # Dept filter: if user has a forced department, override any URL param
    forced_dept = get_dept_filter()
    department = forced_dept if forced_dept else request.args.get("dept", "")
    branch = request.args.get("branch", "")
    pagination = _repo.get_all(page=page, per_page=25, search=search, department=department, branch=branch)
    departments = _repo.get_departments()
    branches = _repo.get_branches()
    return render_template(
        "employees/index.html",
        title="Employees",
        pagination=pagination,
        employees=pagination.items,
        search=search,
        department=department,
        branch=branch,
        departments=departments,
        branches=branches,
        dept_locked=bool(forced_dept),
    )


@employees_bp.route("/create", methods=["GET", "POST"])
@login_required
@hr_required
def create():
    form = CreateEmployeeForm()
    form.manager_id.choices = _svc.get_managers_choices()

    # Show preview of what the next code will be
    next_code = _repo.get_next_employee_code()

    if form.validate_on_submit():
        photo = request.files.get("profile_photo")
        ok, msg, emp = _svc.create_employee(
            form_data={
                "first_name": form.first_name.data,
                "last_name": form.last_name.data,
                "email": form.email.data,
                "role": form.role.data,
                "department": form.department.data,
                "designation": form.designation.data,
                "branch": form.branch.data,
                "employment_type": form.employment_type.data,
                "shift_name": form.shift_name.data,
                "date_joined": form.date_joined.data,
                "date_of_birth": form.date_of_birth.data,
                "gender": form.gender.data,
                "mobile": form.mobile.data,
                "nationality": form.nationality.data,
                "manager_id": form.manager_id.data if form.manager_id.data else None,
                "created_by": current_user.id,
            },
            photo=photo if (photo and photo.filename) else None,
        )
        if ok:
            flash(msg, "success")
            return redirect(url_for("employees.detail", employee_id=emp.id))
        else:
            flash(msg, "danger")
    return render_template("employees/create.html", title="Add Employee", form=form, next_code=next_code)


@employees_bp.route("/next-code")
@login_required
@hr_required
def next_code_api():
    """JSON — returns the next auto-generated employee code."""
    from flask import jsonify
    code = _repo.get_next_employee_code()
    return jsonify({"code": code})


@employees_bp.route("/<int:employee_id>")
@login_required
def detail(employee_id: int):
    employee = _repo.get_by_id_or_404(employee_id)
    from app.blueprints.authentication.repository import AuthRepository
    auth_repo = AuthRepository()
    login_history = auth_repo.get_login_history(employee.user_id, limit=10)
    return render_template(
        "employees/detail.html",
        title=employee.full_name,
        employee=employee,
        login_history=login_history,
    )


@employees_bp.route("/<int:employee_id>/edit", methods=["GET", "POST"])
@login_required
@hr_required
def edit(employee_id: int):
    employee = _repo.get_by_id_or_404(employee_id)
    form = EditEmployeeForm(obj=employee)
    form.manager_id.choices = _svc.get_managers_choices(exclude_id=employee_id)

    if request.method == "GET":
        # Pre-populate from User model
        form.first_name.data = employee.user.first_name
        form.last_name.data = employee.user.last_name
        form.email.data = employee.user.email
        form.role.data = employee.user.role
        form.status.data = employee.user.status

    if form.validate_on_submit():
        photo = request.files.get("profile_photo")
        ok, msg = _svc.update_employee(
            employee_id,
            form_data={
                "first_name": form.first_name.data,
                "last_name": form.last_name.data,
                "email": form.email.data,
                "role": form.role.data,
                "status": form.status.data,
                "department": form.department.data,
                "designation": form.designation.data,
                "branch": form.branch.data,
                "employment_type": form.employment_type.data,
                "shift_name": form.shift_name.data,
                "date_joined": form.date_joined.data,
                "date_of_birth": form.date_of_birth.data,
                "gender": form.gender.data,
                "mobile": form.mobile.data,
                "nationality": form.nationality.data,
                "personal_email": form.personal_email.data,
                "address": form.address.data,
                "emergency_contact_name": form.emergency_contact_name.data,
                "emergency_contact_phone": form.emergency_contact_phone.data,
                "manager_id": form.manager_id.data if form.manager_id.data else None,
            },
            photo=photo if (photo and photo.filename) else None,
        )
        flash(msg, "success" if ok else "danger")
        if ok:
            return redirect(url_for("employees.detail", employee_id=employee_id))
    return render_template("employees/edit.html", title="Edit Employee", form=form, employee=employee)


@employees_bp.route("/<int:employee_id>/reset-password", methods=["GET", "POST"])
@login_required
@hr_required
def reset_password(employee_id: int):
    employee = _repo.get_by_id_or_404(employee_id)
    form = ResetPasswordForm()
    if form.validate_on_submit():
        ok, msg = _svc.reset_password(employee_id, form.new_password.data)
        flash(msg, "success" if ok else "danger")
        return redirect(url_for("employees.detail", employee_id=employee_id))
    return render_template("employees/reset_password.html", title="Reset Password", form=form, employee=employee)


@employees_bp.route("/<int:employee_id>/toggle-status", methods=["POST"])
@login_required
@hr_required
def toggle_status(employee_id: int):
    new_status = request.form.get("status", "inactive")
    ok, msg = _svc.toggle_account_status(employee_id, new_status)
    flash(msg, "success" if ok else "danger")
    return redirect(url_for("employees.detail", employee_id=employee_id))


@employees_bp.route("/<int:employee_id>/unlock", methods=["POST"])
@login_required
@hr_required
def unlock(employee_id: int):
    ok, msg = _svc.unlock_account(employee_id)
    flash(msg, "success" if ok else "danger")
    return redirect(url_for("employees.detail", employee_id=employee_id))


@employees_bp.route("/<int:employee_id>/delete", methods=["POST"])
@login_required
@hr_required
def delete(employee_id: int):
    ok, msg = _svc.delete_employee(employee_id, current_user.id)
    flash(msg, "success" if ok else "danger")
    return redirect(url_for("employees.index"))
