"""
Coordinator attendance kiosk routes.
11-step attendance workflow: employee search, camera, photo capture, check-in/out.
"""

from flask import render_template, request, jsonify
from app.blueprints.coordinator import coordinator_bp
from app.models.employee import Employee
from app.models.attendance import Attendance
from app import db
from datetime import datetime
import json


@coordinator_bp.route("/", methods=["GET"])
def dashboard():
    """Render the coordinator attendance kiosk dashboard."""
    return render_template("coordinator/dashboard.html")


@coordinator_bp.route("/search", methods=["POST"])
def search_employee():
    """
    Search for an employee by code or name.
    
    Expected JSON:
        {
            "search_term": "E-2603028" or "John Doe"
        }
    
    Returns:
        JSON with employee details or error message
    """
    try:
        data = request.get_json()
        search_term = data.get("search_term", "").strip()
        
        if not search_term:
            return jsonify({"success": False, "error": "Search term is required"}), 400
        
        # Search by employee code or name
        employee = Employee.query.filter(
            (Employee.employee_code == search_term) |
            (Employee.first_name.ilike(f"%{search_term}%")) |
            (Employee.last_name.ilike(f"%{search_term}%"))
        ).first()
        
        if not employee:
            return jsonify({"success": False, "error": "Employee not found"}), 404
        
        return jsonify({
            "success": True,
            "employee": {
                "id": employee.id,
                "employee_code": employee.employee_code,
                "first_name": employee.first_name,
                "last_name": employee.last_name,
                "email": employee.email,
                "phone": employee.phone,
                "department": employee.department.name if employee.department else "N/A",
                "designation": employee.designation if hasattr(employee, 'designation') else "N/A"
            }
        }), 200
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@coordinator_bp.route("/kiosk_checkin", methods=["POST"])
def kiosk_checkin():
    """
    Process attendance check-in with photo.
    
    Expected JSON:
        {
            "employee_id": 123,
            "photo_base64": "data:image/jpeg;base64,..."
        }
    
    Returns:
        JSON with check-in confirmation or error
    """
    try:
        data = request.get_json()
        employee_id = data.get("employee_id")
        photo_data = data.get("photo_base64")
        
        if not employee_id:
            return jsonify({"success": False, "error": "Employee ID is required"}), 400
        
        employee = Employee.query.get(employee_id)
        if not employee:
            return jsonify({"success": False, "error": "Employee not found"}), 404
        
        # Create attendance record for check-in
        now = datetime.now()
        attendance = Attendance(
            employee_id=employee_id,
            date=now.date(),
            check_in=now.time(),
            check_in_photo=photo_data if photo_data else None,
            status="Present"
        )
        
        db.session.add(attendance)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": f"Check-in successful for {employee.first_name} {employee.last_name}",
            "timestamp": now.isoformat()
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@coordinator_bp.route("/kiosk_checkout", methods=["POST"])
def kiosk_checkout():
    """
    Process attendance check-out with photo.
    
    Expected JSON:
        {
            "employee_id": 123,
            "photo_base64": "data:image/jpeg;base64,..."
        }
    
    Returns:
        JSON with check-out confirmation or error
    """
    try:
        data = request.get_json()
        employee_id = data.get("employee_id")
        photo_data = data.get("photo_base64")
        
        if not employee_id:
            return jsonify({"success": False, "error": "Employee ID is required"}), 400
        
        employee = Employee.query.get(employee_id)
        if not employee:
            return jsonify({"success": False, "error": "Employee not found"}), 404
        
        # Find today's attendance record and update check-out
        now = datetime.now()
        attendance = Attendance.query.filter_by(
            employee_id=employee_id,
            date=now.date()
        ).first()
        
        if not attendance:
            return jsonify({"success": False, "error": "No check-in found for today"}), 404
        
        attendance.check_out = now.time()
        attendance.check_out_photo = photo_data if photo_data else None
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": f"Check-out successful for {employee.first_name} {employee.last_name}",
            "timestamp": now.isoformat()
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
