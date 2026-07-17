"""blueprints/reports/service.py — report queries using simple per-employee DB calls."""

import logging
from datetime import date
from typing import Optional

from app.extensions.database import db
from app.models.attendance import Attendance
from app.models.employee import Employee
from app.models.leave import LeaveRequest
from app.models.user import User
from sqlalchemy import extract, func

logger = logging.getLogger(__name__)


class ReportService:

    # ── Attendance Summary ────────────────────────────────────────────

    def attendance_summary(
        self,
        start: date,
        end: date,
        department: str = "",
        employee_id: Optional[int] = None,
    ) -> list:
        """
        Return one dict per employee with attendance counts for the date range.
        Uses simple per-employee subqueries — avoids SQLAlchemy case() version issues.
        """
        emp_q = db.session.query(Employee, User).join(User, Employee.user_id == User.id).filter(
            Employee.is_deleted == False
        )
        if department:
            emp_q = emp_q.filter(Employee.department == department)
        if employee_id:
            emp_q = emp_q.filter(Employee.id == employee_id)
        employees = emp_q.order_by(Employee.employee_code).all()

        results = []
        for emp, usr in employees:
            base = Attendance.query.filter(
                Attendance.employee_id == emp.id,
                Attendance.date >= start,
                Attendance.date <= end,
                Attendance.is_deleted == False,
            )
            present   = base.filter(Attendance.status == "present").count()
            absent    = base.filter(Attendance.status == "absent").count()
            half_day  = base.filter(Attendance.status == "half_day").count()
            on_leave  = base.filter(Attendance.status == "on_leave").count()
            late_days = base.filter(Attendance.is_late == True).count()
            mins_row  = db.session.query(
                func.coalesce(func.sum(Attendance.working_minutes), 0)
            ).filter(
                Attendance.employee_id == emp.id,
                Attendance.date >= start,
                Attendance.date <= end,
                Attendance.is_deleted == False,
            ).scalar() or 0

            results.append({
                "employee":   emp,
                "user":       usr,
                "total_days": present + absent + half_day + on_leave,
                "present":    present,
                "absent":     absent,
                "half_day":   half_day,
                "on_leave":   on_leave,
                "late_days":  late_days,
                "total_hours": round(mins_row / 60, 1),
            })
        return results

    def daily_attendance(self, for_date: date) -> list:
        rows = (
            db.session.query(Employee, User, Attendance)
            .join(User, Employee.user_id == User.id)
            .outerjoin(
                Attendance,
                (Attendance.employee_id == Employee.id) &
                (Attendance.date == for_date) &
                (Attendance.is_deleted == False),
            )
            .filter(Employee.is_deleted == False)
            .order_by(Employee.employee_code)
            .all()
        )
        return [{"employee": r.Employee, "user": r.User, "attendance": r.Attendance} for r in rows]

    # ── Leave Summary ─────────────────────────────────────────────────

    def leave_summary(self, year: int) -> list:
        employees = (
            db.session.query(Employee, User)
            .join(User, Employee.user_id == User.id)
            .filter(Employee.is_deleted == False)
            .order_by(Employee.employee_code)
            .all()
        )
        results = []
        for emp, usr in employees:
            base = LeaveRequest.query.filter(
                LeaveRequest.employee_id == emp.id,
                LeaveRequest.is_deleted == False,
                extract("year", LeaveRequest.start_date) == year,
            )
            total     = base.count()
            approved  = db.session.query(
                func.coalesce(func.sum(LeaveRequest.total_days), 0)
            ).filter(
                LeaveRequest.employee_id == emp.id,
                LeaveRequest.is_deleted == False,
                LeaveRequest.status == "approved",
                extract("year", LeaveRequest.start_date) == year,
            ).scalar() or 0
            pending   = base.filter(LeaveRequest.status == "pending").count()
            rejected  = base.filter(LeaveRequest.status == "rejected").count()

            results.append({
                "employee":       emp,
                "user":           usr,
                "total_requests": total,
                "approved_days":  float(approved),
                "pending_count":  pending,
                "rejected_count": rejected,
            })
        return results

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
            "by_type": [{"type": r.employment_type.replace("_", " ").title(), "count": r.count} for r in by_type],
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
