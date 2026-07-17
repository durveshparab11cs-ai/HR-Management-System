"""
blueprints/authentication/forms.py
=====================================
Flask-WTF forms for authentication.

Login and Registration now use Employee Code instead of Email.
"""

import re
from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, SelectField, StringField
from wtforms.validators import DataRequired, EqualTo, Length, ValidationError
from app.constants.enums import DEPARTMENT_CHOICES


def validate_password_strength(form, field):
    """
    Enforce password policy:
        - Minimum 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - At least one special character
    """
    pwd = field.data or ""
    errors = []
    if len(pwd) < 8:
        errors.append("at least 8 characters")
    if not re.search(r"[A-Z]", pwd):
        errors.append("one uppercase letter")
    if not re.search(r"[a-z]", pwd):
        errors.append("one lowercase letter")
    if not re.search(r"\d", pwd):
        errors.append("one digit")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-\+\=\[\]\\\/]", pwd):
        errors.append("one special character")
    if errors:
        raise ValidationError(f"Password must contain: {', '.join(errors)}.")


class LoginForm(FlaskForm):
    """Login with Employee Code + Password + Department."""

    employee_code = StringField(
        "Employee Code",
        validators=[
            DataRequired(message="Employee Code is required."),
            Length(min=2, max=30, message="Enter a valid Employee Code."),
        ],
        render_kw={
            "placeholder": "e.g. E-2603028",
            "autofocus": True,
            "autocomplete": "username",
            "class": "",
        },
    )
    department = SelectField(
        "Department",
        choices=[("", "— Select Your Department —")] + DEPARTMENT_CHOICES,
        validators=[DataRequired(message="Please select your department.")],
        default="",
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired(message="Password is required.")],
        render_kw={"placeholder": "Enter your password", "autocomplete": "current-password"},
    )
    remember_me = BooleanField("Keep me signed in for 30 days")


class RegisterForm(FlaskForm):
    """
    First-time self-registration using Employee Code.

    Flow:
        1. Employee enters their code
        2. JS fetches their name from /auth/lookup-employee
        3. They set a password
        4. Submit creates their User account
    """

    employee_code = StringField(
        "Employee Code",
        validators=[
            DataRequired(message="Employee Code is required."),
            Length(min=2, max=30, message="Enter a valid Employee Code."),
        ],
        render_kw={
            "placeholder": "e.g. E-2603028",
            "autofocus": True,
            "autocomplete": "off",
        },
    )
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(),
            Length(min=8, max=128),
            validate_password_strength,
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
    """Request password reset via Employee Code."""

    employee_code = StringField(
        "Employee Code",
        validators=[
            DataRequired(message="Employee Code is required."),
            Length(min=2, max=30),
        ],
        render_kw={"placeholder": "e.g. E-2603028", "autofocus": True},
    )


class ResetPasswordForm(FlaskForm):
    """Set a new password (used after admin-verified reset)."""

    password = PasswordField(
        "New Password",
        validators=[
            DataRequired(),
            Length(min=8, max=128),
            validate_password_strength,
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
