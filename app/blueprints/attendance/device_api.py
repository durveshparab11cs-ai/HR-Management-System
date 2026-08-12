"""
app/blueprints/attendance/device_api.py
=========================================
API endpoints for device management (super admin only).
"""

import logging
from flask import jsonify, request
from flask_login import login_required

from app.core.security import super_admin_required
from app.repositories.office_device_repo import OfficeDeviceRepository
from .device_service import DeviceService
from . import attendance_bp

logger = logging.getLogger("attendance")

_device_repo = OfficeDeviceRepository()
_device_svc = DeviceService(_device_repo)


@attendance_bp.route("/api/current-device-ip", methods=["GET"])
@login_required
@super_admin_required
def api_current_device_ip():
    """Get current device/request IP address (super admin only).
    
    Super admin uses this endpoint to get their own device IP for registration.
    """
    ip = _device_svc.get_client_ip()
    is_allowed = _device_repo.is_ip_allowed(ip)

    return jsonify({
        "ip_address": ip,
        "is_allowed": is_allowed,
    })


@attendance_bp.route("/api/devices", methods=["GET"])
@login_required
@super_admin_required
def api_list_devices():
    """List all registered office devices (super admin only)."""
    devices = _device_repo.get_all()
    return jsonify([d.to_dict() for d in devices])


@attendance_bp.route("/api/devices", methods=["POST"])
@login_required
@super_admin_required
def api_add_device():
    """Add a new office device (super admin only).
    
    Request body:
        {
            "ip_address": "192.168.1.100",
            "device_name": "Front Desk",
            "description": "Main entrance"
        }
    """
    data = request.get_json() or {}
    
    ip_address = data.get("ip_address", "").strip()
    device_name = data.get("device_name", "").strip()
    description = data.get("description", "").strip()

    # Validation
    if not ip_address or not device_name:
        return jsonify({
            "success": False,
            "message": "ip_address and device_name are required"
        }), 400

    # Check if IP already exists
    existing = _device_repo.get_by_ip(ip_address)
    if existing:
        return jsonify({
            "success": False,
            "message": f"IP address {ip_address} already registered"
        }), 409

    try:
        device = _device_repo.create(
            ip_address=ip_address,
            device_name=device_name,
            description=description if description else None,
        )
        logger.info(f"Device added: {ip_address} by super_admin")
        
        return jsonify({
            "success": True,
            "message": f"Device '{device_name}' registered successfully",
            "device": device.to_dict()
        }), 201
    except Exception as e:
        logger.error(f"Error adding device: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error adding device: {str(e)}"
        }), 500


@attendance_bp.route("/api/devices/<int:device_id>", methods=["DELETE"])
@login_required
@super_admin_required
def api_delete_device(device_id):
    """Delete an office device (super admin only)."""
    device = _device_repo.get_by_id(device_id)
    if not device:
        return jsonify({"success": False, "message": "Device not found"}), 404

    ip_address = device.ip_address
    try:
        _device_repo.delete(device_id)
        logger.info(f"Device deleted: {ip_address} by super_admin")
        
        return jsonify({
            "success": True,
            "message": f"Device {ip_address} deleted successfully"
        })
    except Exception as e:
        logger.error(f"Error deleting device: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error deleting device: {str(e)}"
        }), 500


@attendance_bp.route("/api/devices/<int:device_id>/toggle", methods=["POST"])
@login_required
@super_admin_required
def api_toggle_device(device_id):
    """Toggle device active/inactive status (super admin only)."""
    device = _device_repo.get_by_id(device_id)
    if not device:
        return jsonify({"success": False, "message": "Device not found"}), 404

    device.is_active = not device.is_active
    try:
        device = _device_repo.update(device)
        logger.info(f"Device {device.ip_address} toggled to active={device.is_active}")
        
        return jsonify({
            "success": True,
            "message": f"Device {'enabled' if device.is_active else 'disabled'} successfully",
            "device": device.to_dict()
        })
    except Exception as e:
        logger.error(f"Error toggling device: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error toggling device: {str(e)}"
        }), 500
