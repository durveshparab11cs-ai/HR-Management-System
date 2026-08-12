"""
app/blueprints/attendance/device_api.py
=========================================
API endpoints for device management (employees only, no admin UI).
"""

import logging
from flask import jsonify
from flask_login import login_required

from app.repositories.office_device_repo import OfficeDeviceRepository
from .device_service import DeviceService
from . import attendance_bp

logger = logging.getLogger("attendance")

_device_repo = OfficeDeviceRepository()
_device_svc = DeviceService(_device_repo)


@attendance_bp.route("/api/current-device-ip", methods=["GET"])
@login_required
def api_current_device_ip():
    """Get current device/request IP address (for employee to see their IP).
    
    Employees use this to get their device IP to provide to HR admin
    for registration.
    """
    ip = _device_svc.get_client_ip()
    is_allowed = _device_repo.is_ip_allowed(ip)

    return jsonify({
        "ip_address": ip,
        "is_allowed": is_allowed,
    })
