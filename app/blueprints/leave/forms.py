"""
blueprints/leave/forms.py
============================
Flask-WTF forms for leave, half-day, and early-leave.
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import DateField, SelectField, TextAreaField, TimeField
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


class ApplyEarlyLeaveForm(FlaskForm):
    date = DateField("Date", validators=[DataRequired()])
    requested_leave_time = TimeField("Planned Leave Time", validators=[DataRequired()])
    reason = TextAreaField("Reason", validators=[DataRequired(), Length(min=5, max=500)],
                           render_kw={"rows": 2})
