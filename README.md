# Smart HRMS

A production-grade **Human Resource Management System** built with Python 3.13, Flask, and Bootstrap 5.

---

## What is Smart HRMS?

Smart HRMS is a full-featured, enterprise-ready HR platform designed to manage the complete employee lifecycle — from onboarding to payroll, attendance, leave, and reporting — in a single, integrated system.

---

## Key Features (Roadmap)

| Module | Status |
|---|---|
| Authentication & RBAC | Foundation ready |
| Employee Management | Foundation ready |
| Attendance (GPS-verified) | Foundation ready |
| Leave Management | Foundation ready |
| Payroll Processing | Foundation ready |
| Reports & Data Export | Foundation ready |
| Notifications | Foundation ready |
| Company / Department Setup | Foundation ready |
| Admin Panel | Foundation ready |
| REST API (v1) | Foundation ready |

---

## Tech Stack

**Backend:** Python 3.13 · Flask · SQLAlchemy · Flask-Migrate · Flask-Login · Flask-WTF · Flask-Mail · Flask-Limiter · Flask-Caching · APScheduler

**Database:** PostgreSQL 16 (production) · SQLite (development)

**Frontend:** Bootstrap 5 · Vanilla ES6 · Chart.js · Bootstrap Icons

**Infrastructure:** Gunicorn · Nginx · Redis · Docker · Docker Compose

---

## Quick Start

```bash
# 1. Clone and enter the project
git clone https://github.com/your-org/smart-hrms.git
cd smart-hrms/smart_hrms

# 2. Set up virtual environment
python -m venv venv && source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate  # Windows

# 3. Install dependencies
pip install -r requirements/development.txt

# 4. Configure environment
cp .env.example .env
# Edit .env: set SECRET_KEY and DATABASE_URL at minimum

# 5. Set up database and create admin
flask db upgrade
flask create-admin

# 6. Run development server
flask run
```

Open **http://127.0.0.1:5000**

For Docker setup and production deployment, see [docs/installation.md](docs/installation.md).

---

## Project Structure

```
smart_hrms/
├── app/                 # Application package (blueprints, models, services…)
├── config/              # Configuration classes (Dev/Test/Production)
├── tests/               # pytest test suite
├── scripts/             # Operational scripts (deploy check, Nginx config)
├── docs/                # Documentation
├── requirements/        # Pinned dependencies per environment
├── run.py               # WSGI entry point
├── Dockerfile
└── docker-compose.yml
```

Full structure: [docs/folder_structure.md](docs/folder_structure.md)

---

## Architecture

Smart HRMS follows a strict layered architecture enforced by convention:

```
Routes  →  Services  →  Repositories  →  Models  →  Database
```

- **Routes** handle HTTP only — no business logic
- **Services** contain all business rules
- **Repositories** contain all database queries
- **Models** define schema and data behaviour
- **Utils** are pure functions with no Flask dependency

See [docs/coding_standards.md](docs/coding_standards.md) for full rules.

---

## Running Tests

```bash
pytest                          # Full suite
pytest tests/unit/              # Unit tests only
pytest tests/integration/       # Integration tests only
pytest --cov=app                # With coverage
```

---

## CLI Commands

```bash
flask db-init        # Create all tables (dev quick-start)
flask db upgrade     # Run pending Alembic migrations
flask db migrate -m  # Generate a new migration
flask create-admin   # Create a SUPER_ADMIN user interactively
flask seed-db        # Seed development reference data
```

---

## Documentation

| Document | Description |
|---|---|
| [docs/installation.md](docs/installation.md) | Full setup guide (local + Docker) |
| [docs/folder_structure.md](docs/folder_structure.md) | Every folder and file explained |
| [docs/coding_standards.md](docs/coding_standards.md) | Style rules, naming conventions, architecture laws |

---

## Security

- CSRF protection on all state-changing requests (Flask-WTF)
- bcrypt password hashing with configurable rounds
- Account lockout after 5 failed login attempts
- Rate limiting on authentication endpoints (Flask-Limiter)
- Security HTTP headers injected on every response
- Soft-delete — no data is permanently destroyed in production
- Audit log for all data mutations
- Environment-based configuration — no secrets in source code

---

## License

Proprietary — All rights reserved. See LICENSE file for details.
