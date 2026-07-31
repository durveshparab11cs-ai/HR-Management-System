"""
blueprints/api/v1/employees.py
================================
Employee REST API endpoints for mobile app.

Endpoints:
    GET  /api/v1/employees/me            - My profile
    PUT  /api/v1/employees/me            - Update my profile
    POST /api/v1/employees/me/photo      - Upload profile photo
    GET  /api/v1/employees/me/documents  - My documents
    GET  /api/v1/employees               - List employees (admin/hr)
    GET  /api/v1/employees/<id>          - Get employee details (admin/hr)
"""

import os
from flask import g, request, current_app

from app.blueprints.api import api_bp
from app.blueprints.employees.repository import EmployeeRepository
from app.utils.response_utils import (
    success_response, error_response, validation_error_response,
    not_found_response, paginated_response
)
from app.utils.jwt_utils import jwt_required
from app.utils.pagination_utils import get_page_args
from app.utils.filter_utils import get_search_param
from app.extensions.limiter import limiter
from app.constants.limits import Limits

_repo = EmployeeRepository()


def _serialize_employee(emp) -> dict:
    """Serialize employee with all details."""
    user = emp.user
    
    return {
        "id": emp.id,
        "employee_code": emp.employee_code,
        "full_name": emp.full_name,
        "first_name": user.first_name if user else "",
        "last_name": user.last_name if user else "",
        "email": user.email if user else "",
        "department": emp.department,
        "designation": emp.designation,
        "branch": emp.branch,
        "employment_type": emp.employment_type,
        "gender": emp.gender,
        "nationality": emp.nationality,
        "mobile": emp.mobile,
        "personal_email": emp.personal_email,
        "address": emp.address,
        "date_joined": emp.date_joined.isoformat() if emp.date_joined else None,
        "date_of_birth": emp.date_of_birth.isoformat() if emp.date_of_birth else None,
        "shift_name": emp.shift_name,
        "profile_photo": emp.profile_photo,
        "emergency_contact_name": emp.emergency_contact_name,
        "emergency_contact_phone": emp.emergency_contact_phone,
        "role": user.role if user else "employee",
        "status": user.status if user else "active",
        "is_admin": user.role in ["admin", "super_admin", "hr_manager", "hr_staff"] if user else False,
    }


def _serialize_employee_basic(emp) -> dict:
    """Serialize employee with minimal details for list view."""
    return {
        "id": emp.id,
        "employee_code": emp.employee_code,
        "full_name": emp.full_name,
        "department": emp.department,
        "designation": emp.designation,
        "branch": emp.branch,
        "profile_photo": emp.profile_photo,
        "shift_name": emp.shift_name,
    }


# ── My Profile ───────────────────────────────────────────────────────

@api_bp.route("/employees/me", methods=["GET"])
@jwt_required
@limiter.limit(Limits.RateLimit.API_DEFAULT)
def my_profile():
    """Get current user's employee profile."""
    user = g.current_user
    employee = _repo.get_by_user_id(user.id)
    
    if not employee:
        return error_response(
            message="Employee profile not found",
            code="PROFILE_NOT_FOUND",
            status_code=404
        )
    
    # Get additional data from employee_master
    master_data = {}
    try:
        from app.models.employee_master import EmployeeMaster  # noqa: PLC0415
        master = EmployeeMaster.query.filter_by(
            employee_code=employee.employee_code
        ).first()
        if master:
            master_data = {
                "reporting_manager": master.reporting_manager,
                "hospital_name": master.hospital_name,
                "hospital_code": master.hospital_code,
            }
    except Exception:
        pass
    
    data = _serialize_employee(employee)
    data.update(master_data)
    
    return success_response(data=data)


# ── Update My Profile ────────────────────────────────────────────────

@api_bp.route("/employees/me", methods=["PUT"])
@jwt_required
@limiter.limit("20 per hour")
def update_my_profile():
    """
    Update my profile (allowed fields only).
    
    Request Body:
        {
            "mobile": "+91-9876543210",
            "personal_email": "personal@gmail.com",
            "address": "123 Main Street, Mumbai",
            "emergency_contact_name": "Jane Doe",
            "emergency_contact_phone": "+91-9876543211"
        }
    """
    user = g.current_user
    employee = _repo.get_by_user_id(user.id)
    
    if not employee:
        return error_response(message="Employee profile not found", code="PROFILE_NOT_FOUND", status_code=404)
    
    data = request.get_json() or {}
    
    # Only allow specific fields to be updated by employee
    allowed_fields = [
        "mobile", "personal_email", "address",
        "emergency_contact_name", "emergency_contact_phone"
    ]
    
    updated = False
    for field in allowed_fields:
        if field in data:
            setattr(employee, field, data[field])
            updated = True
    
    if not updated:
        return validation_error_response({"fields": "No valid fields provided to update"})
    
    try:
        from app.extensions.database import db  # noqa: PLC0415
        db.session.add(employee)
        db.session.commit()
    except Exception as e:
        from app.extensions.database import db  # noqa: PLC0415
        db.session.rollback()
        current_app.logger.error(f"Profile update failed: {str(e)}")
        return error_response(message="Failed to update profile", code="UPDATE_FAILED", status_code=500)
    
    return success_response(
        data=_serialize_employee(employee),
        message="Profile updated successfully"
    )


# ── Upload Profile Photo ─────────────────────────────────────────────

@api_bp.route("/employees/me/photo", methods=["POST"])
@jwt_required
@limiter.limit("10 per hour")
def upload_profile_photo():
    """
    Upload profile photo.
    
    Accepts multipart/form-data with 'photo' field.
    """
    user = g.current_user
    employee = _repo.get_by_user_id(user.id)
    
    if not employee:
        return error_response(message="Employee profile not found", code="PROFILE_NOT_FOUND", status_code=404)
    
    file = request.files.get("photo")
    if not file:
        return validation_error_response({"photo": "Photo file is required"})
    
    # Validate file type
    allowed_types = {"image/jpeg", "image/png", "image/jpg", "image/webp"}
    if file.content_type not in allowed_types:
        return validation_error_response({"photo": "Only JPEG, PNG, and WebP images are allowed"})
    
    # Save photo
    try:
        from werkzeug.utils import secure_filename  # noqa: PLC0415
        import uuid  # noqa: PLC0415
        
        ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'jpg'
        filename = f"profile_{employee.employee_code}_{uuid.uuid4().hex[:8]}.{ext}"
        
        upload_dir = os.path.join(current_app.static_folder, "uploads", "profiles")
        os.makedirs(upload_dir, exist_ok=True)
        
        # Delete old photo
        if employee.profile_photo:
            old_path = os.path.join(upload_dir, employee.profile_photo)
            if os.path.exists(old_path):
                os.remove(old_path)
        
        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)
        
        # Update employee record
        employee.profile_photo = f"uploads/profiles/{filename}"
        
        from app.extensions.database import db  # noqa: PLC0415
        db.session.add(employee)
        db.session.commit()
        
        return success_response(
            data={
                "profile_photo": employee.profile_photo,
                "photo_url": f"/static/{employee.profile_photo}",
            },
            message="Profile photo updated successfully"
        )
    except Exception as e:
        current_app.logger.error(f"Photo upload failed: {str(e)}")
        return error_response(message="Failed to upload photo", code="UPLOAD_FAILED", status_code=500)


# ── Employee List (Admin/HR) ─────────────────────────────────────────

@api_bp.route("/employees", methods=["GET"])
@jwt_required
@limiter.limit(Limits.RateLimit.API_DEFAULT)
def employee_list():
    """
    Get paginated employee list. Admin/HR only.
    
    Query Parameters:
        page, per_page, search, department, status
    """
    user = g.current_user
    
    # Only admin/HR can list all employees
    if user.role not in ["admin", "super_admin", "hr_manager", "hr_staff"]:
        return error_response(message="Admin access required", code="FORBIDDEN", status_code=403)
    
    page, per_page = get_page_args()
    search = get_search_param()
    
    from app.models.employee import Employee  # noqa: PLC0415
    from app.models.user import User  # noqa: PLC0415
    
    query = Employee.query.filter_by(is_deleted=False).join(User, Employee.user_id == User.id)
    
    if search:
        query = query.filter(
            (Employee.employee_code.ilike(f"%{search}%")) |
            (User.first_name.ilike(f"%{search}%")) |
            (User.last_name.ilike(f"%{search}%")) |
            (Employee.department.ilike(f"%{search}%")) |
            (Employee.designation.ilike(f"%{search}%"))
        )
    
    department = request.args.get("department")
    if department:
        query = query.filter(Employee.department == department)
    
    pagination = query.order_by(Employee.employee_code.asc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    records = [_serialize_employee_basic(emp) for emp in pagination.items]
    
    return paginated_response(
        items=records,
        total=pagination.total,
        page=pagination.page,
        per_page=pagination.per_page,
    )


# ── Employee Details (Admin/HR) ──────────────────────────────────────

@api_bp.route("/employees/<int:emp_id>", methods=["GET"])
@jwt_required
@limiter.limit(Limits.RateLimit.API_DEFAULT)
def employee_detail(emp_id: int):
    """Get employee details by ID. Admin/HR or own profile only."""
    user = g.current_user
    
    from app.models.employee import Employee  # noqa: PLC0415
    employee = Employee.query.filter_by(id=emp_id, is_deleted=False).first()
    
    if not employee:
        return not_found_response("Employee")
    
    # Own profile or admin/HR
    is_admin = user.role in ["admin", "super_admin", "hr_manager", "hr_staff"]
    if employee.user_id != user.id and not is_admin:
        return error_response(message="Access denied", code="FORBIDDEN", status_code=403)
    
    return success_response(data=_serialize_employee(employee))
