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

# Import routes to register them
from . import routes  # noqa: F401
