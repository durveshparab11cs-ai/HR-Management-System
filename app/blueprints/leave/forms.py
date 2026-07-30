"""
blueprints/leave/forms.py
============================
Flask-WTF forms for leave, half-day, and early-leave.
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import DateField, SelectField, StringField, TextAreaField, TimeField
from wtforms.validators import DataRequired, Length, Optional as Opt


# ══════════════════════════════════════════════════════════════════════
# REPORTING MANAGERS LIST (Predefined)
# ══════════════════════════════════════════════════════════════════════
REPORTING_MANAGERS = [
    ("Ekta Sunil More", "Ekta Sunil More"),
    ("Pallavi Mangesh Mali", "Pallavi Mangesh Mali"),
    ("Prasad Morje", "Prasad Morje"),
    ("Rutuja Suresh Pawar", "Rutuja Suresh Pawar"),
    ("Sampada Arvind Thakur", "Sampada Arvind Thakur"),
    ("Sanam Desai", "Sanam Desai"),
    ("Shubham Sanjay Pednekar", "Shubham Sanjay Pednekar"),
    ("Tejas Ashok Jadhav", "Tejas Ashok Jadhav"),
    ("Umesh Pradeep Devare", "Umesh Pradeep Devare"),
    ("Vijay Shankar Manjare", "Vijay Shankar Manjare"),
    ("Akshay Darsharth Ghadi", "Akshay Darsharth Ghadi"),
    ("Aditya Nivas Mayekar", "Aditya Nivas Mayekar"),
    ("Durvesh Parab", "Durvesh Parab"),
    ("Sakshi Jadhav", "Sakshi Jadhav"),
    ("Pratik Dinkar Mohite", "Pratik Dinkar Mohite"),
    ("Sakshi Anil Yeram", "Sakshi Anil Yeram"),
    ("Atharva Bhosale", "Atharva Bhosale"),
]


def get_manager_choices():
    """Return list of reporting manager choices with empty option."""
    return [("", "-- Select Reporting Manager --")] + REPORTING_MANAGERS


class ApplyLeaveForm(FlaskForm):
    leave_type_id = SelectField("Leave Type", coerce=int, validators=[DataRequired()])
    start_date = DateField("Start Date", validators=[DataRequired()])
    end_date = DateField("End Date", validators=[DataRequired()])
    reason = TextAreaField("Reason", validators=[DataRequired(), Length(min=5, max=1000)],
                           render_kw={"rows": 3, "placeholder": "Briefly describe the reason for your leave…"})
    reporting_manager = SelectField(
        "Reporting Manager",
        choices=[],  # Will be populated in the route
        validators=[DataRequired(message="Please select a Reporting Manager.")],
        render_kw={"class": "form-select searchable-select"}
    )
    attachment = FileField("Supporting Document (optional)",
                           validators=[FileAllowed(["pdf", "jpg", "jpeg", "png", "doc", "docx"], "PDF, image, or Word doc only.")])


class ReviewLeaveForm(FlaskForm):
    comment = TextAreaField("Comment (optional)", validators=[Opt(), Length(max=500)],
                            render_kw={"rows": 2, "placeholder": "Add a comment for the employee…"})


class ApplyHalfDayForm(FlaskForm):
    date = DateField("Date", validators=[DataRequired()])
    half_type = SelectField("Half", choices=[("morning", "Morning Half"), ("afternoon", "Afternoon Half")],
                            validators=[DataRequired()])
    reason = TextAreaField("Reason", validators=[DataRequired(), Length(min=5, max=500)],
                           render_kw={"rows": 2})
    reporting_manager = SelectField(
        "Reporting Manager",
        choices=[],  # Will be populated in the route
        validators=[DataRequired(message="Please select a Reporting Manager.")],
        render_kw={"class": "form-select searchable-select"}
    )


class ApplyEarlyLeaveForm(FlaskForm):
    date = DateField("Date", validators=[DataRequired()])
    requested_leave_time = TimeField("Planned Leave Time", validators=[DataRequired()])
    reason = TextAreaField("Reason", validators=[DataRequired(), Length(min=5, max=500)],
                           render_kw={"rows": 2})
    reporting_manager = SelectField(
        "Reporting Manager",
        choices=[],  # Will be populated in the route
        validators=[DataRequired(message="Please select a Reporting Manager.")],
        render_kw={"class": "form-select searchable-select"}
    )
