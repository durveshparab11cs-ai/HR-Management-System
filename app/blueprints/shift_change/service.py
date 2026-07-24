"""
app/blueprints/shift_change/service.py
========================================
Business logic for Shift Change Management
"""

import datetime
import os
from typing import Tuple, Optional, List, Dict

from flask import current_app
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from app.extensions.database import db
from app.blueprints.shift_change.repository import (
    ShiftRepository,
    EmployeeShiftAssignmentRepository,
    ShiftChangeRequestRepository
)
from app.models.employee import Employee
from app.models.user import User
from app.models.notification import Notification


class ShiftChangeService:
    """Business logic for shift change management."""
    
    def __init__(self):
        self.shift_repo = ShiftRepository()
        self.assignment_repo = EmployeeShiftAssignmentRepository()
        self.request_repo = ShiftChangeRequestRepository()
    
    def get_employee_current_shift(self, employee_id: int, as_of_date: datetime.date = None) -> Optional[Dict]:
        """
        Get employee's current shift assignment.
        
        Returns:
            Dict with shift details or None
        """
        assignment = self.assignment_repo.get_current_assignment(employee_id, as_of_date)
        
        if assignment and assignment.shift:
            return {
                "assignment_id": assignment.id,
                "shift_id": assignment.shift.id,
                "shift_name": assignment.shift.name,
                "shift_code": assignment.shift.code,
                "start_time": assignment.shift.start_time,
                "end_time": assignment.shift.end_time,
                "working_hours": assignment.shift.working_hours,
                "effective_from": assignment.effective_from,
                "effective_until": assignment.effective_until
            }
        
        # Return default shift if no assignment
        default_shift = self.shift_repo.get_default()
        if default_shift:
            return {
                "assignment_id": None,
                "shift_id": default_shift.id,
                "shift_name": default_shift.name + " (Default)",
                "shift_code": default_shift.code,
                "start_time": default_shift.start_time,
                "end_time": default_shift.end_time,
                "working_hours": default_shift.working_hours,
                "effective_from": None,
                "effective_until": None
            }
        
        return None
    
    def submit_shift_change_request(
        self,
        employee_id: int,
        current_shift_id: int,
        requested_start_time: datetime.time,
        requested_end_time: datetime.time,
        effective_date: datetime.date,
        reason: str,
        reporting_manager_code: str,
        remarks: str = None,
        requested_shift_id: int = None,
        attachment: FileStorage = None
    ) -> Tuple[bool, str, Optional[int]]:
        """
        Submit shift change request.
        
        Returns:
            (success: bool, message: str, request_id: int or None)
        """
        try:
            # Validation: reporting manager code
            manager_code = reporting_manager_code.strip().upper()
            if not manager_code:
                return False, "Reporting Manager Code is required", None
            
            # Validate manager exists and get name
            from app.models.employee_master import EmployeeMaster
            manager = EmployeeMaster.query.filter_by(employee_code=manager_code, is_active=True).first()
            if not manager:
                return False, f"Reporting Manager with code {manager_code} not found or inactive", None
            
            # Prevent self-approval
            employee = Employee.query.get(employee_id)
            if employee and employee.employee_code.upper() == manager_code:
                return False, "You cannot select yourself as Reporting Manager", None
            
            manager_name = manager.employee_name
            
            # Validation: effective date not in past
            if effective_date < datetime.date.today():
                return False, "Effective date cannot be in the past", None
            
            # Validation: end time after start time
            if requested_end_time <= requested_start_time:
                # Allow overnight shifts but warn
                if requested_end_time == requested_start_time:
                    return False, "End time must be after start time", None
            
            # Validation: check duplicate
            if self.request_repo.check_duplicate(employee_id, effective_date):
                return False, f"You already have a pending/approved request for {effective_date.strftime('%d %b %Y')}", None
            
            # Validation: working hours
            start_dt = datetime.datetime.combine(datetime.date.today(), requested_start_time)
            end_dt = datetime.datetime.combine(datetime.date.today(), requested_end_time)
            if end_dt <= start_dt:
                end_dt += datetime.timedelta(days=1)
            
            total_hours = (end_dt - start_dt).total_seconds() / 3600
            if total_hours > 14:
                return False, "Shift duration cannot exceed 14 hours", None
            
            # Handle attachment
            attachment_path = None
            if attachment and attachment.filename:
                attachment_path = self._save_attachment(attachment, employee_id)
            
            # Create request
            request = self.request_repo.create(
                employee_id=employee_id,
                current_shift_id=current_shift_id,
                requested_start_time=requested_start_time,
                requested_end_time=requested_end_time,
                effective_date=effective_date,
                reason=reason,
                attachment_path=attachment_path,
                remarks=remarks,
                requested_shift_id=requested_shift_id,
                reporting_manager_code=manager_code,
                reporting_manager_name=manager_name
            )
            
            # Find manager's user account and set as approver
            manager_emp = Employee.query.filter_by(employee_code=manager_code).first()
            if manager_emp and manager_emp.user_id:
                self.request_repo.update_approver(request.id, "Manager", manager_emp.user_id)
                
                # Notify manager
                self._send_notification(
                    user_id=manager_emp.user_id,
                    title="New Shift Change Request",
                    message=f"{employee.name} ({employee.employee_code}) has requested a shift change effective from {effective_date.strftime('%d %b %Y')}",
                    category="shift_change",
                    link=f"/shift-change/approvals/{request.id}"
                )
            
            db.session.commit()
            
            return True, f"Shift change request submitted successfully to {manager_name}", request.id
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error submitting shift change request: {str(e)}")
            return False, f"Error: {str(e)}", None
    
    def approve_request(
        self,
        request_id: int,
        approver_id: int,
        remarks: str,
        action: str = "approve"
    ) -> Tuple[bool, str]:
        """
        Approve, reject, or return shift change request.
        
        Args:
            request_id: Request ID
            approver_id: Approver user ID
            remarks: Approval/rejection remarks
            action: "approve", "reject", or "return"
        
        Returns:
            (success: bool, message: str)
        """
        try:
            request = self.request_repo.get_by_id(request_id)
            if not request:
                return False, "Request not found"
            
            if request.status != "pending":
                return False, f"Request is already {request.status}"
            
            # Verify approver
            if request.current_approver_id != approver_id:
                # Check if user has permission (HR, Admin, CEO can override)
                approver = User.query.get(approver_id)
                if not approver or approver.role not in ["super_admin", "hr", "ceo"]:
                    return False, "You are not authorized to approve this request"
            
            if action == "reject":
                # Reject request
                self.request_repo.update_status(request_id, "rejected", approver_id, remarks)
                
                # Notify employee
                self._send_notification(
                    user_id=request.employee.user_id,
                    title="Shift Change Request Rejected",
                    message=f"Your shift change request for {request.effective_date.strftime('%d %b %Y')} has been rejected. Reason: {remarks}",
                    category="shift_change",
                    link=f"/shift-change/my-requests"
                )
                
                db.session.commit()
                return True, "Request rejected successfully"
            
            elif action == "return":
                # Return for correction
                self.request_repo.update_status(request_id, "returned", approver_id, remarks)
                
                # Notify employee
                self._send_notification(
                    user_id=request.employee.user_id,
                    title="Shift Change Request Returned",
                    message=f"Your shift change request for {request.effective_date.strftime('%d %b %Y')} has been returned for correction. Remarks: {remarks}",
                    category="shift_change",
                    link=f"/shift-change/my-requests"
                )
                
                db.session.commit()
                return True, "Request returned for correction"
            
            elif action == "approve":
                # Check if this is final approval or needs escalation
                approver = User.query.get(approver_id)
                needs_escalation = self._needs_escalation(request, approver)
                
                if needs_escalation:
                    # Escalate to next level
                    next_approver = self._get_next_approver(request, approver)
                    if next_approver:
                        self.request_repo.update_approver(
                            request_id,
                            next_approver["level"],
                            next_approver["user_id"]
                        )
                        
                        # Notify next approver
                        self._send_notification(
                            user_id=next_approver["user_id"],
                            title="Shift Change Request Escalated",
                            message=f"{request.employee.name} ({request.employee.employee_code}) shift change request needs your approval",
                            category="shift_change",
                            link=f"/shift-change/approvals/{request_id}"
                        )
                        
                        db.session.commit()
                        return True, f"Request forwarded to {next_approver['level']} for approval"
                
                # Final approval - create shift assignment
                self.request_repo.update_status(request_id, "approved", approver_id, remarks)
                
                # Get current assignment
                current_assignment = self.assignment_repo.get_current_assignment(request.employee_id)
                previous_shift_id = current_assignment.shift_id if current_assignment else None
                
                # Close previous assignment
                self.assignment_repo.close_previous_assignment(
                    request.employee_id,
                    request.effective_date
                )
                
                # Create new assignment
                # Determine shift ID: use requested_shift_id if selected, otherwise create custom
                shift_id = request.requested_shift_id if request.requested_shift_id else request.current_shift_id
                
                self.assignment_repo.create_assignment(
                    employee_id=request.employee_id,
                    shift_id=shift_id,
                    effective_from=request.effective_date,
                    assigned_by=approver_id,
                    reason=request.reason,
                    remarks=f"Approved shift change request #{request_id}. {remarks}",
                    previous_shift_id=previous_shift_id,
                    shift_change_request_id=request_id
                )
                
                # Notify employee
                self._send_notification(
                    user_id=request.employee.user_id,
                    title="Shift Change Request Approved",
                    message=f"Your shift change request has been approved! New shift effective from {request.effective_date.strftime('%d %b %Y')}",
                    category="shift_change",
                    link=f"/shift-change/my-requests"
                )
                
                db.session.commit()
                return True, "Request approved and shift assignment updated successfully"
            
            return False, "Invalid action"
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error processing shift change request: {str(e)}")
            return False, f"Error: {str(e)}"
    
    def cancel_request(self, request_id: int, employee_id: int) -> Tuple[bool, str]:
        """Cancel pending request (employee only)."""
        try:
            request = self.request_repo.get_by_id(request_id)
            if not request:
                return False, "Request not found"
            
            if request.employee_id != employee_id:
                return False, "You can only cancel your own requests"
            
            if request.status != "pending":
                return False, f"Cannot cancel {request.status} request"
            
            if self.request_repo.cancel_request(request_id):
                db.session.commit()
                return True, "Request cancelled successfully"
            
            return False, "Failed to cancel request"
            
        except Exception as e:
            db.session.rollback()
            return False, f"Error: {str(e)}"
    
    def get_shift_for_attendance(
        self,
        employee_id: int,
        attendance_date: datetime.date
    ) -> Optional[Dict]:
        """
        Get employee's shift for a specific attendance date.
        This is used by attendance engine to calculate working hours.
        
        Returns:
            Dict with shift details
        """
        return self.get_employee_current_shift(employee_id, attendance_date)
    
    # Helper methods
    
    def _needs_escalation(self, request: 'ShiftChangeRequest', approver: User) -> bool:
        """Check if request needs escalation to higher authority."""
        # Manager approved -> escalate to AGM (if exists)
        if approver.role == "manager":
            return True
        
        # AGM approved -> escalate to CEO/HR
        if approver.role == "agm":
            return True
        
        # CEO/HR/Admin -> final approval
        return False
    
    def _get_next_approver(self, request: 'ShiftChangeRequest', current_approver: User) -> Optional[Dict]:
        """Get next approver in hierarchy."""
        # Manager -> AGM
        if current_approver.role == "manager":
            agm = User.query.filter_by(role="agm", is_active=True).first()
            if agm:
                return {"level": "AGM", "user_id": agm.id}
            # Skip to CEO if no AGM
            ceo = User.query.filter_by(role="ceo", is_active=True).first()
            if ceo:
                return {"level": "CEO", "user_id": ceo.id}
        
        # AGM -> CEO
        if current_approver.role == "agm":
            ceo = User.query.filter_by(role="ceo", is_active=True).first()
            if ceo:
                return {"level": "CEO", "user_id": ceo.id}
            # Fallback to HR
            hr = User.query.filter_by(role="hr", is_active=True).first()
            if hr:
                return {"level": "HR", "user_id": hr.id}
        
        return None
    
    def _save_attachment(self, file: FileStorage, employee_id: int) -> str:
        """Save uploaded attachment."""
        if not file or not file.filename:
            return None
        
        # Secure filename
        filename = secure_filename(file.filename)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"shift_change_{employee_id}_{timestamp}_{filename}"
        
        # Upload directory
        upload_dir = os.path.join(current_app.config.get("UPLOAD_FOLDER", "instance/uploads"), "shift_changes")
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file
        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)
        
        # Return relative path
        return os.path.join("shift_changes", filename)
    
    def _send_notification(
        self,
        user_id: int,
        title: str,
        message: str,
        category: str,
        link: str = None
    ):
        """Send notification to user."""
        try:
            notification = Notification(
                user_id=user_id,
                title=title,
                message=message,
                category=category,
                link=link,
                is_read=False,
                created_at=datetime.datetime.utcnow()
            )
            db.session.add(notification)
        except Exception as e:
            current_app.logger.error(f"Error sending notification: {str(e)}")
