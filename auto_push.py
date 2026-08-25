#!/usr/bin/env python3
"""Automatic git push for coordinator fix"""

import subprocess
import os
import sys

os.chdir(r"c:\Users\Administrator\Documents\HRMS\smart_hrms")

# Stage files
print("Adding files...")
subprocess.call(["git", "add", "app/blueprints/coordinator/routes.py"])
subprocess.call(["git", "add", "app/blueprints/coordinator/templates/coordinator/portal.html"])

# Commit
msg = """Fix: Coordinator Portal API returning JSON instead of HTML

- Bypass Flask-Login for public kiosk API endpoints
- Register routes directly with Flask app
- Add @csrf.exempt to API endpoints
- Correct API endpoint URLs in frontend
- Add /coordinator/portal route to serve portal page
- All API responses now return valid JSON

API endpoints:
- POST /coordinator/api/search-employee
- POST /coordinator/api/submit-attendance
- POST /coordinator/api/get-gps
- GET /coordinator/portal"""

print("Committing...")
subprocess.call(["git", "commit", "-m", msg])

# Push
print("Pushing...")
subprocess.call(["git", "push", "-u", "origin", "main"])

print("Done!")
