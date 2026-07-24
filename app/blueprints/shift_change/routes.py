"""
app/blueprints/shift_change/routes.py
=======================================
Routes for Shift Change Management
"""

import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import login_required, current_user

from app.blueprints.shift_change.forms import (
    ShiftChangeRequestForm,
    ShiftChangeApprovalForm,
    ShiftChangeFilterForm
)
from app.blueprints.shift_change.service import ShiftChangeService
from app.blueprints.shift_change.repository import (
    ShiftRepository,
    ShiftChangeRequestRepository,
    EmployeeShiftAssignmentRepository
)
from app.models.employee import Employee
from app.extensions.database import db


# Create blueprint
bp = Blueprint(
    "shift_change",
    __name__,
    url_prefix="/shift-change",
    template_folder="templates",
    static_folder="static"
)

# Initialize service
service = ShiftChangeService()
shift_repo = ShiftRepository()
request_repo = ShiftChangeRequestRepository()
assignment_repo = EmployeeShiftAssignmentRepository()


# ============================================================================
# EMPLOYEE ROUTES
# ============================================================================

@bp.route("/lookup-manager")
@login_required
def lookup_manager():
    """AJAX: validate a reporting manager code and return their details."""
    from app.models.employee_master import EmployeeMaster
    
    code = request.args.get("code", "").strip().upper()
    if not code:
        return jsonify(found=False, message="Please enter a manager code.")
    
    # Check if user is trying to select themselves
    employee = Employee.query.filter_by(user_id=current_user.id).first()
    if employee and employee.employee_code.upper() == code:
        return jsonify(found=False, message="You cannot select yourself as Reporting Manager.")
    
    # Look up manager in employee master
    master = EmployeeMaster.query.filter_by(employee_code=code, is_active=True).first()
    if not master:
        return jsonify(found=False, message="Reporting Manager not found or inactive.")
    
    return jsonify(
        found=True,
        name=master.employee_name,
        designation=master.designation or "N/A",
        department=master.department or "N/A"
    )


@bp.route("/my-approvals")
@login_required
def my_approvals():
    """Shift change requests assigned to me as reporting manager."""
    employee = Employee.query.filter_by(user_id=current_user.id).first()
    if not employee:
        flash("Employee profile not found", "danger")
        return redirect(url_for("dashboard.index"))
    
    # Get pending requests where this employee is the reporting manager
    from app.models.shift_change_request import ShiftChangeRequest
    
    pending_requests = ShiftChangeRequest.query.filter_by(
        reporting_manager_code=employee.employee_code.upper(),
        status="pending",
        is_deleted=False
    ).order_by(ShiftChangeRequest.submitted_date.desc()).all()
    
    return render_template(
        "shift_change/my_approvals.html",
        requests=pending_requests
    )


@bp.route("/")
@bp.route("/dashboard")
@login_required
def dashboard():
    """Shift change dashboard."""
    try:
        # Get current employee
        employee = Employee.query.filter_by(user_id=current_user.id).first()
        if not employee:
            flash("Employee profile not found", "danger")
            return redirect(url_for("dashboard.index"))
        
        # Get current shift
        current_shift = service.get_employee_current_shift(employee.id)
        
        # Get upcoming shift (if any approved request exists)
        upcoming_shift = None
        try:
            future_assignment = assignment_repo.get_current_assignment(
                employee.id,
                datetime.date.today() + datetime.timedelta(days=1)
            )
            if future_assignment and future_assignment.shift and future_assignment.effective_from > datetime.date.today():
                upcoming_shift = {
                    "shift_name": future_assignment.shift.name,
                    "start_time": future_assignment.shift.start_time,
                    "end_time": future_assignment.shift.end_time,
                    "effective_from": future_assignment.effective_from
                }
        except Exception as e:
            from flask import current_app
            current_app.logger.error(f"Error getting upcoming shift: {str(e)}")
            upcoming_shift = None
        
        # Get requests summary
        all_requests = request_repo.get_employee_requests(employee.id)
        pending_requests = [r for r in all_requests if r.status == "pending"]
        approved_requests = [r for r in all_requests if r.status == "approved"]
        rejected_requests = [r for r in all_requests if r.status == "rejected"]
        
        # Get shift history
        shift_history = assignment_repo.get_assignment_history(employee.id, limit=10)
        
        return render_template(
            "shift_change/dashboard.html",
            current_shift=current_shift,
            upcoming_shift=upcoming_shift,
            pending_count=len(pending_requests),
            approved_count=len(approved_requests),
            rejected_count=len(rejected_requests),
            recent_requests=all_requests[:5] if all_requests else [],
            shift_history=shift_history[:5] if shift_history else []
        )
    except Exception as e:
        from flask import current_app
        current_app.logger.exception(f"Error in shift change dashboard: {str(e)}")
        flash(f"Error loading dashboard: {str(e)}", "danger")
        return redirect(url_for("dashboard.index"))


@bp.route("/request", methods=["GET", "POST"])
@login_required
def create_request():
    """Create new shift change request."""
    # Get current employee
    employee = Employee.query.filter_by(user_id=current_user.id).first()
    if not employee:
        flash("Employee profile not found", "danger")
        return redirect(url_for("dashboard.index"))
    
    # Get current shift
    current_shift = service.get_employee_current_shift(employee.id)
    if not current_shift:
        flash("Your current shift is not assigned. Please contact HR.", "warning")
        return redirect(url_for("shift_change.dashboard"))
    
    form = ShiftChangeRequestForm()
    
    # Populate shift choices
    active_shifts = shift_repo.get_all_active()
    form.requested_shift_id.choices = [(0, "Custom Timing")] + [
        (s.id, f"{s.name} ({s.start_time.strftime('%H:%M')} - {s.end_time.strftime('%H:%M')})")
        for s in active_shifts
    ]
    
    if form.validate_on_submit():
        # Submit request
        success, message, request_id = service.submit_shift_change_request(
            employee_id=employee.id,
            current_shift_id=current_shift["shift_id"],
            requested_start_time=form.requested_start_time.data,
            requested_end_time=form.requested_end_time.data,
            effective_date=form.effective_date.data,
            reason=form.reason.data,
            reporting_manager_code=form.reporting_manager_code.data,
            remarks=form.remarks.data,
            requested_shift_id=form.requested_shift_id.data if form.requested_shift_id.data > 0 else None,
            attachment=form.attachment.data
        )
        
        if success:
            flash(message, "success")
            return redirect(url_for("shift_change.view_request", request_id=request_id))
        else:
            flash(message, "danger")
    
    # Pre-fill current shift
    form.current_shift_display.data = f"{current_shift['shift_name']} ({current_shift['start_time'].strftime('%H:%M')} - {current_shift['end_time'].strftime('%H:%M')})"
    form.current_shift_id.data = current_shift["shift_id"]
    
    return render_template(
        "shift_change/request_form.html",
        form=form,
        current_shift=current_shift
    )


@bp.route("/my-requests")
@login_required
def my_requests():
    """View all my shift change requests."""
    employee = Employee.query.filter_by(user_id=current_user.id).first()
    if not employee:
        flash("Employee profile not found", "danger")
        return redirect(url_for("dashboard.index"))
    
    # Get filter parameters
    status_filter = request.args.get("status", "")
    
    # Get requests
    if status_filter:
        requests = request_repo.get_all_requests(status=status_filter, employee_id=employee.id)
    else:
        requests = request_repo.get_employee_requests(employee.id)
    
    return render_template(
        "shift_change/my_requests.html",
        requests=requests,
        status_filter=status_filter
    )


@bp.route("/request/<int:request_id>")
@login_required
def view_request(request_id):
    """View shift change request details."""
    req = request_repo.get_by_id(request_id)
    if not req:
        flash("Request not found", "danger")
        return redirect(url_for("shift_change.dashboard"))
    
    # Check permission
    employee = Employee.query.filter_by(user_id=current_user.id).first()
    if employee and req.employee_id != employee.id:
        # Check if user is approver or admin
        if current_user.role not in ["super_admin", "hr", "ceo", "agm", "manager"]:
            flash("You don't have permission to view this request", "danger")
            return redirect(url_for("shift_change.dashboard"))
    
    return render_template("shift_change/request_detail.html", request=req)


@bp.route("/request/<int:request_id>/cancel", methods=["POST"])
@login_required
def cancel_request(request_id):
    """Cancel pending request."""
    employee = Employee.query.filter_by(user_id=current_user.id).first()
    if not employee:
        return jsonify({"success": False, "message": "Employee not found"}), 400
    
    success, message = service.cancel_request(request_id, employee.id)
    
    if success:
        flash(message, "success")
    else:
        flash(message, "danger")
    
    return redirect(url_for("shift_change.my_requests"))


@bp.route("/history")
@login_required
def shift_history():
    """View shift assignment history."""
    employee = Employee.query.filter_by(user_id=current_user.id).first()
    if not employee:
        flash("Employee profile not found", "danger")
        return redirect(url_for("dashboard.index"))
    
    history = assignment_repo.get_assignment_history(employee.id)
    
    return render_template("shift_change/history.html", history=history)


# ============================================================================
# APPROVER ROUTES
# ============================================================================

@bp.route("/approvals")
@login_required
def approvals():
    """View shift change requests pending approval."""
    # Check if user is approver
    if current_user.role not in ["manager", "agm", "ceo", "hr", "super_admin"]:
        flash("You don't have permission to access approvals", "danger")
        return redirect(url_for("shift_change.dashboard"))
    
    # Get pending requests for this approver
    pending_requests = request_repo.get_pending_requests_for_approver(current_user.id)
    
    # Admins can see all pending requests
    if current_user.role in ["super_admin", "hr"]:
        all_pending = request_repo.get_all_requests(status="pending")
        # Merge and deduplicate
        pending_requests = list({r.id: r for r in (pending_requests + all_pending)}.values())
    
    return render_template(
        "shift_change/approvals.html",
        requests=pending_requests
    )


@bp.route("/approvals/<int:request_id>", methods=["GET", "POST"])
@login_required
def approval_detail(request_id):
    """View and process shift change request approval."""
    # Check permission
    if current_user.role not in ["manager", "agm", "ceo", "hr", "super_admin"]:
        flash("You don't have permission to approve requests", "danger")
        return redirect(url_for("shift_change.dashboard"))
    
    req = request_repo.get_by_id(request_id)
    if not req:
        flash("Request not found", "danger")
        return redirect(url_for("shift_change.approvals"))
    
    form = ShiftChangeApprovalForm()
    form.request_id.data = request_id
    
    if form.validate_on_submit():
        success, message = service.approve_request(
            request_id=request_id,
            approver_id=current_user.id,
            remarks=form.remarks.data,
            action=form.action.data
        )
        
        if success:
            flash(message, "success")
            return redirect(url_for("shift_change.approvals"))
        else:
            flash(message, "danger")
    
    return render_template(
        "shift_change/approval_detail.html",
        request=req,
        form=form
    )


# ============================================================================
# ADMIN ROUTES
# ============================================================================

@bp.route("/admin/all-requests")
@login_required
def admin_all_requests():
    """View all shift change requests (admin only)."""
    if current_user.role not in ["super_admin", "hr"]:
        flash("You don't have permission to access this page", "danger")
        return redirect(url_for("shift_change.dashboard"))
    
    # Get filter parameters
    status = request.args.get("status", "")
    employee_code = request.args.get("employee_code", "")
    from_date = request.args.get("from_date", "")
    to_date = request.args.get("to_date", "")
    
    # Parse dates
    from_date_obj = datetime.datetime.strptime(from_date, "%Y-%m-%d").date() if from_date else None
    to_date_obj = datetime.datetime.strptime(to_date, "%Y-%m-%d").date() if to_date else None
    
    # Get employee ID from code
    employee_id = None
    if employee_code:
        emp = Employee.query.filter_by(employee_code=employee_code).first()
        if emp:
            employee_id = emp.id
    
    # Get requests
    requests = request_repo.get_all_requests(
        status=status or None,
        employee_id=employee_id,
        from_date=from_date_obj,
        to_date=to_date_obj,
        limit=200
    )
    
    return render_template(
        "shift_change/admin_requests.html",
        requests=requests,
        filters={
            "status": status,
            "employee_code": employee_code,
            "from_date": from_date,
            "to_date": to_date
        }
    )


# ============================================================================
# API ROUTES
# ============================================================================

@bp.route("/api/shift/<int:shift_id>")
@login_required
def api_get_shift(shift_id):
    """Get shift details (API)."""
    shift = shift_repo.get_by_id(shift_id)
    if not shift:
        return jsonify({"error": "Shift not found"}), 404
    
    return jsonify({
        "id": shift.id,
        "name": shift.name,
        "code": shift.code,
        "start_time": shift.start_time.strftime("%H:%M"),
        "end_time": shift.end_time.strftime("%H:%M"),
        "working_hours": shift.working_hours,
        "break_minutes": shift.break_minutes,
        "grace_period_minutes": shift.grace_period_minutes
    })


@bp.route("/api/employee/<int:employee_id>/current-shift")
@login_required
def api_get_employee_shift(employee_id):
    """Get employee's current shift (API for attendance system)."""
    # Check permission
    current_employee = Employee.query.filter_by(user_id=current_user.id).first()
    if not current_employee or (current_employee.id != employee_id and current_user.role not in ["super_admin", "hr"]):
        return jsonify({"error": "Permission denied"}), 403
    
    shift = service.get_employee_current_shift(employee_id)
    if not shift:
        return jsonify({"error": "Shift not assigned"}), 404
    
    return jsonify(shift)


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@bp.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    flash("The requested page was not found", "warning")
    return redirect(url_for("shift_change.dashboard"))


@bp.errorhandler(403)
def forbidden(error):
    """Handle 403 errors."""
    flash("You don't have permission to access this resource", "danger")
    return redirect(url_for("shift_change.dashboard"))
