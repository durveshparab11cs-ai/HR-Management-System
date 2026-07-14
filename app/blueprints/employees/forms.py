"""
blueprints/employees/forms.py
================================
Flask-WTF forms for employee management.
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import (
    DateField, EmailField, SelectField, StringField, TextAreaField, PasswordField, BooleanField
)
from wtforms.validators import DataRequired, Email, Length, Optional as Opt


ROLE_CHOICES = [
    ("employee", "Employee"),
    ("manager", "Manager"),
    ("hr_staff", "HR Staff"),
    ("hr_manager", "HR Manager"),
    ("admin", "Admin"),
]

STATUS_CHOICES = [
    ("active", "Active"),
    ("inactive", "Inactive"),
    ("pending_verification", "Pending Verification"),
    ("suspended", "Suspended"),
]

GENDER_CHOICES = [
    ("", "Select gender"),
    ("male", "Male"),
    ("female", "Female"),
    ("non_binary", "Non-binary"),
    ("prefer_not_to_say", "Prefer not to say"),
]

EMPLOYMENT_CHOICES = [
    ("full_time", "Full Time"),
    ("part_time", "Part Time"),
    ("contract", "Contract"),
    ("intern", "Intern"),
    ("temporary", "Temporary"),
]


class CreateEmployeeForm(FlaskForm):
    # Account
    first_name = StringField("First Name", validators=[DataRequired(), Length(max=50)])
    last_name = StringField("Last Name", validators=[DataRequired(), Length(max=50)])
    email = EmailField("Work Email", validators=[DataRequired(), Email()])
    role = SelectField("Role", choices=ROLE_CHOICES, validators=[DataRequired()])

    # Employment
    department = StringField("Department", validators=[Opt(), Length(max=100)])
    designation = StringField("Designation", validators=[Opt(), Length(max=100)])
    branch = StringField("Branch / Office", validators=[Opt(), Length(max=100)])
    employment_type = SelectField("Employment Type", choices=EMPLOYMENT_CHOICES)
    shift_name = StringField("Shift", validators=[Opt(), Length(max=50)])
    date_joined = DateField("Date of Joining", validators=[Opt()])

    # Personal
    gender = SelectField("Gender", choices=GENDER_CHOICES, validators=[Opt()])
    date_of_birth = DateField("Date of Birth", validators=[Opt()])
    mobile = StringField("Mobile", validators=[Opt(), Length(max=20)])
    nationality = StringField("Nationality", validators=[Opt(), Length(max=50)])

    # Manager
    manager_id = SelectField("Reporting Manager", choices=[], coerce=int, validators=[Opt()])

    # Photo
    profile_photo = FileField("Profile Photo", validators=[
        FileAllowed(["jpg", "jpeg", "png", "webp"], "Images only (JPG, PNG, WEBP).")
    ])


class EditEmployeeForm(FlaskForm):
    first_name = StringField("First Name", validators=[DataRequired(), Length(max=50)])
    last_name = StringField("Last Name", validators=[DataRequired(), Length(max=50)])
    email = EmailField("Work Email", validators=[DataRequired(), Email()])
    role = SelectField("Role", choices=ROLE_CHOICES)
    status = SelectField("Account Status", choices=STATUS_CHOICES)

    department = StringField("Department", validators=[Opt(), Length(max=100)])
    designation = StringField("Designation", validators=[Opt(), Length(max=100)])
    branch = StringField("Branch / Office", validators=[Opt(), Length(max=100)])
    employment_type = SelectField("Employment Type", choices=EMPLOYMENT_CHOICES)
    shift_name = StringField("Shift", validators=[Opt(), Length(max=50)])
    date_joined = DateField("Date of Joining", validators=[Opt()])

    gender = SelectField("Gender", choices=GENDER_CHOICES, validators=[Opt()])
    date_of_birth = DateField("Date of Birth", validators=[Opt()])
    mobile = StringField("Mobile", validators=[Opt(), Length(max=20)])
    nationality = StringField("Nationality", validators=[Opt(), Length(max=50)])
    personal_email = EmailField("Personal Email", validators=[Opt(), Email()])
    address = TextAreaField("Address", validators=[Opt(), Length(max=500)])
    emergency_contact_name = StringField("Emergency Contact Name", validators=[Opt(), Length(max=100)])
    emergency_contact_phone = StringField("Emergency Contact Phone", validators=[Opt(), Length(max=20)])
    manager_id = SelectField("Reporting Manager", choices=[], coerce=int, validators=[Opt()])
    profile_photo = FileField("Profile Photo", validators=[
        FileAllowed(["jpg", "jpeg", "png", "webp"], "Images only.")
    ])


class ResetPasswordForm(FlaskForm):
    new_password = PasswordField("New Password", validators=[DataRequired(), Length(min=8, max=128)])
    send_email = BooleanField("Email new password to employee", default=True)
