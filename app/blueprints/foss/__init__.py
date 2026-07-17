"""FOSS — Shift & Office Location Management blueprint."""
from flask import Blueprint

foss_bp = Blueprint(
    "foss",
    __name__,
    url_prefix="/foss",
    template_folder="templates",
)

from . import routes  # noqa: E402, F401
