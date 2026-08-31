#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_production.py
====================
Pre-flight checklist for Smart HRMS production deployment.
Run this before starting Waitress.
"""
import os
import sys
from pathlib import Path

# Force UTF-8 output on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Load production env
os.environ["FLASK_ENV"] = "production"
from dotenv import load_dotenv
root = Path(__file__).parent
prod_env = root / ".env.production"
dev_env  = root / ".env"
load_dotenv(prod_env if prod_env.exists() else dev_env, override=True)

PASS  = " [PASS]"
FAIL  = " [FAIL]"
WARN  = " [WARN]"
errors = 0

print()
print("=" * 60)
print("  Smart HRMS -- Production Pre-flight Checklist")
print("=" * 60)

# 1. Python version
import platform
ver = platform.python_version()
major, minor, *_ = [int(x) for x in ver.split(".")]
ok = major == 3 and minor >= 9
print(f"  [1] Python {ver}{PASS if ok else FAIL}")
if not ok:
    print("      Python 3.9+ required"); errors += 1

# 2. Critical packages
packages = ["flask", "flask_sqlalchemy", "flask_login", "waitress",
            "sqlalchemy", "dotenv", "wtforms"]
for pkg in packages:
    try:
        __import__(pkg.replace("-", "_"))
        print(f"  [2] {pkg}{PASS}")
    except ImportError:
        print(f"  [2] {pkg}{FAIL} -- run: pip install {pkg}"); errors += 1

# 3. Database file
db_url = os.environ.get("DATABASE_URL", "")
if db_url.startswith("sqlite:///"):
    db_path = db_url.replace("sqlite:///", "")
    if Path(db_path).exists():
        size_mb = Path(db_path).stat().st_size / 1_048_576
        print(f"  [3] Database: {db_path}  ({size_mb:.1f} MB){PASS}")
    else:
        print(f"  [3] Database not found: {db_path}{FAIL}"); errors += 1
else:
    print(f"  [3] DATABASE_URL = {db_url[:60]}{PASS}")

# 4. Instance directories
for d in ["instance/sessions", "instance/uploads", "logs"]:
    p = root / d
    p.mkdir(parents=True, exist_ok=True)
    print(f"  [4] Directory {d}{PASS}")

# 5. Flask app loads
print()
print("  [5] Loading Flask application...")
try:
    from app import create_app
    app = create_app("production")
    with app.app_context():
        from app.extensions.database import db
        from app.models.user import User
        from app.models.employee import Employee

        # Check coordinator user
        coord = User.query.filter_by(username="coordinator_kiosk").first()
        if coord and coord.status == "active" and coord.role == "super_admin":
            print(f"  [5] coordinator_kiosk: role={coord.role}, status={coord.status}{PASS}")
        else:
            if not coord:
                print(f"  [5] coordinator_kiosk user NOT FOUND{FAIL}")
                print(f"      Run: python create_coordinator_user.py")
            else:
                print(f"  [5] coordinator_kiosk status={coord.status} role={coord.role}{WARN}")
            errors += 1

        # Count employees
        count = Employee.query.count()
        suffix = PASS if count > 0 else WARN
        print(f"  [5] Employee records: {count}{suffix}")

        # Test coordinator routes registered
        routes = [r.rule for r in app.url_map.iter_rules()]
        required = ["/coordinator/", "/coordinator/search",
                    "/coordinator/check-in", "/coordinator/check-out"]
        for route in required:
            if route in routes:
                print(f"  [5] Route {route}{PASS}")
            else:
                print(f"  [5] Route {route} MISSING{FAIL}"); errors += 1

    print(f"  [5] Flask app loaded OK{PASS}")

except Exception as exc:
    print(f"  [5] Flask app load FAILED: {exc}{FAIL}")
    import traceback; traceback.print_exc()
    errors += 1

# Summary
print()
print("=" * 60)
if errors == 0:
    print("  ALL CHECKS PASSED -- ready to start production server")
    print()
    print("  Start command:")
    print("    waitress-serve --host=0.0.0.0 --port=80 --threads=8 wsgi:app")
    print()
    print("  Or run:  .\\START-PRODUCTION.ps1")
else:
    print(f"  {errors} check(s) FAILED -- fix above before starting")
print("=" * 60)
print()

sys.exit(0 if errors == 0 else 1)
