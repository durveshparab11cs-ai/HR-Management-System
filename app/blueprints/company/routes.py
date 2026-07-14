"""blueprints/company/routes.py"""

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.core.security import admin_required
from .forms import CompanyProfileForm, DepartmentForm, PositionForm, ShiftForm
from .service import CompanyService
from . import company_bp

_svc = CompanyService()


@company_bp.route("/")
@company_bp.route("")
@login_required
@admin_required
def index():
    profile = _svc.get_or_create_profile()
    dept_stats = _svc.get_department_stats()
    return render_template("company/index.html", title="Company", profile=profile, dept_stats=dept_stats)


@company_bp.route("/profile", methods=["GET", "POST"])
@login_required
@admin_required
def profile():
    company = _svc.get_or_create_profile()
    form = CompanyProfileForm(obj=company)
    if form.validate_on_submit():
        ok, msg = _svc.update_profile({
            "name": form.name.data, "industry": form.industry.data,
            "website": form.website.data, "phone": form.phone.data,
            "email": form.email.data, "address": form.address.data,
            "city": form.city.data, "state": form.state.data,
            "country": form.country.data, "pin_code": form.pin_code.data,
            "gstin": form.gstin.data, "pan": form.pan.data,
            "description": form.description.data, "timezone": form.timezone.data,
            "currency": form.currency.data, "currency_symbol": form.currency_symbol.data,
        })
        flash(msg, "success" if ok else "danger")
        if ok:
            return redirect(url_for("company.index"))
    return render_template("company/profile.html", title="Company Profile", form=form, company=company)


@company_bp.route("/departments")
@login_required
@admin_required
def departments():
    depts = _svc.get_all_departments()
    return render_template("company/departments.html", title="Departments", departments=depts)


@company_bp.route("/departments/create", methods=["GET", "POST"])
@login_required
@admin_required
def create_department():
    form = DepartmentForm()
    if form.validate_on_submit():
        ok, msg, dept = _svc.create_department({
            "name": form.name.data, "code": form.code.data,
            "description": form.description.data, "color": form.color.data,
            "created_by": current_user.id,
        })
        flash(msg, "success" if ok else "danger")
        if ok:
            return redirect(url_for("company.departments"))
    return render_template("company/department_form.html", title="Add Department", form=form)


@company_bp.route("/departments/<int:dept_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_department(dept_id: int):
    ok, msg = _svc.delete_department(dept_id, current_user.id)
    flash(msg, "success" if ok else "danger")
    return redirect(url_for("company.departments"))


@company_bp.route("/positions")
@login_required
@admin_required
def positions():
    pos_list = _svc.get_all_positions()
    return render_template("company/positions.html", title="Positions", positions=pos_list)


@company_bp.route("/positions/create", methods=["GET", "POST"])
@login_required
@admin_required
def create_position():
    form = PositionForm()
    form.department_id.choices = [(0, "— None —")] + [(d.id, d.name) for d in _svc.get_all_departments()]
    if form.validate_on_submit():
        ok, msg, pos = _svc.create_position({
            "title": form.title.data, "code": form.code.data,
            "department_id": form.department_id.data or None,
            "grade": form.grade.data, "description": form.description.data,
            "created_by": current_user.id,
        })
        flash(msg, "success" if ok else "danger")
        if ok:
            return redirect(url_for("company.positions"))
    return render_template("company/position_form.html", title="Add Position", form=form)


@company_bp.route("/shifts")
@login_required
@admin_required
def shifts():
    shift_list = _svc.get_all_shifts()
    return render_template("company/shifts.html", title="Shifts", shifts=shift_list)


@company_bp.route("/shifts/create", methods=["GET", "POST"])
@login_required
@admin_required
def create_shift():
    form = ShiftForm()
    if form.validate_on_submit():
        ok, msg, shift = _svc.create_shift({
            "name": form.name.data, "code": form.code.data,
            "start_time": form.start_time.data, "end_time": form.end_time.data,
            "grace_minutes": form.grace_minutes.data, "break_minutes": form.break_minutes.data,
            "working_days": form.working_days.data, "is_night_shift": form.is_night_shift.data,
            "description": form.description.data, "created_by": current_user.id,
        })
        flash(msg, "success" if ok else "danger")
        if ok:
            return redirect(url_for("company.shifts"))
    return render_template("company/shift_form.html", title="Add Shift", form=form)


@company_bp.route("/holidays")
@login_required
@admin_required
def holidays():
    return render_template("company/holidays.html", title="Holidays")


@company_bp.route("/locations")
@login_required
@admin_required
def locations():
    return render_template("company/locations.html", title="Locations")
