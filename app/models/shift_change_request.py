"""
app/models/shift_change_request.py
====================================
ShiftChangeRequest — employee's request to change work shift
"""

import datetime
from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import BaseModel


class ShiftChangeRequest(BaseModel):
    """Employee shift change request with approval workflow."""
    
    __tablename__ = "shift_change_requests"

    # Employee
    employee_id: Mapped[int] = mapped_column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    
    # Current shift
    current_shift_id: Mapped[int] = mapped_column(Integer, ForeignKey("shifts.id"), nullable=False)
    
    # Requested shift details
    requested_shift_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("shifts.id"), nullable=True)
    requested_start_time: Mapped[datetime.time] = mapped_column(Time, nullable=False)
    requested_end_time: Mapped[datetime.time] = mapped_column(Time, nullable=False)
    
    # Effective date
    effective_date: Mapped[datetime.date] = mapped_column(Date, nullable=False, index=True)
    
    # Request details
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    attachment_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Reporting Manager (who will approve/reject)
    reporting_manager_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    reporting_manager_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    
    # Status
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", index=True
    )  # pending, approved, rejected, returned, cancelled, expired
    
    # Approval workflow
    current_approver_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    current_approver_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Final decision
    approved_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    approved_date: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approval_remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    rejected_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    rejected_date: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Timestamps
    submitted_date: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.datetime.utcnow
    )
    
    # Relationships
    employee = relationship("Employee", foreign_keys=[employee_id], backref="shift_change_requests", lazy="joined")
    current_shift = relationship("Shift", foreign_keys=[current_shift_id], lazy="joined")
    requested_shift = relationship("Shift", foreign_keys=[requested_shift_id], lazy="select")
    current_approver = relationship("User", foreign_keys=[current_approver_id], lazy="select")
    approved_by_user = relationship("User", foreign_keys=[approved_by], lazy="select")
    rejected_by_user = relationship("User", foreign_keys=[rejected_by], lazy="select")
    
    @property
    def is_pending(self) -> bool:
        return self.status == "pending"
    
    @property
    def is_approved(self) -> bool:
        return self.status == "approved"
    
    @property
    def is_rejected(self) -> bool:
        return self.status == "rejected"
    
    @property
    def requested_working_hours(self) -> float:
        """Calculate requested working hours."""
        start = datetime.datetime.combine(datetime.date.today(), self.requested_start_time)
        end = datetime.datetime.combine(datetime.date.today(), self.requested_end_time)
        
        if end <= start:
            end += datetime.timedelta(days=1)
        
        total_minutes = (end - start).total_seconds() / 60
        # Assume 60 min break
        working_minutes = total_minutes - 60
        return round(working_minutes / 60, 2)
    
    def __repr__(self) -> str:
        return f"<ShiftChangeRequest id={self.id} emp={self.employee_id} status={self.status}>"
