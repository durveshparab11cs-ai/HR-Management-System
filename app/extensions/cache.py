"""
app/extensions/cache.py
========================
Flask-Caching extension instance.

Used for caching expensive query results, rendered template fragments,
and computed values (e.g., dashboard statistics, dropdown data).

Cache backends:
    Development  — SimpleCache (in-memory, single-process)
    Production   — RedisCache (shared across Gunicorn workers)

Usage:
    from app.extensions import cache

    @cache.cached(timeout=300, key_prefix="dashboard_stats")
    def get_dashboard_stats():
        ...

    # Invalidate explicitly
    cache.delete("dashboard_stats")
    cache.delete_memoized(get_dashboard_stats)
"""

from flask_caching import Cache

# Single Cache instance.
cache: Cache = Cache()
