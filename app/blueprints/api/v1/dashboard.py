"""
blueprints/api/v1/dashboard.py
================================
Dashboard REST API endpoints for mobile app.

Endpoints:
    GET /api/v1/dashboard                 - Complete dashboard summary
    GET /api/v1/dashboard/attendance      - Today's attendance status
    GET /api/v1/dashboard/leave-balance   - Leave balance
    GET /api/v1/dashboard/chart           - 6-month attendance chart data
"""

from datetime import date, datetime
from flask import g

from app.blueprints.api import api_bp
from app.blueprints.attendance.repository import AttendanceRepository
from app.blueprints.employees.repository import EmployeeRepository
from app.blueprints.leave.repository import LeaveRepository
from app.blueprints.leave.service import LeaveService
from app.utils.response_utils import success_response, error_response
from app.utils.jwt_utils import jwt_required
from app.extensions.limiter import limiter
from app.constants.limits import Limits

_emp   = EmployeeRepository()
_att   = AttendanceRepository()
_leave = LeaveRepository()
_lsvc  = LeaveService()


def _serialize_attendance(att, office=None) -> dict:
    """Serialize today's attendance record."""
    if not att:
        return {
            "status": "not_marked",
            "check_in_time": None,
            "check_out_time": None,
            "is_late": False,
            "late_minutes": 0,
            "working_hours": None,
            "is_early_leave": False,
        }

    import pytz  # noqa: PLC0415
    IST = pytz.timezone("Asia/Kolkata")

    def to_ist(dt):
        if not dt:
            return None
        if dt.tzinfo is None:
            dt = pytz.UTC.localize(dt)
        return dt.astimezone(IST).strftime("%H:%M")

    return {
        "id": att.id,
        "date": att.date.isoformat() if att.date else None,
        "status": att.status,
        "check_in_time": to_ist(att.check_in_time),
        "check_out_time": to_ist(att.check_out_time),
        "is_late": att.is_late or False,
        "late_minutes": att.late_minutes or 0,
        "working_hours": att.working_hours_display if att.check_out_time else None,
        "overtime_minutes": att.overtime_minutes or 0,
        "is_early_leave": att.is_early_leave or False,
    }


# ── Dashboard Summary ────────────────────────────────────────────────

@api_bp.route("/dashboard", methods=["GET"])
@jwt_required
@limiter.limit(Limits.RateLimit.API_DEFAULT)
def dashboard():
    """
    Complete dashboard summary for mobile home screen.
    
    Returns today's attendance, leave balance, recent activity, quick actions.
    """
    user = g.current_user
    employee = _emp.get_by_user_id(user.id)
    
    if not employee:
        return error_response(
            message="Employee profile not found",
            code="PROFILE_NOT_FOUND",
            status_code=404
        )
    
    today = date.today()
    
    # Today's attendance
    today_att = None
    try:
        today_att = _att.get_today(employee.id, today)
    except Exception:
        pass
    
    # Office settings
    office = None
    try:
        office = _att.get_office_for_employee(employee)
    except Exception:
        pass
    
    # Leave balances
    balances = []
    try:
        balances = _lsvc.get_balance(employee.id)
    except Exception:
        pass
    
    # Pending leave count
    pending_leaves = 0
    try:
        pagination = _leave.get_employee_requests(employee.id, page=1, per_page=1)
        pending_leaves = LeaveRequest_pending_count(employee.id)
    except Exception:
        pass
    
    # Recent attendance (last 5 records)
    recent_attendance = []
    try:
        history = _att.get_history(employee.id, page=1, per_page=5)
        for att in history.items:
            recent_attendance.append({
                "date": att.date.isoformat(),
                "status": att.status,
                "check_in_time": att.check_in_time.strftime("%H:%M") if att.check_in_time else None,
                "check_out_time": att.check_out_time.strftime("%H:%M") if att.check_out_time else None,
                "is_late": att.is_late or False,
            })
    except Exception:
        pass
    
    # Build quick actions based on today's status
    quick_actions = _build_quick_actions(today_att)
    
    # Check if can check in / check out
    can_check_in = (
        not today_att or 
        (today_att and not today_att.check_in_time)
    )
    can_check_out = (
        today_att and 
        today_att.check_in_time and 
        not today_att.check_out_time
    )
    
    data = {
        "employee": {
            "id": employee.id,
            "employee_code": employee.employee_code,
            "full_name": employee.full_name,
            "department": employee.department,
            "designation": employee.designation,
            "profile_photo": employee.profile_photo,
            "shift_name": employee.shift_name,
        },
        "today": {
            "date": today.isoformat(),
            "day_name": today.strftime("%A"),
            "formatted": today.strftime("%d %B %Y"),
        },
        "attendance": {
            "today": _serialize_attendance(today_att, office),
            "can_check_in": can_check_in,
            "can_check_out": can_check_out,
            "office": {
                "name": office.name if office else None,
                "radius_metres": office.radius_metres if office else None,
                "latitude": float(office.latitude) if office and office.latitude else None,
                "longitude": float(office.longitude) if office and office.longitude else None,
            } if office else None,        },
        "leave": {
            "balances": [
                {
                    "leave_type": b.get("type").name if b.get("type") else "",
                    "leave_type_code": b.get("type").code if b.get("type") else "",
                    "allowed": b.get("max", 0),
                    "taken": b.get("taken", 0),
                    "available": b.get("available", 0),
                    "is_unlimited": b.get("is_unlimited", False),
                }
                for b in balances
            ],
            "pending_requests": pending_leaves,
        },
        "recent_attendance": recent_attendance,
        "quick_actions": quick_actions,
    }
    
    return success_response(data=data)


# ── Today's Attendance ───────────────────────────────────────────────

@api_bp.route("/dashboard/attendance", methods=["GET"])
@jwt_required
@limiter.limit(Limits.RateLimit.API_DEFAULT)
def dashboard_attendance():
    """Today's attendance status with office settings."""
    user = g.current_user
    employee = _emp.get_by_user_id(user.id)
    
    if not employee:
        return error_response(message="Employee profile not found", code="PROFILE_NOT_FOUND", status_code=404)
    
    today = date.today()
    today_att = _att.get_today(employee.id, today)
    office = _att.get_office_for_employee(employee)
    
    return success_response(data={
        "attendance": _serialize_attendance(today_att, office),
        "can_check_in": not today_att or (today_att and not today_att.check_in_time),
        "can_check_out": bool(today_att and today_att.check_in_time and not today_att.check_out_time),
        "office": {
            "name": office.name if office else None,
            "latitude": float(office.latitude) if office and office.latitude else None,
            "longitude": float(office.longitude) if office and office.longitude else None,
            "radius_metres": office.radius_metres if office else 200,
            "allow_gps_override": office.allow_gps_override if office else False,
        } if office else None,
    })


# ── Leave Balance ────────────────────────────────────────────────────

@api_bp.route("/dashboard/leave-balance", methods=["GET"])
@jwt_required
@limiter.limit(Limits.RateLimit.API_DEFAULT)
def dashboard_leave_balance():
    """Leave balance summary."""
    user = g.current_user
    employee = _emp.get_by_user_id(user.id)
    
    if not employee:
        return error_response(message="Employee profile not found", code="PROFILE_NOT_FOUND", status_code=404)
    
    try:
        balances = _lsvc.get_balance(employee.id)
    except Exception:
        balances = []
    
    return success_response(data={
        "balances": [
            {
                "leave_type": b.get("type").name if b.get("type") else "",
                "leave_type_code": b.get("type").code if b.get("type") else "",
                "allowed": b.get("max", 0),
                "taken": b.get("taken", 0),
                "available": b.get("available", 0),
                "is_unlimited": b.get("is_unlimited", False),
            }
            for b in balances
        ],
        "year": date.today().year,
    })


# ── Attendance Chart Data ─────────────────────────────────────────────

@api_bp.route("/dashboard/chart", methods=["GET"])
@jwt_required
@limiter.limit(Limits.RateLimit.API_DEFAULT)
def dashboard_chart():
    """6-month attendance chart data for mobile app graphs."""
    user = g.current_user
    employee = _emp.get_by_user_id(user.id)
    
    if not employee:
        return error_response(message="Employee profile not found", code="PROFILE_NOT_FOUND", status_code=404)
    
    from sqlalchemy import extract, func  # noqa: PLC0415
    from app.extensions.database import db  # noqa: PLC0415
    from app.models.attendance import Attendance  # noqa: PLC0415
    
    today = date.today()
    labels, present, absent, on_leave = [], [], [], []
    
    for i in range(5, -1, -1):
        month = today.month - i
        year = today.year
        while month <= 0:
            month += 12
            year -= 1
        
        labels.append(datetime(year, month, 1).strftime("%b '%y"))
        
        base_q = db.session.query(func.count(Attendance.id)).filter(
            Attendance.employee_id == employee.id,
            Attendance.is_deleted == False,
            extract("year", Attendance.date) == year,
            extract("month", Attendance.date) == month,
        )
        present.append(int(base_q.filter(Attendance.status == "present").scalar() or 0))
        absent.append(int(base_q.filter(Attendance.status == "absent").scalar() or 0))
        on_leave.append(int(base_q.filter(Attendance.status == "on_leave").scalar() or 0))
    
    return success_response(data={
        "labels": labels,
        "datasets": {
            "present": present,
            "absent": absent,
            "on_leave": on_leave,
        }
    })


# ── Helpers ──────────────────────────────────────────────────────────

def LeaveRequest_pending_count(employee_id: int) -> int:
    """Count pending leave requests for employee."""
    try:
        from app.models.leave import LeaveRequest  # noqa: PLC0415
        return LeaveRequest.query.filter_by(
            employee_id=employee_id, status="pending", is_deleted=False
        ).count()
    except Exception:
        return 0


def _build_quick_actions(today_att) -> list:
    """Build list of quick action buttons based on attendance state."""
    actions = []
    
    can_check_in = not today_att or (today_att and not today_att.check_in_time)
    can_check_out = bool(today_att and today_att.check_in_time and not today_att.check_out_time)
    
    if can_check_in:
        actions.append({
            "id": "check_in",
            "label": "Check In",
            "icon": "login",
            "color": "success",
            "route": "/attendance",
        })
    
    if can_check_out:
        actions.append({
            "id": "check_out",
            "label": "Check Out",
            "icon": "logout",
            "color": "warning",
            "route": "/attendance",
        })
    
    actions.extend([
        {"id": "apply_leave", "label": "Apply Leave", "icon": "event_busy", "color": "info", "route": "/leave/apply"},
        {"id": "my_leaves", "label": "My Leaves", "icon": "calendar_today", "color": "primary", "route": "/leave"},
        {"id": "my_profile", "label": "My Profile", "icon": "person", "color": "secondary", "route": "/profile"},
    ])
    
    return actions
