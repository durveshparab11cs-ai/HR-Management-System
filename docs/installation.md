# Smart HRMS — Installation Guide

## Prerequisites

| Requirement | Minimum Version |
|---|---|
| Python | 3.13 |
| pip | 24.x |
| PostgreSQL | 15 (production) |
| Redis | 7 (production) |
| Docker + Compose | 24 (optional) |

---

## Local Development Setup (without Docker)

### 1. Clone the repository

```bash
git clone https://github.com/your-org/smart-hrms.git
cd smart-hrms/smart_hrms
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv

# Linux / macOS
source venv/bin/activate

# Windows (CMD)
venv\Scripts\activate.bat

# Windows (PowerShell)
venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements/development.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
# Edit .env and set at minimum:
#   SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_hex(32))">
#   DATABASE_URL=sqlite:///smart_hrms_dev.db   (for quick start)
#   FLASK_ENV=development
```

### 5. Initialize the database

```bash
# Run migrations (creates all tables)
flask db upgrade

# OR quick-start without migrations (creates tables from models directly)
flask db-init
```

### 6. Create a super admin user

```bash
flask create-admin
# Follow the prompts for email, password, and name
```

### 7. Start the development server

```bash
flask run
# OR use the helper script:
bash scripts/start_dev.sh
```

Open **http://127.0.0.1:5000** in your browser and sign in with the admin credentials.

---

## Docker Setup (Recommended for Production-like Local Testing)

### 1. Copy and configure environment

```bash
cp .env.example .env
# Edit .env — set POSTGRES_PASSWORD, REDIS_PASSWORD, SECRET_KEY, MAIL_* values
```

### 2. Build and start all services

```bash
docker compose up --build -d
```

This starts: **PostgreSQL 16**, **Redis 7**, **Flask/Gunicorn app**, **Nginx**.

### 3. Run migrations inside the container

```bash
docker compose exec app flask db upgrade
```

### 4. Create super admin

```bash
docker compose exec app flask create-admin
```

### 5. Access the application

Open **http://localhost** (Nginx on port 80).

### Useful Docker commands

```bash
# View logs
docker compose logs -f app

# Stop all services
docker compose down

# Stop and remove volumes (WARNING: deletes database)
docker compose down -v

# Rebuild after code changes
docker compose up --build -d app
```

---

## Running Tests

```bash
# Install test dependencies
pip install -r requirements/testing.txt

# Run the full test suite
pytest

# With coverage report
pytest --cov=app --cov-report=html
open htmlcov/index.html

# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/

# Run a specific test file
pytest tests/unit/test_user_model.py -v
```

---

## Database Migrations

```bash
# After modifying a model, generate a new migration
flask db migrate -m "add_employee_table"

# Review the generated script in migrations/versions/
# Then apply it
flask db upgrade

# Rollback one migration
flask db downgrade
```

---

## Environment Variables Reference

See `.env.example` for the full list with descriptions. Critical variables:

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | YES | 32+ character random string — never reuse across environments |
| `DATABASE_URL` | YES | SQLite URI (dev) or PostgreSQL URI (production) |
| `FLASK_ENV` | YES | `development`, `testing`, or `production` |
| `MAIL_SERVER` | For email | SMTP hostname |
| `MAIL_USERNAME` | For email | SMTP login |
| `MAIL_PASSWORD` | For email | SMTP password or app-specific password |
| `CACHE_REDIS_URL` | Production | Redis URL for shared cache |
| `SESSION_TYPE` | Production | Set to `redis` in production |
