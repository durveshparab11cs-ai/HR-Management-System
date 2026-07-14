"""
app/logging_config.py
======================
Centralized logging configuration for Smart HRMS.

Log files:
    logs/application.log  — all INFO+ application events
    logs/error.log        — ERROR+ only (fast triage)
    logs/security.log     — authentication, authorization, suspicious events
    logs/audit.log        — all data mutations (create/update/delete) for compliance
    logs/scheduler.log    — scheduled job execution events

All handlers use RotatingFileHandler with size-based rotation.
Console handler is added in development for real-time feedback.

Usage:
    Called once from create_app() via setup_logging(app).
    Thereafter, modules use:
        import logging
        logger = logging.getLogger(__name__)
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler


def setup_logging(app) -> None:
    """
    Configure the Python logging system for the Flask application.

    Creates log directory if absent, attaches RotatingFileHandlers
    for each log channel, and adds a StreamHandler in development.

    Args:
        app: The Flask application instance (config already loaded).
    """
    log_dir    = app.config.get("LOG_DIR", "./logs")
    log_level_name = app.config.get("LOG_LEVEL", "INFO").upper()
    log_level  = getattr(logging, log_level_name, logging.INFO)
    max_bytes  = app.config.get("LOG_MAX_BYTES", 10 * 1024 * 1024)
    backup_cnt = app.config.get("LOG_BACKUP_COUNT", 10)

    # Ensure log directory exists
    os.makedirs(log_dir, exist_ok=True)

    # Shared formatter — structured, machine-parseable
    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    def _rotating(filename: str, level: int = logging.DEBUG) -> RotatingFileHandler:
        h = RotatingFileHandler(
            os.path.join(log_dir, filename),
            maxBytes=max_bytes,
            backupCount=backup_cnt,
            encoding="utf-8",
        )
        h.setLevel(level)
        h.setFormatter(fmt)
        return h

    # ── Root application logger ─────────────────────────────────────
    app_logger = logging.getLogger("application")
    app_logger.setLevel(log_level)
    app_logger.addHandler(_rotating("application.log", log_level))
    app_logger.propagate = False

    # ── Error-only logger (quick triage) ───────────────────────────
    err_logger = logging.getLogger("error")
    err_logger.setLevel(logging.ERROR)
    err_logger.addHandler(_rotating("error.log", logging.ERROR))
    err_logger.propagate = False

    # ── Security events ─────────────────────────────────────────────
    sec_logger = logging.getLogger("security")
    sec_logger.setLevel(logging.WARNING)
    sec_logger.addHandler(_rotating("security.log", logging.WARNING))
    sec_logger.propagate = False

    # ── Audit trail (compliance) ────────────────────────────────────
    audit_logger = logging.getLogger("audit")
    audit_logger.setLevel(logging.INFO)
    audit_logger.addHandler(_rotating("audit.log", logging.INFO))
    audit_logger.propagate = False

    # ── Scheduler ──────────────────────────────────────────────────
    sched_logger = logging.getLogger("apscheduler")
    sched_logger.setLevel(logging.WARNING)
    sched_logger.addHandler(_rotating("scheduler.log", logging.WARNING))
    sched_logger.propagate = False

    # ── Attendance ─────────────────────────────────────────────────
    att_logger = logging.getLogger("attendance")
    att_logger.setLevel(logging.INFO)
    att_logger.addHandler(_rotating("attendance.log", logging.INFO))
    att_logger.propagate = False

    # ── Flask's own logger → application.log ───────────────────────
    app.logger.setLevel(log_level)
    if not app.logger.handlers:
        app.logger.addHandler(_rotating("application.log", log_level))

    # ── Console output in development ──────────────────────────────
    if app.config.get("DEBUG"):
        console = logging.StreamHandler(sys.stdout)
        console.setLevel(logging.DEBUG)
        console.setFormatter(logging.Formatter(
            "%(asctime)s %(levelname)-8s %(name)s — %(message)s",
            datefmt="%H:%M:%S",
        ))
        for lg in (app_logger, app.logger):
            if not any(isinstance(h, logging.StreamHandler) for h in lg.handlers):
                lg.addHandler(console)

    app.logger.info(
        "Logging initialized | env=%s | level=%s | dir=%s",
        app.config.get("FLASK_ENV", "unknown"),
        log_level_name,
        log_dir,
    )
