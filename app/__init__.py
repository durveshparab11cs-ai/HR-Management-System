"""
app/__init__.py
================
Smart HRMS Application Factory.

The create_app() factory is the single entry point for constructing
the Flask application. It follows the Application Factory Pattern which:
    - Allows multiple instances (testing, production) with different configs
    - Avoids circular imports by deferring extension init until app creation
    - Makes the test suite trivially instantiate isolated app instances

Initialization pipeline (order is intentional):
    1. Load configuration
    2. Setup logging (needs config first)
    3. Initialize Flask extensions
    4. Register middleware (ProxyFix, security headers, request logger)
    5. Register blueprints
    6. Register error handlers
    7. Register context processors
    8. Register CLI commands
    9. Initialize scheduler (after app fully configured)
   10. Ensure upload/instance directories exist

Usage:
    from app import create_app
    app = create_app("production")
"""

import os
import logging
from flask import Flask

logger = logging.getLogger(__name__)


def create_app(env: str = "development") -> Flask:
    """
    Construct and fully configure a Flask application instance.

    Args:
        env: Environment name — 'development', 'testing', or 'production'.
             Resolved against config_registry in config/settings.py.
             Defaults to 'development'.

    Returns:
        Fully initialized Flask application instance.
    """
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )

    # ── 1. Configuration ────────────────────────────────────────────
    _load_config(app, env)

    # ── 2. Logging ──────────────────────────────────────────────────
    from app.logging_config import setup_logging  # noqa: PLC0415
    setup_logging(app)

    # ── 3. Extensions ────────────────────────────────────────────────
    _init_extensions(app)

    # ── 4. Middleware ────────────────────────────────────────────────
    from app.middleware import register_middleware  # noqa: PLC0415
    register_middleware(app)

    # ── 5. Blueprints ────────────────────────────────────────────────
    from app.blueprints import register_blueprints  # noqa: PLC0415
    register_blueprints(app)

    # ── 6. Error Handlers ────────────────────────────────────────────
    from app.error_handlers import register_error_handlers  # noqa: PLC0415
    register_error_handlers(app)

    # ── 7. Context Processors ───────────────────────────────────────
    from app.core.context_processors import register_context_processors  # noqa: PLC0415
    register_context_processors(app)

    # ── 7b. Template Globals ─────────────────────────────────────────
    _register_template_globals(app)

    # ── 7c. Jinja2 filters (IST conversion, fmt_minutes, etc.) ──────
    _register_template_filters(app)

    # ── 8. CLI Commands ──────────────────────────────────────────────
    _register_cli(app)

    # ── 9. Scheduler ────────────────────────────────────────────────
    from app.extensions.scheduler import configure_scheduler  # noqa: PLC0415
    configure_scheduler(app)

    # ── 10. Runtime directories ──────────────────────────────────────
    _ensure_directories(app)

    # ── Health check endpoint ────────────────────────────────────────
    _register_health(app)

    # ── Root redirect ────────────────────────────────────────────────
    _register_root_redirect(app)

    # ── Auto-create DB tables (safe on first boot) ───────────────────
    _auto_create_tables(app)

    app.logger.info(
        "Smart HRMS started | env=%s | debug=%s",
        env,
        app.config.get("DEBUG"),
    )

    return app


# ─────────────────────────────────────────────────────────────────────────
# Private helpers
# ─────────────────────────────────────────────────────────────────────────

def _load_config(app: Flask, env: str) -> None:
    """
    Load the correct configuration class from the registry.

    Falls back to DevelopmentConfig when the env string is unknown.

    Args:
        app: Flask instance.
        env: Environment name string.
    """
    from config import config_registry  # noqa: PLC0415

    config_class = config_registry.get(env, config_registry["default"])
    app.config.from_object(config_class)

    # Allow an optional instance/config.py to override without source changes
    instance_cfg = os.path.join(app.instance_path, "config.py")
    if os.path.exists(instance_cfg):
        app.config.from_pyfile(instance_cfg, silent=True)
        app.logger.info("Loaded instance config override: %s", instance_cfg)

    app.logger.debug("Configuration loaded: %s", config_class.__name__)


def _init_extensions(app: Flask) -> None:
    """
    Initialize all Flask extensions by calling their init_app() methods.
    """
    from app.extensions.database import db          # noqa: PLC0415
    from app.extensions.migrate  import migrate     # noqa: PLC0415
    from app.extensions.login    import login_manager, configure_login_manager  # noqa: PLC0415
    from app.extensions.mail     import mail        # noqa: PLC0415
    from app.extensions.csrf     import csrf        # noqa: PLC0415
    from app.extensions.limiter  import limiter     # noqa: PLC0415
    from app.extensions.cache    import cache       # noqa: PLC0415
    from app.extensions.session  import server_session  # noqa: PLC0415

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    configure_login_manager(app)
    mail.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    cache.init_app(app)

    # Flask-Session: ensure session dir exists, fallback to no server-session
    session_type = app.config.get("SESSION_TYPE", "filesystem")
    if session_type == "filesystem":
        session_dir = app.config.get("SESSION_FILE_DIR", "/tmp/hrms_sessions")
        try:
            os.makedirs(session_dir, exist_ok=True)
        except OSError:
            pass
        app.config["SESSION_FILE_DIR"] = session_dir

    server_session.init_app(app)

    # Import all models so Alembic discovers them for migrations
    from app.models import User  # noqa: F401, PLC0415

    app.logger.debug("Extensions initialized.")


def _register_cli(app: Flask) -> None:
    """
    Register custom Flask CLI commands for database and admin operations.

    Commands added:
        flask db-init       — create all tables (non-migration quick start)
        flask create-admin  — create a superadmin user interactively
        flask seed-db       — seed reference data for development

    Args:
        app: Flask instance.
    """
    import click  # noqa: PLC0415

    @app.cli.command("db-init")
    def db_init():
        """Create all database tables from SQLAlchemy models."""
        from app.extensions.database import db as _db  # noqa: PLC0415
        _db.create_all()
        click.secho("Database tables created.", fg="green")

    @app.cli.command("create-admin")
    @click.option("--email",     prompt="Admin email")
    @click.option("--password",  prompt="Admin password", hide_input=True, confirmation_prompt=True)
    @click.option("--first-name", prompt="First name", default="Super")
    @click.option("--last-name",  prompt="Last name",  default="Admin")
    def create_admin(email, password, first_name, last_name):
        """Create a SUPER_ADMIN user account."""
        from app.extensions.database import db as _db   # noqa: PLC0415
        from app.models.user import User                 # noqa: PLC0415
        from app.constants.enums import UserRole, UserStatus  # noqa: PLC0415

        existing = User.query.filter_by(email=email).first()
        if existing:
            click.secho(f"User {email} already exists.", fg="yellow")
            return

        user = User(
            email=email,
            username=email.split("@")[0],
            first_name=first_name,
            last_name=last_name,
            role=UserRole.SUPER_ADMIN.value,
            status=UserStatus.ACTIVE.value,
            email_verified=True,
        )
        user.set_password(password)
        _db.session.add(user)
        _db.session.commit()
        click.secho(f"Super admin created: {email}", fg="green")

    @app.cli.command("seed-db")
    def seed_db():
        """Seed development reference data (leave types, office settings)."""
        click.secho("Seeding development data…", fg="cyan")
        from app.extensions.database import db as _db  # noqa: PLC0415
        from app.models.leave import LeaveType  # noqa: PLC0415
        from app.models.office_settings import OfficeSettings  # noqa: PLC0415
        import datetime  # noqa: PLC0415

        # ── Default office settings ──────────────────────────────────
        if not OfficeSettings.query.first():
            office = OfficeSettings(
                name="Head Office",
                is_default=True,
                latitude=18.520430,
                longitude=73.856743,
                radius_metres=100,
                office_start_time=datetime.time(9, 0),
                office_end_time=datetime.time(18, 0),
                grace_period_minutes=10,
                half_day_threshold_minutes=240,  # < 4h = half day
            )
            _db.session.add(office)
            click.secho("  ✓ Default office settings created", fg="green")
        else:
            click.secho("  - Office settings already exist", fg="yellow")

        # ── Default leave types ───────────────────────────────────────
        leave_types = [
            {"name": "Casual Leave",        "code": "CL",    "max_days_per_year": 12, "is_paid": True,  "color": "#3b82f6"},
            {"name": "Sick Leave",          "code": "SL",    "max_days_per_year": 12, "is_paid": True,  "color": "#ef4444", "requires_document": True},
            {"name": "Paid Leave",          "code": "PL",    "max_days_per_year": 15, "is_paid": True,  "color": "#10b981"},
            {"name": "Loss of Pay",         "code": "LOP",   "max_days_per_year": 30, "is_paid": False, "color": "#f59e0b"},
            {"name": "Comp Off",            "code": "COMP",  "max_days_per_year": 6,  "is_paid": True,  "color": "#8b5cf6"},
            {"name": "Maternity Leave",     "code": "ML",    "max_days_per_year": 180,"is_paid": True,  "color": "#ec4899"},
            {"name": "Paternity Leave",     "code": "PTL",   "max_days_per_year": 15, "is_paid": True,  "color": "#0891b2"},
            {"name": "Bereavement Leave",   "code": "BL",    "max_days_per_year": 5,  "is_paid": True,  "color": "#6b7280"},
        ]
        for lt_data in leave_types:
            if not LeaveType.query.filter_by(code=lt_data["code"]).first():
                lt = LeaveType(**lt_data)
                _db.session.add(lt)
                click.secho(f"  ✓ Leave type: {lt_data['name']}", fg="green")
            else:
                click.secho(f"  - Leave type {lt_data['code']} already exists", fg="yellow")

        _db.session.commit()
        click.secho("\nSeed complete.", fg="green")

    app.logger.debug("CLI commands registered.")


def _register_template_globals(app: Flask) -> None:
    """Register Jinja2 globals: render_field macro, csrf_token_field, etc."""
    from jinja2 import ChoiceLoader, FileSystemLoader  # noqa: PLC0415
    import os  # noqa: PLC0415

    # Add macros folder to Jinja2 loader path
    macros_path = os.path.join(app.root_path, "templates", "macros")

    @app.context_processor
    def inject_macros():
        return {}

    # Global: csrf_token_field — renders a hidden CSRF input
    @app.template_global()
    def csrf_token_field():
        from flask_wtf.csrf import generate_csrf  # noqa: PLC0415
        from markupsafe import Markup  # noqa: PLC0415
        token = generate_csrf()
        return Markup(f'<input type="hidden" name="csrf_token" value="{token}">')

    # Global: render_field — delegates to macro but usable as a function
    @app.template_global()
    def render_field(field, placeholder='', label_override='', extra_class=''):
        from markupsafe import Markup  # noqa: PLC0415
        has_errors = bool(field.errors)
        err_class = "is-invalid " if has_errors else ""

        ftype = field.type if hasattr(field, 'type') else ''
        if ftype in ('SelectField', 'SelectMultipleField'):
            widget = field(class_=f"form-select form-select-sm {err_class}{extra_class}")
        elif ftype == 'TextAreaField':
            widget = field(class_=f"form-control form-control-sm {err_class}{extra_class}",
                           placeholder=placeholder or '')
        elif ftype == 'FileField':
            widget = field(class_=f"form-control form-control-sm {err_class}{extra_class}")
        elif ftype == 'BooleanField':
            cb = field(class_=f"form-check-input {err_class}")
            lbl = f'<label class="form-check-label small" for="{field.id}">{field.label.text}</label>'
            widget = Markup(f'<div class="form-check">{cb}{lbl}</div>')
        else:
            widget = field(class_=f"form-control form-control-sm {err_class}{extra_class}",
                           placeholder=placeholder or '')

        label_text = label_override or field.label.text
        label_html = Markup(f'<label for="{field.id}" class="form-label fw-medium small">{label_text}</label>')

        errors_html = Markup("".join(
            f'<div class="invalid-feedback d-block">{e}</div>' for e in field.errors
        ))

        return Markup(f'{label_html}{widget}{errors_html}')


def _ensure_directories(app: Flask) -> None:
    """
    Create required runtime directories if they don't exist.

    Args:
        app: Flask instance.
    """
    dirs = [
        app.config.get("UPLOAD_FOLDER", "./instance/uploads"),
        app.config.get("SESSION_FILE_DIR", "./instance/sessions"),
        app.config.get("LOG_DIR", "./logs"),
        app.instance_path,
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)


def _register_template_filters(app: Flask) -> None:
    """Register custom Jinja2 filters for the Jinja2 environment."""
    try:
        import pytz
        IST = pytz.timezone("Asia/Kolkata")
    except ImportError:
        IST = None

    from datetime import datetime as _dt

    @app.template_filter("ist")
    def to_ist(dt, fmt: str = "%H:%M"):
        """Convert UTC datetime to IST. Usage: {{ dt | ist }}"""
        if dt is None:
            return "—"
        if not isinstance(dt, _dt):
            return str(dt)
        if IST is None:
            return dt.strftime(fmt)
        try:
            import pytz as _pytz
            if dt.tzinfo is None:
                dt = _pytz.utc.localize(dt)
            return dt.astimezone(IST).strftime(fmt)
        except Exception:
            return dt.strftime(fmt)

    @app.template_filter("ist_date")
    def to_ist_date(dt):
        """Format datetime as '13 Jul 2026, 02:06 PM IST'."""
        return to_ist(dt, "%d %b %Y, %I:%M %p")

    @app.template_filter("fmt_minutes")
    def fmt_minutes(minutes):
        """
        Format integer minutes as human-readable duration.
        Usage: {{ att.late_minutes | fmt_minutes }}
        Examples: 5 → '5m', 65 → '1h 5m', 455 → '7h 35m'
        """
        if not minutes:
            return "0m"
        try:
            minutes = int(minutes)
        except (TypeError, ValueError):
            return "0m"
        h, m = divmod(minutes, 60)
        if h == 0:
            return f"{m}m"
        if m == 0:
            return f"{h}h"
        return f"{h}h {m}m"


def _register_root_redirect(app: Flask) -> None:
    """Redirect / to login or dashboard depending on auth state."""
    from flask import redirect, url_for  # noqa: PLC0415

    @app.route("/")
    def root():
        from flask_login import current_user  # noqa: PLC0415
        if current_user.is_authenticated:
            from app.blueprints.authentication.service import AuthService
            return redirect(AuthService().get_dashboard_url(current_user))
        return redirect(url_for("authentication.login"))


def _register_health(app: Flask) -> None:
    """
    Register the /health liveness probe endpoint at the app level.

    This is separate from the API blueprint so load balancers can reach it
    without knowing the API prefix, and CSRF/auth are never applied to it.

    Args:
        app: Flask instance.
    """
    from flask import jsonify  # noqa: PLC0415

    @app.route("/health")
    def health():
        """Liveness probe — returns 200 OK when app is running."""
        return jsonify({"status": "ok", "version": app.config.get("APP_VERSION", "1.0.0")}), 200


def _auto_create_tables(app: Flask) -> None:
    """
    Create all DB tables on first boot.
    Runs inside a proper app context after all extensions are initialized.
    Safe to call repeatedly — SQLAlchemy only creates missing tables.
    """
    try:
        with app.app_context():
            from app.extensions.database import db  # noqa: PLC0415
            db.create_all()
            app.logger.info("db.create_all() — tables ready.")
    except Exception as exc:
        app.logger.warning("db.create_all() skipped: %s", exc)
