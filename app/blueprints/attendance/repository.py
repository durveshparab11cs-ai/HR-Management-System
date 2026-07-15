"""
attendance/repository.py
==========================
All database access for the attendance module.
"""

from datetime import date, datetime
from typing import Optional

from sqlalchemy import and_, func

from app.extensions.database import db
from app.models.attendance import Attendance
from app.models.attendance_log import AttendanceLog
from app.models.office_settings import OfficeSettings
from app.models.employee import Employee


class AttendanceRepository:

    # ── Office Settings ───────────────────────────────────────────────

    def get_default_office(self) -> Optional[OfficeSettings]:
        return OfficeSettings.query.filter_by(is_default=True, is_deleted=False).first()

    def get_office_for_employee(self, employee: Employee) -> Optional[OfficeSettings]:
        if employee.office_settings_id:
            o = OfficeSettings.query.filter_by(id=employee.office_settings_id, is_deleted=False).first()
            if o:
                return o
        return self.get_default_office()

    def save_office(self, office: OfficeSettings) -> OfficeSettings:
        db.session.add(office)
        db.session.commit()
        return office

    # ── Attendance Records ────────────────────────────────────────────

    def get_today(self, employee_id: int, today: date) -> Optional[Attendance]:
        return Attendance.query.filter_by(
            employee_id=employee_id,
            date=today,
            is_deleted=False,
        ).first()

    def get_by_id(self, att_id: int) -> Optional[Attendance]:
        return Attendance.query.filter_by(id=att_id, is_deleted=False).first()

    def create(self, attendance: Attendance) -> Attendance:
        db.session.add(attendance)
        db.session.commit()
        return attendance

    def update(self, attendance: Attendance) -> Attendance:
        db.session.add(attendance)
        db.session.commit()
        return attendance

    def get_history(self, employee_id: int, page: int = 1, per_page: int = 30):
        return (
            Attendance.query
            .filter_by(employee_id=employee_id, is_deleted=False)
            .order_by(Attendance.date.desc())
            .paginate(page=page, per_page=per_page, error_out=False)
        )

    def get_history_filtered(
        self,
        employee_id: int,
        start_date=None,
        end_date=None,
        status: str = "",
        page: int = 1,
        per_page: int = 30,
    ):
        """Filtered attendance history with optional date range and status."""
        q = Attendance.query.filter_by(employee_id=employee_id, is_deleted=False)
        if start_date:
            q = q.filter(Attendance.date >= start_date)
        if end_date:
            q = q.filter(Attendance.date <= end_date)
        if status:
            q = q.filter(Attendance.status == status)
        return q.order_by(Attendance.date.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

    def get_history_with_photos(
        self,
        employee_id: int,
        start_date=None,
        end_date=None,
        status: str = "",
        page: int = 1,
        per_page: int = 30,
    ):
        """
        Filtered history including photo objects for each attendance record.
        Returns a paginated list of (Attendance, AttendancePhoto|None) tuples.
        """
        from app.models.attendance_photo import AttendancePhoto
        from sqlalchemy.orm import outerjoin

        q = (
            db.session.query(Attendance, AttendancePhoto)
            .outerjoin(
                AttendancePhoto,
                AttendancePhoto.attendance_id == Attendance.id,
            )
            .filter(
                Attendance.employee_id == employee_id,
                Attendance.is_deleted == False,
            )
        )
        if start_date:
            q = q.filter(Attendance.date >= start_date)
        if end_date:
            q = q.filter(Attendance.date <= end_date)
        if status:
            q = q.filter(Attendance.status == status)

        q = q.order_by(Attendance.date.desc())
        total = q.count()

        offset = (page - 1) * per_page
        items  = q.offset(offset).limit(per_page).all()

        # Build a simple pagination-like object
        class _Pagination:
            def __init__(self, items, total, page, per_page):
                self.items    = items
                self.total    = total
                self.page     = page
                self.per_page = per_page
                self.pages    = max(1, (total + per_page - 1) // per_page)
                self.has_prev = page > 1
                self.has_next = page < self.pages
                self.prev_num = page - 1
                self.next_num = page + 1

            def iter_pages(self, left_edge=1, left_current=2,
                           right_current=3, right_edge=1):
                last = 0
                for num in range(1, self.pages + 1):
                    if (num <= left_edge or
                            self.page - left_current <= num <= self.page + right_current or
                            num > self.pages - right_edge):
                        if last + 1 != num:
                            yield None
                        yield num
                        last = num

        return _Pagination(items, total, page, per_page)

    def get_history_all_filtered(
        self,
        employee_id: int,
        start_date=None,
        end_date=None,
        status: str = "",
    ) -> list:
        """Return ALL matching records (no pagination) for export."""
        q = Attendance.query.filter_by(employee_id=employee_id, is_deleted=False)
        if start_date:
            q = q.filter(Attendance.date >= start_date)
        if end_date:
            q = q.filter(Attendance.date <= end_date)
        if status:
            q = q.filter(Attendance.status == status)
        return q.order_by(Attendance.date.asc()).all()

    def get_month_records(self, employee_id: int, year: int, month: int) -> list:
        from sqlalchemy import extract  # noqa
        return (
            Attendance.query
            .filter(
                Attendance.employee_id == employee_id,
                Attendance.is_deleted == False,
                extract("year", Attendance.date) == year,
                extract("month", Attendance.date) == month,
            )
            .order_by(Attendance.date.asc())
            .all()
        )

    # ── Attendance Logs ───────────────────────────────────────────────

    def log_action(self, log: AttendanceLog) -> AttendanceLog:
        db.session.add(log)
        db.session.commit()
        return log

    # ── Admin Queries ─────────────────────────────────────────────────

    def get_all_today(self, today: date) -> list:
        return (
            Attendance.query
            .filter_by(date=today, is_deleted=False)
            .all()
        )

    def count_checked_in_today(self, today: date) -> int:
        return (
            Attendance.query
            .filter(
                Attendance.date == today,
                Attendance.check_in_time.isnot(None),
                Attendance.is_deleted == False,
            )
            .count()
        )

    def count_checked_out_today(self, today: date) -> int:
        return (
            Attendance.query
            .filter(
                Attendance.date == today,
                Attendance.check_out_time.isnot(None),
                Attendance.is_deleted == False,
            )
            .count()
        )

    def count_late_today(self, today: date) -> int:
        return (
            Attendance.query
            .filter_by(date=today, is_late=True, is_deleted=False)
            .count()
        )

    def get_all_employees_attendance_for_date(self, for_date: date) -> list:
        """
        Returns list of dicts with employee + attendance (or None) for every
        active employee on a given date. Used for the admin daily Excel export.
        """
        from app.models.user import User
        from app.models.attendance_photo import AttendancePhoto
        from app.constants.enums import UserStatus

        employees = (
            Employee.query
            .join(User, Employee.user_id == User.id)
            .filter(
                Employee.is_deleted == False,
                User.status == UserStatus.ACTIVE.value,
            )
            .order_by(Employee.employee_code)
            .all()
        )

        result = []
        for emp in employees:
            att = Attendance.query.filter_by(
                employee_id=emp.id, date=for_date, is_deleted=False
            ).first()
            photo = None
            if att:
                photo = AttendancePhoto.query.filter_by(
                    attendance_id=att.id
                ).first()
            result.append({
                "employee": emp,
                "user": emp.user,
                "attendance": att,
                "photo": photo,
            })
        return result
