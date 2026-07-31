"""
blueprints/api/v1/shifts.py
==============================
Shift Change REST API endpoints for mobile app.

Endpoints:
    GET  /api/v1/shifts/my-shift          - My current shift
    GET  /api/v1/shifts/available         - Available shifts list
    GET  /api/v1/shifts/requests          - My shift change requests
    POST /api/v1/shifts/request-change    - Submit shift change request
    GET  /api/v1/shifts/approvals         - Pending approvals (manager)
    POST /api/v1/shifts/<id>/approve      - Approve request (manager)
    POST /api/v1/shifts/<id>/reject       - Reject request (manager)
    POST /api/v1/shifts/<id>/cancel       - Cancel my request
    GET  /api/v1/shifts/history           - Shift assignment history
"""

from flask import g, request

from app.blueprints.api import api_bp
from app.blueprints.employees.repository import EmployeeRepository
from app.blueprints.shift_change.service import ShiftChangeService
from app.utils.response_utils import (
    success_response, error_response, validation_error_response,
    not_found_response, paginated_response
)
from app.utils.jwt_utils import jwt_required
from app.utils.pagination_utils import get_page_args
from app.extensions.limiter import limiter
from app.constants.limits import Limits

_emp  = EmployeeRepository()
_svc  = ShiftChangeService()


def _serialize_shift_request(req) -> dict:
    """Serialize a shift change request."""
    employee_name = ""
    try:
        employee_name = req.employee.full_name if req.employee else ""
    except Exception:
        pass

    return {
        "id": req.id,
        "employee_name": employee_name,
        "employee_code": req.employee.employee_code if req.employee else "",
        "effective_date": req.effective_date.isoformat() if req.effective_date else None,
        "requested_start_time": req.requested_start_time.strftime("%H:%M") if req.requested_start_time else None,
        "requested_end_time": req.requested_end_time.strftime("%H:%M") if req.requested_end_time else None,
        "reason": req.reason or "",
        "remarks": req.remarks or "",
        "status": req.status,
        "reporting_manager_name": req.reporting_manager_name or "",
        "reporting_manager_code": req.reporting_manager_code or "",
        "created_at": req.created_at.isoformat() if hasattr(req, 'created_at') and req.created_at else None,
        "status_badge": _get_status_badge(req.status),
    }


def _get_status_badge(status: str) -> dict:
    badges = {
        "pending":  {"color": "warning",   "label": "Pending"},
        "approved": {"color": "success",   "label": "Approved"},
        "rejected": {"color": "danger",    "label": "Rejected"},
        "returned": {"color": "info",      "label": "Returned"},
        "cancelled": {"color": "secondary", "label": "Cancelled"},
    }
    return badges.get(status, {"color": "secondary", "label": status.title()})


# ── My Current Shift ─────────────────────────────────────────────────

@api_bp.route("/shifts/my-shift", methods=["GET"])
@jwt_required
@limiter.limit(Limits.RateLimit.API_DEFAULT)
def my_current_shift():
    """Get my current active shift."""
    user = g.current_user
    employee = _emp.get_by_user_id(user.id)

    if not employee:
        return error_response(message="Employee profile not found", code="PROFILE_NOT_FOUND", status_code=404)

    from datetime import date  # noqa: PLC0415
    shift_info = _svc.get_employee_current_shift(employee.id)

    if not shift_info:
        return success_response(data=None, message="No shift assigned")

    return success_response(data=shift_info)


# ── Available Shifts ─────────────────────────────────────────────────

@api_bp.route("/shifts/available", methods=["GET"])
@jwt_required
@limiter.limit(Limits.RateLimit.API_DEFAULT)
def available_shifts():
    """Get list of all available shifts."""
    try:
        from app.models.employee_shift_assignment import Shift  # noqa: PLC0415
    except ImportError:
        try:
            from app.models.shift_change_request import Shift  # noqa: PLC0415
        except ImportError:
            pass

    try:
        # Try to get shifts from company model
        from app.models.company import Shift as CompanyShift  # noqa: PLC0415
        shifts = CompanyShift.query.filter_by(is_active=True).all()
        data = [
            {
                "id": s.id,
                "name": s.name,
                "start_time": s.start_time.strftime("%H:%M") if s.start_time else None,
                "end_time": s.end_time.strftime("%H:%M") if s.end_time else None,
                "duration_hours": s.duration_hours if hasattr(s, 'duration_hours') else None,
            }
            for s in shifts
        ]
        return success_response(data={"shifts": data})
    except Exception:
        return success_response(data={"shifts": []})


# ── My Shift Change Requests ─────────────────────────────────────────

@api_bp.route("/shifts/requests", methods=["GET"])
@jwt_required
@limiter.limit(Limits.RateLimit.API_DEFAULT)
def my_shift_requests():
    """Get my shift change requests with pagination."""
    user = g.current_user
    employee = _emp.get_by_user_id(user.id)

    if not employee:
        return error_response(message="Employee profile not found", code="PROFILE_NOT_FOUND", status_code=404)

    page, per_page = get_page_args()
    status = request.args.get("status", "")

    try:
        from app.models.shift_change_request import ShiftChangeRequest  # noqa: PLC0415

        query = ShiftChangeRequest.query.filter_by(employee_id=employee.id)
        if status:
            query = query.filter_by(status=status)

        pagination = query.order_by(
            ShiftChangeRequest.id.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)

        records = [_serialize_shift_request(req) for req in pagination.items]

        return paginated_response(
            items=records,
            total=pagination.total,
            page=pagination.page,
            per_page=pagination.per_page,
        )
    except Exception as e:
        return success_response(data=[], message="No shift requests found")


# ── Submit Shift Change Request ──────────────────────────────────────

@api_bp.route("/shifts/request-change", methods=["POST"])
@jwt_required
@limiter.limit("20 per hour")
def request_shift_change():
    """
    Submit a shift change request.
    
    Request Body:
        {
            "current_shift_id": 1,
            "requested_start_time": "08:00",
            "requested_end_time": "17:00",
            "effective_date": "2024-08-01",
            "reason": "Personal reasons",
            "reporting_manager_code": "E-2510001"
        }
    """
    from datetime import date, datetime  # noqa: PLC0415

    user = g.current_user
    employee = _emp.get_by_user_id(user.id)

    if not employee:
        return error_response(message="Employee profile not found", code="PROFILE_NOT_FOUND", status_code=404)

    data = request.get_json() or {}

    # Parse times
    try:
        start_time = datetime.strptime(data.get("requested_start_time", ""), "%H:%M").time()
    except (ValueError, TypeError):
        return validation_error_response({"requested_start_time": "Invalid time format. Use HH:MM"})

    try:
        end_time = datetime.strptime(data.get("requested_end_time", ""), "%H:%M").time()
    except (ValueError, TypeError):
        return validation_error_response({"requested_end_time": "Invalid time format. Use HH:MM"})

    # Parse effective date
    try:
        effective_date = date.fromisoformat(data.get("effective_date", ""))
    except (ValueError, TypeError):
        return validation_error_response({"effective_date": "Invalid date format. Use YYYY-MM-DD"})

    mgr_code = data.get("reporting_manager_code", "").strip().upper()
    if not mgr_code:
        return validation_error_response({"reporting_manager_code": "Reporting manager code is required"})

    success, message, request_id = _svc.submit_shift_change_request(
        employee_id=employee.id,
        current_shift_id=data.get("current_shift_id"),
        requested_start_time=start_time,
        requested_end_time=end_time,
        effective_date=effective_date,
        reason=data.get("reason", "").strip(),
        reporting_manager_code=mgr_code,
        remarks=data.get("remarks", "").strip(),
        requested_shift_id=data.get("requested_shift_id"),
    )

    if not success:
        return error_response(message=message, code="SHIFT_REQUEST_FAILED")

    return success_response(
        data={"request_id": request_id},
        message=message
    )


# ── Cancel Shift Request ─────────────────────────────────────────────

@api_bp.route("/shifts/<int:request_id>/cancel", methods=["POST"])
@jwt_required
@limiter.limit("30 per hour")
def cancel_shift_request(request_id: int):
    """Cancel a pending shift change request."""
    user = g.current_user
    employee = _emp.get_by_user_id(user.id)

    if not employee:
        return error_response(message="Employee profile not found", code="PROFILE_NOT_FOUND", status_code=404)

    success, message = _svc.cancel_request(request_id, employee.id)

    if not success:
        return error_response(message=message, code="CANCEL_FAILED")

    return success_response(message=message)


# ── Manager: Pending Shift Approvals ────────────────────────────────

@api_bp.route("/shifts/approvals", methods=["GET"])
@jwt_required
@limiter.limit(Limits.RateLimit.API_DEFAULT)
def shift_approvals():
    """Get pending shift change requests for approval."""
    user = g.current_user
    employee = _emp.get_by_user_id(user.id)

    if not employee:
        return error_response(message="Employee profile not found", code="PROFILE_NOT_FOUND", status_code=404)

    page, per_page = get_page_args()

    try:
        from app.models.shift_change_request import ShiftChangeRequest  # noqa: PLC0415

        # Find requests where this employee's user_id is the current approver
        query = ShiftChangeRequest.query.filter_by(
            current_approver_user_id=user.id,
            status="pending"
        )

        pagination = query.order_by(
            ShiftChangeRequest.id.asc()
        ).paginate(page=page, per_page=per_page, error_out=False)

        records = [_serialize_shift_request(req) for req in pagination.items]

        return paginated_response(
            items=records,
            total=pagination.total,
            page=pagination.page,
            per_page=pagination.per_page,
        )
    except Exception as e:
        return success_response(data=[], message="No pending approvals")


# ── Manager: Approve / Reject ────────────────────────────────────────

@api_bp.route("/shifts/<int:request_id>/approve", methods=["POST"])
@jwt_required
@limiter.limit("60 per hour")
def approve_shift_request(request_id: int):
    """
    Approve a shift change request.
    
    Request Body:
        {
            "remarks": "Approved as requested"
        }
    """
    user = g.current_user
    data = request.get_json() or {}
    remarks = data.get("remarks", "Approved").strip()

    success, message = _svc.approve_request(request_id, user.id, remarks, action="approve")

    if not success:
        return error_response(message=message, code="APPROVAL_FAILED")

    return success_response(message=message)


@api_bp.route("/shifts/<int:request_id>/reject", methods=["POST"])
@jwt_required
@limiter.limit("60 per hour")
def reject_shift_request(request_id: int):
    """
    Reject a shift change request.
    
    Request Body:
        {
            "remarks": "Reason for rejection (required)"
        }
    """
    user = g.current_user
    data = request.get_json() or {}
    remarks = data.get("remarks", "").strip()

    if not remarks:
        return validation_error_response({"remarks": "Rejection reason is required"})

    success, message = _svc.approve_request(request_id, user.id, remarks, action="reject")

    if not success:
        return error_response(message=message, code="REJECTION_FAILED")

    return success_response(message=message)


# ── Shift History ────────────────────────────────────────────────────

@api_bp.route("/shifts/history", methods=["GET"])
@jwt_required
@limiter.limit(Limits.RateLimit.API_DEFAULT)
def shift_history():
    """Get shift assignment history for current employee."""
    user = g.current_user
    employee = _emp.get_by_user_id(user.id)

    if not employee:
        return error_response(message="Employee profile not found", code="PROFILE_NOT_FOUND", status_code=404)

    page, per_page = get_page_args()

    try:
        from app.models.employee_shift_assignment import EmployeeShiftAssignment  # noqa: PLC0415

        pagination = EmployeeShiftAssignment.query.filter_by(
            employee_id=employee.id
        ).order_by(
            EmployeeShiftAssignment.effective_from.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)

        records = []
        for assignment in pagination.items:
            shift = assignment.shift if hasattr(assignment, 'shift') else None
            records.append({
                "id": assignment.id,
                "shift_name": shift.name if shift else "",
                "start_time": shift.start_time.strftime("%H:%M") if shift and shift.start_time else None,
                "end_time": shift.end_time.strftime("%H:%M") if shift and shift.end_time else None,
                "effective_from": assignment.effective_from.isoformat() if assignment.effective_from else None,
                "effective_until": assignment.effective_until.isoformat() if assignment.effective_until else None,
                "is_current": assignment.effective_until is None,
                "reason": assignment.reason or "",
            })

        return paginated_response(
            items=records,
            total=pagination.total,
            page=pagination.page,
            per_page=pagination.per_page,
        )
    except Exception as e:
        return success_response(data=[], message="No shift history found")
