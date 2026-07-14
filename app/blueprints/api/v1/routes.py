"""
blueprints/api/v1/routes.py
==============================
API v1 route definitions.

All routes return JSON using response_utils helpers.
CSRF is exempt — authentication is via Bearer token.
Rate limiting is applied per endpoint.

Current endpoints (skeleton):
    GET  /api/v1/health          — liveness probe
    GET  /api/v1/me              — current authenticated user info
"""

from flask import g
from flask_login import login_required

from app.utils.response_utils import success_response
from app.constants.limits import Limits
from app.extensions.limiter import limiter
from app.extensions.csrf import csrf
from .. import api_bp


# Exempt the entire API blueprint from CSRF — uses token auth instead.
csrf.exempt(api_bp)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@api_bp.route("/health", methods=["GET"])
def health():
    """
    Liveness probe endpoint for load balancers and Docker health checks.

    Returns HTTP 200 with status 'ok' when the application is running.
    Does not require authentication.
    """
    return success_response(data={"status": "ok", "version": "1.0.0"})


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

@api_bp.route("/me", methods=["GET"])
@login_required
@limiter.limit(Limits.RateLimit.API_DEFAULT)
def me():
    """Return the current authenticated user's profile."""
    from flask_login import current_user  # noqa: PLC0415
    return success_response(data={
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
    })
