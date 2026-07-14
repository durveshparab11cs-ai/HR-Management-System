"""
app/utils/response_utils.py
============================
Standardized HTTP JSON response builders for the API blueprint.

Enforces a consistent response envelope shape across all API endpoints:

    Success:
        {
            "success": true,
            "data": { ... },
            "message": "Optional message",
            "meta": { "page": 1, "total": 100, ... }
        }

    Error:
        {
            "success": false,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Human-readable error",
                "details": { "field": "error text" }
            }
        }
"""

from typing import Any, Optional

from flask import jsonify

from app.constants.http import HTTP


def success_response(
    data: Any = None,
    message: Optional[str] = None,
    meta: Optional[dict] = None,
    status_code: int = HTTP.OK,
):
    """
    Build a standardized success JSON response.

    Args:
        data: Response payload (dict, list, or None).
        message: Optional human-readable success message.
        meta: Optional metadata (pagination info, totals, etc.).
        status_code: HTTP status code (default 200).

    Returns:
        Flask Response with JSON body and given status code.
    """
    payload: dict[str, Any] = {"success": True}

    if data is not None:
        payload["data"] = data
    if message:
        payload["message"] = message
    if meta:
        payload["meta"] = meta

    return jsonify(payload), status_code


def created_response(data: Any = None, message: str = "Resource created successfully."):
    """Shortcut for HTTP 201 Created responses."""
    return success_response(data=data, message=message, status_code=HTTP.CREATED)


def no_content_response():
    """Shortcut for HTTP 204 No Content responses (e.g., DELETE success)."""
    return "", HTTP.NO_CONTENT


def error_response(
    message: str,
    code: str = "ERROR",
    details: Optional[dict] = None,
    status_code: int = HTTP.BAD_REQUEST,
):
    """
    Build a standardized error JSON response.

    Args:
        message: Human-readable error description.
        code: Machine-readable error code (UPPER_SNAKE_CASE).
        details: Optional field-level error details dict.
        status_code: HTTP status code (default 400).

    Returns:
        Flask Response with JSON error envelope.
    """
    error_payload: dict[str, Any] = {
        "code": code,
        "message": message,
    }
    if details:
        error_payload["details"] = details

    return jsonify({"success": False, "error": error_payload}), status_code


def validation_error_response(errors: dict[str, str]):
    """
    Build a 422 Unprocessable Entity response for field-level validation errors.

    Args:
        errors: Dict mapping field names to error message strings.

    Returns:
        Flask Response with 422 status.
    """
    return error_response(
        message="Validation failed. Please check the submitted data.",
        code="VALIDATION_ERROR",
        details=errors,
        status_code=HTTP.UNPROCESSABLE_ENTITY,
    )


def not_found_response(resource: str = "Resource"):
    """
    Build a 404 Not Found response.

    Args:
        resource: Name of the resource that wasn't found.

    Returns:
        Flask Response with 404 status.
    """
    return error_response(
        message=f"{resource} not found.",
        code="NOT_FOUND",
        status_code=HTTP.NOT_FOUND,
    )


def unauthorized_response(message: str = "Authentication required."):
    """Build a 401 Unauthorized response."""
    return error_response(
        message=message,
        code="UNAUTHORIZED",
        status_code=HTTP.UNAUTHORIZED,
    )


def forbidden_response(message: str = "You do not have permission to perform this action."):
    """Build a 403 Forbidden response."""
    return error_response(
        message=message,
        code="FORBIDDEN",
        status_code=HTTP.FORBIDDEN,
    )


def paginated_response(
    items: list,
    total: int,
    page: int,
    per_page: int,
    message: Optional[str] = None,
):
    """
    Build a paginated list response with consistent pagination metadata.

    Args:
        items: Serialized list of records for the current page.
        total: Total number of records across all pages.
        page: Current page number (1-based).
        per_page: Number of records per page.
        message: Optional message.

    Returns:
        Flask Response with pagination metadata in 'meta'.
    """
    pages = (total + per_page - 1) // per_page if per_page > 0 else 0
    meta = {
        "page": page,
        "per_page": per_page,
        "total": total,
        "pages": pages,
        "has_next": page < pages,
        "has_prev": page > 1,
    }
    return success_response(data=items, message=message, meta=meta)
