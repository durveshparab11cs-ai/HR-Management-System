#!/usr/bin/env python3
"""
Run Smart HRMS directly with HTTPS (no Nginx).
Uses Flask's built-in SSL support.
"""

import os
import sys
from pathlib import Path

# Load environment
from dotenv import load_dotenv
load_dotenv()

# Fix database URL if needed
_db_url = os.environ.get("DATABASE_URL", "")
if _db_url.startswith("postgres://"):
    os.environ["DATABASE_URL"] = _db_url.replace("postgres://", "postgresql://", 1)

# Create app
from app import create_app
app = create_app(os.environ.get("FLASK_ENV", "production"))

if __name__ == "__main__":
    # Certificate and key paths
    cert_file = r"C:\Smart_HRMS\certs\smart-hrms.crt"
    key_file = r"C:\Smart_HRMS\certs\smart-hrms.key"
    
    # Verify files exist
    if not Path(cert_file).exists() or not Path(key_file).exists():
        print("ERROR: Certificate files not found!")
        print(f"  Certificate: {cert_file}")
        print(f"  Key: {key_file}")
        sys.exit(1)
    
    print("")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║     Smart HRMS - HTTPS Server (Direct Flask + SSL)        ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print("")
    print("Starting server...")
    print("  URL: https://192.168.0.5:443")
    print("  Certificate: self-signed (10 years)")
    print("  Mode: Production (debug=off)")
    print("")
    
    # Run with SSL
    app.run(
        host="0.0.0.0",
        port=443,
        debug=False,
        use_reloader=False,
        use_debugger=False,
        ssl_context=(cert_file, key_file)
    )
