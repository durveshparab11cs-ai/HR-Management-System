#!/usr/bin/env python3
import os
import sys
import subprocess

# Kill existing processes
os.system("taskkill /F /IM python.exe >nul 2>&1")

import time
time.sleep(3)

# Change to app directory
os.chdir(r'C:\Users\Administrator\Documents\HRMS\smart_hrms')

# Start Flask
print("=" * 70)
print("STARTING COORDINATOR PORTAL")
print("=" * 70)
print()

os.system("python run.py")
