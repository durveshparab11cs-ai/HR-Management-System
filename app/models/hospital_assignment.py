"""
app/models/hospital_assignment.py
==================================
Employee Hospital Assignment model — tracks which hospital each employee is assigned to.
"""

from datetime import date
from sqlalchemy import Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import BaseModel


class EmployeeHospitalAssignment(BaseModel):
    """Track hospital assignments for employees."""
    __tablename__ = "employee_hospital_assignments"

    # ── Relationships ────────────────────────────────────────────────
    employee_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("employees.id"), nullable=False, index=True
    )
    hospital_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("hospitals.id"), nullable=True, index=True
    )

    # ── Assignment Details ───────────────────────────────────────────
    hospital_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    effective_from: Mapped[date | None] = mapped_column(Date, nullable=True, default=date.today)
    effective_until: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Relationships ────────────────────────────────────────────────
    employee = relationship("Employee", foreign_keys=[employee_id], lazy="joined")

    def __repr__(self) -> str:
        return f"<EmployeeHospitalAssignment id={self.id} emp_id={self.employee_id} hospital={self.hospital_name!r}>"
