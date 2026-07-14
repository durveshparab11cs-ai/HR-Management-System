"""
app/core/base_repository.py
============================
Generic base repository implementing the Repository Pattern.

The repository pattern decouples the service layer from SQLAlchemy
specifics. Services never call db.session directly — they call
repository methods. This makes the service layer independently
testable by swapping in mock repositories.

Provides standard CRUD operations for any model that extends BaseModel:
    - get_by_id        — fetch single record by PK
    - get_all          — fetch all active records with optional ordering
    - get_paginated    — paginated query with SQLAlchemy Pagination object
    - find_by          — filter by arbitrary kwargs
    - find_one_by      — return first match for kwargs
    - create           — create and persist a new record
    - update           — update fields on an existing record
    - delete           — soft-delete a record
    - hard_delete      — permanent deletion (admin use only)
    - count            — count active records
    - exists           — boolean existence check

Concrete repositories extend this class and add domain-specific query
methods (e.g., EmployeeRepository.get_by_department()).
"""

from typing import Any, Generic, Optional, TypeVar

from sqlalchemy import asc, desc

from app.extensions.database import db

# Generic type variable bound to BaseModel subclasses.
T = TypeVar("T")


class BaseRepository(Generic[T]):
    """
    Generic repository providing standard database access methods.

    Args:
        model: The SQLAlchemy model class this repository manages.

    Usage:
        class EmployeeRepository(BaseRepository[Employee]):
            def __init__(self):
                super().__init__(Employee)

            def get_by_department(self, dept_id: int) -> list[Employee]:
                return self.find_by(department_id=dept_id)
    """

    def __init__(self, model: type[T]) -> None:
        self.model = model

    # ------------------------------------------------------------------
    # Read Operations
    # ------------------------------------------------------------------

    def get_by_id(self, record_id: int) -> Optional[T]:
        """
        Fetch a single active record by its primary key.

        Args:
            record_id: The integer primary key.

        Returns:
            Model instance or None if not found / soft-deleted.
        """
        return (
            self.model.query
            .filter_by(id=record_id, is_deleted=False)
            .first()
        )

    def get_by_id_or_404(self, record_id: int) -> T:
        """
        Fetch a record by PK or raise a 404 HTTP error.

        Args:
            record_id: The integer primary key.

        Returns:
            Model instance.

        Raises:
            werkzeug.exceptions.NotFound: If the record doesn't exist.
        """
        from flask import abort  # noqa: PLC0415
        record = self.get_by_id(record_id)
        if record is None:
            abort(404)
        return record

    def get_all(
        self,
        order_by: str = "created_at",
        direction: str = "desc",
    ) -> list[T]:
        """
        Fetch all active (non-deleted) records.

        Args:
            order_by: Column name to sort by.
            direction: 'asc' or 'desc'.

        Returns:
            List of model instances.
        """
        column = getattr(self.model, order_by, None)
        if column is None:
            column = self.model.created_at

        order_fn = desc(column) if direction == "desc" else asc(column)
        return (
            self.model.query
            .filter_by(is_deleted=False)
            .order_by(order_fn)
            .all()
        )

    def get_paginated(
        self,
        page: int = 1,
        per_page: int = 25,
        order_by: str = "created_at",
        direction: str = "desc",
        error_out: bool = False,
    ):
        """
        Fetch a paginated slice of active records.

        Args:
            page: 1-based page number.
            per_page: Number of records per page.
            order_by: Column name to sort by.
            direction: 'asc' or 'desc'.
            error_out: If True, raise 404 when page is out of range.

        Returns:
            SQLAlchemy Pagination object with .items, .total, .pages,
            .has_next, .has_prev attributes.
        """
        column = getattr(self.model, order_by, None)
        if column is None:
            column = self.model.created_at

        order_fn = desc(column) if direction == "desc" else asc(column)
        return (
            self.model.query
            .filter_by(is_deleted=False)
            .order_by(order_fn)
            .paginate(page=page, per_page=per_page, error_out=error_out)
        )

    def find_by(self, **kwargs: Any) -> list[T]:
        """
        Filter active records by keyword arguments (AND conditions).

        Args:
            **kwargs: Column name/value pairs to filter by.

        Returns:
            List of matching model instances.
        """
        return (
            self.model.query
            .filter_by(is_deleted=False, **kwargs)
            .all()
        )

    def find_one_by(self, **kwargs: Any) -> Optional[T]:
        """
        Return the first active record matching the given filters.

        Args:
            **kwargs: Column name/value pairs to filter by.

        Returns:
            First matching model instance or None.
        """
        return (
            self.model.query
            .filter_by(is_deleted=False, **kwargs)
            .first()
        )

    def count(self, **kwargs: Any) -> int:
        """
        Count active records matching optional filters.

        Args:
            **kwargs: Optional filter conditions.

        Returns:
            Integer count of matching active records.
        """
        return (
            self.model.query
            .filter_by(is_deleted=False, **kwargs)
            .count()
        )

    def exists(self, **kwargs: Any) -> bool:
        """
        Check whether at least one active record matches the filters.

        Args:
            **kwargs: Filter conditions.

        Returns:
            True if a matching record exists, False otherwise.
        """
        return (
            self.model.query
            .filter_by(is_deleted=False, **kwargs)
            .first()
        ) is not None

    # ------------------------------------------------------------------
    # Write Operations
    # ------------------------------------------------------------------

    def create(self, commit: bool = True, **kwargs: Any) -> T:
        """
        Instantiate a new model, persist it, and return the instance.

        Args:
            commit: Whether to commit the transaction immediately.
            **kwargs: Column values for the new record.

        Returns:
            The newly created and persisted model instance.
        """
        instance = self.model(**kwargs)
        db.session.add(instance)
        if commit:
            db.session.commit()
        return instance

    def update(self, instance: T, commit: bool = True, **kwargs: Any) -> T:
        """
        Apply field updates to an existing model instance.

        Args:
            instance: The model instance to update.
            commit: Whether to commit immediately.
            **kwargs: Fields and new values to apply.

        Returns:
            The updated model instance.
        """
        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        db.session.add(instance)
        if commit:
            db.session.commit()
        return instance

    def delete(self, instance: T, deleted_by_id: int | None = None, commit: bool = True) -> T:
        """
        Soft-delete a model instance.

        Args:
            instance: The record to soft-delete.
            deleted_by_id: ID of the user performing the deletion.
            commit: Whether to commit immediately.

        Returns:
            The soft-deleted model instance.
        """
        return instance.soft_delete(deleted_by_id=deleted_by_id, commit=commit)

    def hard_delete(self, instance: T, commit: bool = True) -> None:
        """
        Permanently remove a record from the database.

        WARNING: This is irreversible. Reserve for admin data-purge
        operations and automated test teardown only.

        Args:
            instance: The record to permanently delete.
            commit: Whether to commit immediately.
        """
        db.session.delete(instance)
        if commit:
            db.session.commit()

    def bulk_create(self, records: list[dict], commit: bool = True) -> list[T]:
        """
        Create multiple records efficiently in a single transaction.

        Args:
            records: List of dicts, each containing kwargs for one record.
            commit: Whether to commit the batch transaction.

        Returns:
            List of created model instances.
        """
        instances = [self.model(**data) for data in records]
        db.session.add_all(instances)
        if commit:
            db.session.commit()
        return instances
