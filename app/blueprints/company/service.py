"""
blueprints/company/service.py
================================
Company module service — business logic for all company entities.
"""

import logging
from typing import Optional, Tuple

from app.extensions.database import db
from app.models.company import CompanyProfile, Department, Position, Shift

logger = logging.getLogger(__name__)


class CompanyService:

    # ── Company Profile ───────────────────────────────────────────────

    def get_or_create_profile(self) -> CompanyProfile:
        profile = CompanyProfile.query.filter_by(is_deleted=False).first()
        if not profile:
            profile = CompanyProfile(name="My Company", created_by=1)
            db.session.add(profile)
            db.session.commit()
        return profile

    def update_profile(self, data: dict) -> Tuple[bool, str]:
        profile = self.get_or_create_profile()
        try:
            for key, val in data.items():
                if hasattr(profile, key):
                    setattr(profile, key, val)
            db.session.commit()
            return True, "Company profile updated successfully."
        except Exception as e:
            db.session.rollback()
            logger.error("Company profile update failed: %s", e)
            return False, "Failed to update company profile."

    # ── Departments ───────────────────────────────────────────────────

    def get_all_departments(self) -> list:
        return Department.query.filter_by(is_deleted=False).order_by(Department.name).all()

    def get_department(self, dept_id: int) -> Optional[Department]:
        return Department.query.filter_by(id=dept_id, is_deleted=False).first()

    def create_department(self, data: dict) -> Tuple[bool, str, Optional[Department]]:
        existing = Department.query.filter_by(code=data.get("code", "").upper(), is_deleted=False).first()
        if existing:
            return False, f"Department code '{data['code'].upper()}' already exists.", None
        try:
            dept = Department(
                name=data["name"].strip(),
                code=data["code"].strip().upper(),
                description=data.get("description", "").strip() or None,
                color=data.get("color", "#1a3c6e"),
                is_active=True,
                created_by=data.get("created_by"),
            )
            db.session.add(dept)
            db.session.commit()
            logger.info("Department created: %s", dept.name)
            return True, f"Department '{dept.name}' created.", dept
        except Exception as e:
            db.session.rollback()
            return False, f"Failed to create department: {e}", None

    def update_department(self, dept_id: int, data: dict) -> Tuple[bool, str]:
        dept = self.get_department(dept_id)
        if not dept:
            return False, "Department not found."
        try:
            for key, val in data.items():
                if hasattr(dept, key):
                    setattr(dept, key, val)
            db.session.commit()
            return True, "Department updated."
        except Exception as e:
            db.session.rollback()
            return False, f"Update failed: {e}"

    def delete_department(self, dept_id: int, deleted_by: int) -> Tuple[bool, str]:
        dept = self.get_department(dept_id)
        if not dept:
            return False, "Department not found."
        dept.soft_delete(deleted_by_id=deleted_by)
        return True, "Department removed."

    # ── Positions ─────────────────────────────────────────────────────

    def get_all_positions(self) -> list:
        return Position.query.filter_by(is_deleted=False).order_by(Position.title).all()

    def create_position(self, data: dict) -> Tuple[bool, str, Optional[Position]]:
        existing = Position.query.filter_by(code=data.get("code", "").upper(), is_deleted=False).first()
        if existing:
            return False, f"Position code '{data['code'].upper()}' already exists.", None
        try:
            pos = Position(
                title=data["title"].strip(),
                code=data["code"].strip().upper(),
                department_id=data.get("department_id") or None,
                grade=data.get("grade", "").strip() or None,
                description=data.get("description", "").strip() or None,
                is_active=True,
                created_by=data.get("created_by"),
            )
            db.session.add(pos)
            db.session.commit()
            return True, f"Position '{pos.title}' created.", pos
        except Exception as e:
            db.session.rollback()
            return False, f"Failed: {e}", None

    # ── Shifts ────────────────────────────────────────────────────────

    def get_all_shifts(self) -> list:
        return Shift.query.filter_by(is_deleted=False).order_by(Shift.name).all()

    def create_shift(self, data: dict) -> Tuple[bool, str, Optional[Shift]]:
        existing = Shift.query.filter_by(code=data.get("code", "").upper(), is_deleted=False).first()
        if existing:
            return False, f"Shift code '{data['code'].upper()}' already exists.", None
        try:
            shift = Shift(
                name=data["name"].strip(),
                code=data["code"].strip().upper(),
                start_time=data["start_time"],
                end_time=data["end_time"],
                grace_minutes=int(data.get("grace_minutes", 10)),
                break_minutes=int(data.get("break_minutes", 60)),
                working_days=data.get("working_days", "Mon-Fri"),
                is_night_shift=bool(data.get("is_night_shift", False)),
                is_active=True,
                created_by=data.get("created_by"),
            )
            db.session.add(shift)
            db.session.commit()
            return True, f"Shift '{shift.name}' created.", shift
        except Exception as e:
            db.session.rollback()
            return False, f"Failed: {e}", None

    def get_department_stats(self) -> list:
        """Return department-wise employee count."""
        from app.models.employee import Employee
        from sqlalchemy import func
        rows = (
            db.session.query(Department.name, Department.color, func.count(Employee.id).label("count"))
            .outerjoin(Employee, (Employee.department == Department.name) & (Employee.is_deleted == False))
            .filter(Department.is_deleted == False)
            .group_by(Department.id)
            .order_by(Department.name)
            .all()
        )
        return [{"name": r.name, "color": r.color, "count": r.count} for r in rows]
