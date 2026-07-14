"""
blueprints/leave/service.py
==============================
Leave service — all business logic for leave, half-day, and early leave.
"""

import logging
from datetime import date, datetime, timezone
from typing import Optional, Tuple

from app.extensions.database import db
from app.models.leave import EarlyLeaveRequest, HalfDayRequest, LeaveRequest, LeaveType
from app.models.attendance import Attendance
from app.blueprints.attendance.repository import AttendanceRepository
from .repository import LeaveRepository

logger = logging.getLogger(__name__)
leave_repo = LeaveRepository()
att_repo = AttendanceRepository()


class LeaveService:

    # ── Leave Balance ─────────────────────────────────────────────────

    def get_balance(self, employee_id: int) -> list:
        """Return balance for all active leave types for this employee."""
        year = date.today().year
        types = leave_repo.get_all_types()
        balances = []
        for lt in types:
            taken = leave_repo.count_days_taken(employee_id, lt.id, year)
            available = max(0, lt.max_days_per_year - taken)
            balances.append({
                "type": lt,
                "max": lt.max_days_per_year,
                "taken": taken,
                "available": available,
                "pct": int((taken / lt.max_days_per_year * 100)) if lt.max_days_per_year else 0,
            })
        return balances

    # ── Apply Leave ───────────────────────────────────────────────────

    def apply_leave(self, employee_id: int, form_data: dict, attachment=None) -> Tuple[bool, str, Optional[LeaveRequest]]:
        start = form_data.get("start_date")
        end   = form_data.get("end_date")
        lt_id = form_data.get("leave_type_id")

        if not start or not end or not lt_id:
            return False, "Please fill all required fields.", None

        if end < start:
            return False, "End date cannot be before start date.", None

        if start < date.today():
            return False, "Cannot apply leave for a past date.", None

        # Check balance
        lt = leave_repo.get_type_by_id(int(lt_id))
        if not lt:
            return False, "Invalid leave type.", None

        total_days = self._count_working_days(start, end)
        if total_days <= 0:
            return False, "Selected dates fall on weekends only.", None

        year = start.year
        taken = leave_repo.count_days_taken(employee_id, lt.id, year)
        available = lt.max_days_per_year - taken
        if total_days > available:
            return False, f"Insufficient {lt.name} balance. Available: {available:.0f} days.", None

        # Overlap check
        if leave_repo.has_overlapping(employee_id, start, end):
            return False, "You already have a pending or approved leave for this period.", None

        # Handle attachment
        attachment_path = None
        if attachment and attachment.filename:
            try:
                from app.utils.file_utils import save_file
                attachment_path = save_file(attachment, "leave_attachments",
                                            max_bytes=10 * 1024 * 1024,
                                            allowed_extensions={"pdf", "jpg", "jpeg", "png", "doc", "docx"})
            except Exception as e:
                logger.warning("Leave attachment upload failed: %s", e)

        lr = LeaveRequest(
            employee_id=employee_id,
            leave_type_id=lt.id,
            start_date=start,
            end_date=end,
            total_days=total_days,
            reason=form_data.get("reason", "").strip(),
            attachment=attachment_path,
            status="pending",
            applied_on=datetime.now(timezone.utc),
            created_by=employee_id,
        )
        leave_repo.create(lr)
        logger.info("LEAVE_APPLIED | emp=%s | type=%s | days=%s | from=%s to=%s",
                    employee_id, lt.code, total_days, start, end)
        return True, f"{lt.name} leave applied for {total_days} day(s). Awaiting approval.", lr

    def approve_leave(self, lr_id: int, reviewer_id: int, comment: str = "") -> Tuple[bool, str]:
        lr = leave_repo.get_by_id(lr_id)
        if not lr:
            return False, "Leave request not found."
        if lr.status != "pending":
            return False, f"Cannot approve a request with status '{lr.status}'."
        lr.status = "approved"
        lr.reviewed_by = reviewer_id
        lr.reviewed_on = datetime.now(timezone.utc)
        lr.reviewer_comment = comment
        leave_repo.update(lr)
        # Mark attendance as on_leave for each day
        self._mark_attendance_on_leave(lr)
        logger.info("LEAVE_APPROVED | lr_id=%s | by=%s", lr_id, reviewer_id)
        return True, "Leave request approved."

    def reject_leave(self, lr_id: int, reviewer_id: int, comment: str = "") -> Tuple[bool, str]:
        lr = leave_repo.get_by_id(lr_id)
        if not lr:
            return False, "Leave request not found."
        if lr.status != "pending":
            return False, f"Cannot reject a request with status '{lr.status}'."
        lr.status = "rejected"
        lr.reviewed_by = reviewer_id
        lr.reviewed_on = datetime.now(timezone.utc)
        lr.reviewer_comment = comment
        leave_repo.update(lr)
        return True, "Leave request rejected."

    def cancel_leave(self, lr_id: int, employee_id: int) -> Tuple[bool, str]:
        lr = leave_repo.get_by_id(lr_id)
        if not lr:
            return False, "Leave request not found."
        if lr.employee_id != employee_id:
            return False, "Unauthorised."
        if lr.status not in ("pending", "approved"):
            return False, "This request cannot be cancelled."
        if lr.status == "approved" and lr.start_date <= date.today():
            return False, "Cannot cancel leave that has already started."
        lr.status = "cancelled"
        leave_repo.update(lr)
        return True, "Leave request cancelled."

    # ── Half Day ──────────────────────────────────────────────────────

    def apply_halfday(self, employee_id: int, form_data: dict) -> Tuple[bool, str, Optional[HalfDayRequest]]:
        req_date = form_data.get("date")
        half_type = form_data.get("half_type")
        reason = form_data.get("reason", "").strip()

        if not req_date or not half_type or not reason:
            return False, "All fields are required.", None

        if req_date < date.today():
            return False, "Cannot apply half day for a past date.", None

        # Check no approved full leave on same day
        if leave_repo.has_overlapping(employee_id, req_date, req_date):
            return False, "You already have a leave request for this date.", None

        # No duplicate pending half-day
        existing = HalfDayRequest.query.filter_by(
            employee_id=employee_id, date=req_date,
            status="pending", is_deleted=False
        ).first()
        if existing:
            return False, "A half-day request for this date is already pending.", None

        hd = HalfDayRequest(
            employee_id=employee_id,
            date=req_date,
            half_type=half_type,
            reason=reason,
            status="pending",
            applied_on=datetime.now(timezone.utc),
            created_by=employee_id,
        )
        leave_repo.create_halfday(hd)
        return True, f"Half-day ({half_type.title()}) request submitted for {req_date.strftime('%d %b %Y')}.", hd

    def approve_halfday(self, hd_id: int, reviewer_id: int, comment: str = "") -> Tuple[bool, str]:
        hd = leave_repo.get_halfday_by_id(hd_id)
        if not hd: return False, "Request not found."
        if hd.status != "pending": return False, "Already processed."
        hd.status = "approved"
        hd.reviewed_by = reviewer_id
        hd.reviewed_on = datetime.now(timezone.utc)
        hd.reviewer_comment = comment
        leave_repo.update_halfday(hd)
        # Update attendance
        att = att_repo.get_today(hd.employee_id, hd.date)
        if att:
            att.is_half_day = True
            att.status = "half_day"
            att_repo.update(att)
        return True, "Half-day request approved."

    def reject_halfday(self, hd_id: int, reviewer_id: int, comment: str = "") -> Tuple[bool, str]:
        hd = leave_repo.get_halfday_by_id(hd_id)
        if not hd: return False, "Request not found."
        if hd.status != "pending": return False, "Already processed."
        hd.status = "rejected"
        hd.reviewed_by = reviewer_id
        hd.reviewed_on = datetime.now(timezone.utc)
        hd.reviewer_comment = comment
        leave_repo.update_halfday(hd)
        return True, "Half-day request rejected."

    # ── Early Leave ───────────────────────────────────────────────────

    def apply_earlyleave(self, employee_id: int, form_data: dict) -> Tuple[bool, str, Optional[EarlyLeaveRequest]]:
        req_date = form_data.get("date")
        leave_time = form_data.get("requested_leave_time")
        reason = form_data.get("reason", "").strip()

        if not req_date or not leave_time or not reason:
            return False, "All fields are required.", None

        if req_date < date.today():
            return False, "Cannot apply early leave for a past date.", None

        existing = EarlyLeaveRequest.query.filter_by(
            employee_id=employee_id, date=req_date,
            status="pending", is_deleted=False
        ).first()
        if existing:
            return False, "An early leave request for this date is already pending.", None

        el = EarlyLeaveRequest(
            employee_id=employee_id,
            date=req_date,
            requested_leave_time=leave_time,
            reason=reason,
            status="pending",
            applied_on=datetime.now(timezone.utc),
            created_by=employee_id,
        )
        leave_repo.create_earlyleave(el)
        return True, f"Early leave request submitted for {req_date.strftime('%d %b %Y')}.", el

    def approve_earlyleave(self, el_id: int, reviewer_id: int, comment: str = "") -> Tuple[bool, str]:
        el = leave_repo.get_earlyleave_by_id(el_id)
        if not el: return False, "Request not found."
        if el.status != "pending": return False, "Already processed."
        el.status = "approved"
        el.reviewed_by = reviewer_id
        el.reviewed_on = datetime.now(timezone.utc)
        el.reviewer_comment = comment
        leave_repo.update_earlyleave(el)
        att = att_repo.get_today(el.employee_id, el.date)
        if att:
            att.is_early_leave = True
            att_repo.update(att)
        return True, "Early leave approved."

    def reject_earlyleave(self, el_id: int, reviewer_id: int, comment: str = "") -> Tuple[bool, str]:
        el = leave_repo.get_earlyleave_by_id(el_id)
        if not el: return False, "Request not found."
        if el.status != "pending": return False, "Already processed."
        el.status = "rejected"
        el.reviewed_by = reviewer_id
        el.reviewed_on = datetime.now(timezone.utc)
        el.reviewer_comment = comment
        leave_repo.update_earlyleave(el)
        return True, "Early leave rejected."

    # ── Helpers ───────────────────────────────────────────────────────

    def _count_working_days(self, start: date, end: date) -> int:
        from datetime import timedelta
        days = 0
        current = start
        while current <= end:
            if current.weekday() < 5:  # Mon–Fri
                days += 1
            current += timedelta(days=1)
        return days

    def _mark_attendance_on_leave(self, lr: LeaveRequest) -> None:
        from datetime import timedelta
        current = lr.start_date
        while current <= lr.end_date:
            if current.weekday() < 5:
                att = att_repo.get_today(lr.employee_id, current)
                if att:
                    att.status = "on_leave"
                    att_repo.update(att)
                else:
                    from app.models.attendance import Attendance
                    new_att = Attendance(
                        employee_id=lr.employee_id,
                        date=current,
                        status="on_leave",
                        created_by=lr.reviewed_by,
                    )
                    att_repo.create(new_att)
            current += timedelta(days=1)
