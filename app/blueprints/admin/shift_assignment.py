"""
admin/shift_assignment.py
==========================
Bulk shift assignment for HR/Admin to assign shifts to employees.
"""

from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user

from app.extensions.database import db
from app.models.employee import Employee
from app.models.company import Shift
from app.models.employee_shift_assignment import EmployeeShiftAssignment


def assign_shifts_bulk():
    """Bulk shift assignment page for HR/Admin."""
    
    # Get all active employees
    employees = Employee.query.filter_by(is_active=True).order_by(Employee.employee_code).all()
    
    # Get all active shifts
    shifts = Shift.query.filter_by(is_active=True).order_by(Shift.name).all()
    
    # Get current assignments for each employee
    employee_shifts = {}
    for emp in employees:
        assignment = EmployeeShiftAssignment.query.filter(
            EmployeeShiftAssignment.employee_id == emp.id,
            EmployeeShiftAssignment.effective_until.is_(None)
        ).first()
        employee_shifts[emp.id] = assignment.shift if assignment else None
    
    return render_template(
        'admin/shift_assignment.html',
        employees=employees,
        shifts=shifts,
        employee_shifts=employee_shifts
    )


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
