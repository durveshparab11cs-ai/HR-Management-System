"""
tests/fixtures/factories.py
=============================
Factory Boy model factories for generating test data.

Factory Boy is a fixtures library that declaratively defines
object factories — cleaner and more maintainable than writing
explicit setup code in every test.

Usage:
    from tests.fixtures.factories import UserFactory

    def test_something(db):
        user = UserFactory()                          # uses defaults
        admin = UserFactory(role=UserRole.ADMIN.value)
        users = UserFactory.create_batch(5)           # 5 employees
"""

import factory
from factory.alchemy import SQLAlchemyModelFactory

from app.extensions.database import db
from app.models.user import User
from app.constants.enums import UserRole, UserStatus


class BaseFactory(SQLAlchemyModelFactory):
    """Base factory — all model factories inherit this."""

    class Meta:
        abstract = True
        sqlalchemy_session         = db.session
        sqlalchemy_session_persistence = "commit"


class UserFactory(BaseFactory):
    """Factory for generating User model instances."""

    class Meta:
        model = User

    # Sequences ensure uniqueness across batch creates
    email      = factory.Sequence(lambda n: f"user{n}@testcompany.com")
    username   = factory.Sequence(lambda n: f"user{n}")
    first_name = factory.Faker("first_name")
    last_name  = factory.Faker("last_name")
    role       = UserRole.EMPLOYEE.value
    status     = UserStatus.ACTIVE.value
    email_verified = True
    failed_login_attempts = 0

    @factory.post_generation
    def password(obj, create, extracted, **kwargs):  # noqa: N805
        """Hash and set the password after the object is created."""
        plain = extracted or "Test@1234!"
        obj.set_password(plain)
        if create:
            db.session.add(obj)
            db.session.commit()


class AdminUserFactory(UserFactory):
    """Factory for SUPER_ADMIN users."""
    email    = factory.Sequence(lambda n: f"admin{n}@testcompany.com")
    username = factory.Sequence(lambda n: f"admin{n}")
    role     = UserRole.SUPER_ADMIN.value


class HRManagerFactory(UserFactory):
    """Factory for HR_MANAGER users."""
    email    = factory.Sequence(lambda n: f"hr{n}@testcompany.com")
    username = factory.Sequence(lambda n: f"hr{n}")
    role     = UserRole.HR_MANAGER.value
