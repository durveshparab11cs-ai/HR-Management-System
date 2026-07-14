"""
app/error_handlers.py
======================
Global HTTP and application-level error handlers.

All handlers are registered via register_error_handlers(app) which
is called from create_app() after blueprints are registered.

Design:
    - HTML responses for browser requests (Accept: text/html)
    - JSON responses for API / XHR requests (Accept: application/json
      or X-Requested-With header present)
    - Errors are logged with severity appropriate to the status code
    - 5xx errors include a unique error_id for support correlation
"""

import logging
import traceback
import uuid

from flask import jsonify, render_template, request
from werkzeug.exceptions import HTTPException

from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    BusinessRuleViolation,
    HRMSBaseError,
    RecordNotFoundError,
    ValidationError,
)

logger = logging.getLogger("error")


# ── Helpers ─────────────────────────────────────────────────────────────

def _is_api_request() -> bool:
    """Return True when the request expects a JSON response."""
    return (
        request.path.startswith("/api/")
        or request.headers.get("X-Requested-With") == "XMLHttpRequest"
        or "application/json" in request.headers.get("Accept", "")
    )


def _json_error(code: int, message: str, details=None):
    payload = {"success": False, "error": {"code": code, "message": message}}
    if details:
        payload["error"]["details"] = details
    return jsonify(payload), code


def _html_error(template: str, code: int, **context):
    return render_template(f"errors/{template}.html", **context), code


# ── HTTP Error Handlers ──────────────────────────────────────────────────

def handle_400(e):
    msg = "Bad request. Please check your input and try again."
    if _is_api_request():
        return _json_error(400, msg)
    return _html_error("400", 400)


def handle_401(e):
    msg = "Authentication required. Please sign in to continue."
    if _is_api_request():
        return _json_error(401, msg)
    return _html_error("401", 401)


def handle_403(e):
    msg = "You don't have permission to access this resource."
    logger.warning("403 Forbidden | path=%s | ip=%s", request.path, request.remote_addr)
    if _is_api_request():
        return _json_error(403, msg)
    return _html_error("403", 403)


def handle_404(e):
    if _is_api_request():
        return _json_error(404, f"Resource not found: {request.path}")
    return _html_error("404", 404)


def handle_405(e):
    msg = f"Method {request.method} is not allowed on {request.path}."
    if _is_api_request():
        return _json_error(405, msg)
    return _html_error("405", 405)


def handle_429(e):
    msg = "Too many requests. Please wait before trying again."
    if _is_api_request():
        return _json_error(429, msg)
    return _html_error("429", 429)


def handle_500(e):
    error_id = uuid.uuid4().hex[:12].upper()
    logger.error(
        "500 Internal Server Error | error_id=%s | path=%s\n%s",
        error_id,
        request.path,
        traceback.format_exc(),
    )
    if _is_api_request():
        return _json_error(500, "An internal server error occurred. Our team has been notified.", {"error_id": error_id})
    return _html_error("500", 500, error_id=error_id)


def handle_503(e):
    msg = "Service temporarily unavailable. Please try again shortly."
    if _is_api_request():
        return _json_error(503, msg)
    return _html_error("503", 503)


# ── Generic HTTPException handler ───────────────────────────────────────

def handle_http_exception(e: HTTPException):
    """Catch-all for any Werkzeug HTTP exception not explicitly handled."""
    if _is_api_request():
        return _json_error(e.code, e.description)
    return render_template(
        "errors/base_error.html",
        error_heading=e.name,
        error_body=e.description,
        error_code_bg=e.code,
    ), e.code


# ── Domain Exception Handlers ────────────────────────────────────────────

def handle_record_not_found(e: RecordNotFoundError):
    if _is_api_request():
        return _json_error(404, str(e))
    return _html_error("404", 404)


def handle_auth_error(e: AuthenticationError):
    if _is_api_request():
        return _json_error(401, str(e))
    return _html_error("401", 401)


def handle_authz_error(e: AuthorizationError):
    if _is_api_request():
        return _json_error(403, str(e))
    return _html_error("403", 403)


def handle_validation_error(e: ValidationError):
    if _is_api_request():
        return _json_error(422, str(e), e.errors or None)
    # For browser requests flash the error and redirect back
    from flask import flash, redirect, url_for  # noqa: PLC0415
    flash(str(e), "danger")
    return redirect(request.referrer or url_for("dashboard.index"))


def handle_business_rule(e: BusinessRuleViolation):
    if _is_api_request():
        return _json_error(409, str(e))
    from flask import flash, redirect, url_for  # noqa: PLC0415
    flash(str(e), "warning")
    return redirect(request.referrer or url_for("dashboard.index"))


def handle_csrf_error(e):
    """Handle Flask-WTF CSRF validation failures."""
    from app.constants.messages import Messages  # noqa: PLC0415
    logger.warning("CSRF error | path=%s | ip=%s", request.path, request.remote_addr)
    if _is_api_request():
        return _json_error(400, Messages.Auth.CSRF_ERROR)
    from flask import flash, redirect, url_for  # noqa: PLC0415
    flash(Messages.Auth.CSRF_ERROR, "danger")
    return redirect(url_for("authentication.login"))


# ── Registration ─────────────────────────────────────────────────────────

def register_error_handlers(app) -> None:
    """
    Register all error handlers with the Flask application.

    Called from create_app() after blueprints are registered.

    Args:
        app: The Flask application instance.
    """
    from flask_wtf.csrf import CSRFError  # noqa: PLC0415

    # HTTP status codes
    app.register_error_handler(400, handle_400)
    app.register_error_handler(401, handle_401)
    app.register_error_handler(403, handle_403)
    app.register_error_handler(404, handle_404)
    app.register_error_handler(405, handle_405)
    app.register_error_handler(429, handle_429)
    app.register_error_handler(500, handle_500)
    app.register_error_handler(503, handle_503)

    # Generic HTTP exception fallback
    app.register_error_handler(HTTPException, handle_http_exception)

    # CSRF
    app.register_error_handler(CSRFError, handle_csrf_error)

    # Domain exceptions
    app.register_error_handler(RecordNotFoundError,  handle_record_not_found)
    app.register_error_handler(AuthenticationError,  handle_auth_error)
    app.register_error_handler(AuthorizationError,   handle_authz_error)
    app.register_error_handler(ValidationError,      handle_validation_error)
    app.register_error_handler(BusinessRuleViolation, handle_business_rule)

    app.logger.info("Error handlers registered.")
