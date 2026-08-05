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

    def get_all(self, page: int = 1, per_page: int = 25, search: str = "", department: str | None = None, branch: str | None = None):
        """
        Get all employees from both Employee and EmployeeMaster tables.
        
        Shows employees with User accounts first, then EmployeeMaster records
        that don't have Employee records yet (haven't logged in).
        """
        from app.models.employee_master import EmployeeMaster  # noqa: PLC0415
        
        # Get employees with User accounts
        q_emp = (
            Employee.query
            .join(User, Employee.user_id == User.id)
            .filter(Employee.is_deleted == False)
        )
        
        # Get EmployeeMaster records WITHOUT corresponding Employee record
        q_master = (
            EmployeeMaster.query
            .filter(~EmployeeMaster.employee_code.in_(
                db.session.query(Employee.employee_code).filter(Employee.is_deleted == False)
            ))
        )
        
        # Combine results in memory
        all_employees = []
        
        # Add from Employee table
        for emp in q_emp.all():
            all_employees.append({
                'id': emp.id,
                'first_name': emp.user.first_name,
                'last_name': emp.user.last_name,
                'email': emp.user.email,
                'employee_code': emp.employee_code,
                'mobile': emp.mobile,
                'department': emp.department,
                'branch': emp.branch,
                'designation': emp.designation,
                'user': emp.user,
                'profile_photo': emp.profile_photo if hasattr(emp, 'profile_photo') else None,
                'source': 'employee'
            })
        
        # Add from EmployeeMaster (those not yet created as Employee)
        for master in q_master.all():
            all_employees.append({
                'id': None,
                'first_name': master.employee_name.split()[0] if master.employee_name else '',
                'last_name': ' '.join(master.employee_name.split()[1:]) if len(master.employee_name.split()) > 1 else '',
                'email': None,
                'employee_code': master.employee_code,
                'mobile': None,
                'department': master.department,
                'branch': None,
                'designation': master.designation,
                'user': None,
                'profile_photo': None,
                'source': 'master'
            })
        
        # Apply search filter
        if search:
            term = search.lower()
            all_employees = [
                e for e in all_employees
                if term in (e['first_name'] + ' ' + e['last_name']).lower()
                or (e['email'] and term in e['email'].lower())
                or term in e['employee_code'].lower()
            ]
        
        # Apply department filter
        if department:
            all_employees = [
                e for e in all_employees
                if e['department'] and department.lower() in e['department'].lower()
            ]
        
        # Apply branch filter
        if branch:
            all_employees = [
                e for e in all_employees
                if e['branch'] and branch.lower() in e['branch'].lower()
            ]
        
        # Sort by employee code
        all_employees.sort(key=lambda x: x['employee_code'].upper())
        
        # Manual pagination
        total = len(all_employees)
        start = (page - 1) * per_page
        end = start + per_page
        items = all_employees[start:end]
        
        # Create a dict-based pagination that mimics Flask-SQLAlchemy Pagination
        class DictPagination:
            def __init__(self, items, page, per_page, total):
                self.items = items
                self.page = page
                self.per_page = per_page
                self.total = total
            
            @property
            def pages(self):
                return max(1, (self.total + self.per_page - 1) // self.per_page)
            
            @property
            def has_next(self):
                return self.page < self.pages
            
            @property
            def has_prev(self):
                return self.page > 1
            
            @property
            def next_num(self):
                return self.page + 1 if self.has_next else None
            
            @property
            def prev_num(self):
                return self.page - 1 if self.has_prev else None
            
            def iter_pages(self, left_edge=2, left_window=2, right_window=2, right_edge=2):
                last = self.pages
                if last < 1:
                    return
                
                if last <= left_edge + right_edge:
                    for num in range(1, last + 1):
                        yield num
                else:
                    if self.page > left_edge + left_window:
                        for num in range(1, left_edge + 1):
                            yield num
                        yield None
                    
                    left = max(1, self.page - left_window)
                    right = min(last, self.page + right_window)
                    
                    for num in range(left, right + 1):
                        yield num
                    
                    if self.page < last - right_window - right_edge:
                        yield None
                        for num in range(last - right_edge + 1, last + 1):
                            yield num
        
        return DictPagination(items, page, per_page, total)

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
        from app.models.employee_master import EmployeeMaster  # noqa: PLC0415
        
        # Get from Employee table
        emp_depts = (
            db.session.query(Employee.department)
            .filter(Employee.is_deleted == False, Employee.department.isnot(None))
            .distinct()
            .all()
        )
        
        # Get from EmployeeMaster table
        master_depts = (
            db.session.query(EmployeeMaster.department)
            .filter(EmployeeMaster.department.isnot(None))
            .distinct()
            .all()
        )
        
        # Combine and deduplicate
        depts = set()
        for r in emp_depts:
            if r.department:
                depts.add(r.department)
        for r in master_depts:
            if r.department:
                depts.add(r.department)
        
        return sorted(list(depts))

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
