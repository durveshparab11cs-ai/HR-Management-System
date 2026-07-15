"""
app/models/__init__.py
=======================
Model registry — imports all models so Flask-Migrate (Alembic) can
discover them when generating migration scripts.

Every new model module MUST be imported here. Alembic inspects
SQLAlchemy's metadata, which is only populated after model classes
are imported.

Models available:
    User          — authentication and user accounts
    (future models will be added here as modules are built)
"""

from app.models.user import User  # noqa: F401
from app.models.office_settings import OfficeSettings  # noqa: F401
from app.models.employee import Employee  # noqa: F401
from app.models.employee_master import EmployeeMaster  # noqa: F401
from app.models.login_history import LoginHistory  # noqa: F401
from app.models.attendance import Attendance  # noqa: F401
from app.models.attendance_log import AttendanceLog  # noqa: F401
from app.models.attendance_photo import AttendancePhoto  # noqa: F401
from app.models.gps_log import GPSLog  # noqa: F401
from app.models.leave import LeaveType, LeaveRequest, HalfDayRequest, EarlyLeaveRequest  # noqa: F401
from app.models.notification import Notification  # noqa: F401
from app.models.company import CompanyProfile, Department, Position, Shift  # noqa: F401
from app.models.payroll import SalaryStructure, SalaryComponent, PayrollRun, Payslip  # noqa: F401

__all__ = [
    "User", "OfficeSettings", "Employee", "EmployeeMaster", "LoginHistory",
    "Attendance", "AttendanceLog", "AttendancePhoto", "GPSLog",
    "LeaveType", "LeaveRequest", "HalfDayRequest", "EarlyLeaveRequest",
    "Notification",
    "CompanyProfile", "Department", "Position", "Shift",
    "SalaryStructure", "SalaryComponent", "PayrollRun", "Payslip",
]
