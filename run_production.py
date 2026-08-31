#!/usr/bin/env python
"""
Production Server Startup - Using Waitress (Windows-Compatible)
================================================================
Starts the Smart HRMS application using Waitress, a pure Python WSGI server
that works well on Windows and provides better performance than Flask dev server.

Usage:
    python run_production.py

Configuration:
    - Host: 0.0.0.0 (all interfaces)
    - Port: 8000
    - Workers: 4 threads
    - Timeout: 120 seconds
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Force SQLite if PostgreSQL is present
if os.environ.get("DATABASE_URL", "").startswith("postgresql://"):
    del os.environ["DATABASE_URL"]

from app import create_app  # noqa: E402
from waitress import serve

# Create production app
app = create_app("production")

if __name__ == "__main__":
    print("=" * 70)
    print("Smart HRMS - Starting Production Server (Waitress)")
    print("=" * 70)
    print("Server: http://0.0.0.0:8000")
    print("Environment: production")
    print("Workers: 4 threads")
    print("=" * 70)
    
    # Serve with Waitress - 4 threads for concurrent request handling
    serve(app, host="0.0.0.0", port=8000, threads=4, _quiet=False)
