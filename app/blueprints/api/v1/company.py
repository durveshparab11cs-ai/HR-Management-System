"""
blueprints/api/v1/company.py
================================
Company Master Data REST API endpoints for mobile app.

Master Data - Single Source of Truth

All master data (departments, positions, shifts) is stored in PostgreSQL
and served via these API endpoints. Both website and mobile app use these
same endpoints to fetch master data. This ensures:

1. Single database (no SQLite, Hive, or duplicate data)
2. Single source of truth (always in PostgreSQL)
3. Real-time synchronization (changes immediately visible in both apps)
4. No hardcoded lists in Flutter

Endpoints:
    GET  /api/v1/company/departments    - List all departments (master data)
    GET  /api/v1/company/positions      - List all positions (master data)
    GET  /api/v1/company/shifts         - List all shifts (master data)
"""

from flask import g, request

from app.blueprints.api import api_bp
from app.blueprints.company.service import CompanyService
from app.utils.response_utils import success_response, error_response
from app.utils.jwt_utils import jwt_required
from app.extensions.limiter import limiter
from app.constants.limits import Limits

_svc = CompanyService()


# ── Get All Departments (Master Data) ──────────────────────────────────

@api_bp.route("/company/departments", methods=["GET"])
@limiter.limit(Limits.DEFAULT)
@jwt_required
def get_departments():
    """
    Get all active departments.

    Master Data Endpoint - Single Source of Truth
    =============================================
    Returns all departments stored in PostgreSQL.
    Both website and Flutter use this endpoint.
    No hardcoded lists in Flutter.

    Returns:
        {
            "status": "success",
            "data": [
                {
                    "id": 1,
                    "name": "Medical",
                    "code": "MED",
                    "description": "Medical department",
                    "color": "#1a3c6e",
                    "is_active": true
                },
                ...
            ]
        }
    """
    try:
        departments = _svc.get_all_departments()
        return success_response(
            [
                {
                    "id": d.id,
                    "name": d.name,
                    "code": d.code,
                    "description": d.description,
                    "color": d.color,
                    "is_active": d.is_active,
                }
                for d in departments
            ]
        )
    except Exception as e:
        return error_response(f"Failed to fetch departments: {e}", 500)


# ── Get All Positions (Master Data) ────────────────────────────────────

@api_bp.route("/company/positions", methods=["GET"])
@limiter.limit(Limits.DEFAULT)
@jwt_required
def get_positions():
    """
    Get all active positions.

    Master Data Endpoint - Single Source of Truth
    =============================================
    Returns all positions stored in PostgreSQL.
    Both website and Flutter use this endpoint.

    Query Parameters:
        department_id (optional): Filter by department

    Returns:
        {
            "status": "success",
            "data": [
                {
                    "id": 1,
                    "title": "Senior Doctor",
                    "code": "SD001",
                    "department_id": 1,
                    "grade": "A",
                    "description": "Senior medical professional",
                    "is_active": true
                },
                ...
            ]
        }
    """
    try:
        positions = _svc.get_all_positions()
        return success_response(
            [
                {
                    "id": p.id,
                    "title": p.title,
                    "code": p.code,
                    "department_id": p.department_id,
                    "grade": p.grade,
                    "description": p.description,
                    "is_active": p.is_active,
                }
                for p in positions
            ]
        )
    except Exception as e:
        return error_response(f"Failed to fetch positions: {e}", 500)


# ── Get All Shifts (Master Data) ───────────────────────────────────────

@api_bp.route("/company/shifts", methods=["GET"])
@limiter.limit(Limits.DEFAULT)
@jwt_required
def get_shifts():
    """
    Get all active shifts.

    Master Data Endpoint - Single Source of Truth
    =============================================
    Returns all shifts stored in PostgreSQL.
    Both website and Flutter use this endpoint.
    No hardcoded shift types in Flutter.

    Returns:
        {
            "status": "success",
            "data": [
                {
                    "id": 1,
                    "name": "Morning Shift",
                    "code": "MORN",
                    "type": "morning",
                    "start_time": "06:00",
                    "end_time": "14:00",
                    "grace_minutes": 10,
                    "break_minutes": 60,
                    "working_days": "Mon-Fri",
                    "is_night_shift": false,
                    "is_active": true
                },
                ...
            ]
        }
    """
    try:
        shifts = _svc.get_all_shifts()
        return success_response(
            [
                {
                    "id": s.id,
                    "name": s.name,
                    "code": s.code,
                    "type": s.code.lower(),
                    "start_time": s.start_time.strftime("%H:%M") if hasattr(s.start_time, 'strftime') else str(s.start_time),
                    "end_time": s.end_time.strftime("%H:%M") if hasattr(s.end_time, 'strftime') else str(s.end_time),
                    "grace_minutes": s.grace_minutes,
                    "break_minutes": s.break_minutes,
                    "working_days": s.working_days,
                    "is_night_shift": s.is_night_shift,
                    "is_active": s.is_active,
                }
                for s in shifts
            ]
        )
    except Exception as e:
        return error_response(f"Failed to fetch shifts: {e}", 500)


# ── Get Department Statistics ──────────────────────────────────────────

@api_bp.route("/company/department-stats", methods=["GET"])
@limiter.limit(Limits.DEFAULT)
@jwt_required
def get_department_stats():
    """
    Get department-wise employee count statistics.

    Returns:
        {
            "status": "success",
            "data": [
                {
                    "name": "Medical",
                    "color": "#1a3c6e",
                    "count": 25
                },
                ...
            ]
        }
    """
    try:
        stats = _svc.get_department_stats()
        return success_response(stats)
    except Exception as e:
        return error_response(f"Failed to fetch stats: {e}", 500)
