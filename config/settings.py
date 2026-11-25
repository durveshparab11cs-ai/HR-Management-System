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
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def resolve_database_uri(raw_url: str) -> str:
    """
    Validates and normalizes database URI:
    1. Fixes postgres:// -> postgresql:// for SQLAlchemy 2.x compatibility.
    2. Tests if the PostgreSQL host is resolvable by DNS.
       If it is a Render internal short hostname (e.g. dpg-xxxx-a) that fails resolution,
       tries regional suffixes (e.g. .singapore-postgres.render.com).
    3. If the host is unresolvable or dead, safely falls back to local SQLite so
       the application boots and functions cleanly instead of crashing with Name or service not known.
    """
    if not raw_url:
        return "sqlite:///smart_hrms_dev.db"

    if raw_url.startswith("postgres://"):
        raw_url = raw_url.replace("postgres://", "postgresql://", 1)

    if raw_url.startswith("postgresql://"):
        import re, socket
        m = re.search(r'@([^:/]+)(?::(\d+))?(/[^?]*)(.*)', raw_url)
        if m:
            host = m.group(1)
            port = int(m.group(2) or 5432)
            db_path = m.group(3)
            query = m.group(4) or ""
            auth = raw_url[:m.start(1)]

            reachable = False
            try:
                socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP)
                reachable = True
            except Exception:
                if host.startswith("dpg-") and "." not in host:
                    for region in ["singapore", "oregon", "frankfurt", "ohio"]:
                        cand = f"{host}.{region}-postgres.render.com"
                        try:
                            socket.getaddrinfo(cand, port, proto=socket.IPPROTO_TCP)
                            host = cand
                            raw_url = f"{auth}{host}:{port}{db_path}{query}"
                            reachable = True
                            break
                        except Exception:
                            pass

            if not reachable:
                # Safe SQLite fallback when remote PostgreSQL host is unreachable
                instance_dir = os.path.abspath("instance")
                os.makedirs(instance_dir, exist_ok=True)
                db_path = os.path.join(instance_dir, "smart_hrms.db").replace("\\", "/")
                return f"sqlite:///{db_path}"

            if "sslmode" not in raw_url and "localhost" not in host and "127.0.0.1" not in host:
                sep = "&" if "?" in raw_url else "?"
                raw_url = f"{raw_url}{sep}sslmode=require"

    return raw_url


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
    _raw_db_url = resolve_database_uri(os.environ.get("DATABASE_URL", "sqlite:///smart_hrms_dev.db"))
    SQLALCHEMY_DATABASE_URI: str = _raw_db_url
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_RECORD_QUERIES: bool = False
    SQLALCHEMY_ENGINE_OPTIONS: dict = {
        "pool_pre_ping": True,  # Detect stale connections
        "pool_recycle": int(os.environ.get("DB_POOL_RECYCLE", 1800)),
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
    # Empty — suppresses the yellow "Please log in" flash banner.
    # The login page itself makes the redirect reason obvious.
    LOGIN_MESSAGE: str = ""
    LOGIN_MESSAGE_CATEGORY: str = "info"

    # --------------------------------------------------------------------------
    # Flask-Mail (executivehr0001@gmail.com)
    # --------------------------------------------------------------------------
    MAIL_SERVER: str = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT: int = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS: bool = os.environ.get("MAIL_USE_TLS", "True") == "True"
    MAIL_USE_SSL: bool = os.environ.get("MAIL_USE_SSL", "False") == "True"
    MAIL_USERNAME: str | None = os.environ.get("MAIL_USERNAME", "executivehr0001@gmail.com")
    MAIL_PASSWORD: str | None = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER: str = os.environ.get(
        "MAIL_DEFAULT_SENDER", "CS Creative Solutions HR <executivehr0001@gmail.com>"
    )
    MAIL_MAX_EMAILS: int = int(os.environ.get("MAIL_MAX_EMAILS", 50))
    MAIL_ASCII_ATTACHMENTS: bool = False

    # --------------------------------------------------------------------------
    # Flask-Limiter
    # --------------------------------------------------------------------------
    RATELIMIT_DEFAULT: str = os.environ.get("RATELIMIT_DEFAULT", "1000 per hour")
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
    SESSION_USE_SIGNER: bool = True   # Sign sessions with SECRET_KEY
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
    # Static Files Caching
    # --------------------------------------------------------------------------
    SEND_FILE_MAX_AGE_DEFAULT: int = int(os.environ.get("SEND_FILE_MAX_AGE_DEFAULT", 86400))  # 1 day default

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
    APP_TIMEZONE: str = os.environ.get("APP_TIMEZONE", "Asia/Kolkata")
    ITEMS_PER_PAGE: int = int(os.environ.get("ITEMS_PER_PAGE", 25))
    ADMIN_EMAIL: str = os.environ.get("ADMIN_EMAIL", "admin@smarthrms.com")

    # --------------------------------------------------------------------------
    # APScheduler
    # --------------------------------------------------------------------------
    SCHEDULER_API_ENABLED: bool = os.environ.get("SCHEDULER_API_ENABLED", "False") == "True"
    SCHEDULER_TIMEZONE: str = os.environ.get("SCHEDULER_TIMEZONE", "Asia/Kolkata")

    # --------------------------------------------------------------------------
    # Security Headers (applied by middleware)
    # NOTE: geolocation is intentionally ALLOWED — the attendance system
    # requires browser GPS access. Blocking it with geolocation=() would
    # prevent check-in/check-out for all employees.
    # --------------------------------------------------------------------------
    SECURITY_HEADERS: dict = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "SAMEORIGIN",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        # camera and geolocation are intentionally ALLOWED:
        # the attendance system requires getUserMedia() for selfie capture
        # and navigator.geolocation for GPS check-in/out.
        # Blocking them with camera=() / geolocation=() would deny all employees.
        "Permissions-Policy": "microphone=()",
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

    # PostgreSQL / SQLite with Smart Auto-Resolution
    _db_url = resolve_database_uri(os.environ.get("DATABASE_URL", "sqlite:///smart_hrms_dev.db"))
    SQLALCHEMY_DATABASE_URI: str = _db_url

    # Dynamic connection pool settings: PostgreSQL vs SQLite fallback
    if "sqlite" in _db_url:
        SQLALCHEMY_ENGINE_OPTIONS: dict = {
            "pool_pre_ping": True,
        }
    else:
        # Dynamic connect_args: Neon / PgBouncer pooled connections reject statement_timeout in startup options
        _connect_args = {}
        if "pooler" not in _db_url and "neon.tech" not in _db_url:
            _connect_args["options"] = "-c statement_timeout=30000"

        SQLALCHEMY_ENGINE_OPTIONS: dict = {
            "pool_pre_ping": True,
            "pool_size": int(os.environ.get("DB_POOL_SIZE", 5)),
            "max_overflow": int(os.environ.get("DB_MAX_OVERFLOW", 10)),
            "pool_timeout": int(os.environ.get("DB_POOL_TIMEOUT", 30)),
            "pool_recycle": int(os.environ.get("DB_POOL_RECYCLE", 1800)),
            "connect_args": _connect_args
        }

    # Cache — use Redis if available, else SimpleCache
    CACHE_TYPE: str = os.environ.get("CACHE_TYPE", "SimpleCache")
    CACHE_REDIS_URL: str = os.environ.get("CACHE_REDIS_URL", "redis://localhost:6379/0")

    # Session — use filesystem by default; set SESSION_TYPE=redis if Redis available
    SESSION_TYPE: str = os.environ.get("SESSION_TYPE", "filesystem")
    SESSION_FILE_DIR: str = os.environ.get("SESSION_FILE_DIR", "./instance/sessions")

    # Static asset caching in production (7 days)
    SEND_FILE_MAX_AGE_DEFAULT: int = int(os.environ.get("SEND_FILE_MAX_AGE_DEFAULT", 604800))

    # Production log level
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "WARNING")

    # Stronger password hashing in production
    BCRYPT_LOG_ROUNDS: int = int(os.environ.get("BCRYPT_LOG_ROUNDS", 14))

    # Additional security headers for production
    # NOTE: geolocation is intentionally NOT blocked — GPS attendance requires it.
    # BaseConfig.SECURITY_HEADERS already sets Permissions-Policy without geolocation=().
    SECURITY_HEADERS: dict = {
        **BaseConfig.SECURITY_HEADERS,
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
        "Content-Security-Policy": (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://unpkg.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com https://unpkg.com; "
            "font-src 'self' data: https://fonts.gstatic.com https://cdn.jsdelivr.net https://unpkg.com; "
            "img-src 'self' data: blob: https://*.tile.openstreetmap.org https://*.openstreetmap.org; "
            "connect-src 'self' https://*.tile.openstreetmap.org https://nominatim.openstreetmap.org https://cdn.jsdelivr.net https://unpkg.com; "
            "worker-src blob:; "
            "frame-src 'none';"
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
