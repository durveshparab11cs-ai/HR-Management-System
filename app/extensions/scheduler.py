"""
app/extensions/scheduler.py
============================
APScheduler extension for background task scheduling.

Handles recurring jobs such as:
    - Attendance end-of-day reconciliation
    - Cleaning up expired sessions and temporary files
    - Email notification queues

Architecture for Multi-Worker / Production Deployment:
    - Web Workers (Gunicorn): Must NOT start independent in-memory schedulers
      (prevents duplicate email/attendance job executions).
    - Dedicated Worker: Runs via `python -m app.scheduler_worker` managed
      by a dedicated systemd service (smart-hrms-scheduler.service).
    - Single-Process Development: Can enable in-process scheduler via
      SCHEDULER_AUTOSTART=True in .env.
"""

import os
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.pool import ThreadPoolExecutor

logger = logging.getLogger("apscheduler")

# Job store configuration
_jobstores = {
    "default": MemoryJobStore(),
}

# Executor configuration — thread pool for I/O-bound jobs
_executors = {
    "default": ThreadPoolExecutor(max_workers=10),
}

# Job defaults
_job_defaults = {
    "coalesce": True,           # Merge missed runs into one execution
    "max_instances": 1,         # Prevent overlapping runs of the same job
    "misfire_grace_time": 300,  # Allow up to 5 minutes late
}

# Single BackgroundScheduler instance
scheduler: BackgroundScheduler = BackgroundScheduler(
    jobstores=_jobstores,
    executors=_executors,
    job_defaults=_job_defaults,
)


def register_standard_jobs(app) -> None:
    """Register all recurring maintenance and background jobs with error handlers."""
    from app.extensions.database import db
    from sqlalchemy import text
    from datetime import datetime

    def job_wrapper(job_func, job_name):
        def _wrapped():
            with app.app_context():
                try:
                    logger.info("SCHEDULED_JOB_START | name=%s | time=%s", job_name, datetime.utcnow())
                    job_func()
                    logger.info("SCHEDULED_JOB_SUCCESS | name=%s", job_name)
                except Exception as exc:
                    logger.error("SCHEDULED_JOB_ERROR | name=%s | reason=%s", job_name, exc, exc_info=True)
        return _wrapped

    def db_keepalive_job():
        """Periodic query to keep connection pool alive and verify health."""
        db.session.execute(text("SELECT 1"))

    def cleanup_temp_uploads():
        """Clean temporary files older than 24 hours."""
        import time
        from pathlib import Path
        temp_dir = Path(app.config.get("UPLOAD_FOLDER", "./instance/uploads")) / "temp"
        if temp_dir.exists():
            now = time.time()
            for p in temp_dir.glob("*"):
                if p.is_file() and now - p.stat().st_mtime > 86400:
                    try:
                        p.unlink()
                    except Exception:
                        pass

    # Add jobs if not already added
    if not scheduler.get_job("db_keepalive"):
        scheduler.add_job(
            job_wrapper(db_keepalive_job, "db_keepalive"),
            trigger="interval",
            minutes=10,
            id="db_keepalive",
            replace_existing=True,
        )

    if not scheduler.get_job("cleanup_temp_uploads"):
        scheduler.add_job(
            job_wrapper(cleanup_temp_uploads, "cleanup_temp_uploads"),
            trigger="cron",
            hour=2,
            minute=0,
            id="cleanup_temp_uploads",
            replace_existing=True,
        )


def configure_scheduler(app) -> None:
    """
    Configure and optionally start the scheduler.
    In web workers under Gunicorn, scheduler autostart is disabled by default
    to prevent duplicate execution. Set SCHEDULER_AUTOSTART=True to override.
    """
    if app.config.get("TESTING"):
        return

    # In production multi-worker Gunicorn, the dedicated worker process runs the scheduler.
    autostart = os.environ.get("SCHEDULER_AUTOSTART", "False").lower() in ("true", "1", "yes")

    if not autostart:
        app.logger.info("APScheduler web worker bypass active (dedicated scheduler worker mode enabled).")
        return

    if not scheduler.running:
        tz = app.config.get("SCHEDULER_TIMEZONE", "Asia/Kolkata")
        scheduler.configure(timezone=tz)
        register_standard_jobs(app)
        scheduler.start()
        app.logger.info("APScheduler started in-process with timezone=%s.", tz)
