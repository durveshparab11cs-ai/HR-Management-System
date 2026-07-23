"""
blueprints/leave/repository.py
================================
All database access for the leave module.
"""

from datetime import date
from typing import Optional
from sqlalchemy import and_, extract, func
from app.extensions.database import db
from app.models.leave import (
    LeaveType, LeaveRequest, HalfDayRequest, EarlyLeaveRequest
)


class LeaveRepository:

    # ── Leave Types ───────────────────────────────────────────────────

    def get_all_types(self) -> list:
        return LeaveType.query.filter_by(is_active=True).order_by(LeaveType.name).all()

    def get_type_by_id(self, lt_id: int) -> Optional[LeaveType]:
        return LeaveType.query.filter_by(id=lt_id, is_active=True).first()

    def get_type_by_code(self, code: str) -> Optional[LeaveType]:
        return LeaveType.query.filter_by(code=code.upper(), is_active=True).first()

    def create_type(self, lt: LeaveType) -> LeaveType:
        db.session.add(lt); db.session.commit(); return lt

    def update_type(self, lt: LeaveType) -> LeaveType:
        db.session.add(lt); db.session.commit(); return lt

    # ── Leave Requests ────────────────────────────────────────────────

    def get_by_id(self, lr_id: int) -> Optional[LeaveRequest]:
        return LeaveRequest.query.filter_by(id=lr_id, is_deleted=False).first()

    def get_by_id_or_404(self, lr_id: int) -> LeaveRequest:
        from flask import abort
        r = self.get_by_id(lr_id)
        if not r: abort(404)
        return r

    def get_employee_requests(self, employee_id: int, page: int = 1, per_page: int = 20):
        return (
            LeaveRequest.query
            .filter_by(employee_id=employee_id, is_deleted=False)
            .order_by(LeaveRequest.applied_on.desc())
            .paginate(page=page, per_page=per_page, error_out=False)
        )

    def get_pending(self, page: int = 1, per_page: int = 30):
        return (
            LeaveRequest.query
            .filter_by(status="pending", is_deleted=False)
            .order_by(LeaveRequest.applied_on.asc())
            .paginate(page=page, per_page=per_page, error_out=False)
        )

    def get_all_requests(self, page: int = 1, per_page: int = 30, status: str = ""):
        q = LeaveRequest.query.filter_by(is_deleted=False)
        if status:
            q = q.filter_by(status=status)
        return q.order_by(LeaveRequest.applied_on.desc()).paginate(page=page, per_page=per_page, error_out=False)

    def create(self, lr: LeaveRequest) -> LeaveRequest:
        db.session.add(lr); db.session.commit(); return lr

    def update(self, lr: LeaveRequest) -> LeaveRequest:
        db.session.add(lr); db.session.commit(); return lr

    def count_days_taken(self, employee_id: int, leave_type_id: int, year: int) -> float:
        """Total approved leave days for an employee in a given year."""
        result = (
            db.session.query(func.sum(LeaveRequest.total_days))
            .filter(
                LeaveRequest.employee_id == employee_id,
                LeaveRequest.leave_type_id == leave_type_id,
                LeaveRequest.status == "approved",
                LeaveRequest.is_deleted == False,
                extract("year", LeaveRequest.start_date) == year,
            )
            .scalar()
        )
        return float(result or 0)

    def has_overlapping(self, employee_id: int, start: date, end: date, exclude_id: int = None) -> bool:
        q = LeaveRequest.query.filter(
            LeaveRequest.employee_id == employee_id,
            LeaveRequest.is_deleted == False,
            LeaveRequest.status.in_(["pending", "approved"]),
            LeaveRequest.start_date <= end,
            LeaveRequest.end_date >= start,
        )
        if exclude_id:
            q = q.filter(LeaveRequest.id != exclude_id)
        return q.first() is not None

    def count_pending(self) -> int:
        return LeaveRequest.query.filter_by(status="pending", is_deleted=False).count()

    # ── Half Day Requests ─────────────────────────────────────────────

    def get_halfday_by_id(self, hd_id: int) -> Optional[HalfDayRequest]:
        return HalfDayRequest.query.filter_by(id=hd_id, is_deleted=False).first()

    def get_halfday_by_id_or_404(self, hd_id: int) -> HalfDayRequest:
        from flask import abort
        r = self.get_halfday_by_id(hd_id)
        if not r: abort(404)
        return r

    def get_employee_halfdays(self, employee_id: int, page: int = 1, per_page: int = 20):
        return (
            HalfDayRequest.query
            .filter_by(employee_id=employee_id, is_deleted=False)
            .order_by(HalfDayRequest.applied_on.desc())
            .paginate(page=page, per_page=per_page, error_out=False)
        )

    def get_pending_halfdays(self, page: int = 1, per_page: int = 30, department: str = None):
        q = HalfDayRequest.query.filter_by(status="pending", is_deleted=False)
        if department:
            from app.models.employee import Employee  # noqa: PLC0415
            q = q.join(Employee, HalfDayRequest.employee_id == Employee.id).filter(Employee.department == department)
        return q.order_by(HalfDayRequest.applied_on.asc()).paginate(page=page, per_page=per_page, error_out=False)

    def get_halfdays_for_manager(self, mgr_employee_code: str, page: int = 1, per_page: int = 30, status: str = ""):
        """Return half-day requests where the logged-in employee is the reporting manager."""
        try:
            q = HalfDayRequest.query.filter_by(
                reporting_manager_code=mgr_employee_code.upper(), is_deleted=False
            )
            if status:
                q = q.filter_by(status=status)
            return q.order_by(HalfDayRequest.applied_on.desc()).paginate(page=page, per_page=per_page, error_out=False)
        except Exception:  # noqa: BLE001 — column may not exist yet
            from sqlalchemy.orm.query import Query  # noqa: PLC0415
            class _EmptyPage:
                items = []; total = 0; pages = 1; page = 1
                has_prev = False; has_next = False
                prev_num = 0; next_num = 2
            return _EmptyPage()

    def count_manager_pending_halfdays(self, mgr_employee_code: str) -> int:
        try:
            return HalfDayRequest.query.filter_by(
                reporting_manager_code=mgr_employee_code.upper(),
                status="pending", is_deleted=False
            ).count()
        except Exception:
            return 0

    def create_halfday(self, hd: HalfDayRequest) -> HalfDayRequest:
        db.session.add(hd); db.session.commit(); return hd

    def update_halfday(self, hd: HalfDayRequest) -> HalfDayRequest:
        db.session.add(hd); db.session.commit(); return hd

    def count_pending_halfdays(self) -> int:
        return HalfDayRequest.query.filter_by(status="pending", is_deleted=False).count()

    # ── Early Leave Requests ──────────────────────────────────────────

    def get_earlyleave_by_id(self, el_id: int) -> Optional[EarlyLeaveRequest]:
        return EarlyLeaveRequest.query.filter_by(id=el_id, is_deleted=False).first()

    def get_earlyleave_by_id_or_404(self, el_id: int) -> EarlyLeaveRequest:
        from flask import abort
        r = self.get_earlyleave_by_id(el_id)
        if not r: abort(404)
        return r

    def get_employee_earlyleaves(self, employee_id: int, page: int = 1, per_page: int = 20):
        return (
            EarlyLeaveRequest.query
            .filter_by(employee_id=employee_id, is_deleted=False)
            .order_by(EarlyLeaveRequest.applied_on.desc())
            .paginate(page=page, per_page=per_page, error_out=False)
        )

    def get_pending_earlyleaves(self, page: int = 1, per_page: int = 30, department: str = None):
        q = EarlyLeaveRequest.query.filter_by(status="pending", is_deleted=False)
        if department:
            from app.models.employee import Employee  # noqa: PLC0415
            q = q.join(Employee, EarlyLeaveRequest.employee_id == Employee.id).filter(Employee.department == department)
        return q.order_by(EarlyLeaveRequest.applied_on.asc()).paginate(page=page, per_page=per_page, error_out=False)

    def get_earlyleaves_for_manager(self, mgr_employee_code: str, page: int = 1, per_page: int = 30, status: str = ""):
        """Return early-leave requests where the logged-in employee is the reporting manager."""
        try:
            q = EarlyLeaveRequest.query.filter_by(
                reporting_manager_code=mgr_employee_code.upper(), is_deleted=False
            )
            if status:
                q = q.filter_by(status=status)
            return q.order_by(EarlyLeaveRequest.applied_on.desc()).paginate(page=page, per_page=per_page, error_out=False)
        except Exception:  # noqa: BLE001 — column may not exist yet
            class _EmptyPage:
                items = []; total = 0; pages = 1; page = 1
                has_prev = False; has_next = False
                prev_num = 0; next_num = 2
            return _EmptyPage()

    def count_manager_pending_earlyleaves(self, mgr_employee_code: str) -> int:
        try:
            return EarlyLeaveRequest.query.filter_by(
                reporting_manager_code=mgr_employee_code.upper(),
                status="pending", is_deleted=False
            ).count()
        except Exception:
            return 0

    def create_earlyleave(self, el: EarlyLeaveRequest) -> EarlyLeaveRequest:
        db.session.add(el); db.session.commit(); return el

    def update_earlyleave(self, el: EarlyLeaveRequest) -> EarlyLeaveRequest:
        db.session.add(el); db.session.commit(); return el

    def count_pending_earlyleaves(self) -> int:
        return EarlyLeaveRequest.query.filter_by(status="pending", is_deleted=False).count()
