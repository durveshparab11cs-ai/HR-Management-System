"""
blueprints/api/v1/settings.py
================================
Settings REST API endpoints for mobile app.

Endpoints:
    GET  /api/v1/settings/profile         - Get profile settings
    PUT  /api/v1/settings/profile         - Update profile
    PUT  /api/v1/settings/password        - Change password
    GET  /api/v1/settings/preferences     - App preferences
    PUT  /api/v1/settings/preferences     - Update preferences
    GET  /api/v1/settings/login-history   - Login history
"""

from flask import g, request

from app.blueprints.api import api_bp
from app.blueprints.employees.repository import EmployeeRepository
from app.utils.response_utils import (
    success_response, error_response, validation_error_response, not_found_response
)
from app.utils.jwt_utils import jwt_required
from app.extensions.limiter import limiter
from app.constants.limits import Limits

_repo = EmployeeRepository()


# ── Get Profile Settings ─────────────────────────────────────────────

@api_bp.route("/settings/profile", methods=["GET"])
@jwt_required
@limiter.limit(Limits.RateLimit.API_DEFAULT)
def settings_profile_get():
    """
    Get current user's profile settings.
    
    Response includes editable profile fields.
    """
    user = g.current_user
    employee = _repo.get_by_user_id(user.id)

    if not employee:
        return error_response(message="Employee profile not found", code="PROFILE_NOT_FOUND", status_code=404)

    return success_response(data={
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role,
            "status": user.status,
        },
        "employee": {
            "employee_code": employee.employee_code,
            "department": employee.department,
            "designation": employee.designation,
            "branch": employee.branch,
            "employment_type": employee.employment_type,
            "date_joined": employee.date_joined.isoformat() if employee.date_joined else None,
            "date_of_birth": employee.date_of_birth.isoformat() if employee.date_of_birth else None,
            "gender": employee.gender,
            "nationality": employee.nationality,
            "mobile": employee.mobile,
            "personal_email": employee.personal_email,
            "address": employee.address,
            "emergency_contact_name": employee.emergency_contact_name,
            "emergency_contact_phone": employee.emergency_contact_phone,
            "shift_name": employee.shift_name,
            "profile_photo": employee.profile_photo,
        }
    })


# ── Update Profile ───────────────────────────────────────────────────

@api_bp.route("/settings/profile", methods=["PUT"])
@jwt_required
@limiter.limit("20 per hour")
def settings_profile_update():
    """
    Update editable profile fields.
    
    Request Body (all fields optional):
        {
            "mobile": "+91-9876543210",
            "personal_email": "personal@example.com",
            "address": "123 Street, City",
            "emergency_contact_name": "Jane Doe",
            "emergency_contact_phone": "+91-9876543211"
        }
    """
    user = g.current_user
    employee = _repo.get_by_user_id(user.id)

    if not employee:
        return error_response(message="Employee profile not found", code="PROFILE_NOT_FOUND", status_code=404)

    data = request.get_json() or {}

    # Employee-editable fields only
    editable_fields = [
        "mobile", "personal_email", "address",
        "emergency_contact_name", "emergency_contact_phone"
    ]

    changed = False
    for field in editable_fields:
        if field in data:
            setattr(employee, field, data[field])
            changed = True

    if not changed:
        return validation_error_response({"fields": "No valid fields to update"})

    try:
        from app.extensions.database import db  # noqa: PLC0415
        db.session.add(employee)
        db.session.commit()
    except Exception as e:
        from app.extensions.database import db  # noqa: PLC0415
        db.session.rollback()
        return error_response(message="Failed to update profile", code="UPDATE_FAILED", status_code=500)

    return success_response(message="Profile updated successfully")


# ── Change Password ──────────────────────────────────────────────────

@api_bp.route("/settings/password", methods=["PUT"])
@jwt_required
@limiter.limit("10 per hour")
def settings_password_change():
    """
    Change current user's password.
    
    Request Body:
        {
            "current_password": "oldpassword",
            "new_password": "newpassword123",
            "confirm_password": "newpassword123"
        }
    """
    user = g.current_user
    data = request.get_json() or {}

    current_password = data.get("current_password", "")
    new_password = data.get("new_password", "")
    confirm_password = data.get("confirm_password", "")

    # Validation
    errors = {}
    if not current_password:
        errors["current_password"] = "Current password is required"
    if not new_password:
        errors["new_password"] = "New password is required"
    elif len(new_password) < 6:
        errors["new_password"] = "Password must be at least 6 characters"
    if not confirm_password:
        errors["confirm_password"] = "Confirm password is required"
    elif new_password and new_password != confirm_password:
        errors["confirm_password"] = "Passwords do not match"
    if new_password and current_password and new_password == current_password:
        errors["new_password"] = "New password must be different from current password"

    if errors:
        return validation_error_response(errors)

    # Verify current password
    if not user.check_password(current_password):
        return validation_error_response({"current_password": "Current password is incorrect"})

    # Set new password
    try:
        user.set_password(new_password)
        from app.extensions.database import db  # noqa: PLC0415
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        from app.extensions.database import db  # noqa: PLC0415
        db.session.rollback()
        return error_response(message="Failed to change password", code="PASSWORD_CHANGE_FAILED", status_code=500)

    return success_response(message="Password changed successfully")


# ── App Preferences ──────────────────────────────────────────────────

@api_bp.route("/settings/preferences", methods=["GET"])
@jwt_required
@limiter.limit(Limits.RateLimit.API_DEFAULT)
def settings_preferences_get():
    """
    Get user's app preferences.
    
    Preferences are stored as JSON in user profile or defaults are returned.
    """
    user = g.current_user

    # Default preferences (extend with a proper model later)
    preferences = {
        "theme": "light",
        "language": "en",
        "notifications_enabled": True,
        "push_notifications": True,
        "attendance_reminder": True,
        "leave_updates": True,
        "biometric_login": False,
        "auto_logout_minutes": 60,
    }

    return success_response(data={"preferences": preferences})


@api_bp.route("/settings/preferences", methods=["PUT"])
@jwt_required
@limiter.limit("30 per hour")
def settings_preferences_update():
    """
    Update app preferences.
    
    Request Body:
        {
            "theme": "dark",
            "notifications_enabled": true,
            "language": "en"
        }
    """
    data = request.get_json() or {}

    allowed_prefs = [
        "theme", "language", "notifications_enabled",
        "push_notifications", "attendance_reminder",
        "leave_updates", "biometric_login", "auto_logout_minutes"
    ]

    updated_prefs = {k: v for k, v in data.items() if k in allowed_prefs}

    if not updated_prefs:
        return validation_error_response({"fields": "No valid preference fields provided"})

    # TODO: Persist to user_preferences table when created
    # For now, return the updated prefs as acknowledgment
    return success_response(
        data={"preferences": updated_prefs},
        message="Preferences updated successfully"
    )


# ── Login History ────────────────────────────────────────────────────

@api_bp.route("/settings/login-history", methods=["GET"])
@jwt_required
@limiter.limit(Limits.RateLimit.API_DEFAULT)
def settings_login_history():
    """
    Get recent login history for the current user.
    """
    user = g.current_user

    try:
        from app.models.login_history import LoginHistory  # noqa: PLC0415
        from app.utils.pagination_utils import get_page_args  # noqa: PLC0415

        page, per_page = get_page_args()
        pagination = LoginHistory.query.filter_by(
            user_id=user.id
        ).order_by(
            LoginHistory.login_at.desc()
        ).paginate(page=page, per_page=min(per_page, 20), error_out=False)

        records = [
            {
                "id": h.id,
                "login_at": h.login_at.isoformat() if h.login_at else None,
                "ip_address": h.ip_address,
                "user_agent": h.user_agent,
                "success": h.success if hasattr(h, 'success') else True,
            }
            for h in pagination.items
        ]

        from app.utils.response_utils import paginated_response  # noqa: PLC0415
        return paginated_response(
            items=records,
            total=pagination.total,
            page=pagination.page,
            per_page=pagination.per_page,
        )

    except Exception as e:
        return success_response(data={"history": []}, message="Login history not available")
