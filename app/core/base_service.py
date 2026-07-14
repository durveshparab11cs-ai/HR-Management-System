"""
app/core/base_service.py
=========================
Abstract base class for the service layer.

Services contain ALL business logic. They:
    - Orchestrate repository calls
    - Apply business rules and validations
    - Coordinate cross-model operations
    - Emit audit log entries
    - Handle exceptions and translate them to domain exceptions
    - Never expose SQLAlchemy models directly to routes (return dicts or DTOs)

Routes call services. Services call repositories. Repositories talk to the DB.
Services NEVER import from blueprints/routes. Repositories NEVER contain
business logic.

Concrete services extend BaseService and inject their repository dependency
via the constructor (Dependency Inversion Principle).

Usage:
    class EmployeeService(BaseService):
        def __init__(self):
            super().__init__()
            self.repo = EmployeeRepository()

        def get_employee(self, emp_id: int) -> dict:
            employee = self.repo.get_by_id_or_404(emp_id)
            return employee.to_dict()
"""

import logging
from typing import Any, Optional

from app.core.exceptions import (
    BusinessRuleViolation,
    RecordNotFoundError,
    ValidationError,
)

logger = logging.getLogger(__name__)


class BaseService:
    """
    Abstract base class providing shared service infrastructure.

    Subclasses gain access to:
        - self.logger       — named logger for the concrete service
        - self._get_current_user_id()  — safe current user resolver
        - self._validate_required()    — field presence checker
        - self._emit_audit()           — audit log helper
    """

    def __init__(self) -> None:
        # Each service gets a logger named after its concrete class.
        self.logger = logging.getLogger(
            f"{__name__}.{self.__class__.__name__}"
        )

    # ------------------------------------------------------------------
    # Current User Helpers
    # ------------------------------------------------------------------

    def _get_current_user_id(self) -> Optional[int]:
        """
        Safely retrieve the authenticated user's ID from Flask-Login.

        Returns None if called outside a request context or when the
        user is not authenticated (e.g., during scheduled jobs).

        Returns:
            User ID integer or None.
        """
        try:
            from flask_login import current_user  # noqa: PLC0415

            if current_user and current_user.is_authenticated:
                return current_user.id
        except RuntimeError:
            # Outside application context — safe to return None.
            pass
        return None

    # ------------------------------------------------------------------
    # Validation Helpers
    # ------------------------------------------------------------------

    def _validate_required(self, data: dict, fields: list[str]) -> None:
        """
        Assert that required fields are present and non-empty in data.

        Args:
            data: Dictionary of input data to validate.
            fields: List of field names that must be present and truthy.

        Raises:
            ValidationError: If any required field is missing or blank.
        """
        errors: dict[str, str] = {}
        for field in fields:
            if not data.get(field):
                errors[field] = f"{field.replace('_', ' ').title()} is required."
        if errors:
            raise ValidationError("Validation failed.", errors=errors)

    def _validate_unique(
        self,
        repository: Any,
        field: str,
        value: Any,
        exclude_id: Optional[int] = None,
    ) -> None:
        """
        Assert that a field value is unique in the repository.

        Args:
            repository: Repository instance with a find_one_by() method.
            field: The model field name to check.
            value: The value to check for uniqueness.
            exclude_id: Record ID to exclude (for update operations).

        Raises:
            BusinessRuleViolation: If the value already exists.
        """
        existing = repository.find_one_by(**{field: value})
        if existing and (exclude_id is None or existing.id != exclude_id):
            raise BusinessRuleViolation(
                f"A record with {field}='{value}' already exists."
            )

    # ------------------------------------------------------------------
    # Audit Logging
    # ------------------------------------------------------------------

    def _emit_audit(
        self,
        action: str,
        resource_type: str,
        resource_id: Any,
        details: Optional[str] = None,
    ) -> None:
        """
        Write a structured audit log entry.

        Audit logs are written to the dedicated audit logger which
        routes to logs/audit.log via the logging configuration.

        Args:
            action: The action performed (from AuditAction enum).
            resource_type: The model/entity type affected (e.g. 'Employee').
            resource_id: The PK of the affected record.
            details: Optional human-readable description of the change.
        """
        audit_logger = logging.getLogger("audit")
        user_id = self._get_current_user_id()
        audit_logger.info(
            "AUDIT | user_id=%s | action=%s | resource=%s | id=%s | details=%s",
            user_id,
            action,
            resource_type,
            resource_id,
            details or "",
        )

    # ------------------------------------------------------------------
    # Exception Translators
    # ------------------------------------------------------------------

    def _not_found(self, resource: str, identifier: Any) -> RecordNotFoundError:
        """
        Build a RecordNotFoundError with a consistent message.

        Args:
            resource: Human-readable resource name (e.g., 'Employee').
            identifier: The ID or key used to look up the record.

        Returns:
            RecordNotFoundError ready to be raised.
        """
        return RecordNotFoundError(f"{resource} with id={identifier} was not found.")
