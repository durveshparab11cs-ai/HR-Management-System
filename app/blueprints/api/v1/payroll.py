"""
blueprints/api/v1/payroll.py
==============================
Payroll REST API endpoints for mobile app.

Endpoints:
    GET /api/v1/payroll/payslips          - My payslips (paginated)
    GET /api/v1/payroll/payslips/latest   - Latest payslip
    GET /api/v1/payroll/payslips/<id>     - Payslip details
"""

from flask import g

from app.blueprints.api import api_bp
from app.blueprints.employees.repository import EmployeeRepository
from app.utils.response_utils import (
    success_response, error_response, not_found_response, paginated_response
)
from app.utils.jwt_utils import jwt_required
from app.utils.pagination_utils import get_page_args
from app.extensions.limiter import limiter
from app.constants.limits import Limits

_emp = EmployeeRepository()


def _serialize_payslip(payroll) -> dict:
    """Serialize a payroll/payslip record."""
    return {
        "id": payroll.id,
        "month": payroll.month if hasattr(payroll, 'month') else None,
        "year": payroll.year if hasattr(payroll, 'year') else None,
        "pay_period": f"{getattr(payroll, 'month', '')} {getattr(payroll, 'year', '')}".strip(),
        "basic_salary": float(getattr(payroll, 'basic_salary', 0) or 0),
        "gross_salary": float(getattr(payroll, 'gross_salary', 0) or 0),
        "net_salary": float(getattr(payroll, 'net_salary', 0) or 0),
        "deductions": float(getattr(payroll, 'total_deductions', 0) or 0),
        "allowances": float(getattr(payroll, 'total_allowances', 0) or 0),
        "days_worked": getattr(payroll, 'days_worked', 0) or 0,
        "days_absent": getattr(payroll, 'days_absent', 0) or 0,
        "status": getattr(payroll, 'status', 'generated'),
        "generated_on": payroll.created_at.isoformat() if hasattr(payroll, 'created_at') and payroll.created_at else None,
    }


# ── My Payslips ──────────────────────────────────────────────────────

@api_bp.route("/payroll/payslips", methods=["GET"])
@jwt_required
@limiter.limit(Limits.RateLimit.API_DEFAULT)
def my_payslips():
    """
    Get paginated payslips for current employee.
    
    Query Parameters:
        page, per_page, year
    """
    user = g.current_user
    employee = _emp.get_by_user_id(user.id)

    if not employee:
        return error_response(message="Employee profile not found", code="PROFILE_NOT_FOUND", status_code=404)

    page, per_page = get_page_args()

    try:
        from app.models.payroll import Payroll  # noqa: PLC0415
        from flask import request  # noqa: PLC0415

        query = Payroll.query.filter_by(employee_id=employee.id, is_deleted=False)

        year = request.args.get("year", type=int)
        if year:
            query = query.filter(Payroll.year == year)

        # Try ordering by year and month
        try:
            query = query.order_by(Payroll.year.desc(), Payroll.month.desc())
        except Exception:
            query = query.order_by(Payroll.id.desc())

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        records = [_serialize_payslip(p) for p in pagination.items]

        return paginated_response(
            items=records,
            total=pagination.total,
            page=pagination.page,
            per_page=pagination.per_page,
        )

    except Exception as e:
        return success_response(data=[], message="No payslips available")


# ── Latest Payslip ───────────────────────────────────────────────────

@api_bp.route("/payroll/payslips/latest", methods=["GET"])
@jwt_required
@limiter.limit(Limits.RateLimit.API_DEFAULT)
def latest_payslip():
    """Get the most recent payslip."""
    user = g.current_user
    employee = _emp.get_by_user_id(user.id)

    if not employee:
        return error_response(message="Employee profile not found", code="PROFILE_NOT_FOUND", status_code=404)

    try:
        from app.models.payroll import Payroll  # noqa: PLC0415

        payslip = Payroll.query.filter_by(
            employee_id=employee.id, is_deleted=False
        ).order_by(Payroll.id.desc()).first()

        if not payslip:
            return success_response(data=None, message="No payslips found")

        return success_response(data=_serialize_payslip(payslip))

    except Exception as e:
        return success_response(data=None, message="No payslips available")


# ── Payslip Detail ───────────────────────────────────────────────────

@api_bp.route("/payroll/payslips/<int:payslip_id>", methods=["GET"])
@jwt_required
@limiter.limit(Limits.RateLimit.API_DEFAULT)
def payslip_detail(payslip_id: int):
    """Get detailed payslip by ID."""
    user = g.current_user
    employee = _emp.get_by_user_id(user.id)

    if not employee:
        return error_response(message="Employee profile not found", code="PROFILE_NOT_FOUND", status_code=404)

    try:
        from app.models.payroll import Payroll  # noqa: PLC0415

        payslip = Payroll.query.filter_by(
            id=payslip_id, employee_id=employee.id, is_deleted=False
        ).first()

        if not payslip:
            return not_found_response("Payslip")

        data = _serialize_payslip(payslip)

        # Add extra detail fields if available
        for field in ['hra', 'da', 'ta', 'pf', 'esi', 'tds', 'other_allowances', 'other_deductions']:
            if hasattr(payslip, field):
                data[field] = float(getattr(payslip, field) or 0)

        return success_response(data=data)

    except Exception as e:
        return not_found_response("Payslip")
