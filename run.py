"""
Smart HRMS — Application Entry Point
Supports both production (Render/Gunicorn with PostgreSQL) and local development.
"""
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Load .env if present without overriding explicit platform environment variables
from dotenv import load_dotenv
load_dotenv(override=False)

# Normalize and auto-resolve DATABASE_URL
from config.settings import resolve_database_uri
raw_db = os.environ.get("DATABASE_URL", "")
resolved_db = resolve_database_uri(raw_db)
if raw_db != resolved_db:
    os.environ["DATABASE_URL"] = resolved_db

env = os.environ.get("FLASK_ENV", "production")
from app import create_app

app = create_app(env)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    if env == "production":
        from werkzeug.serving import make_server
        server = make_server("0.0.0.0", port, app, threaded=True)
        app.logger.info(f"Starting server on http://0.0.0.0:{port} ({env} mode)")
        server.serve_forever()
    else:
        app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
