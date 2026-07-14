"""
app/models/payroll.py
======================
Payroll models: SalaryStructure, SalaryComponent, PayrollRun, Payslip.
"""

import datetime
from sqlalchemy import Boolean, Date, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import BaseModel
from app.extensions.database import db


class SalaryStructure(BaseModel):
    """Template defining salary components for a grade/role."""
    __tablename__ = "salary_structures"

    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    code: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    components = relationship("SalaryComponent", backref="structure", lazy="select",
                              foreign_keys="SalaryComponent.structure_id")

    def __repr__(self) -> str:
        return f"<SalaryStructure {self.code!r}>"


class SalaryComponent(BaseModel):
    """Individual earning or deduction within a salary structure."""
    __tablename__ = "salary_components"

    structure_id: Mapped[int] = mapped_column(Integer, ForeignKey("salary_structures.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    component_type: Mapped[str] = mapped_column(String(20), nullable=False, default="earning")
    # earning | deduction | tax | reimbursement
    calculation_type: Mapped[str] = mapped_column(String(20), nullable=False, default="fixed")
    # fixed | percentage_of_basic | percentage_of_gross
    value: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    is_taxable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    def __repr__(self) -> str:
        return f"<SalaryComponent {self.name!r} {self.component_type!r}>"


class PayrollRun(BaseModel):
    """Monthly payroll processing run."""
    __tablename__ = "payroll_runs"

    month: Mapped[int] = mapped_column(Integer, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    period_label: Mapped[str] = mapped_column(String(20), nullable=False)  # "July 2026"
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft", index=True)
    # draft | processing | processed | approved | paid | cancelled
    total_gross: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    total_deductions: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    total_net: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    employee_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    approved_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    approved_on: Mapped[datetime.datetime | None] = mapped_column(db.DateTime(timezone=True), nullable=True)

    payslips = relationship("Payslip", backref="run", lazy="select")

    @property
    def period(self) -> str:
        return self.period_label or f"{self.month:02d}/{self.year}"

    def __repr__(self) -> str:
        return f"<PayrollRun {self.period_label!r} status={self.status!r}>"


class Payslip(BaseModel):
    """Individual employee payslip for a payroll run."""
    __tablename__ = "payslips"

    run_id: Mapped[int] = mapped_column(Integer, ForeignKey("payroll_runs.id"), nullable=False, index=True)
    employee_id: Mapped[int] = mapped_column(Integer, ForeignKey("employees.id"), nullable=False, index=True)

    # Salary details
    basic_salary: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    gross_salary: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    total_deductions: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    net_salary: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Attendance-based
    working_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    days_present: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    days_absent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    leave_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Breakdown (stored as text — JSON string)
    earnings_breakdown: Mapped[str | None] = mapped_column(Text, nullable=True)
    deductions_breakdown: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    employee = relationship("Employee", foreign_keys=[employee_id], lazy="joined")

    @property
    def net_display(self) -> str:
        return f"₹{self.net_salary:,.2f}"

    def __repr__(self) -> str:
        return f"<Payslip id={self.id} emp={self.employee_id} run={self.run_id}>"
