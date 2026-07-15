"""
config/settings.py
==================
Hierarchical configuration classes for the Smart HRMS application.

Hierarchy:
    BaseConfig  ←  DevelopmentConfig
                ←  TestingConfig
                ←  ProductionConfig

All settings are read from environment variables with sensible
defaults so the application can boot without a .env file in CI/CD.

NEVER hard-code secrets here — always use os.environ.get().
"""

import os
from datetime import timedelta


class BaseConfig:
    """
    Base configuration shared by all environments.

    Contains default values that are safe for all environments.
    Subclasses override or extend these as needed.
    """

    # --------------------------------------------------------------------------
    # Flask Core
    # --------------------------------------------------------------------------
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")
    APP_NAME: str = os.environ.get("APP_NAME", "Smart HRMS")
    APP_VERSION: str = os.environ.get("APP_VERSION", "1.0.0")

    # --------------------------------------------------------------------------
    # SQLAlchemy
    # --------------------------------------------------------------------------
    SQLALCHEMY_DATABASE_URI: str = os.environ.get(
        "DATABASE_URL", "sqlite:///smart_hrms_dev.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_RECORD_QUERIES: bool = False
    SQLALCHEMY_ENGINE_OPTIONS: dict = {
        "pool_pre_ping": True,  # Detect stale connections
        "pool_recycle": int(os.environ.get("DB_POOL_RECYCLE", 3600)),
    }

    # --------------------------------------------------------------------------
    # Security
    # --------------------------------------------------------------------------
    WTF_CSRF_ENABLED: bool = True
    WTF_CSRF_TIME_LIMIT: int = int(os.environ.get("WTF_CSRF_TIME_LIMIT", 3600))
    SESSION_COOKIE_SECURE: bool = os.environ.get("SESSION_COOKIE_SECURE", "False") == "True"
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = os.environ.get("SESSION_COOKIE_SAMESITE", "Lax")
    REMEMBER_COOKIE_DURATION: timedelta = timedelta(
        seconds=int(os.environ.get("REMEMBER_COOKIE_DURATION", 2592000))
    )
    REMEMBER_COOKIE_SECURE: bool = os.environ.get("REMEMBER_COOKIE_SECURE", "False") == "True"
    REMEMBER_COOKIE_HTTPONLY: bool = True
    BCRYPT_LOG_ROUNDS: int = int(os.environ.get("BCRYPT_LOG_ROUNDS", 12))

    # --------------------------------------------------------------------------
    # Flask-Login
    # --------------------------------------------------------------------------
    LOGIN_VIEW: str = "authentication.login"
    LOGIN_MESSAGE: str = "Please log in to access this page."
    LOGIN_MESSAGE_CATEGORY: str = "warning"

    # --------------------------------------------------------------------------
    # Flask-Mail
    # --------------------------------------------------------------------------
    MAIL_SERVER: str = os.environ.get("MAIL_SERVER", "localhost")
    MAIL_PORT: int = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS: bool = os.environ.get("MAIL_USE_TLS", "True") == "True"
    MAIL_USE_SSL: bool = os.environ.get("MAIL_USE_SSL", "False") == "True"
    MAIL_USERNAME: str | None = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD: str | None = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER: str = os.environ.get(
        "MAIL_DEFAULT_SENDER", "Smart HRMS <noreply@smarthrms.com>"
    )
    MAIL_MAX_EMAILS: int = int(os.environ.get("MAIL_MAX_EMAILS", 50))
    MAIL_ASCII_ATTACHMENTS: bool = False

    # --------------------------------------------------------------------------
    # Flask-Limiter
    # --------------------------------------------------------------------------
    RATELIMIT_DEFAULT: str = os.environ.get("RATELIMIT_DEFAULT", "200 per day;50 per hour")
    RATELIMIT_STORAGE_URL: str = os.environ.get("RATELIMIT_STORAGE_URL", "memory://")
    RATELIMIT_STRATEGY: str = os.environ.get("RATELIMIT_STRATEGY", "fixed-window")
    RATELIMIT_HEADERS_ENABLED: bool = True

    # --------------------------------------------------------------------------
    # Flask-Caching
    # --------------------------------------------------------------------------
    CACHE_TYPE: str = os.environ.get("CACHE_TYPE", "SimpleCache")
    CACHE_DEFAULT_TIMEOUT: int = int(os.environ.get("CACHE_DEFAULT_TIMEOUT", 300))
    CACHE_KEY_PREFIX: str = "hrms_"

    # --------------------------------------------------------------------------
    # Flask-Session
    # --------------------------------------------------------------------------
    SESSION_TYPE: str = os.environ.get("SESSION_TYPE", "filesystem")
    SESSION_FILE_DIR: str = os.environ.get("SESSION_FILE_DIR", "./instance/sessions")
    SESSION_PERMANENT: bool = False
    PERMANENT_SESSION_LIFETIME: timedelta = timedelta(
        seconds=int(os.environ.get("PERMANENT_SESSION_LIFETIME", 86400))
    )

    # --------------------------------------------------------------------------
    # File Uploads
    # --------------------------------------------------------------------------
    UPLOAD_FOLDER: str = os.environ.get("UPLOAD_FOLDER", "./instance/uploads")
    MAX_CONTENT_LENGTH: int = int(os.environ.get("MAX_CONTENT_LENGTH", 16 * 1024 * 1024))  # 16 MB
    ALLOWED_IMAGE_EXTENSIONS: set = {"png", "jpg", "jpeg", "gif", "webp"}
    ALLOWED_DOCUMENT_EXTENSIONS: set = {"pdf", "doc", "docx", "xls", "xlsx", "csv"}

    # --------------------------------------------------------------------------
    # Logging
    # --------------------------------------------------------------------------
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")
    LOG_DIR: str = os.environ.get("LOG_DIR", "./logs")
    LOG_MAX_BYTES: int = int(os.environ.get("LOG_MAX_BYTES", 10 * 1024 * 1024))  # 10 MB
    LOG_BACKUP_COUNT: int = int(os.environ.get("LOG_BACKUP_COUNT", 10))

    # --------------------------------------------------------------------------
    # Application Domain Settings
    # --------------------------------------------------------------------------
    APP_TIMEZONE: str = os.environ.get("APP_TIMEZONE", "UTC")
    ITEMS_PER_PAGE: int = int(os.environ.get("ITEMS_PER_PAGE", 25))
    ADMIN_EMAIL: str = os.environ.get("ADMIN_EMAIL", "admin@smarthrms.com")

    # --------------------------------------------------------------------------
    # APScheduler
    # --------------------------------------------------------------------------
    SCHEDULER_API_ENABLED: bool = os.environ.get("SCHEDULER_API_ENABLED", "False") == "True"
    SCHEDULER_TIMEZONE: str = os.environ.get("SCHEDULER_TIMEZONE", "UTC")

    # --------------------------------------------------------------------------
    # Security Headers (applied by middleware)
    # --------------------------------------------------------------------------
    SECURITY_HEADERS: dict = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "SAMEORIGIN",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    }


class DevelopmentConfig(BaseConfig):
    """
    Development configuration.

    Debug mode enabled, relaxed security, SQLite database,
    verbose SQL logging for query analysis.
    """

    DEBUG: bool = True
    TESTING: bool = False

    # Verbose SQL query logging during development
    SQLALCHEMY_RECORD_QUERIES: bool = True
    SQLALCHEMY_ECHO: bool = False  # Set True to print raw SQL

    # Relaxed rate limiting in development
    RATELIMIT_ENABLED: bool = False

    # Plaintext emails in dev — no real SMTP needed
    MAIL_SUPPRESS_SEND: bool = False

    # More lenient password hashing for faster test cycles
    BCRYPT_LOG_ROUNDS: int = 4

    # Log everything in development
    LOG_LEVEL: str = "DEBUG"


class TestingConfig(BaseConfig):
    """
    Testing configuration.

    Uses in-memory SQLite, disables CSRF for test client simplicity,
    disables rate limiting and mail sending.
    """

    DEBUG: bool = False
    TESTING: bool = True

    # In-memory database — reset after each test
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///:memory:"

    # Disable CSRF for test client
    WTF_CSRF_ENABLED: bool = False

    # Disable rate limiting in tests
    RATELIMIT_ENABLED: bool = False

    # Never send actual emails during testing
    MAIL_SUPPRESS_SEND: bool = True

    # Fast password hashing for test performance
    BCRYPT_LOG_ROUNDS: int = 4

    # Use simple in-memory session for tests
    SESSION_TYPE: str = "filesystem"
    SESSION_FILE_DIR: str = "./instance/sessions_test"

    # Use simple in-memory cache for tests
    CACHE_TYPE: str = "SimpleCache"

    # Suppress scheduled jobs in tests
    SCHEDULER_API_ENABLED: bool = False


class ProductionConfig(BaseConfig):
    """
    Production configuration.

    Strict security settings, PostgreSQL, Redis, full rate limiting.
    All sensitive values MUST be set via environment variables.
    """

    DEBUG: bool = False
    TESTING: bool = False

    # Enforce secure cookies in production
    SESSION_COOKIE_SECURE: bool = True
    REMEMBER_COOKIE_SECURE: bool = True
    SESSION_COOKIE_SAMESITE: str = "Strict"

    # Stronger CSRF timeout in production
    WTF_CSRF_TIME_LIMIT: int = 1800

    # PostgreSQL — fix postgres:// → postgresql:// for SQLAlchemy 2.x
    _db_url = os.environ.get("DATABASE_URL", "sqlite:///smart_hrms_dev.db")
    SQLALCHEMY_DATABASE_URI: str = (
        _db_url.replace("postgres://", "postgresql://", 1)
        if _db_url else "sqlite:///smart_hrms_dev.db"
    )

    # PostgreSQL connection pool settings
    SQLALCHEMY_ENGINE_OPTIONS: dict = {
        "pool_pre_ping": True,
        "pool_size": int(os.environ.get("DB_POOL_SIZE", 10)),
        "max_overflow": int(os.environ.get("DB_MAX_OVERFLOW", 20)),
        "pool_timeout": int(os.environ.get("DB_POOL_TIMEOUT", 30)),
        "pool_recycle": int(os.environ.get("DB_POOL_RECYCLE", 3600)),
    }

    # Cache — use Redis if available, else SimpleCache
    CACHE_TYPE: str = os.environ.get("CACHE_TYPE", "SimpleCache")
    CACHE_REDIS_URL: str = os.environ.get("CACHE_REDIS_URL", "redis://localhost:6379/0")

    # Session — use filesystem (Redis optional)
    SESSION_TYPE: str = os.environ.get("SESSION_TYPE", "filesystem")
    SESSION_FILE_DIR: str = os.environ.get("SESSION_FILE_DIR", "./instance/sessions")

    # Production log level
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "WARNING")

    # Stronger password hashing in production
    BCRYPT_LOG_ROUNDS: int = int(os.environ.get("BCRYPT_LOG_ROUNDS", 14))

    # Additional security headers for production
    SECURITY_HEADERS: dict = {
        **BaseConfig.SECURITY_HEADERS,
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
        "Content-Security-Policy": (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net; "
            "img-src 'self' data: blob:; "
            "connect-src 'self';"
        ),
    }


# ------------------------------------------------------------------------------
# Configuration Registry
# Maps environment name strings to configuration classes.
# Used by the application factory to select the correct config.
# ------------------------------------------------------------------------------
config_registry: dict = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "render": ProductionConfig,   # alias used on Render.com
    "default": DevelopmentConfig,
}
