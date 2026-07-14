"""
app/extensions/__init__.py
==========================
Central export point for all Flask extension instances.

Import extensions from here — never from individual extension modules —
to avoid circular imports throughout the application.

Usage:
    from app.extensions import db, login_manager, mail
"""

from .cache import cache
from .csrf import csrf
from .database import db
from .limiter import limiter
from .login import login_manager
from .mail import mail
from .migrate import migrate
from .scheduler import scheduler
from .session import server_session

__all__ = [
    "db",
    "migrate",
    "login_manager",
    "mail",
    "csrf",
    "limiter",
    "cache",
    "scheduler",
    "server_session",
]
