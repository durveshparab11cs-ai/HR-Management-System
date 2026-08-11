"""
app/blueprints/leave/comp_off_service.py
==========================================
Compensatory Off Management Service

Rules:
- Employee works on holiday → eligible for 1 comp off
- Can use within 90 days of earning
- Can use only ONCE per comp off earned
- HR notified immediately when used
"""

import logging
from datetime import date, datetime, timedelta
from typing import Optional, Tuple

from app.extensions.database import db
from app.models.leave import LeaveRequest, LeaveType
from sqlalchemy import and_

logger = logging.getLogger(__name__)


class CompOffService:
    """Service for managing Compensatory Off (Comp Off)."""

    def earn_comp_off(
        self,
        employee_id: int,
        work_date: date,
        holiday_name: str = "",
    ) -> Tuple[bool, str]:
        """
        Record that employee worked on a holiday and earned comp off.
        
        Args:
            employee_id: Employee who worked on holiday
            work_date: Date employee worked (holiday date)
            holiday_name: Name of holiday (optional)
        
        Returns:
            (success, message)
        """
        try:
            from app.models.employee import Employee  # noqa: PLC0415
            
            emp = Employee.query.get(employee_id)
            if not emp:
                return False, "Employee not found."
            
            # Get Comp Off leave type
            comp_off_type = LeaveType.query.filter_by(code='CO').first()
            if not comp_off_type:
                logger.error("Comp Off leave type not found in system")
                return False, "Comp Off not configured in system."
            
            # Create comp off record (not yet used, just earned)
            comp_off = LeaveRequest(
                employee_id=employee_id,
                leave_type_id=comp_off_type.id,
                start_date=work_date,
                end_date=work_date,
                total_days=1,
                reason=f"Worked on holiday: {holiday_name}",
                status="approved",  # Auto-approved when earned
                comp_off_work_date=work_date,
                comp_off_expiry_date=work_date + timedelta(days=90),
                comp_off_notified=False,
                applied_on=datetime.utcnow(),
                reviewed_on=datetime.utcnow(),
                created_by=employee_id,
            )
            
            db.session.add(comp_off)
            db.session.commit()
            
            logger.info(
                "COMP_OFF_EARNED | emp=%s | work_date=%s | expiry=%s | holiday=%s",
                employee_id, work_date, comp_off.comp_off_expiry_date, holiday_name
            )
            return True, f"Comp off earned for {work_date.strftime('%d %b %Y')}. Valid until {comp_off.comp_off_expiry_date.strftime('%d %b %Y')}."
            
        except Exception as e:
            logger.error("Error earning comp off: %s", e, exc_info=True)
            db.session.rollback()
            return False, "Error recording comp off."

    def get_available_comp_offs(self, employee_id: int) -> list:
        """
        Get all available (unused, not expired) comp offs for an employee.
        
        Returns:
            List of LeaveRequest objects (earned comp offs)
        """
        today = date.today()
        
        comp_offs = LeaveRequest.query.filter(
            and_(
                LeaveRequest.employee_id == employee_id,
                LeaveRequest.status == "approved",
                LeaveRequest.comp_off_work_date != None,  # Only earned comp offs
                LeaveRequest.comp_off_expiry_date >= today,  # Not expired
                LeaveRequest.comp_off_used_on == None,  # Not yet used
                LeaveRequest.is_deleted == False,
            )
        ).order_by(LeaveRequest.comp_off_expiry_date.asc()).all()
        
        return comp_offs

    def mark_comp_off_used(
        self,
        leave_request_id: int,
        employee_id: int,
    ) -> Tuple[bool, str]:
        """
        Mark comp off as used when employee takes the leave.
        Immediately notify HR admins.
        
        Args:
            leave_request_id: The leave request ID for comp off
            employee_id: Employee using the comp off
        
        Returns:
            (success, message)
        """
        try:
            from app.models.employee import Employee  # noqa: PLC0415
            from app.models.user import User  # noqa: PLC0415
            from app.models.notification import Notification  # noqa: PLC0415
            
            lr = LeaveRequest.query.get(leave_request_id)
            if not lr:
                return False, "Leave request not found."
            
            if lr.leave_type.code != 'CO':
                return False, "This is not a comp off leave."
            
            if lr.comp_off_used_on:
                return False, "Comp off already used."
            
            # Mark as used
            lr.comp_off_used_on = datetime.utcnow()
            db.session.add(lr)
            db.session.flush()
            
            # Notify all HR admins
            emp = Employee.query.get(employee_id)
            emp_name = emp.user.full_name if emp and emp.user else f"Employee {employee_id}"
            
            hr_users = User.query.filter(
                User.role.in_(["admin", "hr_manager", "hr_staff"]),
                User.is_active == True,
                User.is_deleted == False
            ).all()
            
            for hr_user in hr_users:
                notif = Notification(
                    user_id=hr_user.id,
                    title="⏰ Comp Off Used",
                    message=f"{emp_name} has used their compensatory off on {lr.start_date.strftime('%d %b %Y')}",
                    category="warning",
                )
                db.session.add(notif)
            
            db.session.commit()
            
            logger.info(
                "COMP_OFF_USED | emp=%s | lr_id=%s | used_on=%s | notified_hr=%d",
                employee_id, leave_request_id, lr.comp_off_used_on, len(hr_users)
            )
            return True, "Comp off marked as used. HR notified."
            
        except Exception as e:
            logger.error("Error marking comp off as used: %s", e, exc_info=True)
            db.session.rollback()
            return False, "Error updating comp off status."

    def check_expired_comp_offs(self, employee_id: int) -> dict:
        """
        Check for expired (unused) comp offs.
        
        Returns:
            {
                "expired_count": int,
                "expiring_soon": list of dicts,
                "expired": list of dicts
            }
        """
        today = date.today()
        
        # Find comp offs that expired today or before
        expired = LeaveRequest.query.filter(
            and_(
                LeaveRequest.employee_id == employee_id,
                LeaveRequest.status == "approved",
                LeaveRequest.comp_off_work_date != None,
                LeaveRequest.comp_off_expiry_date < today,
                LeaveRequest.comp_off_used_on == None,  # Never used
                LeaveRequest.is_deleted == False,
            )
        ).all()
        
        # Find comp offs expiring in next 7 days
        expiring_soon = LeaveRequest.query.filter(
            and_(
                LeaveRequest.employee_id == employee_id,
                LeaveRequest.status == "approved",
                LeaveRequest.comp_off_work_date != None,
                LeaveRequest.comp_off_expiry_date >= today,
                LeaveRequest.comp_off_expiry_date <= today + timedelta(days=7),
                LeaveRequest.comp_off_used_on == None,
                LeaveRequest.is_deleted == False,
            )
        ).all()
        
        return {
            "expired_count": len(expired),
            "expiring_soon": [
                {
                    "id": co.id,
                    "work_date": co.comp_off_work_date,
                    "expires": co.comp_off_expiry_date,
                    "days_left": (co.comp_off_expiry_date - today).days,
                }
                for co in expiring_soon
            ],
            "expired": [
                {
                    "id": co.id,
                    "work_date": co.comp_off_work_date,
                    "expired_on": co.comp_off_expiry_date,
                }
                for co in expired
            ],
        }
