"""blueprints/company/forms.py"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import BooleanField, FloatField, IntegerField, SelectField, StringField, TextAreaField, TimeField
from wtforms.validators import DataRequired, Length, Optional as Opt, URL


class CompanyProfileForm(FlaskForm):
    name        = StringField("Company Name", validators=[DataRequired(), Length(max=200)])
    industry    = StringField("Industry", validators=[Opt(), Length(max=100)])
    website     = StringField("Website", validators=[Opt(), Length(max=255)])
    phone       = StringField("Phone", validators=[Opt(), Length(max=30)])
    email       = StringField("Email", validators=[Opt(), Length(max=254)])
    address     = TextAreaField("Address", validators=[Opt(), Length(max=500)])
    city        = StringField("City", validators=[Opt(), Length(max=100)])
    state       = StringField("State", validators=[Opt(), Length(max=100)])
    country     = StringField("Country", validators=[Opt(), Length(max=100)])
    pin_code    = StringField("PIN / ZIP", validators=[Opt(), Length(max=20)])
    gstin       = StringField("GSTIN", validators=[Opt(), Length(max=30)])
    pan         = StringField("PAN", validators=[Opt(), Length(max=20)])
    description = TextAreaField("About", validators=[Opt(), Length(max=2000)])
    timezone    = SelectField("Timezone", choices=[("Asia/Kolkata","IST (India)"),("UTC","UTC"),("US/Eastern","EST (US)")])
    currency    = StringField("Currency Code", validators=[Opt(), Length(max=10)])
    currency_symbol = StringField("Currency Symbol", validators=[Opt(), Length(max=5)])
    logo        = FileField("Logo", validators=[FileAllowed(["png","jpg","jpeg","svg","webp"])])


class DepartmentForm(FlaskForm):
    name        = StringField("Department Name", validators=[DataRequired(), Length(max=100)])
    code        = StringField("Code", validators=[DataRequired(), Length(max=20)])
    description = TextAreaField("Description", validators=[Opt(), Length(max=500)])
    color       = StringField("Color", default="#1a3c6e", validators=[Opt()])


class PositionForm(FlaskForm):
    title         = StringField("Position Title", validators=[DataRequired(), Length(max=100)])
    code          = StringField("Code", validators=[DataRequired(), Length(max=20)])
    department_id = SelectField("Department", coerce=int, validators=[Opt()])
    grade         = StringField("Grade", validators=[Opt(), Length(max=20)])
    description   = TextAreaField("Description", validators=[Opt(), Length(max=500)])


class ShiftForm(FlaskForm):
    name          = StringField("Shift Name", validators=[DataRequired(), Length(max=100)])
    code          = StringField("Code", validators=[DataRequired(), Length(max=20)])
    start_time    = TimeField("Start Time", validators=[DataRequired()])
    end_time      = TimeField("End Time",   validators=[DataRequired()])
    grace_minutes = IntegerField("Grace Period (min)", default=10)
    break_minutes = IntegerField("Break (min)", default=60)
    working_days  = StringField("Working Days", default="Mon-Fri", validators=[Opt()])
    is_night_shift= BooleanField("Night Shift")
    description   = TextAreaField("Notes", validators=[Opt(), Length(max=500)])
