"""
Smart HRMS — Application Entry Point
=====================================
This is the WSGI entry point for both development and production.

Usage:
    Development:  flask run  (or)  python run.py
    Production:   gunicorn run:app

The 'app' object is exposed at module level so that WSGI servers
(Gunicorn, uWSGI) can discover it without executing the dev server code.
"""

import os

from dotenv import load_dotenv

# Load environment variables before importing the factory so that
# configuration classes pick them up during module initialization.
load_dotenv()

# Render.com provides DATABASE_URL as postgres:// — SQLAlchemy 2.x requires postgresql://
_db_url = os.environ.get("DATABASE_URL", "")
if _db_url.startswith("postgres://"):
    os.environ["DATABASE_URL"] = _db_url.replace("postgres://", "postgresql://", 1)

from app import create_app  # noqa: E402 — must come after load_dotenv

# Resolve the environment name from the environment variable.
# Defaults to 'development' if not set.
environment = os.environ.get("FLASK_ENV", "development")

# Create the WSGI application instance.
app = create_app(environment)

if __name__ == "__main__":
    # Bind to 'localhost' not '127.0.0.1'.
    # Chrome treats 'localhost' as a secure context, so navigator.geolocation
    # works without HTTPS — no certificate or Chrome flags needed.
    app.run(
        host="localhost",
        port=5000,
        debug=app.config.get("DEBUG", False),
    )
