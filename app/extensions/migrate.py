"""
app/extensions/migrate.py
==========================
Flask-Migrate extension instance.

Manages Alembic database migrations for SQLAlchemy models.
Provides `flask db init`, `flask db migrate`, `flask db upgrade` CLI commands.

Initialized without an app; bound in the application factory via
migrate.init_app(app, db).
"""

from flask_migrate import Migrate

# Single Migrate instance.
# Bound to both the app and the db instance in the factory.
migrate: Migrate = Migrate()
