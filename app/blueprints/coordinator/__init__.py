"""
Coordinator attendance kiosk blueprint.
Provides employee search and attendance check-in/out workflow.
"""

from flask import Blueprint

coordinator_bp = Blueprint(
    "coordinator",
    __name__,
    template_folder="templates",
    static_folder=None,
    url_prefix="/coordinator"
)

from app.blueprints.coordinator import routes  # noqa: F401, E402
