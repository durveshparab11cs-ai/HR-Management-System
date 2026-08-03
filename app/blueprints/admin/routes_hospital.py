"""
app/blueprints/admin/routes_hospital.py
========================================
Hospital Management and Employee Allocation Routes
"""

from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user

from app.core.security import admin_required
from app.extensions.database import db
from app.services.hospital_service import HospitalService
from app.services.employee_allocation_service import EmployeeAllocationService
from .forms_hospital import (
    HospitalForm, 
    HospitalImportForm, 
    EmployeeAllocationImportForm,
    HospitalSearchForm
)
from . import admin_bp

hospital_service = HospitalService()
allocation_service = EmployeeAllocationService()


# ============================================================================
# HOSPITAL MANAGEMENT ROUTES
# ============================================================================

@admin_bp.route("/hospitals")
@login_required
@admin_required
def hospitals_list():
    """List all hospitals with search."""
    search_form = HospitalSearchForm()
    
    # Get filters
    query = request.args.get('search_query', '').strip()
    status_filter = request.args.get('status_filter', '')
    
    # Get hospitals
    if query:
        hospitals = hospital_service.search_hospitals(query)
    else:
        include_inactive = (status_filter == 'Inactive')
        hospitals = hospital_service.get_all_hospitals(include_inactive=True)
    
    # Apply status filter
    if status_filter:
        hospitals = [h for h in hospitals if h.status == status_filter]
    
    return render_template(
        'admin/hospitals_list.html',
        hospitals=hospitals,
        search_form=search_form,
        query=query,
        status_filter=status_filter
    )


@admin_bp.route("/hospitals/add", methods=['GET', 'POST'])
@login_required
@admin_required
def hospital_add():
    """Add new hospital."""
    form = HospitalForm()
    
    if form.validate_on_submit():
        success, message, hospital = hospital_service.create_hospital(
            hospital_name=form.hospital_name.data,
            hospital_code=form.hospital_code.data,
            latitude=form.latitude.data,
            longitude=form.longitude.data,
            location=form.location.data,
            address=form.address.data,
            city=form.city.data,
            state=form.state.data,
            allowed_radius_metres=form.allowed_radius_metres.data,
            is_active=form.is_active.data,
            status=form.status.data
        )
        
        if success:
            flash(message, 'success')
            return redirect(url_for('admin.hospitals_list'))
        else:
            flash(message, 'danger')
    
    return render_template('admin/hospital_form.html', form=form, mode='add')


@admin_bp.route("/hospitals/<int:hospital_id>/edit", methods=['GET', 'POST'])
@login_required
@admin_required
def hospital_edit(hospital_id):
    """Edit existing hospital."""
    hospital = hospital_service.get_hospital(hospital_id)
    if not hospital:
        flash('Hospital not found', 'danger')
        return redirect(url_for('admin.hospitals_list'))
    
    form = HospitalForm(obj=hospital)
    
    if form.validate_on_submit():
        success, message, updated = hospital_service.update_hospital(
            hospital_id=hospital_id,
            hospital_name=form.hospital_name.data,
            hospital_code=form.hospital_code.data,
            latitude=form.latitude.data,
            longitude=form.longitude.data,
            location=form.location.data,
            address=form.address.data,
            city=form.city.data,
            state=form.state.data,
            allowed_radius_metres=form.allowed_radius_metres.data,
            is_active=form.is_active.data,
            status=form.status.data
        )
        
        if success:
            flash(message, 'success')
            return redirect(url_for('admin.hospitals_list'))
        else:
            flash(message, 'danger')
    
    return render_template('admin/hospital_form.html', form=form, mode='edit', hospital=hospital)


@admin_bp.route("/hospitals/<int:hospital_id>/view")
@login_required
@admin_required
def hospital_view(hospital_id):
    """View hospital details."""
    hospital = hospital_service.get_hospital(hospital_id)
    if not hospital:
        flash('Hospital not found', 'danger')
        return redirect(url_for('admin.hospitals_list'))
    
    return render_template('admin/hospital_detail.html', hospital=hospital)


@admin_bp.route("/hospitals/<int:hospital_id>/delete", methods=['POST'])
@login_required
@admin_required
def hospital_delete(hospital_id):
    """Delete hospital (soft delete)."""
    success, message = hospital_service.delete_hospital(hospital_id)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
    
    return redirect(url_for('admin.hospitals_list'))


@admin_bp.route("/hospitals/import", methods=['GET', 'POST'])
@login_required
@admin_required
def hospitals_import():
    """Import hospitals from Excel."""
    form = HospitalImportForm()
    
    if form.validate_on_submit():
        file = form.file.data
        
        success, message, stats = hospital_service.import_hospitals_from_excel(
            file=file,
            imported_by_user_id=current_user.id
        )
        
        if success:
            flash(message, 'success')
            
            # Show detailed statistics
            if stats.get('errors'):
                flash(f"Errors encountered: {len(stats['errors'])} rows failed", 'warning')
        else:
            flash(message, 'danger')
        
        return redirect(url_for('admin.hospitals_list'))
    
    return render_template('admin/hospitals_import.html', form=form)


# ============================================================================
# EMPLOYEE ALLOCATION ROUTES
# ============================================================================

@admin_bp.route("/employee-allocation")
@login_required
@admin_required
def employee_allocation():
    """Employee allocation dashboard with employee list."""
    from app.models.employee import Employee
    from app.models.hospital import Hospital
    
    try:
        # Get filters from request
        search_query = request.args.get('search', '').strip()
        hospital_filter = request.args.get('hospital', '', type=int)
        shift_filter = request.args.get('shift', '').strip()
        page = request.args.get('page', 1, type=int)
        per_page = 50
        
        # Build simple query without hospital_id and current_shift (fields don't exist yet)
        query = Employee.query.filter_by(is_deleted=False)
        
        # Apply search filter only on employee_code (it's a real database column)
        if search_query:
            query = query.filter(
                Employee.employee_code.ilike(f'%{search_query}%')
            )
        
        # Order by employee code
        query = query.order_by(Employee.employee_code)
        
        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Get all hospitals for filter dropdown (if table exists)
        all_hospitals = []
        try:
            all_hospitals = Hospital.query.filter_by(is_deleted=False).order_by(Hospital.hospital_name).all()
        except Exception:
            all_hospitals = []
        
        return render_template(
            'admin/employee_allocation.html',
            pagination=pagination,
            employees_with_hospitals=pagination.items,
            all_hospitals=all_hospitals,
            search_query=search_query,
            hospital_filter=hospital_filter,
            shift_filter=shift_filter,
            stats={'total_allocated': 0, 'pending': 0, 'conflicts': 0}
        )
    except Exception as e:
        import logging
        logger = logging.getLogger('admin')
        logger.error('employee_allocation error: %s', str(e))
        flash('Error loading employee allocations. Please try again.', 'danger')
        return redirect(url_for('admin.index'))


@admin_bp.route("/employee-allocation/import", methods=['GET', 'POST'])
@login_required
@admin_required
def employee_allocation_import():
    """Import employee allocations from Excel."""
    form = EmployeeAllocationImportForm()
    
    if form.validate_on_submit():
        file = form.file.data
        
        success, message, stats = allocation_service.import_employee_allocations_from_excel(
            file=file,
            imported_by_user_id=current_user.id
        )
        
        if success:
            flash(message, 'success')
            
            # Show detailed statistics
            if stats.get('errors'):
                error_summary = f"{len(stats['errors'])} rows had errors"
                flash(error_summary, 'warning')
        else:
            flash(message, 'danger')
        
        return redirect(url_for('admin.employee_allocation'))
    
    return render_template('admin/employee_allocation_import.html', form=form)


# ============================================================================
# API ENDPOINTS
# ============================================================================

@admin_bp.route("/api/hospitals/search")
@login_required
@admin_required
def api_hospitals_search():
    """API: Search hospitals (for autocomplete)."""
    query = request.args.get('q', '').strip()
    
    if not query or len(query) < 2:
        return jsonify([])
    
    hospitals = hospital_service.search_hospitals(query)
    
    results = [
        {
            'id': h.id,
            'name': h.hospital_name,
            'code': h.hospital_code,
            'location': h.location,
            'latitude': h.latitude,
            'longitude': h.longitude
        }
        for h in hospitals[:10]  # Limit to 10 results
    ]
    
    return jsonify(results)


@admin_bp.route("/api/hospitals/<int:hospital_id>")
@login_required
@admin_required
def api_hospital_detail(hospital_id):
    """API: Get hospital details."""
    hospital = hospital_service.get_hospital(hospital_id)
    
    if not hospital:
        return jsonify({'error': 'Hospital not found'}), 404
    
    return jsonify(hospital.to_dict())
