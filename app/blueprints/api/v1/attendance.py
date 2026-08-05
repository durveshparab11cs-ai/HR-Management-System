"""
blueprints/api/v1/attendance.py
================================
Attendance REST API endpoints for mobile app.

Endpoints:
    GET  /api/v1/attendance/today         - Today's attendance status
    POST /api/v1/attendance/check-in      - Check in with GPS + photo
    POST /api/v1/attendance/check-out     - Check out with GPS + photo
    POST /api/v1/attendance/upload-photo  - Upload check-in proof photo
    POST /api/v1/attendance/upload-checkout-photo - Upload check-out photo
    GET  /api/v1/attendance/history       - Attendance history (paginated)
    GET  /api/v1/attendance/office        - Office/GPS settings
"""

import base64
from datetime import date
from io import BytesIO

from flask import g, request

from app.blueprints.api import api_bp
from app.blueprints.attendance.repository import AttendanceRepository
from app.blueprints.attendance.service import AttendanceService
from app.blueprints.employees.repository import EmployeeRepository
from app.utils.response_utils import (
    success_response, error_response, validation_error_response, paginated_response
)
from app.utils.jwt_utils import jwt_required
from app.utils.pagination_utils import get_page_args
from app.utils.filter_utils import get_date_range_params, get_status_filter
from app.extensions.limiter import limiter
from app.constants.limits import Limits

_emp  = EmployeeRepository()
_att  = AttendanceRepository()
_svc  = AttendanceService()


def _serialize_attendance_record(att) -> dict:
    """Serialize a single attendance record for API response."""
    import pytz  # noqa: PLC0415
    IST = pytz.timezone("Asia/Kolkata")

    def fmt_time(dt):
        if not dt:
            return None
        if dt.tzinfo is None:
            dt = pytz.UTC.localize(dt)
        return dt.astimezone(IST).strftime("%H:%M")

    def fmt_time_full(dt):
        if not dt:
            return None
        if dt.tzinfo is None:
            dt = pytz.UTC.localize(dt)
        return dt.astimezone(IST).strftime("%H:%M:%S")

    return {
        "id": att.id,
        "date": att.date.isoformat(),
        "status": att.status,
        "check_in_time": fmt_time(att.check_in_time),
        "check_out_time": fmt_time(att.check_out_time),
        "check_in_time_full": fmt_time_full(att.check_in_time),
        "check_out_time_full": fmt_time_full(att.check_out_time),
        "is_late": att.is_late or False,
        "late_minutes": att.late_minutes or 0,
        "is_early_leave": att.is_early_leave or False,
        "working_hours": att.working_hours_display if att.check_out_time else None,
        "overtime_minutes": att.overtime_minutes or 0,
        "check_in_distance_metres": round(att.check_in_distance_metres or 0, 1),
        "check_out_distance_metres": round(att.check_out_distance_metres or 0, 1) if att.check_out_distance_metres else None,
    }


# ── Today's Attendance ───────────────────────────────────────────────

@api_bp.route("/attendance/today", methods=["GET"])
@jwt_required
@limiter.limit(Limits.RateLimit.API_DEFAULT)
def attendance_today():
    """
    Get today's attendance status.
    
    Response:
        {
            "success": true,
            "data": {
                "attendance": { ... },
                "can_check_in": true,
                "can_check_out": false,
                "has_checkin_photo": false,
                "has_checkout_photo": false
            }
        }
    """
    user = g.current_user
    employee = _emp.get_by_user_id(user.id)
    
    if not employee:
        return error_response(message="Employee profile not found", code="PROFILE_NOT_FOUND", status_code=404)
    
    today = date.today()
    today_att = _att.get_today(employee.id, today)
    
    # Check photo status
    has_checkin_photo = False
    has_checkout_photo = False
    
    if today_att and today_att.id:
        from app.models.attendance_photo import AttendancePhoto  # noqa: PLC0415
        photo = AttendancePhoto.query.filter_by(attendance_id=today_att.id).first()
        if photo:
            has_checkin_photo = bool(photo.image_data or photo.file_path)
            has_checkout_photo = bool(photo.checkout_image_data)
    
    return success_response(data={
        "attendance": _serialize_attendance_record(today_att) if today_att else None,
        "can_check_in": not today_att or (today_att and not today_att.check_in_time),
        "can_check_out": bool(today_att and today_att.check_in_time and not today_att.check_out_time),
        "has_checkin_photo": has_checkin_photo,
        "has_checkout_photo": has_checkout_photo,
        "date": today.isoformat(),
    })


# ── Check In ─────────────────────────────────────────────────────────

@api_bp.route("/attendance/check-in", methods=["POST"])
@jwt_required
@limiter.limit("30 per hour")
def check_in():
    """
    Mark check-in with GPS coordinates.
    
    Photo can be uploaded before or after check-in.
    
    Request Body:
        {
            "latitude": "19.0760",
            "longitude": "72.8777",
            "accuracy": "10.5"
        }
    
    Response:
        {
            "success": true,
            "data": {
                "check_in_time": "09:15",
                "is_late": false,
                "late_minutes": 0,
                "distance_metres": 45.2,
                "message": "Check-in recorded at 09:15 IST."
            }
        }
    """
    user = g.current_user
    employee = _emp.get_by_user_id(user.id)
    
    if not employee:
        return error_response(message="Employee profile not found", code="PROFILE_NOT_FOUND", status_code=404)
    
    data = request.get_json() or {}
    
    lat = str(data.get("latitude", "")).strip()
    lon = str(data.get("longitude", "")).strip()
    acc = str(data.get("accuracy", "")).strip()
    
    if not lat or not lon:
        return validation_error_response({
            "latitude": "Latitude is required" if not lat else None,
            "longitude": "Longitude is required" if not lon else None,
        })
    
    # Perform check-in (photo is optional at check-in time)
    ok, message, attendance, gps_detail = _svc.check_in(employee, lat, lon, acc)
    
    if not ok:
        return error_response(
            message=message,
            code="CHECKIN_FAILED",
            details={"gps": gps_detail} if gps_detail else None
        )
    
    import pytz  # noqa: PLC0415
    IST = pytz.timezone("Asia/Kolkata")
    ist_time = attendance.check_in_time.replace(tzinfo=pytz.UTC).astimezone(IST)
    
    return success_response(
        data={
            "check_in_time": ist_time.strftime("%H:%M"),
            "is_late": attendance.is_late or False,
            "late_minutes": attendance.late_minutes or 0,
            "distance_metres": round(gps_detail.get("distance_metres", 0), 1) if gps_detail else 0,
            "attendance_id": attendance.id,
        },
        message=message
    )


# ── Check Out ────────────────────────────────────────────────────────

@api_bp.route("/attendance/check-out", methods=["POST"])
@jwt_required
@limiter.limit("30 per hour")
def check_out():
    """
    Mark check-out with GPS coordinates.
    
    Note: Checkout photo must be uploaded first via /attendance/upload-checkout-photo.
    
    Request Body:
        {
            "latitude": "19.0760",
            "longitude": "72.8777",
            "accuracy": "10.5"
        }
    """
    user = g.current_user
    employee = _emp.get_by_user_id(user.id)
    
    if not employee:
        return error_response(message="Employee profile not found", code="PROFILE_NOT_FOUND", status_code=404)
    
    data = request.get_json() or {}
    
    lat = str(data.get("latitude", "")).strip()
    lon = str(data.get("longitude", "")).strip()
    acc = str(data.get("accuracy", "")).strip()
    
    if not lat or not lon:
        return validation_error_response({
            "latitude": "Latitude is required" if not lat else None,
            "longitude": "Longitude is required" if not lon else None,
        })
    
    # Validate checkout photo
    today = date.today()
    attendance_today = _att.get_today(employee.id, today)
    
    if not attendance_today or not attendance_today.check_in_time:
        return error_response(
            message="No check-in found for today. Please check in first.",
            code="NOT_CHECKED_IN"
        )
    
    from app.models.attendance_photo import AttendancePhoto  # noqa: PLC0415
    photo = AttendancePhoto.query.filter_by(attendance_id=attendance_today.id).first()
    if not photo or not photo.checkout_image_data:
        return error_response(
            message="Checkout photo is required. Please upload a selfie first.",
            code="PHOTO_REQUIRED"
        )
    
    # Perform check-out
    ok, message, attendance, gps_detail = _svc.check_out(employee, lat, lon, acc)
    
    if not ok:
        return error_response(
            message=message,
            code="CHECKOUT_FAILED",
            details={"gps": gps_detail} if gps_detail else None
        )
    
    import pytz  # noqa: PLC0415
    IST = pytz.timezone("Asia/Kolkata")
    ist_time = attendance.check_out_time.replace(tzinfo=pytz.UTC).astimezone(IST)
    
    return success_response(
        data={
            "check_out_time": ist_time.strftime("%H:%M"),
            "working_hours": attendance.working_hours_display,
            "overtime_minutes": attendance.overtime_minutes or 0,
            "distance_metres": round(gps_detail.get("distance_metres", 0), 1) if gps_detail else 0,
        },
        message=message
    )


# ── Upload Check-in Photo ────────────────────────────────────────────

@api_bp.route("/attendance/upload-photo", methods=["POST"])
@jwt_required
@limiter.limit("60 per hour")
def upload_checkin_photo():
    """
    Upload check-in proof photo.
    
    Accepts multipart/form-data with 'photo' field.
    
    Response:
        {
            "success": true,
            "data": {
                "has_photo": true,
                "can_check_in": true
            }
        }
    """
    user = g.current_user
    employee = _emp.get_by_user_id(user.id)
    
    if not employee:
        return error_response(message="Employee profile not found", code="PROFILE_NOT_FOUND", status_code=404)
    
    file = request.files.get("photo")
    if not file:
        return validation_error_response({"photo": "Photo file is required"})
    
    ok, message, photo = _svc.upload_photo(employee, file)
    
    if not ok:
        return error_response(message=message, code="PHOTO_UPLOAD_FAILED")
    
    today = date.today()
    attendance_today = _att.get_today(employee.id, today)
    
    return success_response(
        data={
            "has_photo": True,
            "can_check_in": bool(
                attendance_today and
                not attendance_today.check_in_time
            ),
        },
        message=message
    )


# ── Upload Check-out Photo ───────────────────────────────────────────

@api_bp.route("/attendance/upload-checkout-photo", methods=["POST"])
@jwt_required
@limiter.limit("60 per hour")
def upload_checkout_photo():
    """
    Upload check-out proof photo.
    
    Accepts multipart/form-data with 'photo' field.
    """
    user = g.current_user
    employee = _emp.get_by_user_id(user.id)
    
    if not employee:
        return error_response(message="Employee profile not found", code="PROFILE_NOT_FOUND", status_code=404)
    
    file = request.files.get("photo")
    if not file:
        return validation_error_response({"photo": "Photo file is required"})
    
    ok, message, photo = _svc.upload_checkout_photo(employee, file)
    
    if not ok:
        return error_response(message=message, code="PHOTO_UPLOAD_FAILED")
    
    today = date.today()
    attendance_today = _att.get_today(employee.id, today)
    
    return success_response(
        data={
            "has_photo": True,
            "can_check_out": bool(
                attendance_today and
                attendance_today.check_in_time and
                not attendance_today.check_out_time
            ),
        },
        message=message
    )


# ── Attendance History ───────────────────────────────────────────────

@api_bp.route("/attendance/history", methods=["GET"])
@jwt_required
@limiter.limit(Limits.RateLimit.API_DEFAULT)
def attendance_history():
    """
    Get paginated attendance history.
    
    Query Parameters:
        page: Page number (default: 1)
        per_page: Records per page (default: 20, max: 100)
        start_date: Filter from date (YYYY-MM-DD)
        end_date: Filter to date (YYYY-MM-DD)
        status: Filter by status (present/absent/on_leave/holiday/weekend)
    
    Response:
        {
            "success": true,
            "data": [ ... attendance records ... ],
            "meta": {
                "page": 1,
                "per_page": 20,
                "total": 245,
                "pages": 13,
                "has_next": true,
                "has_prev": false
            }
        }
    """
    user = g.current_user
    employee = _emp.get_by_user_id(user.id)
    
    if not employee:
        return error_response(message="Employee profile not found", code="PROFILE_NOT_FOUND", status_code=404)
    
    page, per_page = get_page_args()
    start_date, end_date = get_date_range_params()
    status = get_status_filter()
    
    pagination = _att.get_history_filtered(
        employee_id=employee.id,
        start_date=start_date,
        end_date=end_date,
        status=status or "",
        page=page,
        per_page=per_page,
    )
    
    records = [_serialize_attendance_record(att) for att in pagination.items]
    
    return paginated_response(
        items=records,
        total=pagination.total,
        page=pagination.page,
        per_page=pagination.per_page,
    )


# ── Office Settings ──────────────────────────────────────────────────

@api_bp.route("/attendance/office", methods=["GET"])
@jwt_required
@limiter.limit(Limits.RateLimit.API_DEFAULT)
def attendance_office():
    """
    Get office settings for GPS validation.
    
    Response:
        {
            "success": true,
            "data": {
                "name": "Main Office",
                "latitude": 19.076,
                "longitude": 72.877,
                "radius_metres": 200,
                "allow_gps_override": false,
                "shift_start": "09:00",
                "shift_end": "18:00",
                "late_threshold_minutes": 15
            }
        }
    """
    user = g.current_user
    employee = _emp.get_by_user_id(user.id)
    
    if not employee:
        return error_response(message="Employee profile not found", code="PROFILE_NOT_FOUND", status_code=404)
    
    office = _att.get_office_for_employee(employee)
    
    if not office:
        return error_response(message="No office configuration found", code="NO_OFFICE_CONFIG", status_code=404)
    
    return success_response(data={
        "id": office.id,
        "name": office.name,
        "latitude": float(office.latitude) if office.latitude else None,
        "longitude": float(office.longitude) if office.longitude else None,
        "radius_metres": office.radius_metres or 200,
        "allow_remote_checkin": office.allow_remote_checkin,
        "selfie_required": office.selfie_required,
        "office_start_time": office.office_start_time.strftime("%H:%M") if office.office_start_time else "09:00",
        "office_end_time": office.office_end_time.strftime("%H:%M") if office.office_end_time else "18:00",
        "grace_period_minutes": office.grace_period_minutes or 10,
        "min_gps_accuracy_metres": office.min_gps_accuracy_metres,
        "auto_checkout_enabled": office.auto_checkout_enabled,
        "half_day_threshold_minutes": office.half_day_threshold_minutes,
    })
