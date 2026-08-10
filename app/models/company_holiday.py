"""
app/models/company_holiday.py
================================
Company Holiday model for storing official company holidays.

Stores:
    - holiday_date: The date of the holiday
    - holiday_name: Name of the holiday
    - holiday_type: Type (e.g., National Holiday, Company Holiday, Regional Holiday)
    - description: Optional description/details
"""

from datetime import date
from sqlalchemy import Date, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import BaseModel


class CompanyHoliday(BaseModel):
    """Company holiday calendar entry."""
    __tablename__ = "company_holidays"

    holiday_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    holiday_name: Mapped[str] = mapped_column(String(200), nullable=False)
    holiday_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Unique constraint: prevent duplicate holidays (same date + name)
    __table_args__ = (
        UniqueConstraint('holiday_date', 'holiday_name', name='uk_holiday_date_name'),
    )

    def __repr__(self) -> str:
        return f"<CompanyHoliday id={self.id} date={self.holiday_date} name={self.holiday_name!r}>"
