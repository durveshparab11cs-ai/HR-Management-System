#!/usr/bin/env python
"""
manage_office_devices.py
==========================
Script to manage office device IP addresses from the command line.

Usage:
    python manage_office_devices.py add <ip_address> <device_name> [description]
    python manage_office_devices.py list
    python manage_office_devices.py delete <device_id>
    python manage_office_devices.py enable <device_id>
    python manage_office_devices.py disable <device_id>

Example:
    python manage_office_devices.py add 192.168.1.100 "Front Desk" "Main entrance desk"
    python manage_office_devices.py list
    python manage_office_devices.py delete 1
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from app.models.office_device import OfficeDevice
from app.repositories.office_device_repo import OfficeDeviceRepository
from app.extensions.database import db

def main():
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        print(__doc__)
        return

    app = create_app()
    repo = OfficeDeviceRepository()

    command = sys.argv[1].lower()

    with app.app_context():
        if command == "add":
            if len(sys.argv) < 4:
                print("Usage: python manage_office_devices.py add <ip_address> <device_name> [description]")
                return

            ip_address = sys.argv[2]
            device_name = sys.argv[3]
            description = sys.argv[4] if len(sys.argv) > 4 else None

            # Check if IP already exists
            existing = repo.get_by_ip(ip_address)
            if existing:
                print(f"❌ IP {ip_address} already registered as '{existing.device_name}'")
                return

            device = repo.create(ip_address, device_name, description)
            print(f"✅ Device added successfully!")
            print(f"   ID: {device.id}")
            print(f"   IP: {device.ip_address}")
            print(f"   Name: {device.device_name}")
            print(f"   Description: {device.description or '(none)'}")
            print(f"   Status: Active")

        elif command == "list":
            devices = repo.get_all()
            if not devices:
                print("No devices configured yet.")
                return

            print("\n📊 Office Devices:\n")
            print(f"{'ID':<5} {'IP Address':<20} {'Device Name':<25} {'Status':<10} {'Description'}")
            print("-" * 100)

            for device in devices:
                status = "✓ Active" if device.is_active else "✗ Inactive"
                desc = device.description if device.description else "—"
                print(f"{device.id:<5} {device.ip_address:<20} {device.device_name:<25} {status:<10} {desc}")

            print(f"\nTotal: {len(devices)} device(s)")

        elif command == "delete":
            if len(sys.argv) < 3:
                print("Usage: python manage_office_devices.py delete <device_id>")
                return

            device_id = int(sys.argv[2])
            device = repo.get_by_id(device_id)

            if not device:
                print(f"❌ Device with ID {device_id} not found")
                return

            ip_address = device.ip_address
            repo.delete(device_id)
            print(f"✅ Device deleted: {ip_address}")

        elif command == "enable":
            if len(sys.argv) < 3:
                print("Usage: python manage_office_devices.py enable <device_id>")
                return

            device_id = int(sys.argv[2])
            device = repo.get_by_id(device_id)

            if not device:
                print(f"❌ Device with ID {device_id} not found")
                return

            device.is_active = True
            repo.update(device)
            print(f"✅ Device enabled: {device.ip_address} ({device.device_name})")

        elif command == "disable":
            if len(sys.argv) < 3:
                print("Usage: python manage_office_devices.py disable <device_id>")
                return

            device_id = int(sys.argv[2])
            device = repo.get_by_id(device_id)

            if not device:
                print(f"❌ Device with ID {device_id} not found")
                return

            device.is_active = False
            repo.update(device)
            print(f"✅ Device disabled: {device.ip_address} ({device.device_name})")

        else:
            print(f"Unknown command: {command}")
            print(__doc__)

if __name__ == "__main__":
    main()
