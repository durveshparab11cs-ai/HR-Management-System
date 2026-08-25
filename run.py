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

# CLEAR any PostgreSQL DATABASE_URL from Render to force SQLite
if os.environ.get("DATABASE_URL", "").startswith("postgresql://"):
    del os.environ["DATABASE_URL"]

from app import create_app  # noqa: E402 — must come after load_dotenv

# Resolve the environment name from the environment variable.
# Defaults to 'development' if not set.
environment = os.environ.get("FLASK_ENV", "development")

# Create the WSGI application instance.
app = create_app(environment)

if __name__ == "__main__":
    # Bind to all interfaces (0.0.0.0) so it's accessible from network
    # Listen on port 8000 as configured
    # Use werkzeug's make_server directly to bypass the reloader issues
    from werkzeug.serving import make_server
    
    server = make_server(
        "0.0.0.0",
        8000,
        app,
        threaded=True,
    )
    
    app.logger.info("Starting server on http://0.0.0.0:8000")
    server.serve_forever()
