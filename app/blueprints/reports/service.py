"""blueprints/reports/service.py — real DB queries for all reports."""

import logging
from datetime import date, datetime, timedelta
from typing import Optional

from app.extensions.database import db
from app.models.attendance import Attendance
from app.models.employee import Employee
from app.models.leave import LeaveRequest
from app.models.user import User
from sqlalchemy import case, cast, extract, func, Integer

logger = logging.getLogger(__name__)


class ReportService:

    # ── Attendance Summary ────────────────────────────────────────────

    def attendance_summary(self, start: date, end: date, department: str = "", employee_id: Optional[int] = None) -> list:
        q = (
            db.session.query(
                Employee, User,
                func.count(Attendance.id).label("total_days"),
                func.sum(case((Attendance.status == "present", 1), else_=0)).label("present"),
                func.sum(case((Attendance.status == "absent",  1), else_=0)).label("absent"),
                func.sum(case((Attendance.status == "half_day",1), else_=0)).label("half_day"),
                func.sum(case((Attendance.status == "on_leave",1), else_=0)).label("on_leave"),
                func.sum(case((Attendance.is_late == True,     1), else_=0)).label("late_days"),
                func.sum(cast(Attendance.working_minutes, Integer)).label("total_minutes"),
            )
            .join(User, Employee.user_id == User.id)
            .outerjoin(Attendance, (Attendance.employee_id == Employee.id) &
                       (Attendance.date >= start) & (Attendance.date <= end) &
                       (Attendance.is_deleted == False))
            .filter(Employee.is_deleted == False)
        )
        if department:
            q = q.filter(Employee.department == department)
        if employee_id:
            q = q.filter(Employee.id == employee_id)
        rows = q.group_by(Employee.id, User.id).order_by(Employee.employee_code).all()
        return [
            {
                "employee": r.Employee,
                "user": r.User,
                "total_days": r.total_days or 0,
                "present": r.present or 0,
                "absent": r.absent or 0,
                "half_day": r.half_day or 0,
                "on_leave": r.on_leave or 0,
                "late_days": r.late_days or 0,
                "total_hours": round((r.total_minutes or 0) / 60, 1),
            }
            for r in rows
        ]

    def daily_attendance(self, for_date: date) -> list:
        rows = (
            db.session.query(Employee, User, Attendance)
            .join(User, Employee.user_id == User.id)
            .outerjoin(Attendance, (Attendance.employee_id == Employee.id) &
                       (Attendance.date == for_date) & (Attendance.is_deleted == False))
            .filter(Employee.is_deleted == False)
            .order_by(Employee.employee_code)
            .all()
        )
        return [{"employee": r.Employee, "user": r.User, "attendance": r.Attendance} for r in rows]

    # ── Leave Summary ─────────────────────────────────────────────────

    def leave_summary(self, year: int) -> list:
        q = (
            db.session.query(
                Employee, User,
                func.count(LeaveRequest.id).label("total_requests"),
                func.sum(case((LeaveRequest.status == "approved", LeaveRequest.total_days), else_=0)).label("approved_days"),
                func.sum(case((LeaveRequest.status == "pending",  1), else_=0)).label("pending_count"),
                func.sum(case((LeaveRequest.status == "rejected", 1), else_=0)).label("rejected_count"),
            )
            .join(User, Employee.user_id == User.id)
            .outerjoin(LeaveRequest, (LeaveRequest.employee_id == Employee.id) &
                       (extract("year", LeaveRequest.start_date) == year) &
                       (LeaveRequest.is_deleted == False))
            .filter(Employee.is_deleted == False)
            .group_by(Employee.id, User.id)
            .order_by(Employee.employee_code)
        )
        return [
            {
                "employee": r.Employee, "user": r.User,
                "total_requests": r.total_requests or 0,
                "approved_days": float(r.approved_days or 0),
                "pending_count": r.pending_count or 0,
                "rejected_count": r.rejected_count or 0,
            }
            for r in q.all()
        ]

    # ── Employee Stats ────────────────────────────────────────────────

    def employee_stats(self) -> dict:
        total   = Employee.query.filter_by(is_deleted=False).count()
        by_dept = (
            db.session.query(Employee.department, func.count(Employee.id).label("count"))
            .filter(Employee.is_deleted == False, Employee.department.isnot(None))
            .group_by(Employee.department)
            .order_by(func.count(Employee.id).desc())
            .all()
        )
        by_type = (
            db.session.query(Employee.employment_type, func.count(Employee.id).label("count"))
            .filter(Employee.is_deleted == False)
            .group_by(Employee.employment_type)
            .all()
        )
        return {
            "total": total,
            "by_department": [{"dept": r.department or "Unassigned", "count": r.count} for r in by_dept],
            "by_type": [{"type": r.employment_type.replace("_"," ").title(), "count": r.count} for r in by_type],
        }

    def get_departments(self) -> list:
        rows = (
            db.session.query(Employee.department)
            .filter(Employee.is_deleted == False, Employee.department.isnot(None))
            .distinct().order_by(Employee.department).all()
        )
        return [r.department for r in rows]

    def get_all_employees_simple(self) -> list:
        return (
            db.session.query(Employee, User)
            .join(User, Employee.user_id == User.id)
            .filter(Employee.is_deleted == False)
            .order_by(Employee.employee_code)
            .all()
        )
