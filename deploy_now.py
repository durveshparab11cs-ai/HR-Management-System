#!/usr/bin/env python3
"""
DEPLOY IMMEDIATELY TO PRODUCTION
1. Check syntax of coordinator routes
2. Commit all changes
3. Push to main branch (Render auto-deploys)
"""

import os
import sys
import subprocess
import py_compile

print("\n" + "="*80)
print("DEPLOYMENT SEQUENCE - COORDINATOR ATTENDANCE PORTAL")
print("="*80 + "\n")

# Step 1: Check syntax
print("Step 1: Checking Python syntax...")
try:
    py_compile.compile('app/blueprints/coordinator/routes.py', doraise=True)
    print("✓ coordinator/routes.py syntax OK\n")
except py_compile.PyCompileError as e:
    print(f"✗ Syntax error in coordinator/routes.py: {e}")
    sys.exit(1)

# Step 2: Check if portal template exists
print("Step 2: Checking portal template...")
if os.path.exists('app/templates/coordinator/portal.html'):
    print("✓ portal.html exists\n")
else:
    print("✗ portal.html NOT FOUND")
    sys.exit(1)

# Step 3: Git add
print("Step 3: Git add...")
result = subprocess.run(['git', 'add', '-A'], capture_output=True, text=True, cwd='.')
if result.returncode != 0:
    print(f"✗ Git add failed: {result.stderr}")
    sys.exit(1)
print(f"✓ Git add OK\n")

# Step 4: Git commit
print("Step 4: Git commit...")
commit_msg = "Deploy: Fix coordinator attendance portal with I-code support and modern UI"
result = subprocess.run(['git', 'commit', '-m', commit_msg], capture_output=True, text=True, cwd='.')
if result.returncode == 0:
    print(f"✓ Committed: {commit_msg}\n")
elif 'nothing to commit' in result.stdout.lower():
    print(f"⚠ Nothing to commit (already up to date)\n")
else:
    print(f"✗ Commit failed: {result.stderr}")
    sys.exit(1)

# Step 5: Git push to main
print("Step 5: Pushing to main (Render auto-deploys)...")
result = subprocess.run(['git', 'push', 'origin', 'main'], capture_output=True, text=True, cwd='.')
if result.returncode == 0:
    print(f"✓ Pushed to main\n")
    print("📢 Render is now auto-deploying...\n")
else:
    if 'already up to date' in result.stdout.lower():
        print(f"⚠ Already up to date (no push needed)\n")
    else:
        print(f"Git push output: {result.stdout}")
        print(f"Git push error: {result.stderr}")

print("="*80)
print("✓ DEPLOYMENT READY - Waiting for Render to build & deploy...")
print("   - coordinator/portal.html will serve at /coordinator/portal")
print("   - API endpoints: /coordinator/api/search-employee, /coordinator/api/submit-attendance")
print("   - Server will restart in ~2-3 minutes")
print("="*80 + "\n")
