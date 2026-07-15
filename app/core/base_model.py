"""
app/core/base_model.py
=======================
Abstract base model that all SQLAlchemy models inherit from.

Provides:
    - Auto-incrementing integer primary key
    - created_at / updated_at audit timestamps (UTC)
    - created_by / updated_by user tracking (foreign key to users)
    - Soft-delete support via is_deleted + deleted_at
    - to_dict()  — serialization to plain dictionary
    - __repr__   — consistent string representation for debugging
    - save()     — convenience commit shortcut
    - delete()   — soft-delete with timestamp

Design decision — soft delete:
    Records are never physically removed in production.  Setting
    is_deleted=True and deleted_at preserves referential integrity,
    enables audit trails, and allows accidental deletion recovery.
    All query repositories MUST filter is_deleted=False by default.
"""

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions.database import db


class TimestampMixin:
    """
    Mixin that adds created_at and updated_at columns.

    Uses server_default and onupdate for database-level accuracy,
    independent of application server time zones.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        doc="UTC timestamp when the record was first created.",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        doc="UTC timestamp of the most recent update to this record.",
    )


class SoftDeleteMixin:
    """
    Mixin that adds soft-delete columns.

    Repositories should always append `.filter_by(is_deleted=False)`
    to avoid returning logically deleted records.
    """

    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        index=True,
        doc="True if this record has been logically deleted.",
    )

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        doc="UTC timestamp when the record was soft-deleted.",
    )

    deleted_by: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        default=None,
        doc="ID of the user who soft-deleted this record.",
    )


class BaseModel(db.Model, TimestampMixin, SoftDeleteMixin):
    """
    Abstract base model inherited by all domain models.

    Provides:
        - Integer primary key
        - Audit timestamps (created_at, updated_at)
        - Soft delete fields (is_deleted, deleted_at, deleted_by)
        - Audit user tracking (created_by, updated_by)
        - Utility methods (save, soft_delete, restore, to_dict)

    Usage:
        class Employee(BaseModel):
            __tablename__ = "employees"
            name: Mapped[str] = mapped_column(String(100))
    """

    __abstract__ = True  # SQLAlchemy will not create a table for this class.

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        doc="Auto-incrementing integer primary key.",
    )

    created_by: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        doc="ID of the user who created this record.",
    )

    updated_by: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        doc="ID of the user who last modified this record.",
    )

    # ------------------------------------------------------------------
    # Utility Methods
    # ------------------------------------------------------------------

    def save(self, commit: bool = True) -> "BaseModel":
        """
        Add this instance to the session and optionally commit.

        Args:
            commit: If True (default), flush and commit the transaction.
                    Pass False when batching multiple saves in a service.

        Returns:
            self, for method chaining.
        """
        db.session.add(self)
        if commit:
            db.session.commit()
        return self

    def soft_delete(self, deleted_by_id: int | None = None, commit: bool = True) -> "BaseModel":
        """
        Logically delete this record without removing it from the database.

        Args:
            deleted_by_id: ID of the user performing the deletion.
            commit: Whether to commit the transaction immediately.

        Returns:
            self, for method chaining.
        """
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        self.deleted_by = deleted_by_id
        return self.save(commit=commit)

    def restore(self, commit: bool = True) -> "BaseModel":
        """
        Reverse a soft delete, making the record active again.

        Args:
            commit: Whether to commit the transaction immediately.

        Returns:
            self, for method chaining.
        """
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        return self.save(commit=commit)

    def to_dict(self, exclude: list[str] | None = None) -> dict:
        """
        Serialize the model instance to a plain Python dictionary.

        Converts datetime objects to ISO 8601 strings for JSON safety.

        Args:
            exclude: List of column names to omit from the output.

        Returns:
            Dictionary representation of the model row.
        """
        exclude = exclude or []
        result = {}
        for column in self.__table__.columns:
            if column.name in exclude:
                continue
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value
        return result

    def __repr__(self) -> str:
        """Human-readable representation for logs and the REPL."""
        return f"<{self.__class__.__name__} id={self.id}>"
