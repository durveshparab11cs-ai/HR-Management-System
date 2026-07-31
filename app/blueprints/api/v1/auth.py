"""
blueprints/api/v1/auth.py
==========================
Authentication REST API endpoints for mobile app.

Provides JWT-based authentication with access and refresh tokens.

Endpoints:
    POST /api/v1/auth/login              - Login with employee_code + password
    POST /api/v1/auth/refresh            - Refresh access token
    POST /api/v1/auth/logout             - Logout (invalidate session)
    POST /api/v1/auth/forgot-password    - Request password reset
    POST /api/v1/auth/reset-password     - Reset password with token
    GET  /api/v1/auth/me                 - Get current user info
    GET  /api/v1/auth/lookup-employee    - Look up employee by code
"""

from flask import request, g
from app.blueprints.api import api_bp
from app.blueprints.authentication.service import AuthService
from app.utils.response_utils import (
    success_response,
    error_response,
    validation_error_response,
    unauthorized_response
)
from app.utils.jwt_utils import (
    generate_access_token,
    generate_refresh_token,
    jwt_required,
    refresh_access_token as refresh_token_util
)
from app.constants.limits import Limits
from app.extensions.limiter import limiter

_auth_svc = AuthService()


# ── Login ────────────────────────────────────────────────────────────

@api_bp.route("/auth/login", methods=["POST"])
@limiter.limit(Limits.RateLimit.LOGIN)
def login():
    """
    Login endpoint for mobile app.
    
    Request Body:
        {
            "employee_code": "E-2510016",
            "password": "password123",
            "department": "IT",
            "device_info": {
                "device_id": "unique_device_id",
                "device_name": "iPhone 12",
                "device_type": "ios",
                "app_version": "1.0.0"
            }
        }
    
    Response:
        {
            "success": true,
            "message": "Login successful",
            "data": {
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                "token_type": "Bearer",
                "expires_in": 86400,
                "user": {
                    "id": 1,
                    "email": "user@example.com",
                    "full_name": "John Doe",
                    "employee_code": "E-2510016",
                    "role": "employee",
                    "department": "IT",
                    "is_admin": false
                }
            }
        }
    """
    data = request.get_json()
    
    if not data:
        return validation_error_response({"error": "Request body is required"})
    
    # Validate required fields
    employee_code = data.get("employee_code", "").strip()
    password = data.get("password", "")
    department = data.get("department", "").strip()
    
    errors = {}
    if not employee_code:
        errors["employee_code"] = "Employee code is required"
    if not password:
        errors["password"] = "Password is required"
    if not department:
        errors["department"] = "Department is required"
    
    if errors:
        return validation_error_response(errors)
    
    # Attempt login using existing AuthService
    success, message, user = _auth_svc.attempt_login(
        employee_code=employee_code,
        password=password,
        department=department,
        remember=False  # Not applicable for API
    )
    
    if not success:
        return unauthorized_response(message=message or "Invalid credentials")
    
    # Get employee details
    from app.models.employee import Employee
    employee = Employee.query.filter_by(user_id=user.id, is_deleted=False).first()
    
    # Generate JWT tokens
    access_token = generate_access_token(
        user_id=user.id,
        employee_code=employee.employee_code if employee else None
    )
    refresh_token = generate_refresh_token(user_id=user.id)
    
    # Build user response data
    user_data = {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "employee_code": employee.employee_code if employee else None,
        "role": user.role,
        "department": employee.department if employee else None,
        "designation": employee.designation if employee else None,
        "branch": employee.branch if employee else None,
        "shift_name": employee.shift_name if employee else None,
        "is_admin": user.role in ["admin", "hr"],
        "profile_photo": employee.profile_photo if employee else None,
    }
    
    response_data = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer",
        "expires_in": 86400,  # 24 hours in seconds
        "user": user_data
    }
    
    return success_response(
        data=response_data,
        message="Login successful"
    )


# ── Refresh Token ────────────────────────────────────────────────────

@api_bp.route("/auth/refresh", methods=["POST"])
@limiter.limit(Limits.RateLimit.API_DEFAULT)
def refresh():
    """
    Refresh access token using refresh token.
    
    Request Body:
        {
            "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
        }
    
    Response:
        {
            "success": true,
            "data": {
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                "token_type": "Bearer",
                "expires_in": 86400
            }
        }
    """
    data = request.get_json()
    
    if not data or not data.get("refresh_token"):
        return validation_error_response({"refresh_token": "Refresh token is required"})
    
    refresh_token = data.get("refresh_token")
    
    # Refresh access token
    success, new_access_token, error_msg = refresh_token_util(refresh_token)
    
    if not success:
        return unauthorized_response(message=error_msg or "Invalid refresh token")
    
    return success_response(data={
        "access_token": new_access_token,
        "token_type": "Bearer",
        "expires_in": 86400
    })


# ── Logout ───────────────────────────────────────────────────────────

@api_bp.route("/auth/logout", methods=["POST"])
@jwt_required
@limiter.limit(Limits.RateLimit.API_DEFAULT)
def logout():
    """
    Logout endpoint (for cleanup on client side).
    
    Since JWT is stateless, actual logout happens on client by removing tokens.
    This endpoint can be used for cleanup operations like removing FCM tokens.
    
    Request Headers:
        Authorization: Bearer <access_token>
    
    Request Body (optional):
        {
            "fcm_token": "firebase_token_to_remove"
        }
    
    Response:
        {
            "success": true,
            "message": "Logged out successfully"
        }
    """
    data = request.get_json() or {}
    fcm_token = data.get("fcm_token")
    
    # Remove FCM token if provided
    if fcm_token:
        try:
            from app.blueprints.notifications.service import NotificationService
            notif_svc = NotificationService()
            notif_svc.deactivate_fcm_token(fcm_token)
        except Exception as e:
            # Log but don't fail logout
            from flask import current_app
            current_app.logger.error(f"Failed to deactivate FCM token: {str(e)}")
    
    return success_response(message="Logged out successfully")


# ── Get Current User ─────────────────────────────────────────────────

@api_bp.route("/auth/me", methods=["GET"])
@jwt_required
@limiter.limit(Limits.RateLimit.API_DEFAULT)
def me():
    """
    Get current authenticated user's profile.
    
    Request Headers:
        Authorization: Bearer <access_token>
    
    Response:
        {
            "success": true,
            "data": {
                "id": 1,
                "email": "user@example.com",
                "full_name": "John Doe",
                "employee_code": "E-2510016",
                "department": "IT",
                "designation": "Software Engineer",
                "role": "employee",
                "profile_photo": "profile_123.jpg",
                "employee_details": {
                    "date_of_joining": "2024-01-15",
                    "reporting_manager": "Manager Name",
                    "hospital": "Hospital Name"
                }
            }
        }
    """
    user = g.current_user
    
    # Get employee details
    from app.models.employee import Employee
    employee = Employee.query.filter_by(user_id=user.id, is_deleted=False).first()
    
    if not employee:
        return error_response(
            message="Employee profile not found",
            code="PROFILE_NOT_FOUND",
            status_code=404
        )
    
    # Build response
    user_data = {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "employee_code": employee.employee_code,
        "department": employee.department,
        "designation": employee.designation,
        "role": user.role,
        "profile_photo": employee.profile_photo,
        "is_admin": user.role in ["admin", "hr"],
        "employee_details": {
            "date_of_joining": employee.date_joined.isoformat() if employee.date_joined else None,
            "date_of_birth": employee.date_of_birth.isoformat() if employee.date_of_birth else None,
            "gender": employee.gender,
            "mobile": employee.mobile,
            "personal_email": employee.personal_email,
            "address": employee.address,
            "emergency_contact_name": employee.emergency_contact_name,
            "emergency_contact_phone": employee.emergency_contact_phone,
            "branch": employee.branch,
            "employment_type": employee.employment_type,
            "nationality": employee.nationality,
            "shift_name": employee.shift_name,
        }
    }
    
    return success_response(data=user_data)


# ── Forgot Password ──────────────────────────────────────────────────

@api_bp.route("/auth/forgot-password", methods=["POST"])
@limiter.limit(Limits.RateLimit.PASSWORD_RESET)
def forgot_password():
    """
    Request password reset token.
    
    Request Body:
        {
            "employee_code": "E-2510016"
        }
    
    Response:
        {
            "success": true,
            "message": "Password reset token generated",
            "data": {
                "reset_token": "abc123xyz..."
            }
        }
    
    Note: In production, the token should be sent via email.
    For now, it's returned in the response for testing.
    """
    data = request.get_json()
    
    if not data or not data.get("employee_code"):
        return validation_error_response({"employee_code": "Employee code is required"})
    
    employee_code = data.get("employee_code", "").strip()
    
    # Generate reset token
    success, token_or_error = _auth_svc.initiate_password_reset(employee_code)
    
    if not success:
        return error_response(message=token_or_error, code="PASSWORD_RESET_FAILED")
    
    # In production, send token via email
    # For now, return it in response
    return success_response(
        data={"reset_token": token_or_error},
        message="Password reset token generated. Please check your email."
    )


# ── Reset Password ───────────────────────────────────────────────────

@api_bp.route("/auth/reset-password", methods=["POST"])
@limiter.limit(Limits.RateLimit.PASSWORD_RESET)
def reset_password():
    """
    Reset password with token.
    
    Request Body:
        {
            "reset_token": "abc123xyz...",
            "new_password": "newpassword123",
            "confirm_password": "newpassword123"
        }
    
    Response:
        {
            "success": true,
            "message": "Password reset successfully"
        }
    """
    data = request.get_json()
    
    if not data:
        return validation_error_response({"error": "Request body is required"})
    
    reset_token = data.get("reset_token", "").strip()
    new_password = data.get("new_password", "")
    confirm_password = data.get("confirm_password", "")
    
    # Validation
    errors = {}
    if not reset_token:
        errors["reset_token"] = "Reset token is required"
    if not new_password:
        errors["new_password"] = "New password is required"
    if not confirm_password:
        errors["confirm_password"] = "Confirm password is required"
    if new_password and confirm_password and new_password != confirm_password:
        errors["confirm_password"] = "Passwords do not match"
    if new_password and len(new_password) < 6:
        errors["new_password"] = "Password must be at least 6 characters"
    
    if errors:
        return validation_error_response(errors)
    
    # Reset password
    success, message = _auth_svc.reset_password(reset_token, new_password)
    
    if not success:
        return error_response(message=message, code="PASSWORD_RESET_FAILED")
    
    return success_response(message=message)


# ── Lookup Employee ──────────────────────────────────────────────────

@api_bp.route("/auth/lookup-employee", methods=["GET"])
@limiter.limit(Limits.RateLimit.API_DEFAULT)
def lookup_employee():
    """
    Look up employee details by employee code.
    Used during registration to verify employee exists in master data.
    
    Query Parameters:
        code: Employee code (e.g., E-2510016)
    
    Response:
        {
            "success": true,
            "data": {
                "found": true,
                "employee_code": "E-2510016",
                "name": "John Doe",
                "department": "IT",
                "designation": "Software Engineer"
            }
        }
    """
    code = request.args.get("code", "").strip().upper()
    
    if not code:
        return validation_error_response({"code": "Employee code is required"})
    
    # Lookup employee
    found, message, data = _auth_svc.lookup_employee(code)
    
    if not found:
        return success_response(data={
            "found": False,
            "message": message
        })
    
    return success_response(data={
        "found": True,
        "employee_code": code,
        "name": data.get("name"),
        "department": data.get("department"),
        "designation": data.get("designation", ""),
        "message": message
    })
