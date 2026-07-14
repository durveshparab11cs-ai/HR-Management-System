"""
attendance/forms.py
=====================
Flask-WTF forms for the attendance module.
"""

from flask_wtf import FlaskForm
from wtforms import BooleanField, FloatField, IntegerField, StringField, TextAreaField, TimeField
from wtforms.validators import DataRequired, NumberRange, Optional as Opt


class OfficeSettingsForm(FlaskForm):
    name    = StringField("Office Name", validators=[DataRequired()])
    address = TextAreaField("Address", validators=[Opt()])

    latitude      = FloatField("Latitude",  validators=[DataRequired(), NumberRange(min=-90,   max=90)])
    longitude     = FloatField("Longitude", validators=[DataRequired(), NumberRange(min=-180, max=180)])
    radius_metres = IntegerField("Geofence Radius (m)", validators=[DataRequired(), NumberRange(min=10, max=5000)])

    office_start_time = TimeField("Office Start Time", validators=[DataRequired()])
    office_end_time   = TimeField("Office End Time",   validators=[DataRequired()])

    grace_period_minutes       = IntegerField("Grace Period (min)", validators=[DataRequired(), NumberRange(min=0,  max=60)])
    half_day_threshold_minutes = IntegerField("Half-Day Threshold (min)", validators=[DataRequired(), NumberRange(min=60, max=480)])
    overtime_threshold_minutes = IntegerField("Overtime Threshold (min)", validators=[DataRequired(), NumberRange(min=0,  max=120)])

    allow_remote_checkin = BooleanField("Allow check-in outside office radius")
    selfie_required      = BooleanField("Require selfie photo on check-in")
