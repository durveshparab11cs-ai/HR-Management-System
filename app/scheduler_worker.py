#!/usr/bin/env python3
"""
app/scheduler_worker.py
=======================
Dedicated standalone background scheduler daemon for Smart HRMS ERP.
Runs outside of Gunicorn web processes to eliminate duplicate job runs.

Usage:
    python -m app.scheduler_worker
    or systemd: smart-hrms-scheduler.service
"""

import os
import sys
import time
import signal
import logging
from pathlib import Path

# Ensure root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

# Load production env if present, else .env
prod_env = PROJECT_ROOT / ".env.production"
dev_env = PROJECT_ROOT / ".env"
if prod_env.exists():
    load_dotenv(prod_env, override=True)
else:
    load_dotenv(dev_env)

# Ensure DATABASE_URL is normalized
db_url = os.environ.get("DATABASE_URL", "")
if db_url.startswith("postgres://"):
    os.environ["DATABASE_URL"] = db_url.replace("postgres://", "postgresql://", 1)

from app import create_app
from app.extensions.scheduler import scheduler, register_standard_jobs

# Configure worker logging
logger = logging.getLogger("scheduler_worker")
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [scheduler_worker] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)

_running = True

def _handle_exit_signal(signum, frame):
    global _running
    logger.info("Received termination signal (%s). Initiating graceful shutdown...", signum)
    _running = False
    if scheduler.running:
        scheduler.shutdown(wait=True)
    logger.info("Scheduler shutdown complete.")
    sys.exit(0)

def run_worker():
    """Main loop for the dedicated scheduler worker."""
    global _running
    signal.signal(signal.SIGINT, _handle_exit_signal)
    signal.signal(signal.SIGTERM, _handle_exit_signal)

    env = os.environ.get("FLASK_ENV", "production")
    logger.info("Booting Smart HRMS Flask application in '%s' environment...", env)
    
    app = create_app(env)

    with app.app_context():
        tz = app.config.get("SCHEDULER_TIMEZONE", "Asia/Kolkata")
        logger.info("Configuring scheduler with timezone: %s", tz)
        scheduler.configure(timezone=tz)
        register_standard_jobs(app)
        
        logger.info("Starting standalone APScheduler...")
        scheduler.start()
        logger.info("✓ Dedicated scheduler worker is active and running.")
        
        for job in scheduler.get_jobs():
            logger.info("  Active Job: id=%s | next_run=%s | trigger=%s", job.id, job.next_run_time, job.trigger)

    # Keep main thread alive
    while _running:
        try:
            time.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            _handle_exit_signal("KEYBOARD_INTERRUPT", None)
            break

if __name__ == "__main__":
    run_worker()
