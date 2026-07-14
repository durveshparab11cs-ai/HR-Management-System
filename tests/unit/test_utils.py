"""
tests/unit/test_utils.py
==========================
Unit tests for utility functions (pure functions — no DB or Flask context needed).
"""

import pytest
from datetime import date, timedelta


class TestDateUtils:
    def test_working_days_mon_to_fri(self):
        from app.utils.date_utils import working_days_between
        monday = date(2024, 1, 1)   # Monday
        friday = date(2024, 1, 5)   # Friday
        assert working_days_between(monday, friday) == 5

    def test_working_days_excludes_weekend(self):
        from app.utils.date_utils import working_days_between
        friday   = date(2024, 1, 5)
        monday   = date(2024, 1, 8)
        assert working_days_between(friday, monday) == 2

    def test_calendar_days_between_inclusive(self):
        from app.utils.date_utils import calendar_days_between
        assert calendar_days_between(date(2024, 1, 1), date(2024, 1, 7)) == 7

    def test_age_from_birthdate(self):
        from app.utils.date_utils import age_from_birthdate, today_utc
        today = today_utc()
        dob   = date(today.year - 30, today.month, today.day)
        assert age_from_birthdate(dob) == 30

    def test_start_of_month(self):
        from app.utils.date_utils import start_of_month
        assert start_of_month(date(2024, 6, 15)) == date(2024, 6, 1)

    def test_end_of_month(self):
        from app.utils.date_utils import end_of_month
        assert end_of_month(date(2024, 2, 10)) == date(2024, 2, 29)  # leap year


class TestPasswordUtils:
    def test_generate_token_is_string(self):
        from app.utils.password_utils import generate_secure_token
        token = generate_secure_token()
        assert isinstance(token, str)
        assert len(token) > 20

    def test_tokens_are_unique(self):
        from app.utils.password_utils import generate_secure_token
        assert generate_secure_token() != generate_secure_token()

    def test_hash_and_verify_token(self):
        from app.utils.password_utils import generate_secure_token, hash_token, verify_token
        token = generate_secure_token()
        hashed = hash_token(token)
        assert verify_token(token, hashed) is True
        assert verify_token("wrong", hashed) is False

    def test_strong_password_passes(self):
        from app.utils.password_utils import validate_password_strength
        valid, errors = validate_password_strength("Secure@123!")
        assert valid is True
        assert errors == []

    def test_weak_password_fails(self):
        from app.utils.password_utils import validate_password_strength
        valid, errors = validate_password_strength("abc")
        assert valid is False
        assert len(errors) > 0

    def test_mask_email(self):
        from app.utils.password_utils import mask_email
        assert mask_email("john.doe@example.com") == "jo******@example.com"


class TestValidationUtils:
    def test_valid_email(self):
        from app.utils.validation_utils import is_valid_email
        assert is_valid_email("user@company.com") is True

    def test_invalid_email(self):
        from app.utils.validation_utils import is_valid_email
        assert is_valid_email("not-an-email") is False
        assert is_valid_email("") is False

    def test_valid_employee_code(self):
        from app.utils.validation_utils import is_valid_employee_code
        assert is_valid_employee_code("EMP-001") is True

    def test_invalid_employee_code_too_short(self):
        from app.utils.validation_utils import is_valid_employee_code
        assert is_valid_employee_code("AB") is False

    def test_normalize_email(self):
        from app.utils.validation_utils import normalize_email
        assert normalize_email("  John.Doe@EXAMPLE.COM  ") == "john.doe@example.com"


class TestStringUtils:
    def test_slugify(self):
        from app.utils.string_utils import slugify
        assert slugify("Hello World!") == "hello-world"

    def test_truncate(self):
        from app.utils.string_utils import truncate
        assert truncate("Hello World", 8) == "Hello..."

    def test_truncate_no_change_when_short(self):
        from app.utils.string_utils import truncate
        assert truncate("Hi", 10) == "Hi"

    def test_initials(self):
        from app.utils.string_utils import initials
        assert initials("John Michael Doe") == "JD"

    def test_pluralize(self):
        from app.utils.string_utils import pluralize
        assert pluralize(1, "day") == "1 day"
        assert pluralize(5, "day") == "5 days"

    def test_format_currency(self):
        from app.utils.string_utils import format_currency
        result = format_currency(1000.5, "₹")
        assert "₹" in result
        assert "1,000.50" in result


class TestGPSUtils:
    def test_distance_same_point_is_zero(self):
        from app.utils.gps_utils import haversine_distance
        assert haversine_distance(51.5, -0.12, 51.5, -0.12) == 0.0

    def test_within_geofence_true(self):
        from app.utils.gps_utils import is_within_geofence
        # Points ~10m apart — well within 200m
        assert is_within_geofence(51.507351, -0.127758, 51.507351, -0.127758, 200) is True

    def test_outside_geofence(self):
        from app.utils.gps_utils import is_within_geofence
        # London to Paris — ~340km
        assert is_within_geofence(51.5, -0.12, 48.85, 2.35, 200) is False
