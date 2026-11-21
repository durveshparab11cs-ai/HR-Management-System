"""
blueprints/leave/service.py
==============================
Leave service — all business logic for leave, half-day, and early leave.
"""

import logging
from datetime import date, datetime, timedelta, timezone
from typing import Optional, Tuple

from app.extensions.database import db
from app.models.leave import EarlyLeaveRequest, HalfDayRequest, LeaveRequest, LeaveType
from app.models.attendance import Attendance
from app.blueprints.attendance.repository import AttendanceRepository
from .repository import LeaveRepository
from sqlalchemy import and_  # noqa: PLC0415

logger = logging.getLogger(__name__)
leave_repo = LeaveRepository()
att_repo = AttendanceRepository()


class LeaveService:

    # ── Leave Balance ─────────────────────────────────────────────────

    def get_balance(self, employee_id: int) -> list:
        """Return balance for all 4 active leave types: Casual, Sick, Paid, Comp Off."""
        from app.models.leave import LeaveType  # noqa: PLC0415
        from datetime import datetime, timedelta  # noqa: PLC0415
        
        year = date.today().year
        today = date.today()
        balances = []
        
        # Get only the 4 leave types (filter by codes)
        # CRITICAL: Accept both 'CO' and 'COMP' for backward compatibility with legacy production databases
        leave_type_codes = ['CL', 'SL', 'PL', 'CO', 'COMP']  # Casual, Sick, Paid, Comp Off (both codes)
        types = LeaveType.query.filter(LeaveType.code.in_(leave_type_codes), LeaveType.is_active == True).all()
        
        # DEDUP: If both CO and COMP exist, only use CO (newer code)
        type_map = {}  # code -> LeaveType
        for lt in types:
            if lt.code == 'COMP':
                # Only add COMP if CO doesn't already exist
                if 'CO' not in type_map:
                    # Treat COMP as CO internally
                    type_map['CO'] = lt
            elif lt.code == 'CO':
                # CO takes precedence over COMP
                type_map['CO'] = lt
            else:
                # CL, SL, PL - add as-is
                type_map[lt.code] = lt
        
        types = list(type_map.values())  # Convert back to list
        
        # CRITICAL FALLBACK: If no CO/COMP type found at all, create a synthetic one
        # This ensures the CO card ALWAYS shows, even if DB is misconfigured
        if not any(lt.code in ('CO', 'COMP') for lt in types):
            logger.warning("CRITICAL: No Comp Off leave type found in database. Creating synthetic CO type.")
            # Create a temporary LeaveType object (not saved to DB, just for display)
            synthetic_co = LeaveType(
                id=9999,  # Synthetic ID
                code='CO',
                name='Comp Off',
                max_days_per_year=6,
                is_paid=True,
                is_active=True,
                color='#8b5cf6',
            )
            types.append(synthetic_co)
        
        for lt in types:
            if lt.code == 'CO':
                # COMP OFF Strict Business Policy:
                # 1. Must be APPROVED by Reporting Manager (no auto-crediting)
                # 2. Employee must have worked AT LEAST 8 hours 30 minutes on that Sunday/Holiday
                # 3. Valid for 90 days, single use
                from .comp_off_service import verify_comp_off_attendance
                
                # Check for approved earned comp off
                comp_off_earned = LeaveRequest.query.filter(
                    and_(
                        LeaveRequest.employee_id == employee_id,
                        LeaveRequest.leave_type_id == lt.id,
                        LeaveRequest.status == "approved",  # Must be approved by manager!
                        LeaveRequest.comp_off_work_date != None,
                        LeaveRequest.comp_off_expiry_date >= today,
                        LeaveRequest.comp_off_used_on == None,
                        LeaveRequest.is_deleted == False,
                    )
                ).first()
                
                is_eligible = False
                att_msg = ""
                if comp_off_earned:
                    is_eligible, _, att_msg = verify_comp_off_attendance(employee_id, comp_off_earned.comp_off_work_date)
                
                if comp_off_earned and is_eligible:
                    # Verified and Available to avail
                    balances.append({
                        "type": lt,
                        "max": 1,
                        "taken": 0,
                        "available": 1,
                        "pct": 0,
                        "is_unlimited": False,
                        "comp_off_expiry": comp_off_earned.comp_off_expiry_date,
                        "note": att_msg,
                    })
                else:
                    # Check if there is a pending request or an approved request awaiting duty completion
                    pending_request = LeaveRequest.query.filter(
                        and_(
                            LeaveRequest.employee_id == employee_id,
                            LeaveRequest.leave_type_id == lt.id,
                            LeaveRequest.comp_off_work_date != None,
                            LeaveRequest.status == "pending",
                            LeaveRequest.is_deleted == False,
                        )
                    ).first()

                    status_note = ""
                    if pending_request:
                        status_note = f"Awaiting Manager Approval ({pending_request.comp_off_work_date.strftime('%d %b')})"
                    elif comp_off_earned and not is_eligible:
                        status_note = f"Manager Approved &bull; {att_msg}"

                    balances.append({
                        "type": lt,
                        "max": 1,
                        "taken": 1,
                        "available": 0,
                        "pct": 100,
                        "is_unlimited": False,
                        "comp_off_expiry": comp_off_earned.comp_off_expiry_date if comp_off_earned else None,
                        "note": status_note,
                    })
            
            elif lt.code in ['CL', 'SL']:
                # CASUAL & SICK LEAVE - Unlimited
                balances.append({
                    "type": lt,
                    "max": "Unlimited",
                    "taken": 0,
                    "available": "Unlimited",
                    "pct": 0,
                    "is_unlimited": True,
                })
            
            elif lt.code == 'PL':
                # PAID LEAVE - 12 days per year
                taken = leave_repo.count_days_taken(employee_id, lt.id, year)
                available = max(0, 12 - taken)  # Fixed 12 days for Paid Leave
                balances.append({
                    "type": lt,
                    "max": 12,
                    "taken": taken,
                    "available": available,
                    "pct": int((taken / 12 * 100)) if taken > 0 else 0,
                    "is_unlimited": False,
                })
        
        return balances

    # ── Apply Leave ───────────────────────────────────────────────────

    def apply_leave(self, employee_id: int, form_data: dict, attachment=None) -> Tuple[bool, str, Optional[LeaveRequest]]:
        start = form_data.get("start_date")
        end   = form_data.get("end_date")
        lt_id = form_data.get("leave_type_id")
        mgr_code = (form_data.get("reporting_manager_code") or "").strip().upper()

        if not start or not end or not lt_id:
            return False, "Please fill all required fields.", None
        if not mgr_code:
            return False, "Reporting Manager Employee Code is required.", None

        if end < start:
            return False, "End date cannot be before start date.", None
        if start < date.today():
            return False, "Cannot apply leave for a past date.", None

        # Validate manager
        ok, mgr_name, mgr_err = self._validate_manager(employee_id, mgr_code)
        if not ok:
            return False, mgr_err, None

        lt = leave_repo.get_type_by_id(int(lt_id))
        if not lt:
            return False, "Invalid leave type.", None

        total_days = self._count_working_days(start, end)
        if total_days <= 0:
            # Fallback to calendar days for weekend / hospital shift duty
            total_days = max(1, (end - start).days + 1)

        # ── PAID LEAVE (PL) VALIDATION ───────────────────────────────────
        if lt.code.upper() == "PL":
            # Rule 1: Maximum 12 Paid Leaves per calendar year
            year = start.year
            taken_this_year = leave_repo.count_days_taken(employee_id, lt.id, year)
            if taken_this_year + total_days > 12:
                available = max(0, 12 - taken_this_year)
                return False, f"Paid Leave limit exceeded. You have {available} Paid Leave(s) remaining for {year}.", None
            
            # Note: 2-month rule removed as per new requirement
        
        # ── UNLIMITED LEAVE TYPES (CL, SL, COMP) ─────────────────────────
        # No balance validation required for unlimited types
        if lt.max_days_per_year < 999:
            # Only validate balance for limited leave types (e.g., PL)
            year = start.year
            taken = leave_repo.count_days_taken(employee_id, lt.id, year)
            available = lt.max_days_per_year - taken
            if total_days > available:
                return False, f"Insufficient {lt.name} balance. Available: {available:.0f} days.", None

        if leave_repo.has_overlapping(employee_id, start, end):
            return False, "You already have a pending or approved leave for this period.", None

        attachment_path = None
        if attachment and attachment.filename:
            try:
                from app.utils.file_utils import save_file
                attachment_path = save_file(attachment, "leave_attachments",
                                            max_bytes=10 * 1024 * 1024,
                                            allowed_extensions={"pdf", "jpg", "jpeg", "png", "doc", "docx"})
            except Exception as e:
                logger.warning("Leave attachment upload failed: %s", e)

        comp_off_work_date = form_data.get("comp_off_work_date")
        user_reason = form_data.get("reason", "").strip()

        if lt.code.upper() == "CO":
            from .comp_off_service import CompOffService
            comp_svc = CompOffService()
            avail = comp_svc.get_available_comp_offs(employee_id)
            if not avail:
                return False, "You do not have any Comp Off available! Comp Off can only be availed after completing an approved Sunday/Holiday duty of at least 8 hours 30 minutes.", None

            if not comp_off_work_date:
                return False, "Please specify the Sunday or Holiday date on which you performed duty.", None
            if (date.today() - comp_off_work_date).days > 90:
                return False, f"Comp Off for {comp_off_work_date.strftime('%d %b %Y')} has expired (validity is 90 days from the work date).", None
            if total_days > 1:
                return False, "Comp Off can strictly be availed for 1 day per Sunday or Holiday worked.", None

            from app.models.leave import LeaveRequest as LRModel

            # 1. STRICT SINGLE-USE CHECK: Check if this work date was already availed
            already_claimed = LRModel.query.filter(
                LRModel.employee_id == employee_id,
                LRModel.comp_off_work_date == comp_off_work_date,
                LRModel.start_date != comp_off_work_date,
                LRModel.status.in_(["pending", "approved"]),
                LRModel.is_deleted == False
            ).first()
            if already_claimed:
                return False, f"STRICT SINGLE-USE POLICY: The Comp Off for {comp_off_work_date.strftime('%d %b %Y')} has ALREADY been availed on {already_claimed.start_date.strftime('%d %b %Y')} and cannot be claimed again.", None

            # 2. MANAGER APPROVAL CHECK on duty permission request
            duty_req = LRModel.query.filter(
                LRModel.employee_id == employee_id,
                LRModel.comp_off_work_date == comp_off_work_date,
                LRModel.start_date == comp_off_work_date,
                LRModel.is_deleted == False
            ).first()
            if duty_req and duty_req.status != "approved":
                return False, f"Comp Off for {comp_off_work_date.strftime('%d %b %Y')} cannot be credited until your Reporting Manager approves your Sunday/Holiday duty request (Current Status: {duty_req.status.capitalize()}).", None

            # 3. ATTENDANCE VERIFICATION CHECK: Minimum 8h 30m required
            from app.blueprints.leave.comp_off_service import verify_comp_off_attendance
            is_eligible, mins, att_msg = verify_comp_off_attendance(employee_id, comp_off_work_date)
            if not is_eligible:
                return False, f"Comp Off credit requires at least 8 hours 30 minutes of completed duty on {comp_off_work_date.strftime('%d %b %Y')}. ({att_msg})", None

            work_date_str = comp_off_work_date.strftime("%d %b %Y (%a)")
            if f"Sunday/Holiday: {work_date_str}" not in user_reason:
                user_reason = f"{user_reason} [Availing Comp Off for Sunday/Holiday worked on {work_date_str} - STRICT SINGLE-USE]"

        lr = LeaveRequest(
            employee_id=employee_id,
            leave_type_id=lt.id,
            start_date=start,
            end_date=end,
            total_days=total_days,
            reason=user_reason,
            attachment=attachment_path,
            reporting_manager_code=mgr_code,
            reporting_manager_name=mgr_name,
            comp_off_work_date=comp_off_work_date if lt.code.upper() == "CO" else None,
            comp_off_expiry_date=(comp_off_work_date + timedelta(days=90)) if (lt.code.upper() == "CO" and comp_off_work_date) else None,
            comp_off_used_on=datetime.utcnow() if lt.code.upper() == "CO" else None,
            status="pending",
            applied_on=datetime.utcnow(),
            created_by=employee_id,
        )
        
        # ── COMP OFF USAGE TRACKING ───────────────────────────────────────
        # When comp off leave is applied, mark any matching earned credit record as used
        if lt.code.upper() == "CO" and comp_off_work_date:
            from app.models.leave import LeaveRequest as LRModel
            earned_credit = LRModel.query.filter(
                LRModel.employee_id == employee_id,
                LRModel.comp_off_work_date == comp_off_work_date,
                LRModel.comp_off_used_on == None,
                LRModel.status == "approved",
                LRModel.is_deleted == False
            ).first()
            if earned_credit:
                earned_credit.comp_off_used_on = datetime.utcnow()
                db.session.add(earned_credit)
            logger.info("COMP_OFF_USAGE_MARKED | emp=%s | work_date=%s | comp_off_used_on=%s", employee_id, comp_off_work_date, lr.comp_off_used_on)
        
        leave_repo.create(lr)

        # Notify the reporting manager
        self._notify_manager(employee_id, mgr_code, "leave", start, lr.id)
        
        # ── NOTIFY HR WHEN COMP OFF IS USED ───────────────────────────────
        # Trigger HR notification immediately when comp off is applied
        if lt.code.upper() == "CO":
            self._notify_hr_compoff_used(employee_id, lr.id)

        logger.info("LEAVE_APPLIED | emp=%s | type=%s | days=%s | from=%s to=%s | mgr=%s",
                    employee_id, lt.code, total_days, start, end, mgr_code)
        return True, f"{lt.name} leave applied for {total_days} day(s). Awaiting approval.", lr

    def apply_holiday_work_permission(self, employee_id: int, form_data: dict) -> Tuple[bool, str]:
        """
        Record permission / notification to work on Sunday or Company Holiday.
        Saves the Comp Off earned date into the employee's system/portal.
        """
        work_date = form_data.get("work_date")
        reason = form_data.get("reason", "").strip()
        mgr_code = (form_data.get("reporting_manager_code") or "").strip().upper()

        if not work_date or not reason:
            return False, "Work date and purpose of duty are required."
        if not mgr_code:
            return False, "Reporting manager is required."

        # Validate manager
        ok, mgr_name, mgr_err = self._validate_manager(employee_id, mgr_code)
        if not ok:
            return False, mgr_err

        from app.models.leave import LeaveType, LeaveRequest
        comp_off_type = LeaveType.query.filter_by(code='CO').first()
        if not comp_off_type:
            return False, "Comp Off leave type not configured in system."

        # Check if already recorded
        existing = LeaveRequest.query.filter(
            LeaveRequest.employee_id == employee_id,
            LeaveRequest.comp_off_work_date == work_date,
            LeaveRequest.is_deleted == False
        ).first()
        if existing:
            return False, f"Sunday/Holiday duty for {work_date.strftime('%d %b %Y')} is already saved in your portal."

        # Create the Sunday/Holiday Work Permission Request in PENDING status
        credit = LeaveRequest(
            employee_id=employee_id,
            leave_type_id=comp_off_type.id,
            start_date=work_date,
            end_date=work_date,
            total_days=1,
            reason=f"Sunday/Holiday Duty Permission: {reason}",
            reporting_manager_code=mgr_code,
            reporting_manager_name=mgr_name,
            comp_off_work_date=work_date,
            comp_off_expiry_date=work_date + timedelta(days=90),
            status="pending",  # PENDING MANAGER APPROVAL
            applied_on=datetime.utcnow(),
            created_by=employee_id,
        )
        db.session.add(credit)
        db.session.commit()

        # Send notification to Reporting Manager & HR
        try:
            self._notify_manager(employee_id, mgr_code, "leave", work_date, credit.id)
        except Exception as e:
            logger.warning("Holiday work notification failed: %s", e)

        return True, f"Permission request for Sunday/Holiday duty on {work_date.strftime('%d %b %Y')} submitted to {mgr_name}! Awaiting manager approval. (Comp Off will activate once approved by your manager AND at least 8 hours 30 minutes of duty is completed on that day)."

    def approve_leave(self, lr_id: int, reviewer_id: int, comment: str = "") -> Tuple[bool, str]:
        lr = leave_repo.get_by_id(lr_id)
        if not lr:
            return False, "Leave request not found."
        if lr.status != "pending":
            return False, f"Cannot approve a request with status '{lr.status}'."
        
        # ── RE-VALIDATE PAID LEAVE BEFORE APPROVAL ───────────────────────
        if lr.leave_type.code.upper() == "PL":
            year = lr.start_date.year
            # Rule 1: Check yearly limit (exclude this request from count) - 12 days max
            from sqlalchemy import extract  # noqa: PLC0415
            taken_this_year = db.session.query(db.func.sum(LeaveRequest.total_days)).filter(
                and_(
                    LeaveRequest.employee_id == lr.employee_id,
                    LeaveRequest.leave_type_id == lr.leave_type_id,
                    LeaveRequest.status == "approved",
                    LeaveRequest.is_deleted == False,
                    LeaveRequest.id != lr.id,  # exclude current request
                    extract("year", LeaveRequest.start_date) == year
                )
            ).scalar() or 0
            
            if taken_this_year + lr.total_days > 12:
                return False, f"Cannot approve. Employee would exceed 12 Paid Leaves for {year}."
        
        # ── COMP OFF SPECIAL LOGIC ───────────────────────────────────────
        # When comp off is approved, set expiry date to 90 days from today
        if lr.leave_type.code.upper() == "CO":
            from datetime import timedelta  # noqa: PLC0415
            lr.comp_off_expiry_date = date.today() + timedelta(days=90)
            logger.info("COMP_OFF_APPROVED | lr_id=%s | expiry_date=%s", lr_id, lr.comp_off_expiry_date)
        
        lr.status = "approved"
        lr.reviewed_by = reviewer_id
        lr.reviewed_on = datetime.utcnow()
        lr.reviewer_comment = comment
        leave_repo.update(lr)
        # Mark attendance as on_leave for each day
        self._mark_attendance_on_leave(lr)
        logger.info("LEAVE_APPROVED | lr_id=%s | by=%s", lr_id, reviewer_id)
        
        # ── SEND APPROVAL NOTIFICATION TO EMPLOYEE ──────────────────────
        self._notify_leave_employee(lr.employee_id, reviewer_id, lr.leave_type.name, "approved", comment)
        
        return True, "Leave request approved."

    def reject_leave(self, lr_id: int, reviewer_id: int, comment: str = "") -> Tuple[bool, str]:
        lr = leave_repo.get_by_id(lr_id)
        if not lr:
            return False, "Leave request not found."
        if lr.status != "pending":
            return False, f"Cannot reject a request with status '{lr.status}'."
        lr.status = "rejected"
        lr.reviewed_by = reviewer_id
        lr.reviewed_on = datetime.utcnow()
        lr.reviewer_comment = comment
        leave_repo.update(lr)
        logger.info("LEAVE_REJECTED | lr_id=%s | by=%s", lr_id, reviewer_id)
        
        # ── SEND REJECTION NOTIFICATION TO EMPLOYEE ────────────────────
        self._notify_leave_employee(lr.employee_id, reviewer_id, lr.leave_type.name, "rejected", comment)
        
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
        req_date  = form_data.get("date")
        half_type = form_data.get("half_type")
        reason    = form_data.get("reason", "").strip()
        mgr_code  = (form_data.get("reporting_manager_code") or "").strip().upper()

        if not req_date or not half_type or not reason:
            return False, "All fields are required.", None
        if not mgr_code:
            return False, "Reporting Manager Employee Code is required.", None

        if req_date < date.today():
            return False, "Cannot apply half day for a past date.", None

        # Validate manager
        ok, mgr_name, mgr_err = self._validate_manager(employee_id, mgr_code)
        if not ok:
            return False, mgr_err, None

        if leave_repo.has_overlapping(employee_id, req_date, req_date):
            return False, "You already have a leave request for this date.", None

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
            reporting_manager_code=mgr_code,
            reporting_manager_name=mgr_name,
            status="pending",
            applied_on=datetime.utcnow(),
            created_by=employee_id,
        )
        leave_repo.create_halfday(hd)

        # Notify the reporting manager
        self._notify_manager(employee_id, mgr_code, "half_day", req_date, hd.id)

        return True, f"Half-day ({half_type.title()}) request submitted for {req_date.strftime('%d %b %Y')}.", hd

    def approve_halfday(self, hd_id: int, reviewer_id: int, comment: str = "") -> Tuple[bool, str]:
        hd = leave_repo.get_halfday_by_id(hd_id)
        if not hd: return False, "Request not found."
        if hd.status != "pending": return False, "Already processed."
        hd.status = "approved"
        hd.reviewed_by = reviewer_id
        hd.reviewed_on = datetime.utcnow()
        hd.reviewer_comment = comment
        leave_repo.update_halfday(hd)
        att = att_repo.get_today(hd.employee_id, hd.date)
        if att:
            att.is_half_day = True
            att.status = "half_day"
            att_repo.update(att)
        # Notify employee
        self._notify_employee(hd.employee_id, reviewer_id, "half_day", "approved", comment)
        return True, "Half-day request approved."

    def reject_halfday(self, hd_id: int, reviewer_id: int, comment: str = "") -> Tuple[bool, str]:
        hd = leave_repo.get_halfday_by_id(hd_id)
        if not hd: return False, "Request not found."
        if hd.status != "pending": return False, "Already processed."
        hd.status = "rejected"
        hd.reviewed_by = reviewer_id
        hd.reviewed_on = datetime.utcnow()
        hd.reviewer_comment = comment
        leave_repo.update_halfday(hd)
        # Notify employee
        self._notify_employee(hd.employee_id, reviewer_id, "half_day", "rejected", comment)
        return True, "Half-day request rejected."

    # ── Early Leave ───────────────────────────────────────────────────

    def apply_earlyleave(self, employee_id: int, form_data: dict) -> Tuple[bool, str, Optional[EarlyLeaveRequest]]:
        req_date   = form_data.get("date")
        leave_time = form_data.get("requested_leave_time")
        reason     = form_data.get("reason", "").strip()
        mgr_code   = (form_data.get("reporting_manager_code") or "").strip().upper()

        if not req_date or not leave_time or not reason:
            return False, "All fields are required.", None
        if not mgr_code:
            return False, "Reporting Manager Employee Code is required.", None

        if req_date < date.today():
            return False, "Cannot apply early leave for a past date.", None

        ok, mgr_name, mgr_err = self._validate_manager(employee_id, mgr_code)
        if not ok:
            return False, mgr_err, None

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
            reporting_manager_code=mgr_code,
            reporting_manager_name=mgr_name,
            status="pending",
            applied_on=datetime.utcnow(),
            created_by=employee_id,
        )
        leave_repo.create_earlyleave(el)

        # Notify the reporting manager
        self._notify_manager(employee_id, mgr_code, "early_leave", req_date, el.id)

        return True, f"Early leave request submitted for {req_date.strftime('%d %b %Y')}.", el

    def approve_earlyleave(self, el_id: int, reviewer_id: int, comment: str = "") -> Tuple[bool, str]:
        el = leave_repo.get_earlyleave_by_id(el_id)
        if not el: return False, "Request not found."
        if el.status != "pending": return False, "Already processed."
        el.status = "approved"
        el.reviewed_by = reviewer_id
        el.reviewed_on = datetime.utcnow()
        el.reviewer_comment = comment
        leave_repo.update_earlyleave(el)
        att = att_repo.get_today(el.employee_id, el.date)
        if att:
            att.is_early_leave = True
            att_repo.update(att)
        self._notify_employee(el.employee_id, reviewer_id, "early_leave", "approved", comment)
        return True, "Early leave approved."

    def reject_earlyleave(self, el_id: int, reviewer_id: int, comment: str = "") -> Tuple[bool, str]:
        el = leave_repo.get_earlyleave_by_id(el_id)
        if not el: return False, "Request not found."
        if el.status != "pending": return False, "Already processed."
        el.status = "rejected"
        el.reviewed_by = reviewer_id
        el.reviewed_on = datetime.utcnow()
        el.reviewer_comment = comment
        leave_repo.update_earlyleave(el)
        self._notify_employee(el.employee_id, reviewer_id, "early_leave", "rejected", comment)
        return True, "Early leave rejected."

    # ── Helpers ───────────────────────────────────────────────────────

    def _validate_manager(self, employee_id: int, mgr_code: str) -> tuple:
        from app.models.employee_master import EmployeeMaster  # noqa: PLC0415
        from app.models.employee import Employee  # noqa: PLC0415
        emp = Employee.query.filter_by(id=employee_id, is_deleted=False).first()
        if emp and emp.employee_code.upper() == mgr_code:
            return False, "", "You cannot select yourself as Reporting Manager."
        master = EmployeeMaster.query.filter_by(employee_code=mgr_code, is_active=True).first()
        if not master:
            return False, "", "Reporting Manager not found. Please enter a valid Employee Code."
        return True, master.employee_name, ""

    def _notify_manager(self, employee_id: int, mgr_code: str, leave_type: str, req_date, request_id: int) -> None:
        try:
            from app.models.employee import Employee  # noqa: PLC0415
            from app.models.notification import Notification  # noqa: PLC0415
            from app.services.email_notification_service import send_leave_request_to_manager  # noqa: PLC0415
            mgr_code_clean = (mgr_code or "").strip().upper()
            mgr_emp = Employee.query.filter(Employee.employee_code.ilike(mgr_code_clean), Employee.is_deleted == False).first()
            emp = Employee.query.filter_by(id=employee_id, is_deleted=False).first()
            emp_name = emp.full_name if emp else f"Employee #{employee_id}"
            type_label = "Leave" if leave_type == "leave" else ("Half Day" if leave_type == "half_day" else "Early Leave")
            
            # In-App notification
            if mgr_emp and mgr_emp.user_id:
                notif = Notification(
                    user_id=mgr_emp.user_id,
                    title=f"New {type_label} Request",
                    message=f"You have a new {type_label.lower()} request from {emp_name} for {req_date.strftime('%d %b %Y')}.",
                    category="leave",
                    action_url="/leave/my-approvals",
                    action_label="Review Request",
                )
                db.session.add(notif)
                db.session.commit()

            # Retrieve request object for email
            req_obj = None
            if leave_type == "leave":
                req_obj = LeaveRequest.query.get(request_id)
            elif leave_type == "half_day":
                req_obj = HalfDayRequest.query.get(request_id)
            else:
                req_obj = EarlyLeaveRequest.query.get(request_id)

            if req_obj:
                mgr_name = mgr_emp.full_name if mgr_emp else mgr_code
                mgr_email = getattr(mgr_emp, "personal_email", None) if mgr_emp else None
                if not mgr_email and mgr_emp and getattr(mgr_emp, "user", None):
                    mgr_email = mgr_emp.user.email
                
                # Send email to reporting manager with one-click decision buttons
                send_leave_request_to_manager(
                    leave_req=req_obj,
                    employee=emp,
                    manager_name=mgr_name,
                    manager_email=mgr_email,
                    request_type=leave_type
                )

                # Send submission confirmation email to the employee applicant
                try:
                    from app.services.email_notification_service import send_leave_submission_to_employee
                    send_leave_submission_to_employee(
                        leave_req=req_obj,
                        employee=emp,
                        manager_name=mgr_name,
                        request_type=leave_type
                    )
                except Exception as sub_err:
                    logger.warning("Employee leave submission email failed: %s", sub_err)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Manager notification failed: %s", exc)

    def _notify_employee(self, employee_id: int, reviewer_user_id: int, leave_type: str, action: str, comment: str = "") -> None:
        try:
            from app.models.employee import Employee  # noqa: PLC0415
            from app.models.notification import Notification  # noqa: PLC0415
            from app.models.user import User  # noqa: PLC0415
            from app.services.email_notification_service import send_leave_decision_to_employee  # noqa: PLC0415
            emp = Employee.query.filter_by(id=employee_id, is_deleted=False).first()
            if not emp:
                return
            reviewer = User.query.get(reviewer_user_id)
            reviewer_name = reviewer.full_name if reviewer else "Your Manager"
            type_label = "Half Day Leave" if leave_type == "half_day" else "Early Leave"
            if action == "approved":
                msg = f"Your {type_label} has been approved by {reviewer_name}."
                category = "success"
            else:
                msg = f"Your {type_label} has been rejected by {reviewer_name}."
                if comment:
                    msg += f" Reason: {comment}"
                category = "danger"
            notif = Notification(
                user_id=emp.user_id,
                title=f"{type_label} {action.title()}",
                message=msg,
                category=category,
                action_url="/leave",
                action_label="View Request",
            )
            db.session.add(notif)
            db.session.commit()

            # Email notification to employee
            send_leave_decision_to_employee(
                leave_req=None,
                employee=emp,
                action=action,
                reviewer_name=reviewer_name,
                comment=comment,
                request_type=leave_type
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Employee notification failed: %s", exc)

    def _notify_hr_compoff_used(self, employee_id: int, lr_id: int) -> None:
        """Notify HR admins when a comp off is used by an employee."""
        try:
            from app.models.employee import Employee  # noqa: PLC0415
            from app.models.notification import Notification  # noqa: PLC0415
            from app.models.user import User  # noqa: PLC0415
            
            emp = Employee.query.filter_by(id=employee_id, is_deleted=False).first()
            if not emp:
                return
            
            emp_name = emp.full_name or f"Employee #{employee_id}"
            emp_code = emp.employee_code if emp else "N/A"
            
            # Find all HR/Admin/HR Manager/HR Staff users and notify them
            hr_users = User.query.filter(
                User.role.in_(["admin", "hr_manager", "hr_staff"]),
                User.is_active == True,
                User.is_deleted == False
            ).all()
            
            for hr_user in hr_users:
                notif = Notification(
                    user_id=hr_user.id,
                    title="⏰ Compensatory Off Used",
                    message=f"{emp_name} ({emp_code}) has used their compensatory off.",
                    category="warning",
                    action_url="/leave",
                    action_label="View Leave Portal",
                )
                db.session.add(notif)
            
            db.session.commit()
            logger.info("HR_NOTIFIED_COMPOFF_USED | emp=%s | emp_code=%s | lr_id=%s | hr_users=%d", 
                       employee_id, emp_code, lr_id, len(hr_users))
        except Exception as exc:  # noqa: BLE001
            logger.warning("HR comp off notification failed: %s", exc)

    def _notify_leave_employee(self, employee_id: int, reviewer_user_id: int, leave_type_name: str, action: str, comment: str = "") -> None:
        """Send approval/rejection notification for leave requests to employee."""
        try:
            from app.models.employee import Employee  # noqa: PLC0415
            from app.models.notification import Notification  # noqa: PLC0415
            from app.models.user import User  # noqa: PLC0415
            
            emp = Employee.query.filter_by(id=employee_id, is_deleted=False).first()
            if not emp:
                return
            
            reviewer = User.query.get(reviewer_user_id)
            reviewer_name = reviewer.full_name if reviewer else "Your Manager"
            
            if action == "approved":
                msg = f"Your {leave_type_name} request has been approved by {reviewer_name}."
                category = "success"
            else:
                msg = f"Your {leave_type_name} request has been rejected by {reviewer_name}."
                if comment:
                    msg += f" Reason: {comment}"
                category = "danger"
            
            notif = Notification(
                user_id=emp.user_id,
                title=f"{leave_type_name} {action.title()}",
                message=msg,
                category="leave",
                action_url="/leave/",
                action_label="View Request",
                triggered_by=reviewer_user_id,
            )
            db.session.add(notif)
            db.session.commit()
            logger.info("LEAVE_NOTIFICATION | emp=%s | leave_type=%s | action=%s | reviewer=%s", 
                       employee_id, leave_type_name, action, reviewer_user_id)

            # Send email to employee
            try:
                from app.services.email_notification_service import send_leave_decision_to_employee  # noqa: PLC0415
                send_leave_decision_to_employee(
                    leave_req=None,
                    employee=emp,
                    action=action,
                    reviewer_name=reviewer_name,
                    comment=comment,
                    request_type="leave"
                )
            except Exception as mail_err:
                logger.warning("Employee decision email failed: %s", mail_err)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Leave notification failed: %s", exc)

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
