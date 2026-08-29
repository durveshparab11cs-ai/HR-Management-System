"""
Smart HRMS — Application Entry Point
FORCE SQLite - NO Render/Production database
"""

import os
import sys

print("\n" + "="*80)
print("STARTUP: Clearing PostgreSQL environment variables")
print("="*80)

# ===== CRITICAL: Clear ALL database env vars BEFORE anything loads =====
keys_to_delete = []
for k in list(os.environ.keys()):
    if any(x in k.upper() for x in ['DATABASE', 'POSTGRES', 'DB_', 'RENDER', 'DPG-', 'SQL']):
        keys_to_delete.append(k)
        print(f"  Deleting: {k}")

for key in keys_to_delete:
    del os.environ[key]

print(f"\nDeleted {len(keys_to_delete)} PostgreSQL-related environment variables")

# Force development environment and SQLite (before dotenv!)
print("\nSETTING: FLASK_ENV=development")
print("SETTING: DATABASE_URL=sqlite:///smart_hrms_dev.db")

os.environ["FLASK_ENV"] = "development"
os.environ["DATABASE_URL"] = "sqlite:///smart_hrms_dev.db"

# Now load dotenv - but be careful not to override our settings
print("\nLoading .env file...")
from dotenv import load_dotenv
load_dotenv(override=False)  # override=False means our pre-set vars take priority

# RE-ENFORCE after dotenv loads (it WILL try to override our settings)
print("\nRE-ENFORCING SQLite settings after .env load...")
os.environ["FLASK_ENV"] = "development"
os.environ["DATABASE_URL"] = "sqlite:///smart_hrms_dev.db"

print(f"\nFinal DATABASE_URL: {os.environ.get('DATABASE_URL')}")
print(f"Final FLASK_ENV: {os.environ.get('FLASK_ENV')}")
print("="*80 + "\n")

from app import create_app

# Create app in DEVELOPMENT mode with SQLite
app = create_app("development")

if __name__ == "__main__":
    from werkzeug.serving import make_server
    server = make_server("0.0.0.0", 8000, app, threaded=True)
    app.logger.info("Starting server on http://0.0.0.0:8000 (SQLite mode)")
    server.serve_forever()
