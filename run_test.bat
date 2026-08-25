@echo off
cd /d "c:\Users\Administrator\Documents\HRMS\smart_hrms"
python simple_test.py > test_output.txt 2>&1
type test_output.txt
