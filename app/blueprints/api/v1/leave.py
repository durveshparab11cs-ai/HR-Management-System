"""
blueprints/api/v1/leave.py
============================
Leave REST API endpoints for mobile app.

Endpoints:
    GET  /api/v1/leave                   - My leave requests (paginated)
    POST /api/v1/leave/apply             - Apply for leave
    GET  /api/v1/leave/types             - Available leave types
    GET  /api/v1/leave/balance           - Leave balance
    GET  /api/v1/leave/managers          - Reporting managers list
    POST /api/v1/leave/<id>/cancel       - Cancel leave
    GET  /api/v1/leave/approvals         - Pending approvals (manager)
    POST /api/v1/leave/<id>/approve      - Approve leave (manager)
    POST /api/v1/leave/<id>/reject       - Reject leave (manager)
    GET  /api/v1/leave/<id>              - Get single leave request
"""

from datetime import date
from flask import g, request

from app.blueprints.api import api_bp
from app.blueprints.leave.repository import LeaveRepository
from app.blueprints.leave.service import LeaveService
from app.blueprints.employees.repository import EmployeeRepository
from app.utils.response_utils import (
    success_response, error_response, validation_error_response, paginated_response, not_found_response
)
from app.utils.jwt_utils import jwt_required
from app.utils.pagination_utils import get_page_args
from app.utils.filter_utils import get_date_range_params, get_status_filter
from app.extensions.limiter import limiter
from app.constants.limits import Limits

_emp   = EmployeeRepository()
_repo  = LeaveRepository()
_svc   = LeaveService()


def _serialize_leave_request(lr) -> dict:
    """Serialize a leave request for API response."""
    employee_name = ""
    try:
        employee_name = lr.employee.full_name if lr.employee else ""
    except Exception:
        pass
    
    return {
        "id": lr.id,
        "employee_name": employee_name,
        "leave_type": {
            "id": lr.leave_type_id,
            "name": lr.leave_type.name if lr.leave_type else "",
            "code": lr.leave_type.code if lr.leave_type else "",
        },
        "start_date": lr.start_date.isoformat() if lr.start_date else None,
        "end_date": lr.end_date.isoformat() if lr.end_date else None,
        "total_days": float(lr.total_days or 0),
        "reason": lr.reason or "",
        "status": lr.status,
        "applied_on": lr.applied_on.isoformat() if lr.applied_on else None,
        "reviewed_on": lr.reviewed_on.isoformat() if lr.reviewed_on else None,
        "reviewer_comment": lr.reviewer_comment or "",
        "reporting_manager_name": lr.reporting_manager_name or "",
        "reporting_manager_code": lr.reporting_manager_code or "",
        "has_attachment": bool(lr.attachment),
        "status_badge": _get_status_badge(lr.status),
    }


def _get_status_badge(status: str) -> dict:
    """Return color and label for status."""
    badges = {
        "pending":  {"color": "warning",  "label": "Pending"},
        "approved": {"color": "success",  "label": "Approved"},
        "rejected": {"color": "danger",   "label": "Rejected"},
        "cancelled": {"color": "secondary", "label": "Cancelled"},
    }
    return badges.get(status, {"color": "secondary", "label": status.title()})


# ── My Leave Requests ────────────────────────────────────────────────

@api_bp.route("/leave", methods=["GET"])
@jwt_required
@limiter.limit(Limits.RateLimit.API_DEFAULT)
def my_leaves():
    """
    Get my leave requests with pagination and filters.
    
    Query Parameters:
        page, per_page, status, start_date, end_date
    """
    user = g.current_user
    employee = _emp.get_by_user_id(user.id)
    
    if not employee:
        return error_response(message="Employee profile not found", code="PROFILE_NOT_FOUND", status_code=404)
    
    page, per_page = get_page_args()
    
    pagination = _repo.get_employee_requests(
        employee_id=employee.id,
        page=page,
        per_page=per_page
    )
    
    records = [_serialize_leave_request(lr) for lr in pagination.items]
    
    return paginated_response(
        items=records,
        total=pagination.total,
        page=pagination.page,
        per_page=pagination.per_page,
    )


# ── Leave Types ──────────────────────────────────────────────────────

@api_bp.route("/leave/types", methods=["GET"])
@jwt_required
@limiter.limit(Limits.RateLimit.API_DEFAULT)
def leave_types():
    """Get all available leave types."""
    types = _repo.get_all_types()
    
    return success_response(data={
        "types": [
            {
                "id": lt.id,
                "name": lt.name,
                "code": lt.code,
                "max_days_per_year": lt.max_days_per_year,
                "is_unlimited": lt.max_days_per_year >= 999,
                "description": lt.description if hasattr(lt, 'description') else "",
            }
            for lt in types
        ]
    })


# ── Leave Balance ────────────────────────────────────────────────────

@api_bp.route("/leave/balance", methods=["GET"])
@jwt_required
@limiter.limit(Limits.RateLimit.API_DEFAULT)
def leave_balance():
    """Get leave balance for current employee."""
    user = g.current_user
    employee = _emp.get_by_user_id(user.id)
    
    if not employee:
        return error_response(message="Employee profile not found", code="PROFILE_NOT_FOUND", status_code=404)
    
    try:
        balances = _svc.get_balance(employee.id)
    except Exception:
        balances = []
    
    return success_response(data={
        "year": date.today().year,
        "balances": [
            {
                "leave_type": b["type"].name,
                "leave_type_code": b["type"].code,
                "allowed": b["max"],
                "taken": b["taken"],
                "available": b["available"],
                "is_unlimited": b["is_unlimited"],
                "percentage_used": b.get("pct", 0),
            }
            for b in balances
        ]
    })


# ── Reporting Managers List ──────────────────────────────────────────

@api_bp.route("/leave/managers", methods=["GET"])
@jwt_required
@limiter.limit(Limits.RateLimit.API_DEFAULT)
def leave_managers():
    """Get list of reporting managers for leave application."""
    try:
        from app.blueprints.leave.forms import get_manager_choices  # noqa: PLC0415
        choices = get_manager_choices()
        managers = [{"name": name, "value": value} for value, name in choices if value]
    except Exception:
        managers = []
    
    return success_response(data={"managers": managers})


# ── Apply Leave ──────────────────────────────────────────────────────

@api_bp.route("/leave/apply", methods=["POST"])
@jwt_required
@limiter.limit("30 per hour")
def apply_leave():
    """
    Apply for leave.
    
    Request Body:
        {
            "leave_type_id": 1,
            "start_date": "2024-07-01",
            "end_date": "2024-07-03",
            "reason": "Family vacation",
            "reporting_manager_name": "Manager Full Name"
        }
    """
    user = g.current_user
    employee = _emp.get_by_user_id(user.id)
    
    if not employee:
        return error_response(message="Employee profile not found", code="PROFILE_NOT_FOUND", status_code=404)
    
    data = request.get_json() or {}
    
    # Parse dates
    start_date_str = data.get("start_date", "")
    end_date_str = data.get("end_date", "")
    
    try:
        start_date = date.fromisoformat(start_date_str)
    except (ValueError, TypeError):
        return validation_error_response({"start_date": "Invalid date format. Use YYYY-MM-DD"})
    
    try:
        end_date = date.fromisoformat(end_date_str)
    except (ValueError, TypeError):
        return validation_error_response({"end_date": "Invalid date format. Use YYYY-MM-DD"})
    
    # Get manager code from name
    manager_name = data.get("reporting_manager_name", "").strip()
    if not manager_name:
        return validation_error_response({"reporting_manager_name": "Reporting manager is required"})
    
    from app.models.employee_master import EmployeeMaster  # noqa: PLC0415
    manager = EmployeeMaster.query.filter_by(
        employee_name=manager_name, is_active=True
    ).first()
    manager_code = manager.employee_code if manager else ""
    
    ok, msg, lr = _svc.apply_leave(
        employee_id=employee.id,
        form_data={
            "start_date": start_date,
            "end_date": end_date,
            "leave_type_id": data.get("leave_type_id"),
            "reason": data.get("reason", "").strip(),
            "reporting_manager_name": manager_name,
            "reporting_manager_code": manager_code,
        },
        attachment=None  # File upload handled separately if needed
    )
    
    if not ok:
        return error_response(message=msg, code="LEAVE_APPLICATION_FAILED")
    
    return success_response(
        data=_serialize_leave_request(lr),
        message=msg
    )


# ── Apply Half Day ───────────────────────────────────────────────────

@api_bp.route("/leave/halfday", methods=["POST"])
@jwt_required
@limiter.limit("20 per hour")
def apply_halfday():
    """
    Apply for half day leave.
    
    Request Body:
        {
            "date": "2024-07-01",
            "half_type": "first_half",
            "reason": "Personal work",
            "reporting_manager_name": "Manager Full Name"
        }
    """
    user = g.current_user
    employee = _emp.get_by_user_id(user.id)
    
    if not employee:
        return error_response(message="Employee profile not found", code="PROFILE_NOT_FOUND", status_code=404)
    
    data = request.get_json() or {}
    
    req_date_str = data.get("date", "")
    try:
        req_date = date.fromisoformat(req_date_str)
    except (ValueError, TypeError):
        return validation_error_response({"date": "Invalid date format. Use YYYY-MM-DD"})
    
    manager_name = data.get("reporting_manager_name", "").strip()
    from app.models.employee_master import EmployeeMaster  # noqa: PLC0415
    manager = EmployeeMaster.query.filter_by(employee_name=manager_name, is_active=True).first()
    manager_code = manager.employee_code if manager else ""
    
    ok, msg, hd = _svc.apply_halfday(employee.id, {
        "date": req_date,
        "half_type": data.get("half_type", "first_half"),
        "reason": data.get("reason", "").strip(),
        "reporting_manager_name": manager_name,
        "reporting_manager_code": manager_code,
    })
    
    if not ok:
        return error_response(message=msg, code="HALFDAY_APPLICATION_FAILED")
    
    return success_response(message=msg, data={"id": hd.id if hd else None})


# ── Apply Early Leave ────────────────────────────────────────────────

@api_bp.route("/leave/early", methods=["POST"])
@jwt_required
@limiter.limit("20 per hour")
def apply_early_leave():
    """
    Apply for early leave.
    
    Request Body:
        {
            "date": "2024-07-01",
            "requested_leave_time": "15:30",
            "reason": "Doctor appointment",
            "reporting_manager_name": "Manager Full Name"
        }
    """
    from datetime import time  # noqa: PLC0415
    
    user = g.current_user
    employee = _emp.get_by_user_id(user.id)
    
    if not employee:
        return error_response(message="Employee profile not found", code="PROFILE_NOT_FOUND", status_code=404)
    
    data = request.get_json() or {}
    
    req_date_str = data.get("date", "")
    try:
        req_date = date.fromisoformat(req_date_str)
    except (ValueError, TypeError):
        return validation_error_response({"date": "Invalid date format. Use YYYY-MM-DD"})
    
    time_str = data.get("requested_leave_time", "")
    try:
        from datetime import datetime as dt  # noqa: PLC0415
        leave_time = dt.strptime(time_str, "%H:%M").time()
    except (ValueError, TypeError):
        return validation_error_response({"requested_leave_time": "Invalid time format. Use HH:MM"})
    
    manager_name = data.get("reporting_manager_name", "").strip()
    from app.models.employee_master import EmployeeMaster  # noqa: PLC0415
    manager = EmployeeMaster.query.filter_by(employee_name=manager_name, is_active=True).first()
    manager_code = manager.employee_code if manager else ""
    
    ok, msg, el = _svc.apply_earlyleave(employee.id, {
        "date": req_date,
        "requested_leave_time": leave_time,
        "reason": data.get("reason", "").strip(),
        "reporting_manager_name": manager_name,
        "reporting_manager_code": manager_code,
    })
    
    if not ok:
        return error_response(message=msg, code="EARLY_LEAVE_APPLICATION_FAILED")
    
    return success_response(message=msg, data={"id": el.id if el else None})


# ── Cancel Leave ─────────────────────────────────────────────────────

@api_bp.route("/leave/<int:lr_id>/cancel", methods=["POST"])
@jwt_required
@limiter.limit("30 per hour")
def cancel_leave(lr_id: int):
    """Cancel a pending leave request."""
    user = g.current_user
    employee = _emp.get_by_user_id(user.id)
    
    if not employee:
        return error_response(message="Employee profile not found", code="PROFILE_NOT_FOUND", status_code=404)
    
    ok, msg = _svc.cancel_leave(lr_id, employee.id)
    
    if not ok:
        return error_response(message=msg, code="CANCEL_FAILED")
    
    return success_response(message=msg)


# ── Get Leave Request ────────────────────────────────────────────────

@api_bp.route("/leave/<int:lr_id>", methods=["GET"])
@jwt_required
@limiter.limit(Limits.RateLimit.API_DEFAULT)
def get_leave(lr_id: int):
    """Get a specific leave request."""
    user = g.current_user
    employee = _emp.get_by_user_id(user.id)
    
    lr = _repo.get_by_id(lr_id)
    
    if not lr:
        return not_found_response("Leave request")
    
    # Only allow employee to view their own, or manager to view pending requests
    is_admin = user.role in ["admin", "hr_manager", "super_admin"]
    if lr.employee_id != (employee.id if employee else -1) and not is_admin:
        return error_response(message="Access denied", code="FORBIDDEN", status_code=403)
    
    return success_response(data=_serialize_leave_request(lr))


# ── Manager: Pending Approvals ───────────────────────────────────────

@api_bp.route("/leave/approvals", methods=["GET"])
@jwt_required
@limiter.limit(Limits.RateLimit.API_DEFAULT)
def leave_approvals():
    """
    Get pending leave requests for approval.
    Returns requests where current employee is the reporting manager.
    """
    user = g.current_user
    employee = _emp.get_by_user_id(user.id)
    
    if not employee:
        return error_response(message="Employee profile not found", code="PROFILE_NOT_FOUND", status_code=404)
    
    page, per_page = get_page_args()
    
    # Get requests assigned to this manager
    from app.models.leave import LeaveRequest  # noqa: PLC0415
    query = LeaveRequest.query.filter_by(
        reporting_manager_code=employee.employee_code,
        status="pending",
        is_deleted=False
    ).order_by(LeaveRequest.applied_on.asc())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    records = [_serialize_leave_request(lr) for lr in pagination.items]
    
    return paginated_response(
        items=records,
        total=pagination.total,
        page=pagination.page,
        per_page=pagination.per_page,
    )


# ── Manager: Approve Leave ───────────────────────────────────────────

@api_bp.route("/leave/<int:lr_id>/approve", methods=["POST"])
@jwt_required
@limiter.limit("60 per hour")
def approve_leave(lr_id: int):
    """
    Approve a leave request.
    
    Request Body:
        {
            "comment": "Approved"
        }
    """
    user = g.current_user
    data = request.get_json() or {}
    comment = data.get("comment", "").strip()
    
    ok, msg = _svc.approve_leave(lr_id, user.id, comment)
    
    if not ok:
        return error_response(message=msg, code="APPROVAL_FAILED")
    
    return success_response(message=msg)


# ── Manager: Reject Leave ────────────────────────────────────────────

@api_bp.route("/leave/<int:lr_id>/reject", methods=["POST"])
@jwt_required
@limiter.limit("60 per hour")
def reject_leave(lr_id: int):
    """
    Reject a leave request.
    
    Request Body:
        {
            "comment": "Reason for rejection (required)"
        }
    """
    user = g.current_user
    data = request.get_json() or {}
    comment = data.get("comment", "").strip()
    
    if not comment:
        return validation_error_response({"comment": "Rejection reason is mandatory"})
    
    ok, msg = _svc.reject_leave(lr_id, user.id, comment)
    
    if not ok:
        return error_response(message=msg, code="REJECTION_FAILED")
    
    return success_response(message=msg)
