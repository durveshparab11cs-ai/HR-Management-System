"""
blueprints/authentication/forms.py
=====================================
Flask-WTF forms for authentication — login and first-time registration.
"""

from flask_wtf import FlaskForm
from wtforms import BooleanField, EmailField, PasswordField, SelectField, StringField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional as Opt


ROLE_CHOICES = [
    ("employee",   "Employee"),
    ("manager",    "Manager"),
    ("hr_staff",   "HR Staff"),
    ("hr_manager", "HR Manager"),
    ("admin",      "Admin"),
]


class LoginForm(FlaskForm):
    email = EmailField(
        "Email Address",
        validators=[DataRequired(message="Email is required."), Email(message="Enter a valid email.")],
        render_kw={"placeholder": "you@company.com", "autofocus": True},
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired(message="Password is required.")],
        render_kw={"placeholder": "Enter your password"},
    )
    remember_me = BooleanField("Keep me signed in for 30 days")


class RegisterForm(FlaskForm):
    first_name = StringField(
        "First Name",
        validators=[DataRequired(), Length(min=2, max=50)],
        render_kw={"placeholder": "First name"},
    )
    last_name = StringField(
        "Last Name",
        validators=[DataRequired(), Length(min=2, max=50)],
        render_kw={"placeholder": "Last name"},
    )
    email = EmailField(
        "Work Email",
        validators=[DataRequired(), Email()],
        render_kw={"placeholder": "work@email.com"},
    )
    role = SelectField("Role", choices=ROLE_CHOICES, validators=[DataRequired()])
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(),
            Length(min=8, max=128, message="Password must be at least 8 characters."),
        ],
        render_kw={"placeholder": "Min 8 characters"},
    )
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(),
            EqualTo("password", message="Passwords do not match."),
        ],
        render_kw={"placeholder": "Repeat password"},
    )


class ForgotPasswordForm(FlaskForm):
    email = EmailField(
        "Email Address",
        validators=[DataRequired(), Email()],
        render_kw={"placeholder": "your.work@email.com", "autofocus": True},
    )


class ResetPasswordForm(FlaskForm):
    password = PasswordField(
        "New Password",
        validators=[
            DataRequired(),
            Length(min=8, max=128, message="Password must be at least 8 characters."),
        ],
        render_kw={"placeholder": "New password"},
    )
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(),
            EqualTo("password", message="Passwords do not match."),
        ],
        render_kw={"placeholder": "Repeat new password"},
    )
