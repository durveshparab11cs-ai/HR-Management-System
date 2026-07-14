"""
blueprints/employees/repository.py
=====================================
Employee repository — all database access for employee management.
"""

from typing import Optional
from sqlalchemy import or_, func
from app.extensions.database import db
from app.models.employee import Employee
from app.models.user import User
from app.constants.enums import UserRole, UserStatus


class EmployeeRepository:

    def get_by_id(self, emp_id: int) -> Optional[Employee]:
        return Employee.query.filter_by(id=emp_id, is_deleted=False).first()

    def get_by_id_or_404(self, emp_id: int) -> Employee:
        from flask import abort
        emp = self.get_by_id(emp_id)
        if not emp:
            abort(404)
        return emp

    def get_by_user_id(self, user_id: int) -> Optional[Employee]:
        return Employee.query.filter_by(user_id=user_id, is_deleted=False).first()

    def get_by_employee_code(self, code: str) -> Optional[Employee]:
        return Employee.query.filter_by(employee_code=code.upper(), is_deleted=False).first()

    def get_all(self, page: int = 1, per_page: int = 25, search: str = "", department: str = "", branch: str = ""):
        q = (
            Employee.query
            .join(User, Employee.user_id == User.id)
            .filter(Employee.is_deleted == False)
        )
        if search:
            term = f"%{search}%"
            q = q.filter(or_(
                User.first_name.ilike(term),
                User.last_name.ilike(term),
                User.email.ilike(term),
                Employee.employee_code.ilike(term),
                Employee.mobile.ilike(term),
            ))
        if department:
            q = q.filter(Employee.department.ilike(f"%{department}%"))
        if branch:
            q = q.filter(Employee.branch.ilike(f"%{branch}%"))
        return q.order_by(Employee.employee_code.asc()).paginate(page=page, per_page=per_page, error_out=False)

    def get_all_active(self) -> list:
        return (
            Employee.query
            .join(User, Employee.user_id == User.id)
            .filter(Employee.is_deleted == False, User.status == UserStatus.ACTIVE.value)
            .order_by(Employee.employee_code)
            .all()
        )

    def create(self, employee: Employee) -> Employee:
        db.session.add(employee)
        db.session.commit()
        return employee

    def update(self, employee: Employee) -> Employee:
        db.session.add(employee)
        db.session.commit()
        return employee

    def soft_delete(self, employee: Employee, deleted_by: int) -> Employee:
        employee.soft_delete(deleted_by_id=deleted_by)
        return employee

    def get_next_employee_code(self, prefix: str = "EMP") -> str:
        last = (
            Employee.query
            .filter(Employee.employee_code.like(f"{prefix}%"))
            .order_by(Employee.id.desc())
            .first()
        )
        if last:
            try:
                num = int(last.employee_code.replace(prefix, "")) + 1
            except ValueError:
                num = 1
        else:
            num = 1
        return f"{prefix}{num:04d}"

    def get_departments(self) -> list:
        rows = (
            db.session.query(Employee.department)
            .filter(Employee.is_deleted == False, Employee.department.isnot(None))
            .distinct()
            .order_by(Employee.department)
            .all()
        )
        return [r.department for r in rows]

    def get_branches(self) -> list:
        rows = (
            db.session.query(Employee.branch)
            .filter(Employee.is_deleted == False, Employee.branch.isnot(None))
            .distinct()
            .order_by(Employee.branch)
            .all()
        )
        return [r.branch for r in rows]

    # ── User account ops ──────────────────────────────────────────────
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        return User.query.filter_by(id=user_id, is_deleted=False).first()

    def get_user_by_email(self, email: str) -> Optional[User]:
        return User.query.filter_by(email=email.lower().strip(), is_deleted=False).first()

    def create_user(self, user: User) -> User:
        db.session.add(user)
        db.session.commit()
        return user

    def update_user(self, user: User) -> User:
        db.session.add(user)
        db.session.commit()
        return user

    def count_total(self) -> int:
        return Employee.query.filter_by(is_deleted=False).count()
