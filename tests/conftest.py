"""
tests/conftest.py
==================
Root pytest configuration and shared fixtures for the Smart HRMS test suite.

Fixtures provided:
    app              — Flask test application (TestingConfig, in-memory SQLite)
    client           — Flask test client (no auth)
    auth_client      — Test client pre-authenticated as a regular employee
    admin_client     — Test client pre-authenticated as a SUPER_ADMIN
    db_session       — SQLAlchemy session scoped to each test (auto-rollback)
    user_factory     — Factory function for creating User objects
    admin_user       — A persisted SUPER_ADMIN user
    employee_user    — A persisted EMPLOYEE user

Pytest plugins used:
    pytest-flask     — provides `app` fixture integration
    factory-boy      — model factories in tests/fixtures/factories.py
    freezegun        — time freezing for date-sensitive tests
"""

import pytest

from app import create_app
from app.extensions.database import db as _db
from app.constants.enums import UserRole, UserStatus


# ── Application fixture ────────────────────────────────────────────────

@pytest.fixture(scope="session")
def app():
    """
    Create a single Flask app instance shared across the test session.

    Uses TestingConfig which:
        - Sets SQLALCHEMY_DATABASE_URI to sqlite:///:memory:
        - Disables CSRF for test client simplicity
        - Disables rate limiting
        - Suppresses email sending
    """
    flask_app = create_app("testing")
    flask_app.config.update({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SERVER_NAME": "localhost",
    })

    with flask_app.app_context():
        _db.create_all()
        yield flask_app
        _db.drop_all()


# ── Database session fixture ───────────────────────────────────────────

@pytest.fixture(scope="function")
def db(app):
    """
    Provide a clean database state for each test function.

    Uses nested transactions (SAVEPOINT) so each test is rolled back
    automatically after completion — no data bleeds between tests.
    """
    with app.app_context():
        connection  = _db.engine.connect()
        transaction = connection.begin()

        # Bind session to the connection so we can roll back cleanly
        _db.session.configure(bind=connection)

        yield _db

        _db.session.remove()
        transaction.rollback()
        connection.close()


# ── HTTP test clients ──────────────────────────────────────────────────

@pytest.fixture(scope="function")
def client(app):
    """Unauthenticated Flask test client."""
    with app.test_client() as c:
        yield c


@pytest.fixture(scope="function")
def auth_client(app, db, employee_user):
    """Test client authenticated as a regular employee."""
    with app.test_client() as c:
        with app.app_context():
            with c.session_transaction() as sess:
                sess["_user_id"]   = str(employee_user.id)
                sess["_fresh"]     = True
        yield c


@pytest.fixture(scope="function")
def admin_client(app, db, admin_user):
    """Test client authenticated as a SUPER_ADMIN."""
    with app.test_client() as c:
        with app.app_context():
            with c.session_transaction() as sess:
                sess["_user_id"] = str(admin_user.id)
                sess["_fresh"]   = True
        yield c


# ── User fixtures ──────────────────────────────────────────────────────

@pytest.fixture(scope="function")
def user_factory(db, app):
    """
    Factory fixture for creating User instances.

    Usage:
        def test_something(user_factory):
            user = user_factory(email="test@example.com", role=UserRole.HR_MANAGER)
    """
    from app.models.user import User  # noqa: PLC0415

    def _make(
        email="test@example.com",
        password="Test@1234",
        first_name="Test",
        last_name="User",
        role=UserRole.EMPLOYEE,
        status=UserStatus.ACTIVE,
        email_verified=True,
    ):
        with app.app_context():
            user = User(
                email=email,
                username=email.split("@")[0],
                first_name=first_name,
                last_name=last_name,
                role=role.value if hasattr(role, "value") else role,
                status=status.value if hasattr(status, "value") else status,
                email_verified=email_verified,
            )
            user.set_password(password)
            _db.session.add(user)
            _db.session.commit()
            return user

    return _make


@pytest.fixture(scope="function")
def employee_user(user_factory):
    """A persisted EMPLOYEE user for tests that need an authenticated employee."""
    return user_factory(
        email="employee@test.com",
        role=UserRole.EMPLOYEE,
    )


@pytest.fixture(scope="function")
def admin_user(user_factory):
    """A persisted SUPER_ADMIN user for tests requiring admin access."""
    return user_factory(
        email="admin@test.com",
        role=UserRole.SUPER_ADMIN,
    )


@pytest.fixture(scope="function")
def hr_manager_user(user_factory):
    """A persisted HR_MANAGER user."""
    return user_factory(
        email="hr@test.com",
        role=UserRole.HR_MANAGER,
    )
