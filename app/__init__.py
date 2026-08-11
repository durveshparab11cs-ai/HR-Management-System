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

    # ── 3. Extensions ────────────────────────────────────────────────
    _init_extensions(app)

    # ── 4. Middleware ────────────────────────────────────────────────
    from app.middleware import register_middleware  # noqa: PLC0415
    register_middleware(app)

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


def _register_request_handlers(app: Flask) -> None:
    """
    Register global request handlers for admin user redirects and permissions.

    - Redirect admin/super_admin users from /dashboard/* to /admin/
    - Enforce dashboard access control
    """
    from flask import request, redirect, url_for  # noqa: PLC0415
    from flask_login import current_user  # noqa: PLC0415

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
    Create all DB tables on first boot and auto-seed employee master data.
    
    NUCLEAR MODE: If columns are missing, DROP and RECREATE the employee table
    to match the current model definition.
    """
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
                    
                    db.session.execute(create_sql)
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

            # STEP 2: Check if columns exist - if missing, DROP and recreate tables
            try:
                insp = inspect(db.engine)
                required_cols = ['shift_start_time', 'shift_end_time', 'is_flexible_shift', 'required_working_hours']
                emp_cols = insp.get_columns('employees')
                existing_cols = [c.name for c in emp_cols]
                
                missing_cols = [col for col in required_cols if col not in existing_cols]
                if missing_cols:
                    app.logger.warning("⚠️  Missing columns in employees: %s", missing_cols)
                    app.logger.warning("🔥 NUCLEAR MODE: Dropping and recreating employees table...")
                    
                    try:
                        dialect = db.engine.dialect.name
                        if dialect == 'postgresql':
                            db.session.execute(text('DROP TABLE IF EXISTS employees CASCADE'))
                        else:
                            db.session.execute(text('DROP TABLE IF EXISTS employees'))
                        db.session.commit()
                        app.logger.info("✓ Dropped old employees table")
                        
                        db.create_all()
                        app.logger.info("✓ Recreated employees table with new schema")
                    except Exception as drop_err:
                        app.logger.warning("⚠️  Could not drop employees table: %s", drop_err)
                        try:
                            db.session.rollback()
                        except Exception:
                            pass
                
                # Also check attendance_photos for checkout_image_data
                try:
                    photo_cols_list = insp.get_columns('attendance_photos')
                    photo_cols = [c.name for c in photo_cols_list]
                    if 'checkout_image_data' not in photo_cols:
                        app.logger.warning("⚠️  Missing checkout_image_data in attendance_photos")
                        app.logger.warning("🔥 NUCLEAR MODE: Dropping and recreating attendance_photos table...")
                        try:
                            dialect = db.engine.dialect.name
                            if dialect == 'postgresql':
                                db.session.execute(text('DROP TABLE IF EXISTS attendance_photos CASCADE'))
                            else:
                                db.session.execute(text('DROP TABLE IF EXISTS attendance_photos'))
                            db.session.commit()
                            app.logger.info("✓ Dropped old attendance_photos table")
                            
                            db.create_all()
                            app.logger.info("✓ Recreated attendance_photos table with new schema")
                        except Exception as photo_drop_err:
                            app.logger.warning("⚠️  Could not drop attendance_photos table: %s", photo_drop_err)
                            try:
                                db.session.rollback()
                            except Exception:
                                pass
                except Exception as photo_check_err:
                    app.logger.warning("⚠️  Could not check attendance_photos columns: %s", photo_check_err)
                    
            except Exception as exc:
                app.logger.warning("⚠️  Column check failed: %s", exc)

            # STEP 3: Add any still-missing columns
            try:
                _migrate_add_columns(db)
                app.logger.info("✓ Step 3: _migrate_add_columns()")
            except Exception as exc:
                app.logger.warning("⚠️  Step 3: _migrate_add_columns() failed: %s", exc)

            # STEP 4: Seed employees
            try:
                _auto_seed_employees(app)
                app.logger.info("✓ Step 4: _auto_seed_employees()")
            except Exception as exc:
                app.logger.warning("⚠️  Step 4: _auto_seed_employees() failed: %s", exc)
            
            # STEP 4.3: Seed hospitals
            try:
                _auto_seed_hospitals(app)
                app.logger.info("✓ Step 4.3: _auto_seed_hospitals()")
            except Exception as exc:
                app.logger.warning("⚠️  Step 4.3: _auto_seed_hospitals() failed: %s", exc)
            
            # STEP 4.5: Seed shifts
            try:
                _auto_seed_shifts(app)
                app.logger.info("✓ Step 4.5: _auto_seed_shifts()")
            except Exception as exc:
                app.logger.warning("⚠️  Step 4.5: _auto_seed_shifts() failed: %s", exc)

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
        ('employee', 'hospital_id', 'hospital_id INTEGER'),
        ('employee', 'current_shift', 'current_shift VARCHAR(50)'),
        ('employee', 'shift_start_time', 'shift_start_time VARCHAR(20)'),
        ('employee', 'shift_end_time', 'shift_end_time VARCHAR(20)'),
        ('employee', 'is_flexible_shift', 'is_flexible_shift INTEGER'),
        ('employee', 'required_working_hours', 'required_working_hours INTEGER'),
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

    # ── Seed employee master (only if empty) ─────────────────────────
    try:
        from app.models.employee_master import EmployeeMaster  # noqa: PLC0415
        from app.extensions.database import db  # noqa: PLC0415

        if EmployeeMaster.query.count() > 0:
            app.logger.info("employee_master already seeded — skipping.")
            return

        employees = [
            ("E-2603028","Aastha Vishwakarma"),("E-2405029","Abhinay Tiwari"),
            ("E-2506034","Akash Dubey"),("E-2503014","Aman Singh"),
            ("E-2407001","Prabhakar Sharma"),("E-2603029","Preeti Singh"),
            ("E-2509001","Ravendra Yadav"),("E-2501002","Ritik Chaudhari"),
            ("E-2406013","Shewani Tej Prakash Srivastava"),("E-2503007","Sunidhi Rao"),
            ("E-2502012","Surendra Gond"),("E-2511018","Rugvedi Kshitij Badadare"),
            ("E-2605029","Chanchal Patil"),("E-2601005","Harish Kumar"),
            ("E-2407010","Naresh Kumar"),("E-2407025","Priyanshu Singh"),
            ("E-2408012","Rajesh Kumar"),("E-2407008","Siddhi Raghunath Sawant"),
            ("E-2605037","Samiksha Rokade"),("E-2604040","Ramkrushna Supekar"),
            ("E-2403001","Ajay Ramesh Ratnottar"),("E-2408028","Akshay Dinesh Wagh"),
            ("E-2606057","Atharva Jadhav"),("E-2603007","Bhavesh Dattaram Sawant"),
            ("E-2604028","Diksha Sunil Bhat"),("E-2604030","Diksha Supadu Mahale"),
            ("E-2601020","Divesh Deepak Palkar"),("E-2505014","Divya Masane"),
            ("E-2607005","Himanshu Ajay Meher"),("E-2412009","Jyoti Kishanmurari Gupta"),
            ("E-2606016","Manasi Mahadik"),("E-2508007","Nikhil Chandivde"),
            ("E-2604029","Nikita Sunil Thorat"),("E-2603034","Nilam Narayan Shigwan"),
            ("E-2603037","Pratiksha Suresh Bhalerao"),("E-2308016","Rahul Parshuram Nagotkar"),
            ("E-2512018","Rajkumar Singh"),("E-2511014","Revati Vinod Shinde"),
            ("E-2306030","Ritu Raju Ghankutkar"),("E-2411018","Rohan Khandre"),
            ("E-2508008","Sairaj Dinesh Mavle"),("E-2606050","Sakshi Jadyal"),
            ("E-2606045","Sahil Dhawale"),("E-2604027","Sanskruti Sunil Shinde"),
            ("E-2505035","Shantanu Santosh Pisal"),("E-2603035","Sheetal Vishwakarma"),
            ("E-2605038","Shravan Pandurang Shegaji"),("E-2407009","Shravasti Santosh Padelkar"),
            ("E-2510022","Shruti Kamble"),("E-2305020","Shubham Sanjay Pednekar"),
            ("E-2508005","Sneha Santosh Darpe"),("E-2601028","Soham Balkrishna Munj"),
            ("E-2607004","Sujal Pawar"),("E-2606034","Toshvi Dhanu"),
            ("E-2210537","Vaishnavi Mali"),("E-2607010","Vipin Sahani"),
            ("E-2605023","Harish Patil"),("E-2401011","Rutik Dhanjay Mhatre"),
            ("E-2605025","Aditya Misal"),("E-2602013","Ashvini Gajanan Wanare"),
            ("E-2503009","Diksha Bodake"),("E-2511005","Dr. Nandini Omkar Nade"),
            ("E-2601006","Princekumar Umeshkumar Yadav"),("E-2601011","Sumit Bharat Davda"),
            ("E-2405002","Tejal Haresh Nevrekar"),("E-2307012","Vivek Ajay Sawant"),
            ("E-2504006","Aditi Sahu"),("E-2504010","Amit Barman"),
            ("E-2606008","Anuj Barman"),("E-2605007","Anurag Prajapati"),
            ("E-2505033","Palak Rajput"),("E-2605006","Prince Mishra"),
            ("E-2606017","Sapna Singh"),("E-2606027","Sanjay Patel"),
            ("E-2404001","Shivesh Kumar Tiwari"),("E-2504024","Shreya Sonkar"),
            ("E-2606028","Tarun Parste"),("E-2605008","Vivek Tiwari"),
            ("E-2603020","Akshata Mane"),("E-2105113","Mahendra Mestry"),
            ("E-2504016","Radhey Govind pingate"),("E-2403016","Shivani Bhimrao Kamble"),
            ("E-2507008","Tanisha Milind Pawar"),("E-2605016","Aayush Puradkar"),
            ("E-2606024","Aanchal Rajkumar Pal"),("E-2606048","Ajay Kumar"),
            ("E-2606015","Anjali Wankar"),("E-2602004","Bhavana Vikas Zende"),
            ("E-2606014","Chenta Maru"),("E-2511001","Chetna Anant Rambade"),
            ("E-2603031","Divya Arun Manchekar"),("E-2606047","Kunal Shelar"),
            ("E-2607003","Janhvi Shigwan"),("E-2606023","Jyoti Chauhan"),
            ("E-2607012","Nilesh Gavkar"),("E-2607009","Nikhil Malhar"),
            ("E-2606052","Neha Sorkade"),("E-2606030","Prachi Diwale"),
            ("E-2606043","Prachi Dinda"),("E-2606010","Pooja Ram Naresh Jaiswar"),
            ("E-2512006","Prachi Sanjay Nachare"),("E-2606020","Pratik Sonavane"),
            ("E-2604031","Purva Mahesh Shedge"),("E-2606029","Rohan Raju Thakur"),
            ("E-2205031","Rahul Dattaram Bhosale"),("E-2606025","Rishabh Mishra"),
            ("E-2601016","Sahil Raghunath Kudkar"),("E-2310009","Sakshi Balkrishna Jadhav"),
            ("E-2606012","Samruddhi Santosh Arekar"),("E-2510001","Sanika kadam"),
            ("E-2606044","Sanket Kamble"),("E-2011065","Shilpa Chavan"),
            ("E-2605009","Varsha Bule"),("E-2504012","Aditya Suresh Gurav"),
            ("E-2305010","Anuradha Maruti Kurade"),("E-2407024","Kartik Ashok Wadar"),
            ("E-2606060","Pratik Gavali"),("E-2112241","Siddhesh Dinesh Vichare"),
            ("E-2605033","Swaroop Jadhav"),("E-2605034","Yash Dalvi"),
            ("E-2603010","Kaushik Santosh Mahadik"),("E-2412005","Samruddhi Manoj jadhav"),
            ("E-2604036","Ravi Indraraj Diwakar"),("E-2507012","Pratiksha Prakash Tapase"),
            ("E-2503001","Akshata Satish Salve"),("E-2406014","Anjali Yashawant Gawade"),
            ("E-2605028","Aryan Gangurde"),("E-2604016","Dipali Ganesh Lad"),
            ("E-2308010","Komal Dilip Singh"),("E-2303011","Omkar Dhondiba Manere"),
            ("E-2606001","Nashra Shaikh"),("E-2308002","Rahul Ramesh Masaye"),
            ("E-2503017","Sahil Dipak Shirke"),("E-2606002","Sahil Ramakant Mhetar"),
            ("E-2511030","Samiksha Mahendra Pawar"),("E-2510003","Shalini Gupta"),
            ("E-2507001","Sujal Sanjay Dubey"),("E-2607001","Aryan Phatak"),
            ("E-2606054","Suyash Patil"),("E-2606009","Rishkiesh Khandizod"),
            ("E-2606039","Siddhesh Wateka"),("E-2603038","Ravina Monoj Tambe"),
            ("E-2504018","Pratiksha Dhondiram Dhebe"),("E-2409010","Nitesh Maurya"),
            ("E-2605005","Birik Sangma"),("E-2008034","Dhaval Dandge"),
            ("E-2104059","Jaya Devi"),("E-2605003","Karan Sarmah"),
            ("E-2604043","Pragyan Jyoti Baruah"),("E-2606005","Aditya Mayekar"),
            ("E-2512020","Afroze Alim Baig"),("E-2510030","Akash Maitri"),
            ("E-2203011","Akshay Darsharth Ghadi"),("E-2606053","Akshay Dhotre"),
            ("E-2412018","Aman Yogendra Pandey"),("E-2412019","Aman Kumar Singh"),
            ("E-2606007","Ankit Dineshchandra Vaishya"),("E-2607008","Anil Saini"),
            ("E-2605032","Atharva Bhosale"),("E-2606003","Aryan Devrendra"),
            ("E-2102029","Darshan Shah"),("E-2603004","Dhrup Mukesh Jain"),
            ("E-2606022","Disha Shobhnath Maurya"),("E-2605030","Dhrumil Jadhav"),
            ("E-2606056","Devika Kajeri"),("E-2601032","Dr. Mayuri Komredivar"),
            ("E-2606026","Durvesh Parab"),("E-2203114","Ekta Sunil More"),
            ("E-2606059","Gaytari Khalde"),("E-2505029","Harsh Ganesh Katukam"),
            ("E-2401006","Harshala Amol kadam"),("E-2410007","Jindnyasa R Chaudhari"),
            ("E-2506027","Kajol Damodar Nachanekar"),("E-2606021","Kedar Prashant Sangvekar"),
            ("E-2601015","Komal Rokade"),("E-2606046","Kritika Pangle"),
            ("E-2606058","Krutika Jadhav"),("E-1901044","Manisha Sudhakar Palve"),
            ("E-2606051","Manali Shelke"),("E-2505010","Maliha Salimuddin Shaikh"),
            ("E-2607014","Mitesh Sane"),("E-2604038","Moneswar Rabha"),
            ("E-2606038","Muskaan Singh"),("E-2601013","Neha Dhiraj Babariya"),
            ("E-2601002","Nidhi Avinash Kanki"),("E-2602011","Omkar Satyawan Amberkar"),
            ("E-2307007","Pallavi Mangesh Mali"),("E-2606061","Parth Pande"),
            ("E-2607007","Punam Tushar Lavale"),("E-2301009","Pramod Balaram Ghare"),
            ("E-1507005","Prasad Morje"),("E-2601004","Pratik Dinkar Mohite"),
            ("E-2512012","Pratik Prakash Sagvekar"),("E-2602023","Priyanka Krishana Dasare"),
            ("E-2603025","Raj Sanjay Shukla"),("E-2510025","Riddhi Namye"),
            ("E-2606013","Ritu Singh"),("E-2604046","Rohit Salunke"),
            ("E-2011069","Rutuja Suresh Pawar"),("E-2506004","Rutuja Vilas Gaikwad"),
            ("E-2507013","Sakshi Anil Yeram"),("E-2606032","Sakshi Shedge"),
            ("E-2606018","Shakshat Chavan"),("E-2307011","Sampada Arvind Thakur"),
            ("E-2101013","Sanam Desai"),("E-2312031","Shifa Qureshi"),
            ("E-2506011","Shraddha Bharat Yadav"),("E-2506028","Shravani Sanjay Telgade"),
            ("E-2405001","Siddhesh Gautam Kadam"),("E-2601017","Siddhi shantaram Devrukhkar"),
            ("E-2601003","Sneha Jagdish Solanki"),("E-2212009","Sneha Rahul Sonavane"),
            ("E-2506010","Srushti Mahesh Ghadi"),("E-2505001","Sudha Ravi"),
            ("E-2601021","Swaraj Sandesh Kalibag"),("E-2510016","Tejas Ashok Jadhav"),
            ("E-2010044","Tulshidas Bhosale"),("E-1304001","Umesh Pradeep Devare"),
            ("E-2604017","Vaishnavi Pardipkumar Sarjine"),("E-2202079","Vandana Gopal Rathod"),
            ("E-2501011","Vijay Shankar Manjare"),("E-2212022","Ramdas Mahadu Lande"),
            ("E-2205027","Shubhali Rajendra Gamare"),("E-2511009","Aman Raj"),
            ("E-2501007","Ankita Kumari"),("E-2602002","Ashish Kumar Bhagat"),
            ("E-2602031","Ashu Ankita Khalkho"),("E-2603013","Chintu Kumar"),
            ("E-2602022","Kamlesh Kumar Kesri"),("E-2501009","Kunal Kumar"),
            ("E-2601031","Lovely Kumari"),("E-2408004","Poonam Kumari"),
            ("E-2605022","Pradeep Baitha"),("E-2602003","Pratik Raj"),
            ("E-2511012","Rohit Mahto"),("E-2602027","Sachin Kumar Prajapati"),
            ("E-2601019","Saket Kumar"),("E-2502008","Sintu Kumar Mandal"),
            ("E-2602012","Tanu Kumari"),("E-2501006","Umesh Kumar Goswami"),
            ("E-2408025","Anjali Humane"),("E-2212003","Buddhesh Drugsing Gharghumar"),
            ("E-2505028","Dipanshu Shekhar gadikar"),("E-2407016","Khushal Nandlal Mohadikar"),
            ("E-2404008","Minal Govinda umredkar"),("E-2404006","Mitali Manoj Misar"),
            ("E-2403005","Nandini Chaoube"),("E-1904051","Priya yeole"),
            ("E-2200628","Dr. Purnika Nitin Shrivasatva"),("E-2205040","Ritali Pranay Wanjari"),
            ("E-2506033","Sneha Rajat Khadse"),("E-2503004","Sonu Dnyaneshwar Mundle"),
            ("E-2112242","Sushant Sudhir Gamare"),("E-1803023","Sushma Rehepade"),
            ("E-2310001","Vaishnavi Viajay Dhande"),("E-2502002","Washish Gulabrao Saeaithul"),
            ("E-2412016","Abhishek"),("E-2408007","Ranjeet Hanwant"),
            ("E-2605026","Preeti Acharya"),("E-2606055","Sudhir Shendage"),
            ("E-2409020","Warke Vaibhav Nagsen"),("E-2601027","Kumari Nidhi Yadav"),
            ("E-2603006","Archana Upadhyay"),("E-2603016","Kaushal Sudir Gurav"),
            ("E-2508019","Nikhil Satish Harale"),("E-2603018","Tanvi Santosh Patil"),
            ("E-2607006","Balkrushna Laxman Kawle"),("E-2604014","Rutuja Dattatray Mane"),
            ("E-2512023","Priti Yadav"),("E-2407020","Trupti Ramchandra Gotad"),
            ("E-2602030","Tanuja Bhalchandra Gogawale"),("E-2411008","Sakshi Appaso Yadav"),
            ("E-2410017","Shubham Ashok Kamble"),("E-2607011","Armeti Anil Kumar Dnyaneshwar"),
            ("E-2605020","Archana Chauhan"),("E-2601029","Aryan Prakash Yadav"),
            ("E-2603024","Devesh Umesh Bhosle"),("E-1801019","Nilesh Pawar"),
            ("E-2603003","Payal Bibhishan Khandagale"),("E-2604019","Raj Jyotiram Mane"),
            ("E-1801020","Sandeep Jadhav"),("E-2307014","Shraddha Sanjay Pol"),
            ("E-2607013","Shruti Kasar"),("E-2603005","Suknya Sunil Surve"),
            ("E-2603032","Tanmay Sushil Kadam"),("E-1810036","Tushar Chandrakant Amkar"),
            ("E-2411003","Yash Anil Mane"),("E-2401002","Omkar Kale"),
            ("E-2605011","A. Parthsarthii"),("E-2210516","Adimoolam Sai"),
            ("E-2506026","Arun Kumar"),("E-2606004","B. Janardhan Gowda"),
            ("E-2605017","C. Bharath Kumar"),("E-2502004","Chintam Sireesha"),
            ("E-2605021","C. Darvin"),("E-2604035","Dileep K. Yadav"),
            ("E-2601012","Dr. Prathyusha Narasa Reddy Gare"),("E-2503005","H.V. Naveen Kumar"),
            ("E-2511019","K Sasikumar"),("E-2210518","Kadimella Anilkumar"),
            ("E-2503003","Kalluru Bhuvaneshwari"),("E-2605014","Kandula Poojitha"),
            ("E-2602032","Maniru Gayatri"),("E-2212015","Motupalli Nagendra babu"),
            ("E-2605001","Mounika Polamareddy"),("E-2512004","N J K P Sai Teja"),
            ("E-2308007","N.Hemeswari"),("E-2512009","Naga Shankar Banne"),
            ("E-2605036","Nithin Kumar"),("E-2511008","P Anitha"),
            ("E-2605004","P. Nagamani Teja"),("E-2406023","P.Bhanu Priya"),
            ("E-2606019","P. Dhanush"),("E-2503015","Vandadi Narasimhulu"),
            ("E-2604020","Rithika Kuppala"),("E-2408010","Talari Gnanasai"),
            ("E-2603012","Thuduku Reddy Prakash"),("E-2605024","V. Thulasiram"),
            ("E-2312028","Latu Borgohain"),("E-2505012","Moniram"),
            ("E-2312029","Sri Liladitya Gogoi"),("E-2604021","Hariom Dyaneshwar Lohare"),
            ("E-2604024","Narendra Sanjay Patil"),("E-2604018","Sagar Purushottam Pote"),
            ("E-2605010","Sakshil Patil"),("E-2509003","Sandeep Yadav"),
            ("E-2604023","Vijay Dattappa"),("E-2510026","Rutuja Balasaheb Kadam"),
            ("E-2512016","Swayam Anil Sirdawade"),("E-2511021","Siddhi Balkrishna Sakpal"),
            ("E-2510035","Aditya Chavan"),("E-2303018","Akshata Subhash Dhangade"),
            ("E-2405023","Apurva Santosh Kapadi"),("E-2011077","Aruna Kodare"),
            ("E-2508023","Pritee Nagesh Sakpal"),("E-2103039","Sahil Sanjay Gamare"),
            ("E-2200635","Sayali Santosh Humane"),("E-2502014","Shailesh Sambhaji Jadhav"),
            ("E-2411033","Siddhi Gujar"),("E-2511020","Suraj Surendra Chavan"),
            ("E-2012098","Vaibhav Baburav Juwale"),("E-2011061","Yash Gopinath Salvi"),
            ("E-2508003","Disha Bhamre"),("E-2604022","Ganesh Raut"),
            ("E-5505022","Navajyot Santosh Gavanang"),("E-2503018","Nilesh Raju Vairat"),
            ("E-2504009","Parmeshwar Laxmanrao Joshi"),("E-2511033","Pranali Jatin Bare"),
            ("E-2503021","Pratik Baban Walunj"),("E-2502003","Rameshwar Gaikwad"),
            ("E-2512003","Sakshi Bhingaree"),("E-2511031","Sakshi Sham More"),
            ("E-2501010","Yogiraj Yadav Jadhav"),
        ]

        count = 0
        for code, name in employees:
            if not EmployeeMaster.query.filter_by(employee_code=code).first():
                db.session.add(EmployeeMaster(employee_code=code, employee_name=name))
                count += 1

        db.session.commit()
        app.logger.info("Auto-seeded %d employees into employee_master.", count)

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
        
        # Employee codes to ensure as super_admin
        target_codes = [
            {'code': 'E-2512012', 'fallback_name': 'Pratik Prakash Sagvekar'},
            {'code': 'E-2603025', 'fallback_name': 'Raj Sanjay Shukla'},
        ]
        
        made_changes = False
        
        for target in target_codes:
            emp_code = target['code']
            fallback_name = target['fallback_name']
            
            app.logger.info(f"ENSURE_ADMIN: Checking employee code {emp_code}...")
            
            # Step 1: Find user by EMPLOYEE_CODE through Employee table
            # This is how the system actually links users - via Employee.employee_code
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
                # User doesn't exist - need to create
                app.logger.warning(f"ENSURE_ADMIN: User with employee code {emp_code} not found, attempting creation...")
                
                # Try to get employee info from EmployeeMaster
                emp_master = EmployeeMaster.query.filter_by(employee_code=emp_code).first()
                
                if emp_master and emp_master.employee_name:
                    app.logger.info(f"ENSURE_ADMIN: Found {emp_code} in EmployeeMaster: {emp_master.employee_name}")
                    full_name = emp_master.employee_name
                else:
                    app.logger.info(f"ENSURE_ADMIN: No EmployeeMaster entry for {emp_code}, using fallback name")
                    full_name = fallback_name
                
                # Split name into first and last
                name_parts = full_name.split(' ', 1)
                first_name = name_parts[0].strip() if len(name_parts) > 0 else 'Employee'
                last_name = name_parts[1].strip() if len(name_parts) > 1 else 'Account'
                
                # Create username from employee code (lowercase, no dash)
                username = emp_code.lower().replace('-', '')  # e.g. e2512012
                
                # Create placeholder email (internal format used by the system)
                email = f"{username}@hrms.internal"
                
                # Create new user with super_admin role
                app.logger.info(f"ENSURE_ADMIN: Creating user {username} ({first_name} {last_name}) for code {emp_code}...")
                
                new_user = User(
                    username=username,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    role='super_admin',
                    status='active',
                    email_verified=True,
                )
                
                # Set temporary password (user will change on first login)
                new_user.set_password('TempPassword@123')
                
                db.session.add(new_user)
                db.session.flush()  # Flush to get the user.id
                
                # Create Employee record linking user to employee_code
                emp_record = Employee(
                    user_id=new_user.id,
                    employee_code=emp_code,
                    created_by=new_user.id,
                )
                db.session.add(emp_record)
                
                app.logger.info(f"ENSURE_ADMIN: ✅ User {username} staged for creation with role=super_admin and employee_code={emp_code}")
                made_changes = True
            
            else:
                # User exists - check role
                current_role = user.role
                app.logger.info(f"ENSURE_ADMIN: Found user {user.username} (ID={user.id}) for employee code {emp_code}, current role='{current_role}'")
                
                if current_role != 'super_admin':
                    app.logger.warning(f"ENSURE_ADMIN: Updating {user.username} role from '{current_role}' to 'super_admin'...")
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
                app.logger.warning(f"ENSURE_ADMIN: ⚠️  Code {emp_code}: user not found after commit")
        
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
    CRITICAL: Ensure Comp Off (CO) leave type exists in production database.
    
    Handles UNIQUE constraint on code column - will update if exists.
    Called from _auto_create_tables() during app initialization.
    """
    try:
        with app.app_context():
            from app.extensions.database import db  # noqa: PLC0415
            from app.models.leave import LeaveType  # noqa: PLC0415
            
            try:
                co_type = LeaveType.query.filter_by(code='CO').first()
            except Exception as query_err:
                app.logger.warning(f"⚠️  Could not query LeaveType: {query_err}")
                return
            
            if not co_type:
                try:
                    co = LeaveType(
                        code='CO',
                        name='Comp Off',
                        max_days_per_year=6,
                        is_paid=True,
                        requires_document=False,
                        color='#8b5cf6',
                        is_active=True,
                    )
                    db.session.add(co)
                    db.session.commit()
                    app.logger.info("✅ Created Comp Off leave type (CO)")
                except Exception as create_err:
                    app.logger.warning(f"⚠️  Could not create CO: {create_err}")
                    try:
                        db.session.rollback()
                    except Exception:
                        pass
            elif not co_type.is_active:
                try:
                    co_type.is_active = True
                    db.session.commit()
                    app.logger.info("✅ Activated Comp Off leave type (CO)")
                except Exception as activate_err:
                    app.logger.warning(f"⚠️  Could not activate CO: {activate_err}")
                    try:
                        db.session.rollback()
                    except Exception:
                        pass
            else:
                app.logger.info(f"✅ CO exists: id={co_type.id}, active={co_type.is_active}")
    
    except Exception as e:
        app.logger.warning(f"⚠️  _ensure_comp_off_leavetype: {e}")
        try:
            from app.extensions.database import db  # noqa: PLC0415
            db.session.rollback()
        except Exception:
            pass
