"""
app/extensions/scheduler.py
============================
APScheduler extension for background task scheduling.

Handles recurring jobs such as:
    - Sending attendance reminders
    - Generating payroll on schedule
    - Archiving old audit logs
    - Sending birthday/anniversary notifications
    - Cleaning up expired sessions and temporary files

Jobs are registered in their respective service modules and
scheduled during application startup via configure_scheduler().

IMPORTANT: In multi-worker production deployments (Gunicorn with
multiple workers), only one worker should run the scheduler to avoid
duplicate job execution. Use a distributed lock via Redis, or run
the scheduler in a dedicated single worker/process.
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.pool import ThreadPoolExecutor

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

# Single BackgroundScheduler instance.
scheduler: BackgroundScheduler = BackgroundScheduler(
    jobstores=_jobstores,
    executors=_executors,
    job_defaults=_job_defaults,
)


def configure_scheduler(app) -> None:
    """
    Configure and start the scheduler with the Flask app context.

    Called from the application factory. Only starts the scheduler
    if not already running (prevents double-start in reloader mode).

    Args:
        app: The Flask application instance.
    """
    if app.config.get("TESTING") or app.config.get("SCHEDULER_API_ENABLED") is False:
        # Do not start scheduler in test mode or when explicitly disabled.
        return

    if not scheduler.running:
        # Register all recurring jobs here as the application grows.
        # Each module will provide a register_jobs(scheduler) function.
        # Example:
        # from app.services.notification_service import register_jobs
        # register_jobs(scheduler)

        scheduler.configure(timezone=app.config.get("SCHEDULER_TIMEZONE", "UTC"))
        scheduler.start()

        app.logger.info("APScheduler started successfully.")
