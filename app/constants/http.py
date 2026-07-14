"""
app/constants/http.py
======================
HTTP status code constants.

Provides named constants for HTTP status codes used in API responses
and error handlers, eliminating magic integers across the codebase.

Usage:
    from app.constants import HTTP
    return jsonify(data), HTTP.OK
    return jsonify(error=msg), HTTP.BAD_REQUEST
"""


class HTTP:
    """Standard HTTP status codes."""

    # 2xx Success
    OK: int = 200
    CREATED: int = 201
    ACCEPTED: int = 202
    NO_CONTENT: int = 204

    # 3xx Redirection
    MOVED_PERMANENTLY: int = 301
    FOUND: int = 302
    NOT_MODIFIED: int = 304

    # 4xx Client Errors
    BAD_REQUEST: int = 400
    UNAUTHORIZED: int = 401
    FORBIDDEN: int = 403
    NOT_FOUND: int = 404
    METHOD_NOT_ALLOWED: int = 405
    CONFLICT: int = 409
    GONE: int = 410
    UNPROCESSABLE_ENTITY: int = 422
    TOO_MANY_REQUESTS: int = 429

    # 5xx Server Errors
    INTERNAL_SERVER_ERROR: int = 500
    NOT_IMPLEMENTED: int = 501
    BAD_GATEWAY: int = 502
    SERVICE_UNAVAILABLE: int = 503
    GATEWAY_TIMEOUT: int = 504
