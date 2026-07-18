"""
blueprints/leave/routes.py
============================
Leave, half-day, and early-leave routes — thin layer only.
"""

from flask import flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.blueprints.employees.repository import EmployeeRepository
from .forms import ApplyEarlyLeaveForm, ApplyHalfDayForm, ApplyLeaveForm, ReviewLeaveForm
from .repository import LeaveRepository
from .service import LeaveService
from . import leave_bp

_svc  = LeaveService()
_repo = LeaveRepository()
_emp  = EmployeeRepository()


def _get_employee_or_redirect():
    emp = _emp.get_by_user_id(current_user.id)
    if not emp:
        flash("Employee profile not found. Contact HR.", "warning")
        return None
    return emp


# ── Manager Code Lookup (AJAX) ────────────────────────────────────────

@leave_bp.route("/lookup-manager")
@login_required
def lookup_manager():
    """AJAX: validate a reporting manager code and return their details."""
    from app.models.employee_master import EmployeeMaster  # noqa: PLC0415
    code = request.args.get("code", "").strip().upper()
    if not code:
        return jsonify(found=False, message="Enter an Employee Code.")
    my_emp = _emp.get_by_user_id(current_user.id)
    if my_emp and my_emp.employee_code.upper() == code:
        return jsonify(found=False, message="You cannot select yourself as Reporting Manager.")
    master = EmployeeMaster.query.filter_by(employee_code=code, is_active=True).first()
    if not master:
        return jsonify(found=False, message="Reporting Manager not found.")
    return jsonify(
        found=True,
        name=master.employee_name,
        department=master.department or "—",
        designation=master.designation or "—",
    )


# ── Manager: Leave Approval Dashboard ────────────────────────────────

@leave_bp.route("/my-approvals")
@login_required
def my_approvals():
    """Requests assigned to the logged-in employee as reporting manager."""
    emp = _get_employee_or_redirect()
    if not emp:
        return redirect(url_for("dashboard.index"))
    mgr_code = emp.employee_code.upper()
    status_filter = request.args.get("status", "")
    page = request.args.get("page", 1, type=int)

    from app.models.leave import LeaveRequest  # noqa: PLC0415
    lr_q = LeaveRequest.query.filter_by(
        reporting_manager_code=mgr_code, is_deleted=False
    )
    if status_filter:
        lr_q = lr_q.filter_by(status=status_filter)
    lr_list = lr_q.order_by(LeaveRequest.applied_on.desc()).limit(30).all()

    hd_pag = _repo.get_halfdays_for_manager(mgr_code, page=page, status=status_filter)
    el_pag = _repo.get_earlyleaves_for_manager(mgr_code, page=page, status=status_filter)

    return render_template(
        "leave/my_approvals.html",
        title="Leave Approval",
        employee=emp,
        lr_list=lr_list,
        hd_list=hd_pag.items,
        el_list=el_pag.items,
        hd_pag=hd_pag,
        el_pag=el_pag,
        status_filter=status_filter,
    )


# ─── Leave Portal Index ──────────────────────────────────────────────

@leave_bp.route("/")
@login_required
def index():
    emp = _get_employee_or_redirect()
    if not emp:
        return redirect(url_for("dashboard.index"))
    balances = _svc.get_balance(emp.id)
    page = request.args.get("page", 1, type=int)
    pagination = _repo.get_employee_requests(emp.id, page=page)
    hd_pagination  = _repo.get_employee_halfdays(emp.id, page=1, per_page=5)
    el_pagination  = _repo.get_employee_earlyleaves(emp.id, page=1, per_page=5)
    return render_template(
        "leave/index.html", title="Leave Portal",
        employee=emp, balances=balances,
        pagination=pagination,
        hd_list=hd_pagination.items,
        el_list=el_pagination.items,
    )


# ─── Apply Leave ─────────────────────────────────────────────────────

@leave_bp.route("/apply", methods=["GET", "POST"])
@login_required
def apply():
    emp = _get_employee_or_redirect()
    if not emp: return redirect(url_for("dashboard.index"))
    form = ApplyLeaveForm()
    form.leave_type_id.choices = [(lt.id, lt.name) for lt in _repo.get_all_types()]
    if form.validate_on_submit():
        att = request.files.get("attachment")
        ok, msg, lr = _svc.apply_leave(
            employee_id=emp.id,
            form_data={
                "start_date": form.start_date.data,
                "end_date": form.end_date.data,
                "leave_type_id": form.leave_type_id.data,
                "reason": form.reason.data,
                "reporting_manager_code": form.reporting_manager_code.data,
            },
            attachment=att if (att and att.filename) else None,
        )
        flash(msg, "success" if ok else "danger")
        if ok:
            return redirect(url_for("leave.index"))
    return render_template("leave/apply.html", title="Apply for Leave", form=form)


# ─── Cancel Leave ────────────────────────────────────────────────────

@leave_bp.route("/<int:lr_id>/cancel", methods=["POST"])
@login_required
def cancel(lr_id: int):
    emp = _get_employee_or_redirect()
    if not emp: return redirect(url_for("dashboard.index"))
    ok, msg = _svc.cancel_leave(lr_id, emp.id)
    flash(msg, "success" if ok else "danger")
    return redirect(url_for("leave.index"))


# ─── Manager/HR: Review Leave ────────────────────────────────────────

@leave_bp.route("/pending")
@login_required
def pending():
    from app.core.dept_filter import get_dept_filter  # noqa: PLC0415
    page = request.args.get("page", 1, type=int)
    try:
        dept_filter = get_dept_filter()
    except Exception:  # noqa: BLE001
        dept_filter = None
    try:
        pagination = _repo.get_pending(page=page, department=dept_filter)
    except TypeError:
        pagination = _repo.get_pending(page=page)
    try:
        hd_pag = _repo.get_pending_halfdays(page=1, per_page=10, department=dept_filter)
    except TypeError:
        hd_pag = _repo.get_pending_halfdays(page=1, per_page=10)
    try:
        el_pag = _repo.get_pending_earlyleaves(page=1, per_page=10, department=dept_filter)
    except TypeError:
        el_pag = _repo.get_pending_earlyleaves(page=1, per_page=10)
    return render_template(
        "leave/pending.html", title="Pending Approvals",
        pagination=pagination,
        hd_list=hd_pag.items,
        el_list=el_pag.items,
    )


@leave_bp.route("/<int:lr_id>/approve", methods=["POST"])
@login_required
def approve(lr_id: int):
    form = ReviewLeaveForm()
    ok, msg = _svc.approve_leave(lr_id, current_user.id, form.comment.data or "")
    flash(msg, "success" if ok else "danger")
    return redirect(request.referrer or url_for("leave.pending"))


@leave_bp.route("/<int:lr_id>/reject", methods=["POST"])
@login_required
def reject(lr_id: int):
    form = ReviewLeaveForm()
    ok, msg = _svc.reject_leave(lr_id, current_user.id, form.comment.data or "")
    flash(msg, "success" if ok else "danger")
    return redirect(request.referrer or url_for("leave.pending"))


# ─── Half Day ────────────────────────────────────────────────────────

@leave_bp.route("/halfday/apply", methods=["GET", "POST"])
@login_required
def apply_halfday():
    emp = _get_employee_or_redirect()
    if not emp: return redirect(url_for("dashboard.index"))
    form = ApplyHalfDayForm()
    if form.validate_on_submit():
        ok, msg, _ = _svc.apply_halfday(emp.id, {
            "date": form.date.data,
            "half_type": form.half_type.data,
            "reason": form.reason.data,
            "reporting_manager_code": form.reporting_manager_code.data,
        })
        flash(msg, "success" if ok else "danger")
        if ok: return redirect(url_for("leave.index"))
    return render_template("leave/apply_halfday.html", title="Request Half Day", form=form)


@leave_bp.route("/halfday/<int:hd_id>/approve", methods=["POST"])
@login_required
def approve_halfday(hd_id: int):
    ok, msg = _svc.approve_halfday(hd_id, current_user.id)
    flash(msg, "success" if ok else "danger")
    return redirect(request.referrer or url_for("leave.pending"))


@leave_bp.route("/halfday/<int:hd_id>/reject", methods=["POST"])
@login_required
def reject_halfday(hd_id: int):
    ok, msg = _svc.reject_halfday(hd_id, current_user.id)
    flash(msg, "success" if ok else "danger")
    return redirect(request.referrer or url_for("leave.pending"))


# ─── Early Leave ─────────────────────────────────────────────────────

@leave_bp.route("/earlyleave/apply", methods=["GET", "POST"])
@login_required
def apply_earlyleave():
    emp = _get_employee_or_redirect()
    if not emp: return redirect(url_for("dashboard.index"))
    form = ApplyEarlyLeaveForm()
    if form.validate_on_submit():
        ok, msg, _ = _svc.apply_earlyleave(emp.id, {
            "date": form.date.data,
            "requested_leave_time": form.requested_leave_time.data,
            "reason": form.reason.data,
            "reporting_manager_code": form.reporting_manager_code.data,
        })
        flash(msg, "success" if ok else "danger")
        if ok: return redirect(url_for("leave.index"))
    return render_template("leave/apply_earlyleave.html", title="Request Early Leave", form=form)


@leave_bp.route("/earlyleave/<int:el_id>/approve", methods=["POST"])
@login_required
def approve_earlyleave(el_id: int):
    ok, msg = _svc.approve_earlyleave(el_id, current_user.id)
    flash(msg, "success" if ok else "danger")
    return redirect(request.referrer or url_for("leave.pending"))


@leave_bp.route("/earlyleave/<int:el_id>/reject", methods=["POST"])
@login_required
def reject_earlyleave(el_id: int):
    ok, msg = _svc.reject_earlyleave(el_id, current_user.id)
    flash(msg, "success" if ok else "danger")
    return redirect(request.referrer or url_for("leave.pending"))
