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

# Normalize postgres:// -> postgresql:// for SQLAlchemy 2.x compatibility
db_url = os.environ.get("DATABASE_URL", "")
if db_url.startswith("postgres://"):
    os.environ["DATABASE_URL"] = db_url.replace("postgres://", "postgresql://", 1)

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
