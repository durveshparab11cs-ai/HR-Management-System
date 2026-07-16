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
    Create all DB tables on first boot and auto-seed employee master data.
    Also adds new columns to existing tables via ALTER TABLE when needed.
    """
    try:
        with app.app_context():
            from app.extensions.database import db  # noqa: PLC0415
            db.create_all()
            app.logger.info("db.create_all() — tables ready.")

            # Add new GPS accuracy columns if they don't exist yet
            _migrate_add_columns(db)

            # Auto-seed employee master if table is empty
            _auto_seed_employees(app)
    except Exception as exc:
        app.logger.warning("db.create_all() skipped: %s", exc)


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
        ('attendance',     'check_in_accuracy',           'DOUBLE PRECISION' if dialect == 'postgresql' else 'FLOAT'),
        ('attendance',     'check_out_accuracy',          'DOUBLE PRECISION' if dialect == 'postgresql' else 'FLOAT'),
        ('office_settings','min_gps_accuracy_metres',     'INTEGER'),
    ]

    for table, col, col_type in new_cols:
        if not col_exists(table, col):
            try:
                db.session.execute(text(f'ALTER TABLE {table} ADD COLUMN {col} {col_type}'))
                db.session.commit()
                logger.info("Added column %s.%s", table, col)
            except Exception as e:
                db.session.rollback()
                logger.warning("Could not add column %s.%s: %s", table, col, e)


def _auto_seed_employees(app: Flask) -> None:
    """Seed EmployeeMaster if table is empty. Runs once on first boot."""
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
                {"name": "Comp Off",          "code": "COMP", "max_days_per_year": 6,  "is_paid": True,  "color": "#8b5cf6"},
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
