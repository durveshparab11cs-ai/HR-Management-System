"""
app/blueprints/attendance/device_routes.py
=============================================
Admin routes for managing office devices (IP whitelisting).
"""

import logging
from flask import jsonify, request, render_template, flash, redirect, url_for
from flask_login import current_user, login_required

from app.core.security import admin_required
from app.repositories.office_device_repo import OfficeDeviceRepository
from .device_service import DeviceService
from . import attendance_bp

logger = logging.getLogger("attendance")

_device_repo = OfficeDeviceRepository()
_device_svc = DeviceService(_device_repo)


# ── Admin Routes for Device Management ─────────────────────────────

@attendance_bp.route("/admin/devices", methods=["GET"])
@login_required
@admin_required
def admin_devices():
    """List all office devices with their configurations."""
    devices = _device_repo.get_all()
    return render_template(
        "attendance/admin_devices.html",
        title="Office Devices",
        devices=devices,
    )


@attendance_bp.route("/admin/devices/add", methods=["GET", "POST"])
@login_required
@admin_required
def add_device():
    """Add a new office device."""
    if request.method == "POST":
        ip_address = request.form.get("ip_address", "").strip()
        device_name = request.form.get("device_name", "").strip()
        description = request.form.get("description", "").strip()

        # Validation
        if not ip_address or not device_name:
            flash("IP address and device name are required.", "danger")
            return redirect(url_for("attendance.add_device"))

        # Check if IP already exists
        existing = _device_repo.get_by_ip(ip_address)
        if existing:
            flash(f"IP address {ip_address} already registered.", "warning")
            return redirect(url_for("attendance.add_device"))

        try:
            device = _device_repo.create(
                ip_address=ip_address,
                device_name=device_name,
                description=description if description else None,
            )
            logger.info(f"Device added: {ip_address}")
            flash(f"Device '{device_name}' ({ip_address}) added successfully.", "success")
            return redirect(url_for("attendance.admin_devices"))
        except Exception as e:
            logger.error(f"Error adding device: {str(e)}")
            flash(f"Error adding device: {str(e)}", "danger")
            return redirect(url_for("attendance.add_device"))

    return render_template("attendance/device_form.html", title="Add Office Device")


@attendance_bp.route("/admin/devices/<int:device_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_device(device_id):
    """Edit an office device."""
    device = _device_repo.get_by_id(device_id)
    if not device:
        flash("Device not found.", "danger")
        return redirect(url_for("attendance.admin_devices"))

    if request.method == "POST":
        device_name = request.form.get("device_name", "").strip()
        description = request.form.get("description", "").strip()
        is_active = request.form.get("is_active") == "on"

        if not device_name:
            flash("Device name is required.", "danger")
            return redirect(url_for("attendance.edit_device", device_id=device_id))

        device.device_name = device_name
        device.description = description if description else None
        device.is_active = is_active

        try:
            device = _device_repo.update(device)
            logger.info(f"Device updated: {device.ip_address}")
            flash(f"Device '{device_name}' updated successfully.", "success")
            return redirect(url_for("attendance.admin_devices"))
        except Exception as e:
            logger.error(f"Error updating device: {str(e)}")
            flash(f"Error updating device: {str(e)}", "danger")
            return redirect(url_for("attendance.edit_device", device_id=device_id))

    return render_template(
        "attendance/device_form.html",
        title="Edit Office Device",
        device=device,
        is_edit=True,
    )


@attendance_bp.route("/admin/devices/<int:device_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_device(device_id):
    """Delete an office device."""
    device = _device_repo.get_by_id(device_id)
    if not device:
        flash("Device not found.", "danger")
        return redirect(url_for("attendance.admin_devices"))

    ip_address = device.ip_address
    try:
        _device_repo.delete(device_id)
        logger.info(f"Device deleted: {ip_address}")
        flash(f"Device {ip_address} deleted successfully.", "success")
    except Exception as e:
        logger.error(f"Error deleting device: {str(e)}")
        flash(f"Error deleting device: {str(e)}", "danger")

    return redirect(url_for("attendance.admin_devices"))


# ── API Endpoints ────────────────────────────────────────────────────

@attendance_bp.route("/api/devices", methods=["GET"])
@login_required
@admin_required
def api_devices():
    """Get all office devices as JSON."""
    devices = _device_repo.get_all()
    return jsonify([d.to_dict() for d in devices])


@attendance_bp.route("/api/devices/<int:device_id>", methods=["GET"])
@login_required
@admin_required
def api_device_detail(device_id):
    """Get a specific device as JSON."""
    device = _device_repo.get_by_id(device_id)
    if not device:
        return jsonify({"error": "Device not found"}), 404
    return jsonify(device.to_dict())


@attendance_bp.route("/api/devices/toggle-active/<int:device_id>", methods=["POST"])
@login_required
@admin_required
def api_toggle_device(device_id):
    """Toggle device active status."""
    device = _device_repo.get_by_id(device_id)
    if not device:
        return jsonify({"error": "Device not found"}), 404

    device.is_active = not device.is_active
    device = _device_repo.update(device)
    logger.info(f"Device {device.ip_address} toggled to active={device.is_active}")

    return jsonify(device.to_dict())


@attendance_bp.route("/api/current-device-ip", methods=["GET"])
@login_required
def api_current_device_ip():
    """Get current device/request IP address (for admin to get IP from office computer)."""
    ip = _device_svc.get_client_ip()
    is_allowed = _device_repo.is_ip_allowed(ip)

    return jsonify({
        "ip_address": ip,
        "is_allowed": is_allowed,
    })
