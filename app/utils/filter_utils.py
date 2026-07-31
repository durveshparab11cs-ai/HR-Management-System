"""
app/utils/filter_utils.py
==========================
Query filtering and sorting utilities for REST APIs.

Provides helpers to build SQLAlchemy filters from query parameters.
"""

from typing import Any, Optional
from datetime import datetime, date
from flask import request
from sqlalchemy import or_, and_


def get_sort_params(default_sort: str = 'id', default_order: str = 'desc') -> tuple[str, str]:
    """
    Extract sort and order parameters from request.
    
    Args:
        default_sort: Default field to sort by
        default_order: Default sort order ('asc' or 'desc')
    
    Returns:
        Tuple of (sort_field, sort_order)
    """
    sort_field = request.args.get('sort', default_sort)
    sort_order = request.args.get('order', default_order).lower()
    
    # Validate order
    if sort_order not in ['asc', 'desc']:
        sort_order = default_order
    
    return sort_field, sort_order


def apply_sorting(query, model, sort_field: str, sort_order: str):
    """
    Apply sorting to a SQLAlchemy query.
    
    Args:
        query: SQLAlchemy query object
        model: SQLAlchemy model class
        sort_field: Field name to sort by
        sort_order: 'asc' or 'desc'
    
    Returns:
        Query with sorting applied
    """
    if not hasattr(model, sort_field):
        # If field doesn't exist, don't sort
        return query
    
    field = getattr(model, sort_field)
    
    if sort_order == 'desc':
        return query.order_by(field.desc())
    else:
        return query.order_by(field.asc())


def get_date_range_params() -> tuple[Optional[date], Optional[date]]:
    """
    Extract start_date and end_date from request parameters.
    
    Returns:
        Tuple of (start_date, end_date) or (None, None) if not provided
    """
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    start_date = None
    end_date = None
    
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    return start_date, end_date


def apply_date_range_filter(query, field, start_date: Optional[date], end_date: Optional[date]):
    """
    Apply date range filter to query.
    
    Args:
        query: SQLAlchemy query
        field: Model field to filter
        start_date: Start date (inclusive)
        end_date: End date (inclusive)
    
    Returns:
        Query with date filter applied
    """
    if start_date:
        query = query.filter(field >= start_date)
    
    if end_date:
        query = query.filter(field <= end_date)
    
    return query


def get_status_filter() -> Optional[str]:
    """
    Extract status filter from request parameters.
    
    Returns:
        Status value or None
    """
    return request.args.get('status')


def get_search_param() -> Optional[str]:
    """
    Extract search query from request parameters.
    
    Returns:
        Search query string or None
    """
    search = request.args.get('search', '').strip()
    return search if search else None


def apply_search_filter(query, model, search_fields: list[str], search_query: str):
    """
    Apply search filter across multiple fields.
    
    Args:
        query: SQLAlchemy query
        model: Model class
        search_fields: List of field names to search in
        search_query: Search term
    
    Returns:
        Query with search filter applied
    """
    if not search_query:
        return query
    
    search_pattern = f"%{search_query}%"
    conditions = []
    
    for field_name in search_fields:
        if hasattr(model, field_name):
            field = getattr(model, field_name)
            conditions.append(field.ilike(search_pattern))
    
    if conditions:
        query = query.filter(or_(*conditions))
    
    return query


def get_filter_params(allowed_filters: list[str]) -> dict[str, Any]:
    """
    Extract allowed filter parameters from request.
    
    Args:
        allowed_filters: List of allowed filter parameter names
    
    Returns:
        Dictionary of filter key-value pairs
    """
    filters = {}
    
    for filter_name in allowed_filters:
        value = request.args.get(filter_name)
        if value is not None:
            filters[filter_name] = value
    
    return filters


def apply_filters(query, model, filters: dict[str, Any]):
    """
    Apply multiple filters to query.
    
    Args:
        query: SQLAlchemy query
        model: Model class
        filters: Dictionary of field_name: value
    
    Returns:
        Query with filters applied
    """
    for field_name, value in filters.items():
        if hasattr(model, field_name):
            field = getattr(model, field_name)
            
            # Handle boolean values
            if value.lower() in ['true', '1', 'yes']:
                query = query.filter(field == True)
            elif value.lower() in ['false', '0', 'no']:
                query = query.filter(field == False)
            else:
                query = query.filter(field == value)
    
    return query


class QueryBuilder:
    """
    Fluent query builder for common filtering patterns.
    
    Usage:
        builder = QueryBuilder(Attendance.query, Attendance)
        builder.add_pagination()
        builder.add_sorting('date', 'desc')
        builder.add_date_range('date')
        builder.add_status_filter('status')
        query = builder.build()
    """
    
    def __init__(self, query, model):
        self.query = query
        self.model = model
        self.page = 1
        self.per_page = 20
    
    def add_pagination(self):
        """Add pagination parameters."""
        from app.utils.pagination_utils import get_page_args
        self.page, self.per_page = get_page_args()
        return self
    
    def add_sorting(self, default_sort: str = 'id', default_order: str = 'desc'):
        """Add sorting."""
        sort_field, sort_order = get_sort_params(default_sort, default_order)
        self.query = apply_sorting(self.query, self.model, sort_field, sort_order)
        return self
    
    def add_date_range(self, field_name: str):
        """Add date range filter."""
        start_date, end_date = get_date_range_params()
        if hasattr(self.model, field_name):
            field = getattr(self.model, field_name)
            self.query = apply_date_range_filter(self.query, field, start_date, end_date)
        return self
    
    def add_status_filter(self, field_name: str = 'status'):
        """Add status filter."""
        status = get_status_filter()
        if status and hasattr(self.model, field_name):
            field = getattr(self.model, field_name)
            self.query = self.query.filter(field == status)
        return self
    
    def add_search(self, search_fields: list[str]):
        """Add search filter."""
        search_query = get_search_param()
        if search_query:
            self.query = apply_search_filter(self.query, self.model, search_fields, search_query)
        return self
    
    def add_custom_filter(self, field_name: str, value: Any):
        """Add custom filter."""
        if hasattr(self.model, field_name):
            field = getattr(self.model, field_name)
            self.query = self.query.filter(field == value)
        return self
    
    def build(self):
        """Build and return the query."""
        return self.query
    
    def paginate(self):
        """Execute query with pagination."""
        return self.query.paginate(
            page=self.page,
            per_page=self.per_page,
            error_out=False
        )
