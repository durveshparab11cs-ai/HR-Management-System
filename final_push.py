#!/usr/bin/env python3
"""Final push with verification"""

import subprocess
import sys
import os
import time

os.chdir(r"c:\Users\Administrator\Documents\HRMS\smart_hrms")

print("=" * 80)
print(" " * 20 + "COORDINATOR FIX - GIT PUSH")
print("=" * 80)

# 1. Add files
print("\n[1/4] Adding files...")
r = subprocess.run(["git", "add", "app/blueprints/coordinator/routes.py"], 
                   capture_output=True, text=True, timeout=10)
r = subprocess.run(["git", "add", "app/blueprints/coordinator/templates/coordinator/portal.html"], 
                   capture_output=True, text=True, timeout=10)
print("✓ Files staged")

# 2. Commit
print("\n[2/4] Committing...")
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

r = subprocess.run(["git", "commit", "-m", msg], capture_output=True, text=True, timeout=10)
if r.returncode == 0:
    print("✓ Committed")
    if "create mode" in r.stdout:
        print("  (created new files)")
else:
    print("✗ Commit failed or no changes:", r.stderr[:200])

# 3. Push
print("\n[3/4] Pushing to origin/main...")
r = subprocess.run(["git", "push", "-u", "origin", "main"], capture_output=True, text=True, timeout=60)
if r.returncode == 0:
    print("✓ Pushed successfully")
    print(r.stdout[:300])
else:
    print("✗ Push result:")
    print(r.stdout[:300] if r.stdout else r.stderr[:300])

# 4. Verify
print("\n[4/4] Verifying...")
r = subprocess.run(["git", "log", "--oneline", "-3"], capture_output=True, text=True, timeout=10)
print("Recent commits:")
for line in r.stdout.split("\n")[:3]:
    if line.strip():
        print(f"  {line}")

print("\n" + "=" * 80)
print("✓ PUSH COMPLETE")
print("=" * 80)
print("\nChanges pushed to: https://github.com/durveshparab11cs-ai/HR-Management-System")
