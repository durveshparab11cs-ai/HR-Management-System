"""
app/extensions/database.py
===========================
SQLAlchemy extension instance.

Initialized here without an app so the application factory can call
db.init_app(app) at startup, following the Flask application factory pattern.

The db object is the single source of truth for all ORM operations.
All models must import db from this module (via app.extensions).
"""

from flask_sqlalchemy import SQLAlchemy

# Single SQLAlchemy instance for the entire application.
# Models are defined by subclassing db.Model.
db: SQLAlchemy = SQLAlchemy()
