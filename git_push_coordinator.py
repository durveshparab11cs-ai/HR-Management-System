#!/usr/bin/env python3
"""Git push coordinator fix without PowerShell"""

import subprocess
import sys
import os

# Change to repo directory
repo_dir = r"c:\Users\Administrator\Documents\HRMS\smart_hrms"
os.chdir(repo_dir)

print("=" * 70)
print("COORDINATOR PORTAL FIX - GIT PUSH")
print("=" * 70)

def run_cmd(cmd, label):
    """Run a command and print output"""
    print(f"\n{label}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        if result.stdout:
            print(result.stdout)
        if result.returncode != 0 and result.stderr:
            print(f"ERROR: {result.stderr}")
            return False
        return True
    except Exception as e:
        print(f"EXCEPTION: {e}")
        return False

# Stage files
run_cmd('git add "app/blueprints/coordinator/routes.py"', "1. Adding routes.py")
run_cmd('git add "app/blueprints/coordinator/templates/coordinator/portal.html"', "2. Adding portal.html")

# Show status
run_cmd('git status --short', "3. Git status")

# Create commit message
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

# Write message to temp file to avoid issues
msg_file = os.path.join(repo_dir, ".git_msg.txt")
with open(msg_file, "w") as f:
    f.write(msg)

# Commit
if run_cmd(f'git commit -F "{msg_file}"', "4. Committing"):
    print("✓ Commit successful")
else:
    print("✗ Commit failed or no changes to commit")

# Push
if run_cmd('git push -u origin main', "5. Pushing to remote"):
    print("\n✓ PUSH SUCCESSFUL")
else:
    print("\n✗ Push may have failed - check output above")

# Cleanup
try:
    os.remove(msg_file)
except:
    pass

print("\n" + "=" * 70)
print("DONE")
print("=" * 70)
