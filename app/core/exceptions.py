"""
app/core/exceptions.py
=======================
Custom exception hierarchy for the Smart HRMS application.

Using a custom exception tree instead of bare Exception or HTTP errors
in the service/repository layer keeps business logic framework-agnostic
and makes error handling in routes explicit and readable.

Exception hierarchy:
    HRMSBaseError
    ├── ValidationError          — user input failed validation
    ├── BusinessRuleViolation    — operation violates a business rule
    ├── RecordNotFoundError      — requested resource does not exist
    ├── DuplicateRecordError     — unique constraint violation
    ├── AuthenticationError      — invalid credentials / session
    ├── AuthorizationError       — insufficient permissions
    ├── FileOperationError       — file upload/download/processing failure
    ├── ExternalServiceError     — third-party API / mail / SMS failure
    └── DatabaseError            — unexpected persistence failure

Route handlers should catch these exceptions and translate them to
appropriate HTTP responses or flash messages.
"""

from typing import Optional


class HRMSBaseError(Exception):
    """
    Root exception for all application-specific errors.

    All custom exceptions inherit from this to allow broad catch clauses
    when needed:
        except HRMSBaseError as e:
            flash(str(e), "danger")
    """

    def __init__(self, message: str, code: Optional[str] = None) -> None:
        super().__init__(message)
        self.message = message
        self.code = code  # Optional machine-readable error code

    def __str__(self) -> str:
        return self.message


class ValidationError(HRMSBaseError):
    """
    Raised when user-submitted data fails business validation.

    Unlike WTForms validation (which is form-layer), this is raised in the
    service layer when cross-field or business-rule validation fails.

    Attributes:
        errors: Dict mapping field names to error messages, suitable for
                rendering inline form errors.

    Example:
        raise ValidationError("Form data invalid.", errors={"email": "Already in use."})
    """

    def __init__(
        self,
        message: str = "Validation failed.",
        errors: Optional[dict[str, str]] = None,
        code: Optional[str] = None,
    ) -> None:
        super().__init__(message, code)
        self.errors: dict[str, str] = errors or {}


class BusinessRuleViolation(HRMSBaseError):
    """
    Raised when an operation would violate a business rule.

    Examples:
        - Approving leave when balance is insufficient
        - Processing payroll that has already been paid
        - Assigning a role the current user cannot grant
    """

    def __init__(self, message: str, code: Optional[str] = None) -> None:
        super().__init__(message, code)


class RecordNotFoundError(HRMSBaseError):
    """
    Raised when a requested resource cannot be found.

    Services raise this; routes catch it and return a 404 response.
    Prefer this over letting SQLAlchemy's NoResultFound bubble up.
    """

    def __init__(self, message: str = "Record not found.", code: Optional[str] = None) -> None:
        super().__init__(message, code)


class DuplicateRecordError(HRMSBaseError):
    """
    Raised when attempting to create a record that already exists
    (unique constraint violation detected at the service level, before
    hitting the database).

    Examples:
        - Registering an email that is already in use
        - Creating a department with a name that already exists
    """

    def __init__(self, message: str = "A duplicate record already exists.", code: Optional[str] = None) -> None:
        super().__init__(message, code)


class AuthenticationError(HRMSBaseError):
    """
    Raised when authentication fails.

    Examples:
        - Wrong password
        - Invalid or expired token
        - Account locked
    """

    def __init__(self, message: str = "Authentication failed.", code: Optional[str] = None) -> None:
        super().__init__(message, code)


class AuthorizationError(HRMSBaseError):
    """
    Raised when an authenticated user attempts an action they are not
    permitted to perform.

    The route error handler should return HTTP 403.
    """

    def __init__(self, message: str = "You do not have permission to perform this action.", code: Optional[str] = None) -> None:
        super().__init__(message, code)


class FileOperationError(HRMSBaseError):
    """
    Raised when a file operation (upload, delete, resize) fails.

    Examples:
        - Uploaded file type is not allowed
        - File exceeds maximum size
        - Storage write error
    """

    def __init__(self, message: str = "File operation failed.", code: Optional[str] = None) -> None:
        super().__init__(message, code)


class ExternalServiceError(HRMSBaseError):
    """
    Raised when a call to an external service fails.

    Examples:
        - SMTP mail send failure
        - SMS gateway timeout
        - Payment gateway error
    """

    def __init__(self, message: str = "External service is unavailable.", code: Optional[str] = None) -> None:
        super().__init__(message, code)


class DatabaseError(HRMSBaseError):
    """
    Raised when an unexpected database-level error occurs that cannot
    be handled gracefully at the repository level.

    These typically surface as HTTP 500 responses.
    """

    def __init__(self, message: str = "A database error occurred.", code: Optional[str] = None) -> None:
        super().__init__(message, code)
