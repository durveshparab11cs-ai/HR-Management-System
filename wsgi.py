#!/usr/bin/env python3
"""
WSGI entry point for production deployment.
Runs on HTTP internally - Nginx/reverse proxy handles HTTPS
"""

import os
from dotenv import load_dotenv

load_dotenv()

_db_url = os.environ.get("DATABASE_URL", "")
if _db_url.startswith("postgres://"):
    os.environ["DATABASE_URL"] = _db_url.replace("postgres://", "postgresql://", 1)

from app import create_app

app = create_app(os.environ.get("FLASK_ENV", "production"))

if __name__ == "__main__":
    # Run Flask on HTTP port 5000
    # Nginx will proxy HTTPS (443) -> HTTP (5000)
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,
        use_reloader=False
    )
