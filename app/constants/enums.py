"""
app/constants/enums.py
=======================
Application-wide enumeration types.

All domain enumerations are defined here using Python's standard
enum.Enum (or enum.IntEnum for database-stored integers).

Rules:
    - Use string enums for human-readable database storage.
    - Never use bare magic strings in application code — use these enums.
    - Add new values here; never scatter enum-like strings across the codebase.
"""

import enum


class UserRole(str, enum.Enum):
    """
    System-level user roles controlling access permissions.

    Stored as string in the database for readability and safe migration.
    """
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    HR_MANAGER = "hr_manager"
    HR_STAFF = "hr_staff"
    MANAGER = "manager"
    EMPLOYEE = "employee"
    GUEST = "guest"


class UserStatus(str, enum.Enum):
    """
    Lifecycle status of a user account.
    """
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"
    LOCKED = "locked"


class EmploymentType(str, enum.Enum):
    """
    Type of employment contract.
    """
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERN = "intern"
    TEMPORARY = "temporary"
    FREELANCE = "freelance"


class Gender(str, enum.Enum):
    """
    Employee gender options.
    """
    MALE = "male"
    FEMALE = "female"
    NON_BINARY = "non_binary"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


class MaritalStatus(str, enum.Enum):
    """
    Employee marital status.
    """
    SINGLE = "single"
    MARRIED = "married"
    DIVORCED = "divorced"
    WIDOWED = "widowed"
    SEPARATED = "separated"


class DepartmentStatus(str, enum.Enum):
    """
    Operational status of a department.
    """
    ACTIVE = "active"
    INACTIVE = "inactive"
    RESTRUCTURING = "restructuring"


class AttendanceStatus(str, enum.Enum):
    """
    Daily attendance record status.
    """
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    HALF_DAY = "half_day"
    WORK_FROM_HOME = "work_from_home"
    ON_LEAVE = "on_leave"
    HOLIDAY = "holiday"
    WEEKEND = "weekend"


class LeaveType(str, enum.Enum):
    """
    Categories of employee leave.
    """
    ANNUAL = "annual"
    SICK = "sick"
    MATERNITY = "maternity"
    PATERNITY = "paternity"
    UNPAID = "unpaid"
    EMERGENCY = "emergency"
    COMPENSATORY = "compensatory"
    STUDY = "study"
    BEREAVEMENT = "bereavement"


class LeaveStatus(str, enum.Enum):
    """
    Approval workflow status for leave requests.
    """
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    WITHDRAWN = "withdrawn"


class PayrollStatus(str, enum.Enum):
    """
    Payroll processing and payment status.
    """
    DRAFT = "draft"
    PROCESSING = "processing"
    PROCESSED = "processed"
    APPROVED = "approved"
    PAID = "paid"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"


class NotificationChannel(str, enum.Enum):
    """
    Delivery channel for notifications.
    """
    IN_APP = "in_app"
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"


class NotificationStatus(str, enum.Enum):
    """
    Read/delivery status of a notification.
    """
    UNREAD = "unread"
    READ = "read"
    ARCHIVED = "archived"


class AuditAction(str, enum.Enum):
    """
    Categories of auditable actions for the audit log.
    """
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    PASSWORD_CHANGE = "password_change"
    PASSWORD_RESET = "password_reset"
    PERMISSION_CHANGE = "permission_change"
    EXPORT = "export"
    IMPORT = "import"
    APPROVE = "approve"
    REJECT = "reject"


class Department(str, enum.Enum):
    """
    Canonical department list used for login validation and access control.
    """
    CEO           = "CEO"
    PROPRIETOR    = "Proprietor"
    AGM           = "AGM"
    OPERATIONS    = "Operations"
    BDM           = "BDM"
    CLAIM         = "Claim"
    MIS           = "MIS"
    DATA_ANALYTICS = "Data Analytics"
    HR            = "HR"
    ADMIN         = "Admin"
    ACCOUNTS      = "Accounts"
    IT_HARDWARE   = "IT Hardware"
    IT_SOFTWARE   = "IT Software"
    FOSS          = "FOSS"
    SOCIAL_MEDIA  = "Social Media"


# Departments that can see ALL departments (no filter applied)
GLOBAL_ACCESS_DEPARTMENTS = {
    Department.CEO.value,
    Department.PROPRIETOR.value,
    Department.AGM.value,
    Department.ADMIN.value,
}

# Department → label list for the login dropdown
DEPARTMENT_CHOICES = [(d.value, d.value) for d in Department]
