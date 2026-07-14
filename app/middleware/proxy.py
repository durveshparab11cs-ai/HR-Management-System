"""
app/middleware/proxy.py
========================
Werkzeug ProxyFix middleware for reverse proxy support.

When Flask runs behind Nginx or a load balancer, the client's real IP
and the original HTTP scheme are passed via X-Forwarded-* headers.
Without ProxyFix, Flask sees the proxy's IP (127.0.0.1) instead of
the real client IP, breaking:
    - Rate limiting (all clients appear to be the same IP)
    - Audit logs (wrong IP recorded)
    - HTTPS detection (url_for generates http:// links)

ProxyFix trusts exactly one proxy hop (x_for=1, x_proto=1, x_host=1),
which is correct for a single Nginx reverse proxy in front of Gunicorn.

SECURITY: Do NOT set x_for > 1 unless you have multiple trusted proxies.
Setting a higher value opens IP spoofing via X-Forwarded-For injection.
"""

import logging

logger = logging.getLogger(__name__)


def register_proxy_fix(app) -> None:
    """
    Wrap the Flask app with Werkzeug's ProxyFix middleware.

    Only applied in production to avoid masking the real client IP
    during local development without a proxy.

    Args:
        app: The Flask application instance.
    """
    if not app.config.get("DEBUG", True):
        # Production: wrap with ProxyFix
        from werkzeug.middleware.proxy_fix import ProxyFix  # noqa: PLC0415
        app.wsgi_app = ProxyFix(
            app.wsgi_app,
            x_for=1,      # Trust one X-Forwarded-For hop
            x_proto=1,    # Trust X-Forwarded-Proto for HTTPS detection
            x_host=1,     # Trust X-Forwarded-Host
            x_prefix=1,   # Trust X-Forwarded-Prefix for sub-path deployments
        )
        logger.info("ProxyFix middleware applied (production mode).")
    else:
        logger.debug("ProxyFix skipped (development mode).")
