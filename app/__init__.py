"""
app/__init__.py
================
Smart HRMS Application Factory.
Build: 2026-08-03 15:26 - Security and filter fixes deployed
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

    # DEBUG: Log every request
    from flask import request as _request
    
    @app.before_request
    def log_request():
        app.logger.info(f"[REQUEST] {_request.method} {_request.path}")
    
    @app.after_request
    def log_response(response):
        app.logger.info(f"[RESPONSE] {_request.method} {_request.path} -> {response.status_code} {response.content_type}")
        return response

    # ── 3. Extensions ────────────────────────────────────────────────
    _init_extensions(app)

    # ── 4. Middleware ────────────────────────────────────────────────
    from app.middleware import register_middleware  # noqa: PLC0415
    register_middleware(app)

    # ── 4b. EARLY: Register coordinator routes BEFORE blueprints ──────
    # This ensures they're not caught by Flask-Login redirects
    # TEMPORARILY DISABLED: Causing 502 on Render - will add after app is stable
    # from app.blueprints.coordinator.routes import register_coordinator_routes  # noqa: PLC0415
    # register_coordinator_routes(app)

    # ── 5. Blueprints ────────────────────────────────────────────────
    from app.blueprints import register_blueprints  # noqa: PLC0415
    register_blueprints(app)

    # ── 5a. Admin redirect hook ──────────────────────────────────────
    # REMOVED: Dangerous redirect logic that was causing 404s
    # The dashboard and admin pages are separate; users should access
    # the correct one based on their role via URL or navbar link

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

    # ── Global request handler for admin redirects ──────────────────
    _register_request_handlers(app)

    # ── Auto-create DB tables (safe on first boot, non-blocking) ──────
    # Run table creation immediately but don't let it crash the app
    try:
        _auto_create_tables(app)
        # CRITICAL: Ensure Comp Off leave type exists (must run after tables created)
        _ensure_comp_off_leavetype(app)
    except Exception as exc:
        app.logger.error("Table creation failed (non-fatal): %s", exc)

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

    # Dynamic fallback check: ensure database URI is valid and resolvable
    from config.settings import resolve_database_uri  # noqa: PLC0415
    curr_db = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    resolved_db = resolve_database_uri(curr_db)
    if resolved_db != curr_db:
        app.config["SQLALCHEMY_DATABASE_URI"] = resolved_db
        if "sqlite" in resolved_db:
            app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True}
        app.logger.warning(
            "⚠️ Database host in %s was unresolvable. Safe fallback applied: %s",
            curr_db.split("@")[-1] if "@" in curr_db else curr_db,
            "sqlite" if "sqlite" in resolved_db else resolved_db.split("@")[-1]
        )

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
    from app.models.shift_change_log import ShiftChangeLog  # noqa: F401, PLC0415
    # v2 — force redeploy 2026-07-22

    app.logger.debug("Extensions initialized.")


def _register_cli(app: Flask) -> None:
    """
    Register custom Flask CLI commands for database and admin operations.

    Commands added:
        flask db-init       — create all tables (non-migration quick start)
        flask create-admin  — create a superadmin user interactively
        flask seed-db       — seed reference data for development
        flask clear-attendance — clear ALL attendance data (with --confirm flag)

    Args:
        app: Flask instance.
    """
    import click  # noqa: PLC0415
    
    # Register clear-attendance command
    from clear_attendance_cli import init_app as init_clear_attendance  # noqa: PLC0415
    init_clear_attendance(app)

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
                half_day_threshold_minutes=300,  # < 5h = half day
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
            {"name": "Comp Off",            "code": "CO",    "max_days_per_year": 6,  "is_paid": True,  "color": "#8b5cf6"},
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

    @app.cli.command("fix-admin-roles")
    def fix_admin_roles():
        """One-time fix: Update E-2512012 and E-2603025 to super_admin role."""
        from app.models.user import User  # noqa: PLC0415
        from app.extensions.database import db  # noqa: PLC0415
        
        click.secho("=" * 60, fg="cyan")
        click.secho("FIXING ADMIN ROLES", fg="cyan", bold=True)
        click.secho("=" * 60, fg="cyan")
        click.echo()
        
        try:
            # Check current state
            user1 = User.query.filter_by(username='e_2512012').first()
            user2 = User.query.filter_by(username='e_2603025').first()
            
            click.echo("Current state:")
            if user1:
                click.echo(f"  e_2512012: role = '{user1.role}'")
            else:
                click.secho("  e_2512012: NOT FOUND", fg="red")
            
            if user2:
                click.echo(f"  e_2603025: role = '{user2.role}'")
            else:
                click.secho("  e_2603025: NOT FOUND", fg="red")
            
            click.echo()
            
            # Update roles
            if user1 and user1.role != 'super_admin':
                user1.role = 'super_admin'
                db.session.add(user1)
                click.secho("✅ Updated e_2512012 to super_admin", fg="green")
            
            if user2 and user2.role != 'super_admin':
                user2.role = 'super_admin'
                db.session.add(user2)
                click.secho("✅ Updated e_2603025 to super_admin", fg="green")
            
            db.session.commit()
            
            click.echo()
            click.echo("Verification:")
            user1_check = User.query.filter_by(username='e_2512012').first()
            user2_check = User.query.filter_by(username='e_2603025').first()
            
            if user1_check and user1_check.role == 'super_admin':
                click.secho("  ✅ e_2512012: super_admin", fg="green")
            if user2_check and user2_check.role == 'super_admin':
                click.secho("  ✅ e_2603025: super_admin", fg="green")
            
            click.echo()
            click.secho("=" * 60, fg="green")
            click.secho("✅ ROLES FIXED SUCCESSFULLY", fg="green", bold=True)
            click.secho("=" * 60, fg="green")
            
        except Exception as e:
            click.secho(f"❌ ERROR: {e}", fg="red", bold=True)
            db.session.rollback()
            raise
    def migrate_shift_change():
        """Add reporting_manager fields to shift_change_requests table."""
        from app.extensions.database import db as _db  # noqa: PLC0415
        from sqlalchemy import text  # noqa: PLC0415
        
        click.secho("=" * 60, fg="cyan")
        click.secho("SHIFT CHANGE MANAGER FIELDS MIGRATION", fg="cyan", bold=True)
        click.secho("=" * 60, fg="cyan")
        click.echo()
        
        try:
            # Check if columns exist
            click.echo("Checking if columns exist...")
            result = _db.session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'shift_change_requests' 
                AND column_name IN ('reporting_manager_code', 'reporting_manager_name')
            """))
            existing_columns = [row[0] for row in result]
            
            if len(existing_columns) == 2:
                click.secho("✅ Columns already exist. Migration not needed.", fg="green")
                return
            
            click.echo(f"Found {len(existing_columns)} of 2 required columns.")
            click.echo("Running migration...")
            click.echo()
            
            # Add reporting_manager_code
            if 'reporting_manager_code' not in existing_columns:
                click.echo("Adding column: reporting_manager_code...")
                _db.session.execute(text("""
                    ALTER TABLE shift_change_requests 
                    ADD COLUMN IF NOT EXISTS reporting_manager_code VARCHAR(50)
                """))
                _db.session.commit()
                click.secho("✅ Added reporting_manager_code", fg="green")
            
            # Add reporting_manager_name
            if 'reporting_manager_name' not in existing_columns:
                click.echo("Adding column: reporting_manager_name...")
                _db.session.execute(text("""
                    ALTER TABLE shift_change_requests 
                    ADD COLUMN IF NOT EXISTS reporting_manager_name VARCHAR(200)
                """))
                _db.session.commit()
                click.secho("✅ Added reporting_manager_name", fg="green")
            
            # Update existing records
            click.echo("Updating existing records...")
            _db.session.execute(text("""
                UPDATE shift_change_requests 
                SET reporting_manager_code = 'PENDING', 
                    reporting_manager_name = 'To Be Assigned'
                WHERE reporting_manager_code IS NULL OR reporting_manager_code = ''
            """))
            _db.session.commit()
            click.secho("✅ Updated existing records", fg="green")
            
            # Set NOT NULL constraint
            click.echo("Setting NOT NULL constraint...")
            _db.session.execute(text("""
                ALTER TABLE shift_change_requests 
                ALTER COLUMN reporting_manager_code SET DEFAULT ''
            """))
            _db.session.execute(text("""
                ALTER TABLE shift_change_requests 
                ALTER COLUMN reporting_manager_code SET NOT NULL
            """))
            _db.session.commit()
            click.secho("✅ Set NOT NULL constraint", fg="green")
            
            # Create index
            click.echo("Creating index...")
            _db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_shift_change_requests_manager_code 
                ON shift_change_requests(reporting_manager_code)
            """))
            _db.session.commit()
            click.secho("✅ Created index", fg="green")
            
            click.echo()
            click.secho("=" * 60, fg="green")
            click.secho("✅ MIGRATION COMPLETED SUCCESSFULLY", fg="green", bold=True)
            click.secho("=" * 60, fg="green")
            click.echo()
            
        except Exception as e:
            _db.session.rollback()
            click.secho(f"❌ ERROR: {str(e)}", fg="red", bold=True)
            click.echo()
            click.secho("Migration failed. Please check the error above.", fg="red")

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
        """Format datetime (already in IST). Usage: {{ dt | ist }}"""
        if dt is None:
            return "—"
        if not isinstance(dt, _dt):
            return str(dt)
        # Times are already stored in IST, just format them
        try:
            return dt.strftime(fmt)
        except Exception:
            return "—"

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
        # Redirect to auth/login blueprint
        return redirect(url_for("authentication.login"))
    
    @app.route("/login")
    def login_redirect():
        """Convenience redirect to authentication.login"""
        return redirect(url_for("authentication.login"))

    from app.extensions import csrf  # noqa: PLC0415

    @app.route("/kiosk", methods=["GET", "POST"])
    @csrf.exempt
    def kiosk():
        """Dedicated Attendance Kiosk terminal view with password lock."""
        from app.blueprints.attendance.routes import handle_kiosk_request
        return handle_kiosk_request()

    @app.route("/kiosk/unlock", methods=["POST"])
    @csrf.exempt
    def kiosk_unlock():
        """Unlock endpoint for Kiosk terminal."""
        from app.blueprints.attendance.routes import handle_kiosk_unlock
        return handle_kiosk_unlock()

    @app.route("/kiosk/lock", methods=["GET", "POST"])
    def kiosk_lock():
        """Lock endpoint for Kiosk terminal."""
        from app.blueprints.attendance.routes import handle_kiosk_lock
        return handle_kiosk_lock()


def _register_health(app: Flask) -> None:
    """Register the /health liveness probe and /camera-test diagnostic endpoints."""
    from flask import jsonify, render_template  # noqa: PLC0415

    @app.route("/health")
    def health():
        """Lightweight liveness probe endpoint for Render health checks."""
        db_status = "untested"
        try:
            from app.extensions.database import db  # noqa: PLC0415
            from sqlalchemy import text  # noqa: PLC0415
            db.session.execute(text("SELECT 1"))
            db_status = "connected"
        except Exception as e:
            app.logger.warning("Database probe during health check: %s", e)
            db_status = f"warning: {str(e)}"

        # Always return 200 OK so web container passes Render liveness probes
        return jsonify({
            "status": "ok",
            "database": db_status,
            "version": app.config.get("APP_VERSION", "1.0.0")
        }), 200

    @app.route("/camera-test")
    def camera_test():
        """Camera diagnostic page — no auth required, for debugging only."""
        return render_template("camera_test.html")


def _register_request_handlers(app: Flask) -> None:
    """
    Register global request handlers for admin user redirects and permissions.

    - Skip authentication for coordinator API endpoints
    - Redirect admin/super_admin users from /dashboard/* to /admin/
    - Enforce dashboard access control
    """
    from flask import request, redirect, url_for, g, session  # noqa: PLC0415
    from flask_login import current_user
    
    @app.before_request
    def enforce_admin_access():
        """Redirect admin users from /dashboard/ to /admin/."""
        # Skip for non-authenticated users and special routes
        if not current_user.is_authenticated:
            return None

        # Get current path
        current_path = request.path.lower()
        
        # Check if trying to access /dashboard/ or /dashboard/*
        if current_path.startswith("/dashboard"):
            # Admin and super_admin users must use /admin/ dashboard
            user_role = getattr(current_user, "role", None)
            if user_role in ("super_admin", "admin", "hr_manager", "hr_staff"):
                # Redirect to admin dashboard
                return redirect(url_for("admin.index"))
        
        return None


def _auto_create_tables(app: Flask) -> None:
    """
    Create all DB tables on first boot, run safe column migrations,
    and initialize essential records.
    """
    import os  # noqa: PLC0415
    try:
        with app.app_context():
            from app.extensions.database import db  # noqa: PLC0415
            from sqlalchemy import text, inspect  # noqa: PLC0415
            
            # STEP 0.5: Ensure EmployeeHospitalAssignment model is imported so SQLAlchemy knows about it
            try:
                from app.models.hospital_assignment import EmployeeHospitalAssignment  # noqa: F401, PLC0415
                app.logger.info("✓ Step 0.5: EmployeeHospitalAssignment model imported")
            except Exception as exc:
                app.logger.warning("⚠️  Step 0.5: Failed to import EmployeeHospitalAssignment: %s", exc)
            
            # STEP 1: Create all tables
            try:
                db.create_all()
                app.logger.info("✓ Step 1: db.create_all()")
            except Exception as exc:
                app.logger.warning("⚠️  Step 1: db.create_all() failed: %s", exc)

            # STEP 1.5: Verify employee_hospital_assignments table exists (CRITICAL for hospital import)
            try:
                insp = inspect(db.engine)
                tables = insp.get_table_names()
                
                if 'employee_hospital_assignments' not in tables:
                    app.logger.warning("⚠️  employee_hospital_assignments table missing, creating explicitly...")
                    
                    # Use raw SQL to create the table
                    dialect = db.engine.dialect.name
                    if dialect == 'postgresql':
                        create_sql = text("""
                            CREATE TABLE IF NOT EXISTS employee_hospital_assignments (
                                id SERIAL PRIMARY KEY,
                                employee_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
                                hospital_id INTEGER REFERENCES hospitals(id) ON DELETE SET NULL,
                                hospital_name VARCHAR(200),
                                effective_from DATE,
                                effective_until DATE,
                                notes TEXT,
                                is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
                                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                                deleted_at TIMESTAMP WITH TIME ZONE,
                                deleted_by INTEGER
                            );
                            CREATE INDEX IF NOT EXISTS idx_emp_hosp_assign_employee_id ON employee_hospital_assignments(employee_id);
                            CREATE INDEX IF NOT EXISTS idx_emp_hosp_assign_hospital_id ON employee_hospital_assignments(hospital_id);
                            CREATE INDEX IF NOT EXISTS idx_emp_hosp_assign_active ON employee_hospital_assignments(effective_from, effective_until) WHERE is_deleted = FALSE;
                        """)
                    else:
                        create_sql = text("""
                            CREATE TABLE IF NOT EXISTS employee_hospital_assignments (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                employee_id INTEGER NOT NULL REFERENCES employees(id),
                                hospital_id INTEGER REFERENCES hospitals(id),
                                hospital_name VARCHAR(200),
                                effective_from DATE,
                                effective_until DATE,
                                notes TEXT,
                                is_deleted BOOLEAN NOT NULL DEFAULT 0,
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                deleted_at TIMESTAMP,
                                deleted_by INTEGER
                            );
                            CREATE INDEX IF NOT EXISTS idx_emp_hosp_assign_employee_id ON employee_hospital_assignments(employee_id);
                            CREATE INDEX IF NOT EXISTS idx_emp_hosp_assign_hospital_id ON employee_hospital_assignments(hospital_id);
                        """)
                    
                    # Execute statements individually for universal SQLite and PostgreSQL compatibility
                    for raw_stmt in str(create_sql.text).strip().split(";"):
                        stmt = raw_stmt.strip()
                        if stmt:
                            db.session.execute(text(stmt))
                    db.session.commit()
                    app.logger.info("✓ Step 1.5: Created employee_hospital_assignments table explicitly")
                else:
                    app.logger.info("✓ Step 1.5: employee_hospital_assignments table exists")
            except Exception as exc:
                app.logger.warning("⚠️  Step 1.5: Could not create hospital assignment table: %s", exc)
                try:
                    db.session.rollback()
                except Exception:
                    pass

            # STEP 2: Safe Schema Validation (Strictly Non-Destructive)
            try:
                insp = inspect(db.engine)
                table_names = insp.get_table_names()
                if 'employees' in table_names:
                    emp_cols = [c['name'] for c in insp.get_columns('employees')]
                    required_cols = ['shift_start_time', 'shift_end_time', 'is_flexible_shift', 'required_working_hours']
                    missing_cols = [col for col in required_cols if col not in emp_cols]
                    if missing_cols:
                        app.logger.warning("ℹ️  Schema notice: Missing columns in employees: %s. Handled via migrations.", missing_cols)
                
                if 'attendance_photos' in table_names:
                    photo_cols = [c['name'] for c in insp.get_columns('attendance_photos')]
                    if 'checkout_image_data' not in photo_cols:
                        app.logger.warning("ℹ️  Schema notice: Missing checkout_image_data in attendance_photos. Handled via migrations.")
            except Exception as exc:
                app.logger.warning("⚠️  Schema validation check warning: %s", exc)

            # STEP 3: Add any still-missing columns
            try:
                _migrate_add_columns(db)
                app.logger.info("✓ Step 3: _migrate_add_columns()")
            except Exception as exc:
                app.logger.warning("⚠️  Step 3: _migrate_add_columns() failed: %s", exc)

            # STEP 4: Ensure employee master list is always seeded
            try:
                _auto_seed_employees(app)
                app.logger.info("✓ Step 4: _auto_seed_employees() completed")
            except Exception as exc:
                app.logger.warning("⚠️ Step 4: _auto_seed_employees() failed: %s", exc)

            # STEP 5: Ensure admin roles (only if columns exist)
            try:
                insp = inspect(db.engine)
                def col_exists_check(table, col):
                    try:
                        return any(c['name'] == col for c in insp.get_columns(table))
                    except Exception:
                        return False
                
                if col_exists_check('employees', 'is_flexible_shift'):
                    _ensure_super_admin_roles(app)
                    app.logger.info("✓ Step 5: _ensure_super_admin_roles()")
                else:
                    app.logger.info("⊘ Step 5: Skipping admin roles (columns still missing)")
            except Exception as exc:
                app.logger.warning("⚠️  Step 5: _ensure_super_admin_roles() failed: %s", exc)

    except Exception as exc:
        app.logger.error("❌ _auto_create_tables() failed: %s", exc)


def _migrate_add_columns(db) -> None:
    """
    Idempotent ALTER TABLE for new columns added after initial deploy.
    Safe to run on every boot — skips if columns already exist.
    """
    from sqlalchemy import inspect, text  # noqa: PLC0415

    insp = inspect(db.engine)
    dialect = db.engine.dialect.name  # 'postgresql' or 'sqlite'

    def col_exists(table, col):
        try:
            return any(c['name'] == col for c in insp.get_columns(table))
        except Exception:
            return True  # assume exists if we can't check

    new_cols = [
        ('attendance',           'check_in_accuracy',          'check_in_accuracy FLOAT'),
        ('attendance',           'check_out_accuracy',         'check_out_accuracy FLOAT'),
        ('office_settings',      'min_gps_accuracy_metres',    'min_gps_accuracy_metres INTEGER'),
        ('attendance_photos',    'image_data',                 'image_data TEXT'),
        ('attendance_photos',    'checkout_image_data',        'checkout_image_data TEXT'),
        # Reporting manager fields for all leave request types
        ('leave_requests',       'reporting_manager_code',     'reporting_manager_code VARCHAR(30)'),
        ('leave_requests',       'reporting_manager_name',     'reporting_manager_name VARCHAR(200)'),
        ('half_day_requests',    'reporting_manager_code',     'reporting_manager_code VARCHAR(30)'),
        ('half_day_requests',    'reporting_manager_name',     'reporting_manager_name VARCHAR(200)'),
        ('early_leave_requests', 'reporting_manager_code',     'reporting_manager_code VARCHAR(30)'),
        ('early_leave_requests', 'reporting_manager_name',     'reporting_manager_name VARCHAR(200)'),
        # Reporting manager fields for shift change requests
        ('shift_change_requests', 'reporting_manager_code',    'reporting_manager_code VARCHAR(50)'),
        ('shift_change_requests', 'reporting_manager_name',    'reporting_manager_name VARCHAR(200)'),
        # Hospital allocation fields for employees
        ('employees', 'hospital_id', 'hospital_id INTEGER'),
        ('employees', 'current_shift', 'current_shift VARCHAR(50)'),
        ('employees', 'shift_start_time', 'shift_start_time VARCHAR(20)'),
        ('employees', 'shift_end_time', 'shift_end_time VARCHAR(20)'),
        ('employees', 'is_flexible_shift', 'is_flexible_shift INTEGER'),
        ('employees', 'required_working_hours', 'required_working_hours INTEGER'),
        # Hospital allocation fields for employee_master
        ('employee_master', 'working_location', 'working_location VARCHAR(200)'),
        ('employee_master', 'shift_timing', 'shift_timing VARCHAR(100)'),
        ('employee_master', 'working_status', 'working_status VARCHAR(50)'),
        # Comp Off feature fields for leave_requests - NO DEFAULT CLAUSES, NO TYPE ISSUES
        ('leave_requests',       'comp_off_work_date',         'comp_off_work_date DATE'),
        ('leave_requests',       'comp_off_expiry_date',       'comp_off_expiry_date DATE'),
        ('leave_requests',       'comp_off_used_on',           'comp_off_used_on TIMESTAMP'),
        ('leave_requests',       'comp_off_notified',          'comp_off_notified BOOLEAN'),
        # Leave type ordering for UI - NO DEFAULT CLAUSE
        ('leave_types',          'leave_order',                'leave_order INTEGER'),
        # Biometric Face Registration fields
        ('employee_master',      'registered_face_photo',      'registered_face_photo TEXT'),
        ('employee_master',      'face_descriptor',            'face_descriptor TEXT'),
        ('employee_master',      'is_face_registered',         'is_face_registered BOOLEAN DEFAULT FALSE'),
        ('employees',            'registered_face_photo',      'registered_face_photo TEXT'),
        ('employees',            'face_descriptor',            'face_descriptor TEXT'),
        ('employees',            'is_face_registered',         'is_face_registered BOOLEAN DEFAULT FALSE'),
        # Attendance biometric verification metadata
        ('attendance',           'face_verified',              'face_verified BOOLEAN DEFAULT FALSE'),
        ('attendance',           'face_match_score',           'face_match_score FLOAT'),
        ('attendance_master',    'face_verified',              'face_verified BOOLEAN DEFAULT FALSE'),
        ('attendance_master',    'face_match_score',           'face_match_score FLOAT'),
    ]

    for table, col, col_type in new_cols:
        if not col_exists(table, col):
            try:
                # Format: "ALTER TABLE table_name ADD COLUMN col_name TYPE"
                # The col_type already includes the column name, e.g., "comp_off_work_date DATE"
                sql = f'ALTER TABLE {table} ADD COLUMN {col_type}'
                db.session.execute(text(sql))
                db.session.commit()
                logger.info("Added column %s.%s", table, col)
            except Exception as e:
                try:
                    db.session.rollback()
                except Exception:
                    pass
                logger.warning("Could not add column %s.%s: %s", table, col, e)
                # Don't crash the app if migration fails — safe defaults in code will handle it

    # Ensure profile_photo, registered_face_photo, and face_descriptor columns can store full Base64 photos
    try:
        if dialect == 'postgresql':
            text_stmts = [
                "ALTER TABLE employees ALTER COLUMN profile_photo TYPE TEXT",
                "ALTER TABLE employees ALTER COLUMN registered_face_photo TYPE TEXT",
                "ALTER TABLE employees ALTER COLUMN face_descriptor TYPE TEXT",
                "ALTER TABLE users ALTER COLUMN profile_photo TYPE TEXT",
                "ALTER TABLE employee_master ALTER COLUMN registered_face_photo TYPE TEXT",
                "ALTER TABLE employee_master ALTER COLUMN face_descriptor TYPE TEXT",
                "ALTER TABLE attendance_photos ALTER COLUMN image_data TYPE TEXT",
                "ALTER TABLE attendance_photos ALTER COLUMN checkout_image_data TYPE TEXT",
            ]
            for stmt in text_stmts:
                try:
                    db.session.execute(text(stmt))
                    db.session.commit()
                except Exception:
                    db.session.rollback()
            logger.info("Migrated all photo and face descriptor columns to TEXT")
    except Exception as e:
        try:
            db.session.rollback()
        except Exception:
            pass
        logger.warning("Could not alter photo/descriptor columns to TEXT: %s", e)

    def _run_sql_script(db_session, sql_script: str) -> None:
        """Execute raw SQL statements safely across both PostgreSQL and SQLite."""
        for raw_stmt in sql_script.strip().split(";"):
            stmt = raw_stmt.strip()
            if stmt:
                db_session.execute(text(stmt))
        db_session.commit()

    # ── One-Time User & Master Reset for Fresh Biometric Registration ──────────────
    try:
        db.session.execute(text("CREATE TABLE IF NOT EXISTS system_migrations (migration_key VARCHAR(100) PRIMARY KEY, applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"))
        db.session.commit()
        has_reset = db.session.execute(text("SELECT 1 FROM system_migrations WHERE migration_key = 'biometric_reset_v1'")).scalar()
        if not has_reset:
            logger.info("ONE_TIME_BIOMETRIC_RESET: Resetting all employee registrations so everyone re-registers with camera...")
            _run_sql_script(db.session, """
                UPDATE departments SET head_employee_id = NULL;
                UPDATE employees SET manager_id = NULL;
                DELETE FROM employee_hospital_assignments;
                DELETE FROM employee_shift_assignments;
                DELETE FROM employee_salary_masters;
                DELETE FROM payslips;
                DELETE FROM leave_requests;
                DELETE FROM half_day_requests;
                DELETE FROM early_leave_requests;
                DELETE FROM shift_change_logs;
                DELETE FROM shift_change_requests;
                DELETE FROM attendance_photos;
                DELETE FROM attendance_logs;
                DELETE FROM attendance;
                DELETE FROM attendance_master_photos;
                DELETE FROM attendance_master;
                DELETE FROM gps_logs;
                DELETE FROM notifications;
                DELETE FROM login_history;
                DELETE FROM employees;
                DELETE FROM users WHERE role NOT IN ('super_admin');
                UPDATE employee_master 
                SET is_registered = FALSE, 
                    user_id = NULL, 
                    registered_at = NULL,
                    is_face_registered = FALSE,
                    registered_face_photo = NULL,
                    face_descriptor = NULL;
                INSERT INTO system_migrations (migration_key) VALUES ('biometric_reset_v1');
            """)
            logger.info("ONE_TIME_BIOMETRIC_RESET: Completed successfully. All employees must now register fresh with camera.")
    except Exception as reset_err:
        try:
            db.session.rollback()
        except Exception:
            pass
        logger.warning("ONE_TIME_BIOMETRIC_RESET failed or skipped: %s", reset_err)

    # ── Reset E-2606026 so Durvesh Parab can re-register freshly with camera ──
    try:
        has_reset_d = db.session.execute(text("SELECT 1 FROM system_migrations WHERE migration_key = 'reset_durvesh_v2'")).scalar()
        if not has_reset_d:
            logger.info("RESETTING REGISTRATION FOR E-2606026...")
            _run_sql_script(db.session, """
                UPDATE departments SET head_employee_id = NULL WHERE head_employee_id IN (SELECT id FROM employees WHERE employee_code = 'E-2606026');
                UPDATE employees SET manager_id = NULL WHERE manager_id IN (SELECT id FROM employees WHERE employee_code = 'E-2606026');
                DELETE FROM attendance_photos WHERE attendance_id IN (SELECT id FROM attendance WHERE employee_id IN (SELECT id FROM employees WHERE employee_code = 'E-2606026'));
                DELETE FROM attendance_logs WHERE employee_id IN (SELECT id FROM employees WHERE employee_code = 'E-2606026');
                DELETE FROM attendance WHERE employee_id IN (SELECT id FROM employees WHERE employee_code = 'E-2606026');
                DELETE FROM leave_requests WHERE employee_id IN (SELECT id FROM employees WHERE employee_code = 'E-2606026');
                DELETE FROM half_day_requests WHERE employee_id IN (SELECT id FROM employees WHERE employee_code = 'E-2606026');
                DELETE FROM early_leave_requests WHERE employee_id IN (SELECT id FROM employees WHERE employee_code = 'E-2606026');
                DELETE FROM shift_change_requests WHERE employee_id IN (SELECT id FROM employees WHERE employee_code = 'E-2606026');
                DELETE FROM employees WHERE employee_code = 'E-2606026';
                DELETE FROM users WHERE username = 'e2606026' OR email LIKE '%e2606026%';
                UPDATE employee_master 
                SET is_registered = FALSE, 
                    user_id = NULL, 
                    registered_at = NULL, 
                    is_face_registered = FALSE, 
                    registered_face_photo = NULL, 
                    face_descriptor = NULL 
                WHERE employee_code = 'E-2606026';
                INSERT INTO system_migrations (migration_key) VALUES ('reset_durvesh_v2');
            """)
            logger.info("Successfully reset registration for E-2606026.")
    except Exception as reset_e:
        try:
            db.session.rollback()
        except Exception:
            pass
        logger.warning("Could not reset registration for E-2606026: %s", reset_e)

    # ── Reset ALL registrations so everyone can register fresh ──
    try:
        has_reset_all = db.session.execute(text("SELECT 1 FROM system_migrations WHERE migration_key = 'reset_all_registered_employees_v2'")).scalar()
        if not has_reset_all:
            logger.info("RESETTING ALL REGISTERED EMPLOYEES FOR FRESH ENROLLMENT...")
            _run_sql_script(db.session, """
                UPDATE departments SET head_employee_id = NULL;
                UPDATE employees SET manager_id = NULL;
                
                DELETE FROM employee_hospital_assignments;
                DELETE FROM employee_shift_assignments;
                DELETE FROM shift_change_logs;
                DELETE FROM shift_change_requests;
                DELETE FROM payslips;
                DELETE FROM employee_salary_masters;
                DELETE FROM payroll_runs;
                DELETE FROM attendance_photos;
                DELETE FROM attendance_logs;
                DELETE FROM attendance;
                DELETE FROM gps_logs;
                DELETE FROM leave_requests;
                DELETE FROM half_day_requests;
                DELETE FROM early_leave_requests;
                DELETE FROM notifications;
                DELETE FROM login_history;
                DELETE FROM attendance_master_photos;
                DELETE FROM attendance_master;

                DELETE FROM employees;
                DELETE FROM users;

                UPDATE employee_master 
                SET is_registered = FALSE, 
                    user_id = NULL, 
                    registered_at = NULL, 
                    is_face_registered = FALSE, 
                    registered_face_photo = NULL, 
                    face_descriptor = NULL;

                INSERT INTO system_migrations (migration_key) VALUES ('reset_all_registered_employees_v2');
            """)
            logger.info("Successfully reset all registered employees. Everyone can now register fresh.")
    except Exception as reset_all_e:
        try:
            db.session.rollback()
        except Exception:
            pass
        logger.warning("Could not reset all registered employees: %s", reset_all_e)


def _auto_seed_hospitals(app: Flask) -> None:
    """Seed hospitals if not already present."""
    try:
        from app.models.hospital import Hospital  # noqa: PLC0415
        from app.extensions.database import db as _db  # noqa: PLC0415
        
        # Check if hospitals already exist
        if Hospital.query.count() > 0:
            app.logger.info("Hospitals already seeded — skipping.")
            return
        
        # Hospital data with default coordinates (can be updated later)
        hospitals_data = [
            {"name": "AIIMS Hospital (Gorakhpur)", "lat": 26.7606, "lng": 83.1849},
            {"name": "Akurdi Hospital", "lat": 18.6298, "lng": 73.8119},
            {"name": "Ameyash Hospital", "lat": 19.0176, "lng": 72.8479},
            {"name": "Bharatratna Dr.BabaSaheb Ambedkar Hospital", "lat": 19.0760, "lng": 72.8777},
            {"name": "Bhosari Hospital", "lat": 18.6510, "lng": 73.9125},
            {"name": "Claim Team", "lat": 0.0, "lng": 0.0},
            {"name": "Despande Hospital", "lat": 0.0, "lng": 0.0},
            {"name": "Dr. M L Dhavale Hospital", "lat": 18.9220, "lng": 72.8347},
            {"name": "Dr R.N. Cooper Muncipial General Hospital", "lat": 19.0176, "lng": 72.8479},
            {"name": "Hyderabad Omega Hospital (Jabalpur)", "lat": 23.1815, "lng": 79.9864},
            {"name": "Jijamata Hospital", "lat": 19.0576, "lng": 72.8295},
            {"name": "Jupiter Hospital (THANE)", "lat": 19.2183, "lng": 72.9781},
            {"name": "K B Bhaba Hospital-Bandra", "lat": 19.0596, "lng": 72.8295},
            {"name": "KEM Hospital", "lat": 19.0176, "lng": 72.8479},
            {"name": "Kolhapur Cancer Centre", "lat": 16.7050, "lng": 74.2433},
            {"name": "Krishna Hospital", "lat": 0.0, "lng": 0.0},
            {"name": "LDC Hospital", "lat": 19.1136, "lng": 72.8697},
            {"name": "M.W. Desai Hospital", "lat": 18.9626, "lng": 72.8266},
            {"name": "MT Agarwal Hospital (Mulund)", "lat": 19.1686, "lng": 72.9629},
            {"name": "Nair Hospital", "lat": 18.9626, "lng": 72.8266},
            {"name": "Nana Palkar (Parel)", "lat": 19.0176, "lng": 72.8479},
            {"name": "Nana Palkar Hospital(Santacruz)", "lat": 19.0876, "lng": 72.8479},
            {"name": "Nana Palkar Hospital(Thane)", "lat": 19.2183, "lng": 72.9781},
            {"name": "Peerless Hospital Guwahati", "lat": 26.1445, "lng": 91.7362},
            {"name": "Project Office", "lat": 0.0, "lng": 0.0},
            {"name": "Rajawadi Hospital", "lat": 19.1136, "lng": 72.8697},
            {"name": "Ranchi Cancer Hospital", "lat": 23.3441, "lng": 85.3096},
            {"name": "RST RCH Hospital", "lat": 19.0176, "lng": 72.8479},
            {"name": "Satyanand Hospital(Shahjahanpur)", "lat": 27.8817, "lng": 79.6040},
            {"name": "Shankarrao Masulka Eye Hospital", "lat": 18.5204, "lng": 73.8567},
            {"name": "Shantitol Shanghvi Eye Hospital", "lat": 19.0176, "lng": 72.8479},
            {"name": "Shatabdi Hospital", "lat": 19.1136, "lng": 72.8697},
            {"name": "Shree Ramkrishna Netralaya", "lat": 19.0176, "lng": 72.8479},
            {"name": "Shree Ramkrishna Netralaya (Thane)", "lat": 19.2183, "lng": 72.9781},
            {"name": "Shree Ramkrishna Netralaya(Vashi)", "lat": 19.0766, "lng": 72.9966},
            {"name": "Siddhagiri Hospital", "lat": 17.8299, "lng": 73.3149},
            {"name": "Sion Hospital", "lat": 19.0576, "lng": 72.8295},
            {"name": "SVD Sawarkar Hospital (Mulund)", "lat": 19.1686, "lng": 72.9629},
            {"name": "SVICCAR Hospital", "lat": 19.0176, "lng": 72.8479},
            {"name": "Swargadeo Sukafa Multi speciality Hospital", "lat": 26.1445, "lng": 91.7362},
            {"name": "Talera Hospital", "lat": 18.4386, "lng": 73.9144},
            {"name": "Thergoan Hospital", "lat": 18.5204, "lng": 73.8567},
            {"name": "Trauma Hospital", "lat": 0.0, "lng": 0.0},
            {"name": "V.N. Desai Hospital", "lat": 18.9626, "lng": 72.8266},
            {"name": "Walawatkar Hospital", "lat": 18.9220, "lng": 72.8347},
            {"name": "YCM Hospital(Pune)", "lat": 18.5204, "lng": 73.8567},
        ]
        
        for h_data in hospitals_data:
            hospital = Hospital(
                hospital_name=h_data["name"],
                latitude=h_data["lat"],
                longitude=h_data["lng"],
                is_active=True
            )
            _db.session.add(hospital)
        
        _db.session.commit()
        app.logger.info(f"✓ Auto-seeded {len(hospitals_data)} hospitals")
    except Exception as exc:
        app.logger.error("Auto-seed hospitals failed: %s", exc)
        try:
            from app.extensions.database import db  # noqa: PLC0415
            db.session.rollback()
        except Exception:
            pass


def _auto_seed_shifts(app: Flask) -> None:
    """Seed 25 shift timings. Uses UPSERT to replace old shifts with new ones."""
    try:
        from app.models.company import Shift  # noqa: PLC0415
        from app.extensions.database import db as _db  # noqa: PLC0415
        from sqlalchemy import and_
        
        # Define 25 shifts with timings
        shifts_data = [
            {"name": "06:00 AM to 03:00 PM", "code": "SHIFT_0600_1500", "start_time": "06:00", "end_time": "15:00", "is_night": False},
            {"name": "06:30 AM to 03:30 PM", "code": "SHIFT_0630_1530", "start_time": "06:30", "end_time": "15:30", "is_night": False},
            {"name": "07:00 AM to 04:00 PM", "code": "SHIFT_0700_1600", "start_time": "07:00", "end_time": "16:00", "is_night": False},
            {"name": "07:30 AM to 04:30 PM", "code": "SHIFT_0730_1630", "start_time": "07:30", "end_time": "16:30", "is_night": False},
            {"name": "08:00 AM to 05:00 PM", "code": "SHIFT_0800_1700", "start_time": "08:00", "end_time": "17:00", "is_night": False},
            {"name": "08:00 AM to 06:00 PM", "code": "SHIFT_0800_1800", "start_time": "08:00", "end_time": "18:00", "is_night": False},
            {"name": "08:30 AM to 05:30 PM", "code": "SHIFT_0830_1730", "start_time": "08:30", "end_time": "17:30", "is_night": False},
            {"name": "09:00 AM to 06:00 PM", "code": "SHIFT_0900_1800", "start_time": "09:00", "end_time": "18:00", "is_night": False},
            {"name": "09:30 AM to 06:30 PM", "code": "SHIFT_0930_1830", "start_time": "09:30", "end_time": "18:30", "is_night": False},
            {"name": "10:00 AM to 06:00 PM", "code": "SHIFT_1000_1800", "start_time": "10:00", "end_time": "18:00", "is_night": False},
            {"name": "10:00 AM to 07:00 PM", "code": "SHIFT_1000_1900", "start_time": "10:00", "end_time": "19:00", "is_night": False},
            {"name": "10:15 AM to 07:15 PM", "code": "SHIFT_1015_1915", "start_time": "10:15", "end_time": "19:15", "is_night": False},
            {"name": "10:30 AM to 07:30 PM", "code": "SHIFT_1030_1930", "start_time": "10:30", "end_time": "19:30", "is_night": False},
            {"name": "11:00 AM to 08:00 PM", "code": "SHIFT_1100_2000", "start_time": "11:00", "end_time": "20:00", "is_night": False},
            {"name": "11:30 AM to 08:30 PM", "code": "SHIFT_1130_2030", "start_time": "11:30", "end_time": "20:30", "is_night": False},
            {"name": "12:00 PM to 09:00 PM", "code": "SHIFT_1200_2100", "start_time": "12:00", "end_time": "21:00", "is_night": False},
            {"name": "12:30 PM to 09:30 PM", "code": "SHIFT_1230_2130", "start_time": "12:30", "end_time": "21:30", "is_night": False},
            {"name": "12:45 PM to 09:45 PM", "code": "SHIFT_1245_2145", "start_time": "12:45", "end_time": "21:45", "is_night": False},
            {"name": "01:00 PM to 10:00 PM", "code": "SHIFT_1300_2200", "start_time": "13:00", "end_time": "22:00", "is_night": False},
            {"name": "01:00 PM to 06:00 PM", "code": "SHIFT_1300_1800", "start_time": "13:00", "end_time": "18:00", "is_night": False},
            {"name": "07:00 PM to 04:00 AM", "code": "SHIFT_1900_0400", "start_time": "19:00", "end_time": "04:00", "is_night": True},
            {"name": "09:00 PM to 06:00 AM", "code": "SHIFT_2100_0600", "start_time": "21:00", "end_time": "06:00", "is_night": True},
            {"name": "10:00 PM to 06:00 AM", "code": "SHIFT_2200_0600", "start_time": "22:00", "end_time": "06:00", "is_night": True},
            {"name": "10:00 PM to 07:00 AM", "code": "SHIFT_2200_0700", "start_time": "22:00", "end_time": "07:00", "is_night": True},
            {"name": "10:30 PM to 07:30 AM", "code": "SHIFT_2230_0730", "start_time": "22:30", "end_time": "07:30", "is_night": True},
        ]
        
        from datetime import time as dt_time
        
        # UPSERT logic: for each shift, update if exists by code, else insert
        seeded_count = 0
        updated_count = 0
        
        for shift_data in shifts_data:
            start_h, start_m = map(int, shift_data["start_time"].split(":"))
            end_h, end_m = map(int, shift_data["end_time"].split(":"))
            
            # Check if shift exists by code
            existing = Shift.query.filter_by(code=shift_data["code"]).first()
            
            if existing:
                # Update existing shift
                existing.name = shift_data["name"]
                existing.start_time = dt_time(start_h, start_m)
                existing.end_time = dt_time(end_h, end_m)
                existing.is_night_shift = shift_data["is_night"]
                existing.is_active = True
                existing.grace_minutes = 10
                existing.break_minutes = 60
                existing.working_days = "Mon-Sun"
                _db.session.add(existing)
                updated_count += 1
            else:
                # Create new shift
                shift = Shift(
                    name=shift_data["name"],
                    code=shift_data["code"],
                    start_time=dt_time(start_h, start_m),
                    end_time=dt_time(end_h, end_m),
                    is_night_shift=shift_data["is_night"],
                    is_active=True,
                    grace_minutes=10,
                    break_minutes=60,
                    working_days="Mon-Sun"
                )
                _db.session.add(shift)
                seeded_count += 1
        
        _db.session.commit()
        
        total = Shift.query.count()
        app.logger.info(f"✓ Shift seeding complete: {seeded_count} new + {updated_count} updated = {total} total shifts")
    except Exception as exc:
        app.logger.error("Auto-seed shifts failed: %s", exc)
        try:
            from app.extensions.database import db  # noqa: PLC0415
            db.session.rollback()
        except Exception:
            pass


def _auto_seed_holidays(app: Flask) -> None:
    """Seed India/Maharashtra holidays for 2026."""
    try:
        from app.models.company_holiday import CompanyHoliday  # noqa: PLC0415
        from app.extensions.database import db as _hdb  # noqa: PLC0415
        from datetime import date  # noqa: PLC0415
        
        # Check if holidays already exist
        if CompanyHoliday.query.count() > 0:
            app.logger.info("✓ Holidays already seeded — skipping.")
            return
        
        holidays_data = [
            ("2026-01-26", "Republic Day", "National Holiday"),
            ("2026-02-19", "Chhatrapati Shivaji Maharaj Jayanti", "Regional Holiday"),
            ("2026-03-03", "Holi", "National Holiday"),
            ("2026-03-19", "Chaitra Sukladi", "Regional Holiday"),
            ("2026-05-01", "Maharashtra Day / Labour Day", "National Holiday"),
            ("2026-08-15", "Independence Day", "National Holiday"),
            ("2026-08-28", "Raksha Bandhan", "National Holiday"),
            ("2026-09-05", "Dahihandi", "Regional Holiday"),
            ("2026-09-14", "Ganesh Chaturthi", "Regional Holiday"),
            ("2026-10-02", "Mahatma Gandhi Jayanti", "National Holiday"),
            ("2026-10-20", "Dussehra / Vijayadashmi", "National Holiday"),
            ("2026-11-10", "Diwali-Padwa", "National Holiday"),
            ("2026-11-11", "Diwali-Bhaubij", "National Holiday"),
            ("2026-11-24", "Guru Nanak Jayanti", "National Holiday"),
            ("2026-12-25", "Christmas Day", "National Holiday"),
        ]
        
        count = 0
        for date_str, name, holiday_type in holidays_data:
            # Check if already exists
            existing = CompanyHoliday.query.filter_by(
                holiday_date=date_str,
                holiday_name=name
            ).first()
            
            if not existing:
                holiday = CompanyHoliday(
                    holiday_date=date.fromisoformat(date_str),
                    holiday_name=name,
                    holiday_type=holiday_type,
                )
                _hdb.session.add(holiday)
                count += 1
        
        _hdb.session.commit()
        total = CompanyHoliday.query.count()
        app.logger.info(f"✓ Auto-seeded {count} new holidays = {total} total")
    except Exception as exc:
        app.logger.error("Auto-seed holidays failed: %s", exc)
        try:
            from app.extensions.database import db  # noqa: PLC0415
            db.session.rollback()
        except Exception:
            pass


def _auto_seed_employees(app: Flask) -> None:
    """Seed EmployeeMaster if table is empty, and always seed leave types if missing."""
    # ── Seed leave types (always check, not just on first boot) ──────
    try:
        from app.models.leave import LeaveType  # noqa: PLC0415
        from app.extensions.database import db as _ltdb  # noqa: PLC0415
        
        # Try to count leave types
        try:
            count = LeaveType.query.count()
        except Exception as count_err:
            # If we get a column error, the migration hasn't run yet
            app.logger.warning("⚠️  Could not count leave types (column missing?): %s", count_err)
            app.logger.info("✓ Skipping leave type seeding — database not fully migrated yet")
            count = -1  # Force skip
        
        if count == 0:
            leave_defaults = [
                {"name": "Casual Leave",      "code": "CL",   "max_days_per_year": 12, "is_paid": True,  "color": "#3b82f6"},
                {"name": "Sick Leave",        "code": "SL",   "max_days_per_year": 12, "is_paid": True,  "color": "#ef4444", "requires_document": True},
                {"name": "Paid Leave",        "code": "PL",   "max_days_per_year": 15, "is_paid": True,  "color": "#10b981"},
                {"name": "Loss of Pay",       "code": "LOP",  "max_days_per_year": 30, "is_paid": False, "color": "#f59e0b"},
                {"name": "Comp Off",          "code": "CO", "max_days_per_year": 6,  "is_paid": True,  "color": "#8b5cf6"},
                {"name": "Maternity Leave",   "code": "ML",   "max_days_per_year": 180,"is_paid": True,  "color": "#ec4899"},
                {"name": "Paternity Leave",   "code": "PTL",  "max_days_per_year": 15, "is_paid": True,  "color": "#0891b2"},
                {"name": "Bereavement Leave", "code": "BL",   "max_days_per_year": 5,  "is_paid": True,  "color": "#6b7280"},
            ]
            for lt_data in leave_defaults:
                try:
                    if not LeaveType.query.filter_by(code=lt_data["code"]).first():
                        _ltdb.session.add(LeaveType(**lt_data))
                except Exception as add_err:
                    app.logger.warning("⚠️  Could not add leave type %s: %s", lt_data.get("code"), add_err)
                    continue
            
            try:
                _ltdb.session.commit()
                app.logger.info("Auto-seeded 8 leave types.")
            except Exception as commit_err:
                app.logger.warning("⚠️  Could not commit leave types: %s", commit_err)
                _ltdb.session.rollback()
    except Exception as exc:
        app.logger.warning("⚠️  Auto-seed leave types failed: %s", exc)
        try:
            from app.extensions.database import db  # noqa: PLC0415
            db.session.rollback()
        except Exception:
            pass

    # ── Seed employee master (sync with official 541 master dataset) ─────
    try:
        import csv, os
        from app.models.employee_master import EmployeeMaster  # noqa: PLC0415
        from app.extensions.database import db  # noqa: PLC0415

        csv_path = os.path.join(app.root_path, "..", "data", "real_employee_master_541.csv")
        csv_records = {}
        if os.path.exists(csv_path):
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    c = row.get("Employee Code")
                    if c:
                        csv_records[c.strip().upper()] = row

        if csv_records:
            existing = {m.employee_code.strip().upper(): m for m in EmployeeMaster.query.all()}
            added = 0
            for code, row in csv_records.items():
                if code not in existing:
                    m = EmployeeMaster(
                        employee_code=code,
                        employee_name=row.get("Employee Name") or f"Employee {code}",
                        department=row.get("Department") or "General",
                        designation=row.get("Designation") or "Staff",
                        working_location=row.get("Working Location") or "Head Office",
                        is_active=True,
                        is_registered=False
                    )
                    db.session.add(m)
                    added += 1

            # Prune extraneous records that are NOT part of the official 541 dataset
            extra_deleted = 0
            for code, m in existing.items():
                if code not in csv_records:
                    if not getattr(m, "is_registered", False) and not getattr(m, "user_id", None) and not getattr(m, "is_face_registered", False):
                        db.session.delete(m)
                        extra_deleted += 1
                    else:
                        m.is_active = False

            db.session.commit()
            total_active = EmployeeMaster.query.filter_by(is_active=True).count()
            app.logger.info("✓ Synced official 541 master records: %d added, %d extra pruned. Total active: %d", added, extra_deleted, total_active)

    except Exception as exc:
        app.logger.error("Auto-seed employees failed: %s", exc)
        try:
            from app.extensions.database import db  # noqa: PLC0415
            db.session.rollback()
        except Exception:
            pass

    # ── Also seed leave types if missing ────────────────────────────
    try:
        from app.models.leave import LeaveType  # noqa: PLC0415
        from app.extensions.database import db as _db2  # noqa: PLC0415
        if LeaveType.query.count() == 0:
            leave_defaults = [
                {"name": "Casual Leave",      "code": "CL",   "max_days_per_year": 12, "is_paid": True,  "color": "#3b82f6"},
                {"name": "Sick Leave",        "code": "SL",   "max_days_per_year": 12, "is_paid": True,  "color": "#ef4444", "requires_document": True},
                {"name": "Paid Leave",        "code": "PL",   "max_days_per_year": 15, "is_paid": True,  "color": "#10b981"},
                {"name": "Loss of Pay",       "code": "LOP",  "max_days_per_year": 30, "is_paid": False, "color": "#f59e0b"},
                {"name": "Comp Off",          "code": "CO", "max_days_per_year": 6,  "is_paid": True,  "color": "#8b5cf6"},
                {"name": "Maternity Leave",   "code": "ML",   "max_days_per_year": 180,"is_paid": True,  "color": "#ec4899"},
                {"name": "Paternity Leave",   "code": "PTL",  "max_days_per_year": 15, "is_paid": True,  "color": "#0891b2"},
                {"name": "Bereavement Leave", "code": "BL",   "max_days_per_year": 5,  "is_paid": True,  "color": "#6b7280"},
            ]
            for lt_data in leave_defaults:
                if not LeaveType.query.filter_by(code=lt_data["code"]).first():
                    _db2.session.add(LeaveType(**lt_data))
            _db2.session.commit()
            app.logger.info("Auto-seeded %d leave types.", len(leave_defaults))
    except Exception as exc:
        app.logger.error("Auto-seed leave types failed: %s", exc)
        try:
            from app.extensions.database import db  # noqa: PLC0415
            db.session.rollback()
        except Exception:
            pass


def _ensure_super_admin_roles(app: Flask) -> None:
    """
    Production-grade startup routine to ensure E-2512012 and E-2603025 always have super_admin role.
    
    This function:
    - Runs automatically during app startup (in _auto_create_tables)
    - Is idempotent (safe to run multiple times)
    - Uses SQLAlchemy ORM only (no raw SQL)
    - Searches for users by EMPLOYEE_CODE (through Employee table), not username
    - Creates users if they don't exist
    - Updates roles if users exist with wrong role
    - Uses EmployeeMaster data when creating users
    - Logs all actions for debugging
    - Never prevents app from starting
    
    Why this works on Render Free (no shell access):
    - Runs during normal app initialization (gunicorn startup)
    - No manual intervention needed
    - Automatic on every deployment
    - Works even if Render Free doesn't support shell access
    
    KEY FIX: Users are found via Employee.employee_code → User relationship,
    NOT by username (which is often a placeholder email-based value).
    """
    app.logger.info("ENSURE_ADMIN: ▶ Starting admin role verification routine...")
    
    try:
        from app.models.user import User  # noqa: PLC0415
        from app.models.employee import Employee  # noqa: PLC0415
        from app.models.employee_master import EmployeeMaster  # noqa: PLC0415
        from app.extensions.database import db  # noqa: PLC0415
        
        # Employee codes to ensure as super_admin (E-2512012 is a normal employee)
        target_codes = [
            {'code': 'E-2603025', 'fallback_name': 'Raj Sanjay Shukla'},
            {'code': 'E-2606026', 'fallback_name': 'Durvesh Parab'},
        ]
        
        made_changes = False
        
        for target in target_codes:
            emp_code = target['code']
            fallback_name = target['fallback_name']
            
            app.logger.info(f"ENSURE_ADMIN: Checking employee code {emp_code}...")
            
            # Step 1: Find user by EMPLOYEE_CODE through Employee table
            user = (
                db.session.query(User)
                .join(Employee, Employee.user_id == User.id)
                .filter(
                    Employee.employee_code == emp_code,
                    Employee.is_deleted == False,
                    User.is_deleted == False,
                )
                .first()
            )
            
            if user is None:
                # Auto-provision super-admin user and employee record linked to EmployeeMaster
                from datetime import date as _dt_date  # noqa: PLC0415
                m = EmployeeMaster.query.filter_by(employee_code=emp_code).first()
                name_parts = (m.employee_name if m and m.employee_name else fallback_name).strip().split(" ", 1)
                f_name = name_parts[0]
                l_name = name_parts[1] if len(name_parts) > 1 else "."
                clean_username = emp_code.lower().replace("-", "")
                clean_email = f"{clean_username}@cscreativesolutions.com"

                user = User.query.filter((User.username == clean_username) | (User.email == clean_email)).first()
                if not user:
                    user = User(
                        email=clean_email,
                        username=clean_username,
                        first_name=f_name,
                        last_name=l_name,
                        role="super_admin",
                        status="active",
                        email_verified=True,
                    )
                    user.set_password(os.getenv("KIOSK_TERMINAL_PASSWORD", "CEOVIKASDESHMUKH@2013"))
                    db.session.add(user)
                    db.session.flush()
                else:
                    user.role = "super_admin"
                    user.is_deleted = False

                emp = Employee.query.filter_by(employee_code=emp_code).first()
                if not emp:
                    emp = Employee(
                        user_id=user.id,
                        employee_code=emp_code,
                        department=m.department if m and m.department else "IT Software",
                        designation=m.designation if m and m.designation else "Senior software executive",
                        branch=m.working_location if m and m.working_location else "Head Office",
                        date_joined=_dt_date.today(),
                    )
                    db.session.add(emp)
                    db.session.flush()
                else:
                    emp.user_id = user.id
                    emp.is_deleted = False

                if m:
                    m.is_registered = True
                    m.user_id = user.id

                made_changes = True
                app.logger.info(f"ENSURE_ADMIN: ✅ Auto-provisioned {user.username} (code {emp_code}) with role=super_admin")
            else:
                # User exists - check role
                current_role = user.role
                app.logger.info(f"ENSURE_ADMIN: Found user {user.username} (ID={user.id}) for employee code {emp_code}, current role='{current_role}'")
                
                if current_role != 'super_admin':
                    app.logger.info(f"ENSURE_ADMIN: Updating {user.username} role from '{current_role}' to 'super_admin'...")
                    user.role = 'super_admin'
                    db.session.add(user)
                    app.logger.info(f"ENSURE_ADMIN: ✅ User {user.username} role updated to super_admin")
                    made_changes = True
                else:
                    app.logger.info(f"ENSURE_ADMIN: ✓ {user.username} (code {emp_code}) already has role=super_admin (no change needed)")
        
        # Step 2: Commit all changes atomically
        if made_changes:
            try:
                db.session.commit()
                app.logger.info("ENSURE_ADMIN: ✅ All database changes committed successfully")
            except Exception as commit_err:
                app.logger.error(f"ENSURE_ADMIN: ❌ Database commit failed: {commit_err}")
                db.session.rollback()
                app.logger.warning("ENSURE_ADMIN: Changes rolled back due to commit failure")
                # Don't re-raise - app must start even if admin role setup fails
                return
        else:
            app.logger.info("ENSURE_ADMIN: ✓ No changes needed - both users have correct roles")
        
        # Step 3: Final verification
        app.logger.info("ENSURE_ADMIN: ▼ Final verification...")
        for target in target_codes:
            emp_code = target['code']
            final_user = (
                db.session.query(User)
                .join(Employee, Employee.user_id == User.id)
                .filter(
                    Employee.employee_code == emp_code,
                    Employee.is_deleted == False,
                    User.is_deleted == False,
                )
                .first()
            )
            if final_user:
                status = "✅" if final_user.role == 'super_admin' else "❌"
                app.logger.info(f"ENSURE_ADMIN: {status} {final_user.username} (code {emp_code}): role={final_user.role}")
            else:
                app.logger.info(f"ENSURE_ADMIN: ℹ️ Code {emp_code}: registration pending")
        
        app.logger.info("ENSURE_ADMIN: ✅ Routine completed successfully")
    
    except Exception as outer_exc:
        # Log error but don't prevent app startup
        app.logger.error(f"ENSURE_ADMIN: ❌ Routine failed with exception: {outer_exc}")
        import traceback  # noqa: PLC0415
        app.logger.error(f"ENSURE_ADMIN: Traceback:\n{traceback.format_exc()}")
        
        # Attempt rollback
        try:
            from app.extensions.database import db  # noqa: PLC0415
            db.session.rollback()
            app.logger.info("ENSURE_ADMIN: Rolled back any pending changes")
        except Exception as rollback_err:
            app.logger.warning(f"ENSURE_ADMIN: Rollback also failed: {rollback_err}")
        
        app.logger.warning("ENSURE_ADMIN: ⚠️  Continuing app startup despite routine failure")


def _ensure_comp_off_leavetype(app: Flask) -> None:
    """
    Ensure Comp Off (CO) leave type exists in development database.
    In production mode, initial reference data is seeded via migration scripts.
    """
    import os  # noqa: PLC0415
    env_name = app.config.get("ENV") or os.environ.get("FLASK_ENV")
    if env_name == "production":
        return

    try:
        with app.app_context():
            from app.extensions.database import db  # noqa: PLC0415
            from app.models.leave import LeaveType  # noqa: PLC0415
            
            # STEP 1: Check if "Comp Off" exists (by name) - this is the UPSERT key
            try:
                comp_off = LeaveType.query.filter_by(name='Comp Off').first()
            except Exception as query_err:
                app.logger.warning(f"⚠️  Query for 'Comp Off' by name failed: {query_err}")
                return
            
            # STEP 2: If "Comp Off" exists, ensure code is 'CO' and is_active=True
            if comp_off:
                app.logger.info(f"✓ Found 'Comp Off' record (id={comp_off.id}, current code='{comp_off.code}')")
                
                need_update = False
                if comp_off.code != 'CO':
                    app.logger.info(f"  → Updating code from '{comp_off.code}' to 'CO'")
                    comp_off.code = 'CO'
                    need_update = True
                
                if not comp_off.is_active:
                    app.logger.info(f"  → Activating (is_active was False)")
                    comp_off.is_active = True
                    need_update = True
                
                if need_update:
                    try:
                        db.session.add(comp_off)
                        db.session.commit()
                        app.logger.info(f"✅ Updated 'Comp Off' record: code='CO', is_active=True")
                    except Exception as update_err:
                        app.logger.error(f"❌ Failed to update 'Comp Off': {update_err}")
                        try:
                            db.session.rollback()
                        except Exception:
                            pass
                else:
                    app.logger.info(f"✓ 'Comp Off' record already correct (code='CO', is_active=True)")
                
                return  # DONE - we have Comp Off with code CO
            
            # STEP 3: "Comp Off" doesn't exist - try to create it
            # This should be rare (only on fresh databases), but is the fallback
            app.logger.info("ℹ️  'Comp Off' record not found. Creating new one...")
            try:
                co = LeaveType(
                    name='Comp Off',
                    code='CO',
                    max_days_per_year=6,
                    is_paid=True,
                    requires_document=False,
                    color='#8b5cf6',
                    is_active=True,
                )
                db.session.add(co)
                db.session.commit()
                app.logger.info(f"✅ Created 'Comp Off' (CO) record: id={co.id}")
            except Exception as create_err:
                app.logger.error(f"❌ Failed to create 'Comp Off': {create_err}")
                try:
                    db.session.rollback()
                except Exception:
                    pass
    
    except Exception as e:
        app.logger.error(f"❌ _ensure_comp_off_leavetype exception: {e}")
        try:
            from app.extensions.database import db  # noqa: PLC0415
            db.session.rollback()
        except Exception:
            pass
