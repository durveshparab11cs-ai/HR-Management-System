"""
app/utils/pagination_utils.py
==============================
Pagination metadata builders and query parameter helpers.

Centralizes pagination logic so that every list endpoint uses
consistent page/per_page defaults and limits.
"""

from typing import Any

from flask import request

from app.constants.limits import Limits


def get_page_args() -> tuple[int, int]:
    """
    Extract and validate page and per_page from the current request's
    query string parameters.

    Applies sensible defaults and enforces min/max limits.

    Returns:
        Tuple of (page, per_page) integers.
    """
    try:
        page = max(1, int(request.args.get("page", 1)))
    except (ValueError, TypeError):
        page = 1

    try:
        per_page = int(request.args.get("per_page", Limits.Pagination.DEFAULT_PAGE_SIZE))
        per_page = max(Limits.Pagination.MIN_PAGE_SIZE,
                       min(per_page, Limits.Pagination.MAX_PAGE_SIZE))
    except (ValueError, TypeError):
        per_page = Limits.Pagination.DEFAULT_PAGE_SIZE

    return page, per_page


def build_pagination_meta(pagination) -> dict[str, Any]:
    """
    Build a pagination metadata dictionary from a SQLAlchemy Pagination object.

    Args:
        pagination: SQLAlchemy Pagination object from .paginate().

    Returns:
        Dictionary with pagination metadata suitable for JSON responses
        and template context.
    """
    return {
        "page": pagination.page,
        "per_page": pagination.per_page,
        "total": pagination.total,
        "pages": pagination.pages,
        "has_next": pagination.has_next,
        "has_prev": pagination.has_prev,
        "next_num": pagination.next_num,
        "prev_num": pagination.prev_num,
        "iter_pages": list(pagination.iter_pages(
            left_edge=1, left_current=2, right_current=3, right_edge=1
        )),
    }


def build_page_range(current_page: int, total_pages: int, window: int = 5) -> list[int | None]:
    """
    Build a list of page numbers for a pagination widget.

    Inserts None values to represent '...' ellipsis gaps.

    Args:
        current_page: The currently active page.
        total_pages: Total number of pages.
        window: Number of pages to show on each side of current_page.

    Returns:
        List of page numbers and None values for gaps.
        Example: [1, None, 4, 5, 6, None, 10]
    """
    if total_pages <= 0:
        return []

    pages = []
    left_edge = 1
    right_edge = total_pages
    left_window = max(1, current_page - window)
    right_window = min(total_pages, current_page + window)

    # Always include first page
    pages.append(left_edge)

    if left_window > left_edge + 1:
        pages.append(None)  # Ellipsis

    for p in range(left_window, right_window + 1):
        if p not in pages:
            pages.append(p)

    if right_window < right_edge - 1:
        pages.append(None)  # Ellipsis

    if right_edge not in pages:
        pages.append(right_edge)

    return pages
