#!/usr/bin/env python3
import subprocess
import os

os.chdir(r"c:\Users\Administrator\Documents\HRMS\smart_hrms")

try:
    # Add files
    r1 = subprocess.run(["git", "add", "app/blueprints/coordinator/routes.py"], capture_output=True, text=True, timeout=10)
    r2 = subprocess.run(["git", "add", "app/blueprints/coordinator/templates/coordinator/portal.html"], capture_output=True, text=True, timeout=10)
    
    # Commit  
    msg = "Fix: Coordinator Portal API returning JSON instead of HTML\n\n- Bypass Flask-Login for public kiosk API endpoints\n- Register routes directly with Flask app\n- Add @csrf.exempt to API endpoints\n- Correct API endpoint URLs in frontend\n- Add /coordinator/portal route to serve portal page\n- All API responses now return valid JSON\n\nAPI endpoints:\n- POST /coordinator/api/search-employee\n- POST /coordinator/api/submit-attendance\n- POST /coordinator/api/get-gps\n- GET /coordinator/portal"
    
    r3 = subprocess.run(["git", "commit", "-m", msg], capture_output=True, text=True, timeout=10)
    
    # Push
    r4 = subprocess.run(["git", "push", "-u", "origin", "main"], capture_output=True, text=True, timeout=30)
    
    # Print results
    print("=" * 70)
    print("GIT PUSH RESULTS")
    print("=" * 70)
    
    if r3.stdout:
        print("\nCommit:")
        print(r3.stdout[:500])
    
    if r4.stdout:
        print("\nPush:")
        print(r4.stdout[:500])
    
    if r4.returncode == 0:
        print("\n✓ PUSH SUCCESSFUL!")
    else:
        print(f"\n✗ Push error (code: {r4.returncode})")
        if r4.stderr:
            print(r4.stderr[:500])
            
except Exception as e:
    print(f"Error: {e}")
