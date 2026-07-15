"""
run_seed.py — wrapper that calls seed_employees with explicit file path.
Run: python run_seed.py
"""
import sys
import os
sys.argv = ["seed_employees.py", "--file", r"C:\Users\durve\Downloads\Book1.xlsx"]
sys.path.insert(0, os.path.dirname(__file__))
import seed_employees
seed_employees.main()
