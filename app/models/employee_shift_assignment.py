"""
app/models/employee_shift_assignment.py
=========================================
EmployeeShiftAssignment — tracks employee's shift over time
"""

import datetime
from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import BaseModel


class EmployeeShiftAssignment(BaseModel):
    """Employee shift assignment with effective date range."""
    
    __tablename__ = "employee_shift_assignments"

    # Employee
    employee_id: Mapped[int] = mapped_column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    
    # Shift
    shift_id: Mapped[int] = mapped_column(Integer, ForeignKey("shifts.id"), nullable=False)
    
    # Effective date range
    effective_from: Mapped[datetime.date] = mapped_column(Date, nullable=False, index=True)
    effective_until: Mapped[datetime.date | None] = mapped_column(Date, nullable=True, index=True)
    
    # Assignment info
    assigned_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_date: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.datetime.utcnow
    )
    
    # Related shift change request (if applicable)
    shift_change_request_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("shift_change_requests.id"), nullable=True
    )
    
    # Reason
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Previous shift (for audit trail)
    previous_shift_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("shifts.id"), nullable=True)
    
    # Relationships
    employee = relationship("Employee", foreign_keys=[employee_id], backref="shift_assignments", lazy="select")
    shift = relationship("Shift", foreign_keys=[shift_id], lazy="joined")
    previous_shift = relationship("Shift", foreign_keys=[previous_shift_id], lazy="select")
    assigned_by_user = relationship("User", foreign_keys=[assigned_by], lazy="select")
    
    def __repr__(self) -> str:
        return f"<EmployeeShiftAssignment emp={self.employee_id} shift={self.shift_id} from={self.effective_from}>"
