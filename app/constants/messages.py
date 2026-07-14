"""
app/constants/messages.py
==========================
Centralized user-facing flash messages and system messages.

Keeping all messages in one place ensures:
    - Consistent tone and wording across the application.
    - Easy localization in the future (replace with gettext calls).
    - No duplicated strings scattered across route handlers.

Usage:
    from app.constants import Messages
    flash(Messages.Auth.LOGIN_SUCCESS, "success")
"""


class Messages:
    """Namespace container for all application messages."""

    class Auth:
        """Authentication-related messages."""
        LOGIN_SUCCESS = "Welcome back! You have logged in successfully."
        LOGIN_FAILED = "Invalid email or password. Please try again."
        LOGIN_REQUIRED = "Please log in to access this page."
        LOGOUT_SUCCESS = "You have been logged out successfully."
        ACCOUNT_LOCKED = "Your account has been locked due to multiple failed login attempts. Please contact support."
        ACCOUNT_INACTIVE = "Your account is inactive. Please contact your administrator."
        ACCOUNT_SUSPENDED = "Your account has been suspended. Please contact your administrator."
        PASSWORD_RESET_SENT = "Password reset instructions have been sent to your email."
        PASSWORD_RESET_SUCCESS = "Your password has been reset successfully. Please log in."
        PASSWORD_RESET_EXPIRED = "This password reset link has expired. Please request a new one."
        PASSWORD_RESET_INVALID = "Invalid or already used password reset link."
        PASSWORD_CHANGED = "Your password has been changed successfully."
        EMAIL_VERIFIED = "Your email address has been verified successfully."
        VERIFICATION_SENT = "A verification email has been sent to your address."
        SESSION_EXPIRED = "Your session has expired. Please log in again."
        CSRF_ERROR = "Your session has expired or the request was invalid. Please try again."
        UNAUTHORIZED = "You do not have permission to perform this action."
        TWO_FACTOR_REQUIRED = "Please complete two-factor authentication."

    class Employee:
        """Employee management messages."""
        CREATED = "Employee profile created successfully."
        UPDATED = "Employee profile updated successfully."
        DELETED = "Employee record has been removed."
        NOT_FOUND = "Employee not found."
        PHOTO_UPDATED = "Profile photo updated successfully."
        PHOTO_INVALID = "Invalid file type. Please upload a PNG, JPG, or WEBP image."
        PHOTO_TOO_LARGE = "File size exceeds the maximum allowed limit of 5 MB."
        DOCUMENT_UPLOADED = "Document uploaded successfully."
        DOCUMENT_DELETED = "Document removed successfully."

    class Leave:
        """Leave management messages."""
        APPLIED = "Leave request submitted successfully."
        APPROVED = "Leave request has been approved."
        REJECTED = "Leave request has been rejected."
        CANCELLED = "Leave request has been cancelled."
        WITHDRAWN = "Leave request has been withdrawn."
        INSUFFICIENT_BALANCE = "Insufficient leave balance for the requested duration."
        OVERLAPPING = "You already have an approved leave request for this period."
        NOT_FOUND = "Leave request not found."
        CANNOT_MODIFY = "This leave request cannot be modified in its current state."

    class Attendance:
        """Attendance messages."""
        CHECKED_IN = "Check-in recorded successfully."
        CHECKED_OUT = "Check-out recorded successfully."
        ALREADY_CHECKED_IN = "You have already checked in today."
        NOT_CHECKED_IN = "No active check-in found for today."
        LOCATION_REQUIRED = "Location data is required for attendance marking."
        RECORD_UPDATED = "Attendance record updated successfully."

    class Payroll:
        """Payroll messages."""
        GENERATED = "Payroll generated successfully."
        APPROVED = "Payroll approved and queued for payment."
        PAID = "Payroll marked as paid successfully."
        CANCELLED = "Payroll run has been cancelled."
        ALREADY_PROCESSED = "Payroll for this period has already been processed."
        NOT_FOUND = "Payroll record not found."

    class General:
        """Generic CRUD and system messages."""
        CREATED = "Record created successfully."
        UPDATED = "Record updated successfully."
        DELETED = "Record deleted successfully."
        NOT_FOUND = "The requested record was not found."
        SAVE_FAILED = "Failed to save changes. Please try again."
        DELETE_FAILED = "Failed to delete record. Please try again."
        FORM_ERRORS = "Please correct the errors highlighted below."
        OPERATION_SUCCESS = "Operation completed successfully."
        OPERATION_FAILED = "Operation failed. Please try again or contact support."
        EXPORT_SUCCESS = "Report exported successfully."
        EXPORT_FAILED = "Failed to generate export. Please try again."
        UPLOAD_SUCCESS = "File uploaded successfully."
        UPLOAD_FAILED = "File upload failed. Please check the file and try again."
        IMPORT_SUCCESS = "Data imported successfully."
        IMPORT_FAILED = "Import failed. Please check the file format and try again."
        EMAIL_SENT = "Email notification sent successfully."
        EMAIL_FAILED = "Failed to send email notification."
        RATE_LIMITED = "Too many requests. Please wait before trying again."
        SERVER_ERROR = "An internal error occurred. Our team has been notified."
        MAINTENANCE = "The system is currently under maintenance. Please try again later."
