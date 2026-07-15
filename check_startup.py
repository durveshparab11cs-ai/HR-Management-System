"""
check_startup.py
=================
Verifies the Flask app can be created and all routes can be listed
without errors. Does NOT start the HTTP server.

Run: python check_startup.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault("FLASK_ENV", "development")
# Force UTF-8 output so checkmarks render on all terminals
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv
load_dotenv()

print("Creating Flask app...")
from app import create_app
app = create_app("development")

print("\n[OK] App created successfully")

with app.app_context():
    from app.extensions.database import db
    from sqlalchemy import inspect, text

    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print(f"\n[OK] Database connected -- {len(tables)} tables")
    for t in sorted(tables):
        print(f"     - {t}")

    result = db.session.execute(text("SELECT COUNT(*) FROM employee_master")).scalar()
    print(f"\n[OK] employee_master : {result} rows")

    result2 = db.session.execute(text("SELECT COUNT(*) FROM users")).scalar()
    print(f"[OK] users           : {result2} rows")

    rules = sorted(app.url_map.iter_rules(), key=lambda r: r.rule)
    print(f"\n[OK] {len(rules)} routes registered:")
    for rule in rules:
        methods = ','.join(sorted(m for m in rule.methods if m not in ('HEAD','OPTIONS')))
        print(f"  [{methods:10s}]  {rule.rule}")

print("\n[OK] All checks passed. Run 'python run.py' to start the server.")
print("     URL: http://localhost:5000/auth/login")
