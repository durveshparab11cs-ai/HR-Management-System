#!/usr/bin/env python3
import subprocess
import os

os.chdir(r"c:\Users\Administrator\Documents\HRMS\smart_hrms")

# Check recent commits
result = subprocess.run(["git", "log", "--oneline", "-5"], capture_output=True, text=True, timeout=10)
print("Recent commits:")
print(result.stdout)

# Check status
result = subprocess.run(["git", "status"], capture_output=True, text=True, timeout=10)
print("\nGit status:")
print(result.stdout[:500])

# Check remote
result = subprocess.run(["git", "remote", "-v"], capture_output=True, text=True, timeout=10)
print("\nRemotes:")
print(result.stdout)
