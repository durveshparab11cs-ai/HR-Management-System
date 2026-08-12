"""
app/blueprints/attendance/device_service.py
=============================================
Device validation service — checks if check-in/out is allowed from
specific office computers only.
"""

import logging
from flask import request

logger = logging.getLogger("attendance")


class DeviceService:
    """Validates check-in/out requests from allowed office devices."""

    def __init__(self, device_repo):
        """Initialize with device repository."""
        self.device_repo = device_repo

    def get_client_ip(self) -> str:
        """Extract client IP address from request.
        
        Handles X-Forwarded-For header for proxied requests.
        """
        # Check for X-Forwarded-For (used by proxies/load balancers)
        xff = request.headers.get("X-Forwarded-For", "")
        if xff:
            # X-Forwarded-For can contain multiple IPs, get the first one
            return xff.split(",")[0].strip()
        
        # Fall back to direct remote address
        return request.remote_addr or "unknown"

    def is_allowed_device(self, ip_address: str = None) -> tuple[bool, str]:
        """
        Check if the request is from an allowed office device.
        
        Returns:
            (is_allowed, message)
        """
        if ip_address is None:
            ip_address = self.get_client_ip()
        
        logger.info(f"DeviceService.is_allowed_device | ip={ip_address}")
        
        # Check if IP is in allowed list
        if self.device_repo.is_ip_allowed(ip_address):
            logger.info(f"Device ALLOWED | ip={ip_address}")
            return True, f"Device verified: {ip_address}"
        
        # Get allowed IPs for error message
        allowed_ips = self.device_repo.get_allowed_ips()
        
        if not allowed_ips:
            logger.warning("No allowed devices configured")
            return False, "No allowed office devices configured. Contact HR to add your device."
        
        logger.warning(f"Device REJECTED | ip={ip_address} | allowed={allowed_ips}")
        return False, f"Check-in only allowed from office computers. Your device ({ip_address}) is not registered. Contact HR."

    def get_all_allowed_ips(self) -> list[str]:
        """Get list of all allowed IP addresses."""
        return self.device_repo.get_allowed_ips()

    def is_device_check_enabled(self) -> bool:
        """Check if device verification is enabled (at least one device configured)."""
        return len(self.device_repo.get_all_active()) > 0
