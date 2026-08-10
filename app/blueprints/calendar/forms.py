"""
blueprints/calendar/forms.py
==============================
Forms for calendar blueprint.
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileRequired
from wtforms import FileField, SubmitField


class HolidayImportForm(FlaskForm):
    """Form for importing holidays from Excel file."""

    file = FileField(
        "Excel File (.xlsx)",
        validators=[
            FileRequired("Please select a file."),
            FileAllowed(["xlsx"], "Only .xlsx files are allowed."),
        ],
        render_kw={"class": "form-control"},
    )

    submit = SubmitField(
        "Import Holidays",
        render_kw={"class": "btn btn-primary"},
    )
