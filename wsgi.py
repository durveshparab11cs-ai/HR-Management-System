#!/usr/bin/env python3
"""
wsgi.py — Production WSGI entry point for Smart HRMS
=====================================================
Used by Waitress (Windows) and Gunicorn (Linux).

Cloudflare Tunnel → smarthrms.online → http://192.168.0.5:80 → Waitress → Flask

Usage:
    Waitress (Windows):
        waitress-serve --host=0.0.0.0 --port=80 --threads=8 wsgi:app

    Gunicorn (Linux):
        gunicorn --workers=4 --bind=0.0.0.0:80 wsgi:app

    Direct (development only):
        python wsgi.py
"""

import os
import sys
from pathlib import Path

# ── Ensure project root is on the Python path ──────────────
PROJECT_ROOT = Path(__file__).parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ── Load production environment ────────────────────────────
from dotenv import load_dotenv  # noqa: E402

# Load .env.production first (production overrides), then fall back to .env
prod_env = PROJECT_ROOT / ".env.production"
dev_env  = PROJECT_ROOT / ".env"

if prod_env.exists():
    load_dotenv(prod_env, override=True)
else:
    load_dotenv(dev_env)

# ── Fix postgres:// → postgresql:// for SQLAlchemy 2.x ────
_db_url = os.environ.get("DATABASE_URL", "")
if _db_url.startswith("postgres://"):
    os.environ["DATABASE_URL"] = _db_url.replace("postgres://", "postgresql://", 1)

# ── Create Flask app ───────────────────────────────────────
from app import create_app  # noqa: E402

env  = os.environ.get("FLASK_ENV", "production")
app  = create_app(env)

# ── Direct execution (debug only) ─────────────────────────
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 80)),
        debug=False,
        use_reloader=False,
        threaded=True,
    )
