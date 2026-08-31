#!/usr/bin/env python3
"""
Wrapper to execute the urllib test directly and capture output
"""
import subprocess
import sys
import os

# Change to script directory
os.chdir(r'c:\Users\Administrator\Documents\HRMS\smart_hrms')

# Run the urllib test
result = subprocess.run(
    [sys.executable, 'api_test_http_only_urllib.py'],
    capture_output=True,
    text=True,
    timeout=30
)

# Print output
print("STDOUT:")
print("=" * 80)
print(result.stdout)
print("\nSTDERR:")
print("=" * 80)
print(result.stderr)
print("\nReturn Code:", result.returncode)

# Save to file
with open('api_test_http_only_FINAL_OUTPUT.txt', 'w') as f:
    f.write("STDOUT:\n")
    f.write("=" * 80 + "\n")
    f.write(result.stdout)
    f.write("\n\nSTDERR:\n")
    f.write("=" * 80 + "\n")
    f.write(result.stderr)
    f.write("\n\nReturn Code: " + str(result.returncode))

sys.exit(result.returncode)
