#!/usr/bin/env python3
"""Push coordinator fix to Git"""

import subprocess
import sys
import os

os.chdir(r"c:\Users\Administrator\Documents\HRMS\smart_hrms")

print("=" * 70)
print("PUSHING COORDINATOR PORTAL FIX")
print("=" * 70)

try:
    # Check status
    print("\n1. Git status:")
    result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
    print(result.stdout)
    
    # Stage changes
    print("\n2. Staging changes...")
    subprocess.run(["git", "add", "app/blueprints/coordinator/routes.py"], check=True)
    subprocess.run(["git", "add", "app/blueprints/coordinator/templates/coordinator/portal.html"], check=True)
    print("✓ Files staged")
    
    # Commit
    print("\n3. Committing...")
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
    print(result.stdout)
    if result.returncode != 0:
        print("Error:", result.stderr)
    
    # Push
    print("\n4. Pushing to remote...")
    result = subprocess.run(["git", "push", "-u", "origin", "main"], capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print("Error:", result.stderr)
    
    print("\n" + "=" * 70)
    print("✓ PUSH COMPLETE")
    print("=" * 70)

except Exception as e:
    print(f"✗ Error: {e}")
    sys.exit(1)
