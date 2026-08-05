"""
admin/shift_assignment.py
==========================
Bulk shift assignment for HR/Admin to assign shifts to employees.
"""

from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload

from app.extensions.database import db
from app.models.employee import Employee
from app.models.user import User
from app.models.company import Shift
from app.models.employee_shift_assignment import EmployeeShiftAssignment
from app.constants.enums import UserStatus


def assign_shifts_bulk():
    """Bulk shift assignment page for HR/Admin."""
    try:
        from app.models.hospital_assignment import EmployeeHospitalAssignment  # noqa: PLC0415
        from app.models.hospital import Hospital  # noqa: PLC0415
        from app.models.company import Shift  # noqa: PLC0415
        from app.extensions.database import db as _db  # noqa: PLC0415
        import logging
        logger = logging.getLogger('admin')
        
        # Ensure all 25 shifts exist (idempotent UPSERT)
        try:
            from datetime import time as dt_time
            shifts_data = [
                {"name": "06:00 AM to 03:00 PM", "code": "SHIFT_0600_1500", "start_time": "06:00", "end_time": "15:00", "is_night": False},
                {"name": "06:30 AM to 03:30 PM", "code": "SHIFT_0630_1530", "start_time": "06:30", "end_time": "15:30", "is_night": False},
                {"name": "07:00 AM to 04:00 PM", "code": "SHIFT_0700_1600", "start_time": "07:00", "end_time": "16:00", "is_night": False},
                {"name": "07:30 AM to 04:30 PM", "code": "SHIFT_0730_1630", "start_time": "07:30", "end_time": "16:30", "is_night": False},
                {"name": "08:00 AM to 05:00 PM", "code": "SHIFT_0800_1700", "start_time": "08:00", "end_time": "17:00", "is_night": False},
                {"name": "08:00 AM to 06:00 PM", "code": "SHIFT_0800_1800", "start_time": "08:00", "end_time": "18:00", "is_night": False},
                {"name": "08:30 AM to 05:30 PM", "code": "SHIFT_0830_1730", "start_time": "08:30", "end_time": "17:30", "is_night": False},
                {"name": "09:00 AM to 06:00 PM", "code": "SHIFT_0900_1800", "start_time": "09:00", "end_time": "18:00", "is_night": False},
                {"name": "09:30 AM to 06:30 PM", "code": "SHIFT_0930_1830", "start_time": "09:30", "end_time": "18:30", "is_night": False},
                {"name": "10:00 AM to 06:00 PM", "code": "SHIFT_1000_1800", "start_time": "10:00", "end_time": "18:00", "is_night": False},
                {"name": "10:00 AM to 07:00 PM", "code": "SHIFT_1000_1900", "start_time": "10:00", "end_time": "19:00", "is_night": False},
                {"name": "10:15 AM to 07:15 PM", "code": "SHIFT_1015_1915", "start_time": "10:15", "end_time": "19:15", "is_night": False},
                {"name": "10:30 AM to 07:30 PM", "code": "SHIFT_1030_1930", "start_time": "10:30", "end_time": "19:30", "is_night": False},
                {"name": "11:00 AM to 08:00 PM", "code": "SHIFT_1100_2000", "start_time": "11:00", "end_time": "20:00", "is_night": False},
                {"name": "11:30 AM to 08:30 PM", "code": "SHIFT_1130_2030", "start_time": "11:30", "end_time": "20:30", "is_night": False},
                {"name": "12:00 PM to 09:00 PM", "code": "SHIFT_1200_2100", "start_time": "12:00", "end_time": "21:00", "is_night": False},
                {"name": "12:30 PM to 09:30 PM", "code": "SHIFT_1230_2130", "start_time": "12:30", "end_time": "21:30", "is_night": False},
                {"name": "12:45 PM to 09:45 PM", "code": "SHIFT_1245_2145", "start_time": "12:45", "end_time": "21:45", "is_night": False},
                {"name": "01:00 PM to 10:00 PM", "code": "SHIFT_1300_2200", "start_time": "13:00", "end_time": "22:00", "is_night": False},
                {"name": "01:00 PM to 06:00 PM", "code": "SHIFT_1300_1800", "start_time": "13:00", "end_time": "18:00", "is_night": False},
                {"name": "07:00 PM to 04:00 AM", "code": "SHIFT_1900_0400", "start_time": "19:00", "end_time": "04:00", "is_night": True},
                {"name": "09:00 PM to 06:00 AM", "code": "SHIFT_2100_0600", "start_time": "21:00", "end_time": "06:00", "is_night": True},
                {"name": "10:00 PM to 06:00 AM", "code": "SHIFT_2200_0600", "start_time": "22:00", "end_time": "06:00", "is_night": True},
                {"name": "10:00 PM to 07:00 AM", "code": "SHIFT_2200_0700", "start_time": "22:00", "end_time": "07:00", "is_night": True},
                {"name": "10:30 PM to 07:30 AM", "code": "SHIFT_2230_0730", "start_time": "22:30", "end_time": "07:30", "is_night": True},
            ]
            
            for shift_data in shifts_data:
                start_h, start_m = map(int, shift_data["start_time"].split(":"))
                end_h, end_m = map(int, shift_data["end_time"].split(":"))
                
                existing = Shift.query.filter_by(code=shift_data["code"]).first()
                if existing:
                    existing.name = shift_data["name"]
                    existing.start_time = dt_time(start_h, start_m)
                    existing.end_time = dt_time(end_h, end_m)
                    existing.is_night_shift = shift_data["is_night"]
                    existing.is_active = True
                    _db.session.add(existing)
                else:
                    shift = Shift(
                        name=shift_data["name"],
                        code=shift_data["code"],
                        start_time=dt_time(start_h, start_m),
                        end_time=dt_time(end_h, end_m),
                        is_night_shift=shift_data["is_night"],
                        is_active=True,
                        grace_minutes=10,
                        break_minutes=60,
                        working_days="Mon-Sun"
                    )
                    _db.session.add(shift)
            
            _db.session.commit()
        except Exception as e:
            _db.session.rollback()
            logger.error("Shift seeding failed: %s", str(e))
        
        # Get all active employees - use simpler query to avoid join issues
        try:
            employees = (
                Employee.query
                .filter(Employee.is_deleted == False)
                .order_by(Employee.employee_code)
                .all()
            )
            logger.info(f"Loaded {len(employees)} employees")
        except Exception as e:
            logger.error(f"Employee query failed: {e}")
            employees = []
        
        # Get all active shifts
        try:
            shifts = Shift.query.filter_by(is_active=True, is_deleted=False).order_by(Shift.name).all()
            logger.info(f"Loaded {len(shifts)} shifts")
        except Exception as e:
            logger.error(f"Shift query failed: {e}")
            shifts = []
        
        # Get all active hospitals
        try:
            hospitals = Hospital.query.filter_by(is_active=True, is_deleted=False).order_by(Hospital.hospital_name).all()
            logger.info(f"Loaded {len(hospitals)} hospitals")
        except Exception as e:
            logger.error(f"Hospital query failed: {e}")
            hospitals = []
        
        # Get current shift assignments for each employee
        employee_shifts = {}
        for emp in employees:
            try:
                assignment = (
                    EmployeeShiftAssignment.query
                    .options(joinedload(EmployeeShiftAssignment.shift))
                    .filter(
                        EmployeeShiftAssignment.employee_id == emp.id,
                        EmployeeShiftAssignment.effective_until.is_(None)
                    )
                    .first()
                )
                employee_shifts[emp.id] = assignment.shift if assignment and assignment.shift else None
            except Exception as e:
                logger.warning(f"Shift assignment query failed for emp {emp.id}: {e}")
                employee_shifts[emp.id] = None
        
        # Get current hospital assignments for each employee
        employee_hospitals = {}
        for emp in employees:
            try:
                assignment = (
                    EmployeeHospitalAssignment.query
                    .filter(
                        EmployeeHospitalAssignment.employee_id == emp.id,
                        EmployeeHospitalAssignment.effective_until.is_(None)
                    )
                    .first()
                )
                employee_hospitals[emp.id] = assignment.hospital_name if assignment else None
            except Exception as e:
                logger.warning(f"Hospital assignment query failed for emp {emp.id}: {e}")
                employee_hospitals[emp.id] = None
        
        return render_template(
            'admin/shift_assignment.html',
            employees=employees,
            shifts=shifts,
            hospitals=hospitals,
            employee_shifts=employee_shifts,
            employee_hospitals=employee_hospitals,
            today=(datetime.now().date()).isoformat()
        )
    except Exception as e:
        import logging
        import traceback
        logger = logging.getLogger('admin')
        logger.error('shift_assignment error: %s', str(e))
        logger.error('Traceback: %s', traceback.format_exc())
        flash(f'Error loading shift assignment page: {str(e)}', 'danger')
        return redirect(url_for('admin.index'))


def assign_shift_to_employee():
    """Assign shift to a single employee."""
    
    employee_id = request.form.get('employee_id', type=int)
    shift_id = request.form.get('shift_id', type=int)
    effective_date = request.form.get('effective_date')
    
    if not employee_id or not shift_id:
        return jsonify({'success': False, 'message': 'Employee and Shift are required'}), 400
    
    try:
        # Parse date
        if effective_date:
            effective_date = datetime.strptime(effective_date, '%Y-%m-%d').date()
        else:
            effective_date = date.today()
        
        # Get employee and shift
        employee = Employee.query.get(employee_id)
        shift = Shift.query.get(shift_id)
        
        if not employee or not shift:
            return jsonify({'success': False, 'message': 'Employee or Shift not found'}), 404
        
        # Check if employee already has an active assignment
        current_assignment = EmployeeShiftAssignment.query.filter(
            EmployeeShiftAssignment.employee_id == employee_id,
            EmployeeShiftAssignment.effective_until.is_(None)
        ).first()
        
        # Close current assignment if exists and different shift
        if current_assignment:
            if current_assignment.shift_id == shift_id:
                return jsonify({
                    'success': False,
                    'message': f'{employee.name} is already assigned to {shift.name}'
                }), 400
            
            # Close previous assignment
            current_assignment.effective_until = effective_date - timedelta(days=1)
            db.session.add(current_assignment)
        
        # Create new assignment
        new_assignment = EmployeeShiftAssignment(
            employee_id=employee_id,
            shift_id=shift_id,
            effective_from=effective_date,
            assigned_by=current_user.id,
            assigned_date=datetime.utcnow(),
            reason="Initial shift assignment by HR/Admin",
            remarks=f"Assigned {shift.name} shift"
        )
        
        db.session.add(new_assignment)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'✅ {employee.name} assigned to {shift.name} shift',
            'employee_id': employee_id,
            'shift_name': shift.name,
            'shift_timing': f"{shift.start_time.strftime('%I:%M %p')} - {shift.end_time.strftime('%I:%M %p')}"
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


def assign_shifts_bulk_submit():
    """Bulk assign shifts to multiple employees at once."""
    
    assignments = request.json.get('assignments', [])
    effective_date = request.json.get('effective_date')
    
    if not assignments:
        return jsonify({'success': False, 'message': 'No assignments provided'}), 400
    
    try:
        # Parse date
        if effective_date:
            effective_date = datetime.strptime(effective_date, '%Y-%m-%d').date()
        else:
            effective_date = date.today()
        
        success_count = 0
        error_count = 0
        errors = []
        
        for assignment in assignments:
            employee_id = assignment.get('employee_id')
            shift_id = assignment.get('shift_id')
            
            if not employee_id or not shift_id:
                continue
            
            try:
                employee = Employee.query.get(employee_id)
                shift = Shift.query.get(shift_id)
                
                if not employee or not shift:
                    errors.append(f"Employee ID {employee_id} or Shift ID {shift_id} not found")
                    error_count += 1
                    continue
                
                # Check current assignment
                current_assignment = EmployeeShiftAssignment.query.filter(
                    EmployeeShiftAssignment.employee_id == employee_id,
                    EmployeeShiftAssignment.effective_until.is_(None)
                ).first()
                
                # Skip if already assigned to same shift
                if current_assignment and current_assignment.shift_id == shift_id:
                    continue
                
                # Close current assignment if exists
                if current_assignment:
                    current_assignment.effective_until = effective_date - timedelta(days=1)
                    db.session.add(current_assignment)
                
                # Create new assignment
                new_assignment = EmployeeShiftAssignment(
                    employee_id=employee_id,
                    shift_id=shift_id,
                    effective_from=effective_date,
                    assigned_by=current_user.id,
                    assigned_date=datetime.utcnow(),
                    reason="Bulk shift assignment by HR/Admin",
                    remarks=f"Bulk assigned {shift.name} shift"
                )
                
                db.session.add(new_assignment)
                success_count += 1
                
            except Exception as e:
                errors.append(f"Error for employee {employee_id}: {str(e)}")
                error_count += 1
        
        # Commit all changes
        db.session.commit()
        
        message = f"✅ Successfully assigned shifts to {success_count} employees"
        if error_count > 0:
            message += f". {error_count} errors occurred."
        
        return jsonify({
            'success': True,
            'message': message,
            'success_count': success_count,
            'error_count': error_count,
            'errors': errors
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


def remove_shift_assignment():
    """Remove shift assignment from employee."""
    
    employee_id = request.form.get('employee_id', type=int)
    
    if not employee_id:
        return jsonify({'success': False, 'message': 'Employee ID required'}), 400
    
    try:
        employee = Employee.query.get(employee_id)
        if not employee:
            return jsonify({'success': False, 'message': 'Employee not found'}), 404
        
        # Find current assignment
        current_assignment = EmployeeShiftAssignment.query.filter(
            EmployeeShiftAssignment.employee_id == employee_id,
            EmployeeShiftAssignment.effective_until.is_(None)
        ).first()
        
        if not current_assignment:
            return jsonify({'success': False, 'message': 'No active shift assignment found'}), 404
        
        # Close assignment
        current_assignment.effective_until = date.today()
        db.session.add(current_assignment)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'✅ Shift removed from {employee.name}'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


def get_employee_shift_info():
    """Get current shift info for an employee."""
    
    employee_id = request.args.get('employee_id', type=int)
    
    if not employee_id:
        return jsonify({'success': False, 'message': 'Employee ID required'}), 400
    
    try:
        employee = Employee.query.get(employee_id)
        if not employee:
            return jsonify({'success': False, 'message': 'Employee not found'}), 404
        
        # Get current assignment
        assignment = EmployeeShiftAssignment.query.filter(
            EmployeeShiftAssignment.employee_id == employee_id,
            EmployeeShiftAssignment.effective_until.is_(None)
        ).first()
        
        if assignment and assignment.shift:
            shift = assignment.shift
            return jsonify({
                'success': True,
                'has_shift': True,
                'shift_id': shift.id,
                'shift_name': shift.name,
                'start_time': shift.start_time.strftime('%I:%M %p'),
                'end_time': shift.end_time.strftime('%I:%M %p'),
                'working_hours': shift.working_hours,
                'effective_from': assignment.effective_from.strftime('%d %b %Y')
            })
        else:
            return jsonify({
                'success': True,
                'has_shift': False,
                'message': 'No shift assigned'
            })
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


def assign_hospital_to_employee():
    """Assign hospital to a single employee."""
    from app.models.hospital_assignment import EmployeeHospitalAssignment  # noqa: PLC0415
    from datetime import datetime, timedelta, date  # noqa: PLC0415, F401
    
    employee_id = request.form.get('employee_id', type=int)
    hospital_name = request.form.get('hospital_name', '').strip()
    effective_date_str = request.form.get('effective_date', '')
    
    if not employee_id:
        return jsonify({'success': False, 'message': 'Employee ID required'}), 400
    if not hospital_name:
        return jsonify({'success': False, 'message': 'Hospital name required'}), 400
    
    try:
        # Parse effective date
        if effective_date_str:
            effective_date = datetime.strptime(effective_date_str, '%Y-%m-%d').date()
        else:
            effective_date = date.today()
        
        # Get employee
        employee = Employee.query.get(employee_id)
        if not employee:
            return jsonify({'success': False, 'message': 'Employee not found'}), 404
        
        # Check for current assignment
        current_assignment = (
            EmployeeHospitalAssignment.query
            .filter(
                EmployeeHospitalAssignment.employee_id == employee_id,
                EmployeeHospitalAssignment.effective_until.is_(None)
            )
            .first()
        )
        
        # Close current assignment if different hospital
        if current_assignment:
            if current_assignment.hospital_name == hospital_name:
                return jsonify({
                    'success': False,
                    'message': f'{employee.name} is already assigned to {hospital_name}'
                }), 400
            
            # Close previous assignment
            current_assignment.effective_until = effective_date - timedelta(days=1)
            db.session.add(current_assignment)
        
        # Create new assignment
        new_assignment = EmployeeHospitalAssignment(
            employee_id=employee_id,
            hospital_name=hospital_name,
            effective_from=effective_date,
            notes=f"Assigned by {current_user.username if current_user else 'System'}"
        )
        
        db.session.add(new_assignment)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'✅ {employee.name} assigned to {hospital_name}',
            'employee_id': employee_id,
            'hospital_name': hospital_name
        })
        
    except Exception as e:
        db.session.rollback()
        import logging
        logger = logging.getLogger('admin')
        logger.error('Hospital assignment error: %s', str(e))
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
