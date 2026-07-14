"""
tests/fixtures/sample_data.py
================================
Static sample data dictionaries used across integration tests.
Provides a single source of truth for test payloads.
"""

# Valid user registration / creation payload
VALID_USER_DATA = {
    "email":      "newuser@testcompany.com",
    "username":   "newuser",
    "first_name": "New",
    "last_name":  "User",
    "password":   "Secure@1234!",
}

# Valid login payload
VALID_LOGIN_DATA = {
    "email":    "employee@test.com",
    "password": "Test@1234",
}

# Invalid login — wrong password
INVALID_LOGIN_DATA = {
    "email":    "employee@test.com",
    "password": "WrongPassword!1",
}

# Valid forgot-password payload
FORGOT_PASSWORD_DATA = {
    "email": "employee@test.com",
}
