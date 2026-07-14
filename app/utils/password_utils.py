"""
app/utils/password_utils.py
============================
Password policy enforcement and secure token generation.

All cryptographic operations use Python's secrets module or
werkzeug's security helpers — never random or hashlib/md5.
"""

import re
import secrets
import string
from typing import Optional

from app.constants.limits import Limits


# Characters used for generated passwords
_PASSWORD_ALPHABET = string.ascii_letters + string.digits + "!@#$%^&*"


def generate_secure_token(length: int = 64) -> str:
    """
    Generate a cryptographically secure URL-safe random token.

    Suitable for password reset links, email verification tokens,
    and API keys. Uses secrets.token_urlsafe which produces tokens
    safe for use in URLs without encoding.

    Args:
        length: Approximate byte length (output will be longer due to base64).

    Returns:
        URL-safe random token string.
    """
    return secrets.token_urlsafe(length)


def generate_password(length: int = 16) -> str:
    """
    Generate a random password meeting the application's password policy.

    Guarantees at least one uppercase, one lowercase, one digit,
    and one special character.

    Args:
        length: Desired password length (minimum 12).

    Returns:
        A random password string.
    """
    length = max(length, 12)

    # Ensure policy requirements are always met
    password_chars = [
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.digits),
        secrets.choice("!@#$%^&*"),
    ]

    # Fill remaining characters
    password_chars.extend(
        secrets.choice(_PASSWORD_ALPHABET) for _ in range(length - 4)
    )

    # Shuffle to avoid predictable positions
    secrets.SystemRandom().shuffle(password_chars)
    return "".join(password_chars)


def validate_password_strength(password: str) -> tuple[bool, list[str]]:
    """
    Validate a password against the application's password policy.

    Policy (from Limits.Password):
        - Minimum length: 8 characters
        - Maximum length: 128 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - At least one special character

    Args:
        password: The plaintext password to validate.

    Returns:
        Tuple of (is_valid: bool, errors: list[str]).
        errors is empty when is_valid is True.
    """
    errors = []

    if len(password) < Limits.Password.MIN_LENGTH:
        errors.append(
            f"Password must be at least {Limits.Password.MIN_LENGTH} characters long."
        )
    if len(password) > Limits.Password.MAX_LENGTH:
        errors.append(
            f"Password must not exceed {Limits.Password.MAX_LENGTH} characters."
        )
    if not re.search(r"[A-Z]", password):
        errors.append("Password must contain at least one uppercase letter.")
    if not re.search(r"[a-z]", password):
        errors.append("Password must contain at least one lowercase letter.")
    if not re.search(r"\d", password):
        errors.append("Password must contain at least one digit.")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        errors.append("Password must contain at least one special character.")

    return len(errors) == 0, errors


def hash_token(token: str) -> str:
    """
    Hash a token for secure database storage using SHA-256.

    Store the hash; compare by hashing the input and comparing hashes.
    Never store raw tokens in the database.

    Args:
        token: The plaintext token to hash.

    Returns:
        Hex-encoded SHA-256 hash of the token.
    """
    import hashlib  # noqa: PLC0415
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def verify_token(plaintext_token: str, stored_hash: str) -> bool:
    """
    Securely compare a plaintext token against its stored hash.

    Uses hmac.compare_digest to prevent timing attacks.

    Args:
        plaintext_token: The token provided by the user.
        stored_hash: The SHA-256 hash stored in the database.

    Returns:
        True if the token matches the hash.
    """
    import hashlib  # noqa: PLC0415
    import hmac  # noqa: PLC0415
    computed = hashlib.sha256(plaintext_token.encode("utf-8")).hexdigest()
    return hmac.compare_digest(computed, stored_hash)


def mask_email(email: str) -> str:
    """
    Partially obscure an email address for display in UI messages.

    Example: 'john.doe@example.com' → 'jo**@example.com'

    Args:
        email: Full email address.

    Returns:
        Masked email string.
    """
    try:
        local, domain = email.split("@", 1)
        visible = local[:2] if len(local) > 2 else local[0]
        masked = visible + "*" * (len(local) - len(visible))
        return f"{masked}@{domain}"
    except ValueError:
        return "***@***.***"
