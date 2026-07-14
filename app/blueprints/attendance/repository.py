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
