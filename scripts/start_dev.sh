#!/usr/bin/env bash
# ===========================================================================
# Smart HRMS — Development Server Startup Script
# ===========================================================================
# Usage:  bash scripts/start_dev.sh
# Prereq: virtual environment activated, .env file present
# ===========================================================================

set -euo pipefail

echo "============================================"
echo "  Smart HRMS — Development Server"
echo "============================================"

# Verify .env exists
if [ ! -f ".env" ]; then
    echo "ERROR: .env not found. Copy .env.example to .env and configure it."
    exit 1
fi

# Load environment variables
export $(grep -v '^#' .env | xargs)

echo "[1/4] Installing / verifying dependencies..."
pip install -q -r requirements/development.txt

echo "[2/4] Running database migrations..."
flask db upgrade

echo "[3/4] Checking for super admin user..."
# Non-interactive check — create only if users table is empty
python -c "
from app import create_app
from app.extensions.database import db
from app.models.user import User
app = create_app('development')
with app.app_context():
    if User.query.count() == 0:
        print('  No users found. Run: flask create-admin')
    else:
        print('  Users exist — skipping admin creation.')
"

echo "[4/4] Starting Flask development server..."
echo ""
echo "  URL:   http://127.0.0.1:5000"
echo "  Env:   development"
echo "  Debug: enabled"
echo ""
flask run --host=127.0.0.1 --port=5000 --debug
