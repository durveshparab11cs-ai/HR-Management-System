"""
app/extensions/limiter.py
==========================
Flask-Limiter extension instance for rate limiting.

Protects endpoints from brute-force attacks, DoS, and API abuse.
Default limits are configured via RATELIMIT_DEFAULT in app config.

Per-route limits are applied with the @limiter.limit() decorator.
Authentication endpoints have stricter limits defined in their routes.

Storage backend:
    Development  — in-memory (resets on restart)
    Production   — Redis (persistent across workers/restarts)
"""

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Single Limiter instance.
# key_func=get_remote_address uses the client's IP address as the rate
# limit key. In production behind a proxy, configure X-Forwarded-For
# trust via ProxyFix middleware.
limiter: Limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",  # Overridden by RATELIMIT_STORAGE_URL from config
)
