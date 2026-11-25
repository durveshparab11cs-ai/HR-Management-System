"""
blueprints/authentication/forms.py
=====================================
Flask-WTF forms for authentication.

Login and Registration now use Employee Code instead of Email.
"""

import re
from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, SelectField, StringField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional as Opt, ValidationError
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
        choices=[("", "— Select Your Department (Optional) —")] + DEPARTMENT_CHOICES,
        validators=[Opt()],   # Optional — validated in service so Super Admin can bypass
        validate_choice=False,
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
        2. JS fetches their name, department & designation from /auth/lookup-employee
        3. They select/confirm Department and enter actual Designation
        4. They set a password
        5. Submit creates their User account & Employee profile
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
    department = SelectField(
        "Department",
        choices=[("", "— Select Your Department —")] + DEPARTMENT_CHOICES,
        validators=[DataRequired(message="Please select your department.")],
        validate_choice=False,
    )
    designation = StringField(
        "Actual Designation",
        validators=[
            DataRequired(message="Please enter your actual designation."),
            Length(min=2, max=100, message="Designation must be between 2 and 100 characters."),
        ],
        render_kw={"placeholder": "e.g. Senior Operations Executive", "autocomplete": "organization-title"},
    )
    email = StringField(
        "Official Email",
        validators=[
            DataRequired(message="Official Email is strictly required for registration."),
            Email(message="Please enter a valid official email address."),
            Length(max=120, message="Email address is too long."),
        ],
        render_kw={"placeholder": "e.g. name@company.com", "autocomplete": "email"},
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
        validators=[Opt()],
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
