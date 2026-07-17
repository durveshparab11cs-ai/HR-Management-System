"""
app/blueprints/__init__.py
============================
Blueprint registry — imports all blueprint instances and exposes
a single register_blueprints(app) function for the application factory.

Adding a new blueprint:
    1. Create the blueprint package under app/blueprints/<name>/
    2. Import its blueprint instance here
    3. Add it to the _blueprints list below

Order matters for URL routing when multiple blueprints could match
the same path — more specific blueprints should appear first.
"""

from app.blueprints.authentication import authentication_bp
from app.blueprints.dashboard import dashboard_bp
from app.blueprints.company import company_bp
from app.blueprints.employees import employees_bp
from app.blueprints.attendance import attendance_bp
from app.blueprints.leave import leave_bp
from app.blueprints.payroll import payroll_bp
from app.blueprints.reports import reports_bp
from app.blueprints.notifications import notifications_bp
from app.blueprints.settings import settings_bp
from app.blueprints.admin import admin_bp
from app.blueprints.api import api_bp
from app.blueprints.foss import foss_bp

_blueprints = [
    (authentication_bp, None),
    (dashboard_bp, None),
    (company_bp, None),
    (employees_bp, None),
    (attendance_bp, None),
    (leave_bp, None),
    (payroll_bp, None),
    (reports_bp, None),
    (notifications_bp, None),
    (settings_bp, None),
    (admin_bp, None),
    (api_bp, None),
    (foss_bp, None),
]


def register_blueprints(app) -> None:
    """
    Register all application blueprints with the Flask app instance.

    Called from create_app() after extension initialization.

    Args:
        app: The Flask application instance.
    """
    for blueprint, url_prefix in _blueprints:
        if url_prefix:
            app.register_blueprint(blueprint, url_prefix=url_prefix)
        else:
            app.register_blueprint(blueprint)

    app.logger.info(
        "Registered %d blueprints: %s",
        len(_blueprints),
        ", ".join(bp.name for bp, _ in _blueprints),
    )
