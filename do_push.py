#!/usr/bin/env python3
import subprocess
import os

os.chdir(r"c:\Users\Administrator\Documents\HRMS\smart_hrms")

# Stage files
print("Staging files...")
subprocess.run(["git", "add", "app/blueprints/coordinator/routes.py"], check=False)
subprocess.run(["git", "add", "app/blueprints/coordinator/templates/coordinator/portal.html"], check=False)

# Commit
print("Committing...")
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
- GET /coordinator/portal

Employee search workflow now works: code entry -> API search -> camera -> attendance submission"""

result = subprocess.run(["git", "commit", "-m", msg], capture_output=True, text=True)
print(result.stdout if result.stdout else result.stderr)

# Push
print("\nPushing to remote...")
result = subprocess.run(["git", "push", "-u", "origin", "main"], capture_output=True, text=True)
print(result.stdout if result.stdout else result.stderr)

print("\n✓ Done!")
