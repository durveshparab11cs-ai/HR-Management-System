"""
blueprints/leave/forms.py
============================
Flask-WTF forms for leave, half-day, and early-leave.
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import DateField, SelectField, StringField, TextAreaField, TimeField
from wtforms.validators import DataRequired, Length, Optional as Opt


class ApplyLeaveForm(FlaskForm):
    leave_type_id = SelectField("Leave Type", coerce=int, validators=[DataRequired()])
    start_date = DateField("Start Date", validators=[DataRequired()])
    end_date = DateField("End Date", validators=[DataRequired()])
    reason = TextAreaField("Reason", validators=[DataRequired(), Length(min=5, max=1000)],
                           render_kw={"rows": 3, "placeholder": "Briefly describe the reason for your leave…"})
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
    reporting_manager_code = StringField(
        "Reporting Manager Employee Code",
        validators=[DataRequired(message="Reporting Manager Code is required.")],
        render_kw={"placeholder": "e.g. E-2603028", "autocomplete": "off",
                   "oninput": "this.value=this.value.toUpperCase();lookupManager(this.value,'hd')"},
    )


class ApplyEarlyLeaveForm(FlaskForm):
    date = DateField("Date", validators=[DataRequired()])
    requested_leave_time = TimeField("Planned Leave Time", validators=[DataRequired()])
    reason = TextAreaField("Reason", validators=[DataRequired(), Length(min=5, max=500)],
                           render_kw={"rows": 2})
    reporting_manager_code = StringField(
        "Reporting Manager Employee Code",
        validators=[DataRequired(message="Reporting Manager Code is required.")],
        render_kw={"placeholder": "e.g. E-2603028", "autocomplete": "off",
                   "oninput": "this.value=this.value.toUpperCase();lookupManager(this.value,'el')"},
    )
