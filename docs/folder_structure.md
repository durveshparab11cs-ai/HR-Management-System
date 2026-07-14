# Smart HRMS — Folder Structure Guide

## Root Layout

```
smart_hrms/
├── app/                    # Flask application package
├── config/                 # Configuration classes
├── instance/               # Runtime files (uploads, sessions) — gitignored
├── migrations/             # Alembic migration scripts (auto-generated)
├── logs/                   # Rotating log files — gitignored
├── tests/                  # Test suite
├── requirements/           # Pinned dependency files per environment
├── docs/                   # Project documentation
├── scripts/                # Operational shell scripts and SQL
├── run.py                  # WSGI entry point
├── Dockerfile              # Production container definition
├── docker-compose.yml      # Multi-container orchestration
└── .env.example            # Environment variable template
```

## app/ Package

```
app/
├── __init__.py             # Application factory: create_app()
├── logging_config.py       # Logging setup — called from create_app()
├── error_handlers.py       # Global HTTP + domain exception handlers
│
├── blueprints/             # Feature modules (one blueprint per domain)
│   ├── authentication/     # Login, logout, password reset, email verify
│   ├── dashboard/          # Post-login landing page with stats
│   ├── company/            # Company profile, departments, positions, shifts
│   ├── employees/          # Employee CRUD, documents, profile photos
│   ├── attendance/         # Check-in/out (GPS), records, corrections
│   ├── leave/              # Leave applications, approvals, balances
│   ├── payroll/            # Payroll runs, payslips, salary structures
│   ├── reports/            # Data exports (CSV/Excel/PDF), charts
│   ├── notifications/      # In-app notification inbox
│   ├── settings/           # App settings, user preferences
│   ├── admin/              # Super-admin user/system management
│   └── api/v1/             # RESTful JSON API (Bearer token auth)
│
├── models/                 # SQLAlchemy ORM models
│   ├── user.py             # User (auth + account lifecycle)
│   └── __init__.py         # Imports all models for Alembic discovery
│
├── services/               # Business logic layer
│   └── (one file per domain, added as modules are built)
│
├── repositories/           # Database access layer
│   └── (one file per model)
│
├── forms/                  # Flask-WTF form classes
│   └── (one file per domain)
│
├── validators/             # Cross-field / business-rule validators
│
├── helpers/                # Flask-context-aware helpers (url building, etc.)
│
├── utils/                  # Pure utility functions (no Flask dependency)
│   ├── date_utils.py
│   ├── time_utils.py
│   ├── password_utils.py
│   ├── file_utils.py
│   ├── image_utils.py
│   ├── email_utils.py
│   ├── gps_utils.py
│   ├── response_utils.py
│   ├── validation_utils.py
│   ├── pagination_utils.py
│   ├── export_utils.py
│   └── string_utils.py
│
├── extensions/             # Flask extension singletons
│   ├── database.py         # SQLAlchemy db instance
│   ├── migrate.py          # Flask-Migrate
│   ├── login.py            # Flask-Login + user_loader
│   ├── mail.py             # Flask-Mail
│   ├── csrf.py             # Flask-WTF CSRF
│   ├── limiter.py          # Flask-Limiter
│   ├── cache.py            # Flask-Caching
│   ├── session.py          # Flask-Session
│   └── scheduler.py        # APScheduler
│
├── middleware/             # Request/response pipeline hooks
│   ├── security_headers.py # Injects security HTTP headers
│   ├── request_logger.py   # Structured request/response logging
│   └── proxy.py            # Werkzeug ProxyFix for Nginx
│
├── core/                   # Reusable architectural building blocks
│   ├── base_model.py       # Abstract SQLAlchemy base (timestamps, soft-delete)
│   ├── base_repository.py  # Generic CRUD repository (Generic[T])
│   ├── base_service.py     # Abstract service with audit/validation helpers
│   ├── exceptions.py       # Custom exception hierarchy
│   ├── context_processors.py  # Jinja2 template variable injectors
│   └── security.py         # RBAC decorators (roles_required, admin_required)
│
├── constants/              # Application-wide constant values
│   ├── enums.py            # Python Enum types (UserRole, LeaveType, etc.)
│   ├── messages.py         # User-facing flash messages
│   ├── limits.py           # Numerical limits and thresholds
│   └── http.py             # HTTP status code constants
│
├── templates/              # Jinja2 HTML templates
│   ├── layouts/            # base.html, auth_base.html
│   ├── shared/             # sidebar, navbar, footer, flash, pagination, modal
│   ├── errors/             # 400, 401, 403, 404, 405, 429, 500, 503
│   ├── emails/             # Transactional email templates (HTML + txt)
│   ├── dashboard/          # Dashboard page
│   └── authentication/     # login, forgot_password, reset_password, verify_email
│
└── static/                 # Static assets (served by Nginx in production)
    ├── css/
    │   ├── variables.css   # Design tokens (colors, spacing, typography)
    │   ├── common.css      # Global resets and shared utilities
    │   ├── layout.css      # Sidebar, navbar, main content shell
    │   ├── components/     # forms, tables, cards, buttons, alerts
    │   └── <module>.css    # One file per feature module
    ├── js/
    │   ├── common.js       # HRMS namespace: sidebar, flash, modal, CSRF utils
    │   └── <module>.js     # One file per feature module
    ├── images/             # Logos, icons, placeholder images
    ├── fonts/              # Self-hosted web fonts (if any)
    └── vendor/             # Pinned third-party assets (no CDN dependency)
```

## Interaction Map

```
Browser → Nginx → Gunicorn → Flask (create_app)
                                  ↓
                          Middleware pipeline
                          (ProxyFix → SecurityHeaders → RequestLogger)
                                  ↓
                          Blueprint routes
                          (authentication, dashboard, employees, …)
                                  ↓
                          Services (business logic)
                                  ↓
                          Repositories (database access)
                                  ↓
                          SQLAlchemy models → PostgreSQL
```
