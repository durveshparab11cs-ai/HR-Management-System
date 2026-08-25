#!/usr/bin/env python
"""Run the coordinator API test"""

import subprocess
import sys

result = subprocess.run(
    [sys.executable, "-u", "test_coordinator_api.py"],
    cwd=r"c:\Users\Administrator\Documents\HRMS\smart_hrms",
    capture_output=True,
    text=True,
    timeout=30
)

print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)
print("Return code:", result.returncode)
