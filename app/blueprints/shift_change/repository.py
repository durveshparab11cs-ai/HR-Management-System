"""
app/blueprints/shift_change/repository.py
===========================================
Data access layer for Shift Change Management
"""

import datetime
from typing import List, Optional

from sqlalchemy import and_, or_, desc, asc
from sqlalchemy.orm import joinedload

from app.extensions.database import db
from app.models.employee_shift_assignment import EmployeeShiftAssignment
from app.models.shift_change_request import ShiftChangeRequest
from app.models.company import Shift
from app.models.employee import Employee


class ShiftRepository:
    """Repository for Shift operations."""
    
    @staticmethod
    def get_all_active() -> List[Shift]:
        """Get all active shifts."""
        return Shift.query.filter_by(is_active=True).order_by(Shift.name).all()
    
    @staticmethod
    def get_by_id(shift_id: int) -> Optional[Shift]:
        """Get shift by ID."""
        return Shift.query.get(shift_id)
    
    @staticmethod
    def get_by_code(code: str) -> Optional[Shift]:
        """Get shift by code."""
        return Shift.query.filter_by(code=code).first()
    
    @staticmethod
    def get_default() -> Optional[Shift]:
        """Get default shift."""
        return Shift.query.filter_by(is_active=True).order_by(Shift.id).first()


class EmployeeShiftAssignmentRepository:
    """Repository for Employee Shift Assignment operations."""
    
    @staticmethod
    def get_current_assignment(employee_id: int, as_of_date: datetime.date = None) -> Optional[EmployeeShiftAssignment]:
        """
        Get employee's current shift assignment.
        
        Args:
            employee_id: Employee ID
            as_of_date: Date to check (default: today)
        
        Returns:
            Active assignment or None
        """
        if as_of_date is None:
            as_of_date = datetime.date.today()
        
        return EmployeeShiftAssignment.query.filter(
            and_(
                EmployeeShiftAssignment.employee_id == employee_id,
                EmployeeShiftAssignment.effective_from <= as_of_date,
                or_(
                    EmployeeShiftAssignment.effective_until.is_(None),
                    EmployeeShiftAssignment.effective_until >= as_of_date
                )
            )
        ).options(joinedload(EmployeeShiftAssignment.shift)).first()
    
    @staticmethod
    def get_assignment_history(employee_id: int, limit: int = 50) -> List[EmployeeShiftAssignment]:
        """Get employee's shift assignment history."""
        return EmployeeShiftAssignment.query.filter_by(
            employee_id=employee_id
        ).options(
            joinedload(EmployeeShiftAssignment.shift),
            joinedload(EmployeeShiftAssignment.previous_shift)
        ).order_by(desc(EmployeeShiftAssignment.effective_from)).limit(limit).all()
    
    @staticmethod
    def create_assignment(
        employee_id: int,
        shift_id: int,
        effective_from: datetime.date,
        assigned_by: int,
        reason: str = None,
        remarks: str = None,
        previous_shift_id: int = None,
        shift_change_request_id: int = None
    ) -> EmployeeShiftAssignment:
        """Create new shift assignment."""
        assignment = EmployeeShiftAssignment(
            employee_id=employee_id,
            shift_id=shift_id,
            effective_from=effective_from,
            assigned_by=assigned_by,
            assigned_date=datetime.datetime.utcnow(),
            reason=reason,
            remarks=remarks,
            previous_shift_id=previous_shift_id,
            shift_change_request_id=shift_change_request_id
        )
        db.session.add(assignment)
        return assignment
    
    @staticmethod
    def close_previous_assignment(employee_id: int, effective_until: datetime.date):
        """Close previous open-ended assignment."""
        # Find current open-ended assignment
        current = EmployeeShiftAssignment.query.filter(
            and_(
                EmployeeShiftAssignment.employee_id == employee_id,
                EmployeeShiftAssignment.effective_until.is_(None),
                EmployeeShiftAssignment.effective_from < effective_until
            )
        ).first()
        
        if current:
            # Close it one day before new assignment
            current.effective_until = effective_until - datetime.timedelta(days=1)
            db.session.add(current)
            return current
        return None


class ShiftChangeRequestRepository:
    """Repository for Shift Change Request operations."""
    
    @staticmethod
    def create(
        employee_id: int,
        current_shift_id: int,
        requested_start_time: datetime.time,
        requested_end_time: datetime.time,
        effective_date: datetime.date,
        reason: str,
        attachment_path: str = None,
        remarks: str = None,
        requested_shift_id: int = None
    ) -> ShiftChangeRequest:
        """Create new shift change request."""
        request = ShiftChangeRequest(
            employee_id=employee_id,
            current_shift_id=current_shift_id,
            requested_shift_id=requested_shift_id,
            requested_start_time=requested_start_time,
            requested_end_time=requested_end_time,
            effective_date=effective_date,
            reason=reason,
            attachment_path=attachment_path,
            remarks=remarks,
            status="pending",
            submitted_date=datetime.datetime.utcnow()
        )
        db.session.add(request)
        return request
    
    @staticmethod
    def get_by_id(request_id: int) -> Optional[ShiftChangeRequest]:
        """Get request by ID."""
        return ShiftChangeRequest.query.options(
            joinedload(ShiftChangeRequest.employee),
            joinedload(ShiftChangeRequest.current_shift),
            joinedload(ShiftChangeRequest.requested_shift)
        ).get(request_id)
    
    @staticmethod
    def get_employee_requests(employee_id: int, limit: int = 50) -> List[ShiftChangeRequest]:
        """Get all requests by employee."""
        return ShiftChangeRequest.query.filter_by(
            employee_id=employee_id
        ).options(
            joinedload(ShiftChangeRequest.current_shift),
            joinedload(ShiftChangeRequest.requested_shift)
        ).order_by(desc(ShiftChangeRequest.submitted_date)).limit(limit).all()
    
    @staticmethod
    def get_pending_requests_for_approver(approver_id: int) -> List[ShiftChangeRequest]:
        """Get pending requests for specific approver."""
        return ShiftChangeRequest.query.filter(
            and_(
                ShiftChangeRequest.status == "pending",
                ShiftChangeRequest.current_approver_id == approver_id
            )
        ).options(
            joinedload(ShiftChangeRequest.employee),
            joinedload(ShiftChangeRequest.current_shift)
        ).order_by(asc(ShiftChangeRequest.submitted_date)).all()
    
    @staticmethod
    def get_all_requests(
        status: str = None,
        employee_id: int = None,
        from_date: datetime.date = None,
        to_date: datetime.date = None,
        limit: int = 100
    ) -> List[ShiftChangeRequest]:
        """Get filtered requests."""
        query = ShiftChangeRequest.query
        
        if status:
            query = query.filter_by(status=status)
        
        if employee_id:
            query = query.filter_by(employee_id=employee_id)
        
        if from_date:
            query = query.filter(ShiftChangeRequest.effective_date >= from_date)
        
        if to_date:
            query = query.filter(ShiftChangeRequest.effective_date <= to_date)
        
        return query.options(
            joinedload(ShiftChangeRequest.employee),
            joinedload(ShiftChangeRequest.current_shift)
        ).order_by(desc(ShiftChangeRequest.submitted_date)).limit(limit).all()
    
    @staticmethod
    def check_duplicate(employee_id: int, effective_date: datetime.date) -> bool:
        """Check if employee already has pending request for this date."""
        existing = ShiftChangeRequest.query.filter(
            and_(
                ShiftChangeRequest.employee_id == employee_id,
                ShiftChangeRequest.effective_date == effective_date,
                ShiftChangeRequest.status.in_(["pending", "approved"])
            )
        ).first()
        return existing is not None
    
    @staticmethod
    def update_status(
        request_id: int,
        status: str,
        approver_id: int,
        remarks: str
    ) -> Optional[ShiftChangeRequest]:
        """Update request status."""
        request = ShiftChangeRequestRepository.get_by_id(request_id)
        if not request:
            return None
        
        request.status = status
        
        if status == "approved":
            request.approved_by = approver_id
            request.approved_date = datetime.datetime.utcnow()
            request.approval_remarks = remarks
        elif status == "rejected":
            request.rejected_by = approver_id
            request.rejected_date = datetime.datetime.utcnow()
            request.rejection_reason = remarks
        
        db.session.add(request)
        return request
    
    @staticmethod
    def update_approver(request_id: int, approver_level: str, approver_id: int):
        """Update current approver."""
        request = ShiftChangeRequestRepository.get_by_id(request_id)
        if request:
            request.current_approver_level = approver_level
            request.current_approver_id = approver_id
            db.session.add(request)
    
    @staticmethod
    def cancel_request(request_id: int) -> bool:
        """Cancel a pending request."""
        request = ShiftChangeRequestRepository.get_by_id(request_id)
        if request and request.status == "pending":
            request.status = "cancelled"
            db.session.add(request)
            return True
        return False
