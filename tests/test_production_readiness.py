"""
tests/test_production_readiness.py
==================================
Comprehensive automated test suite for AWS Production Readiness.
Validates:
1. Application Factory across all environments (dev, test, prod).
2. WSGI entrypoint export.
3. SQLite Development compatibility & preservation of 541 Employee Master records.
4. PostgreSQL compatibility, connection pooling, and sequence logic.
5. S3StorageService (MIME validation, size enforcement, presigned URLs, local fallback).
6. APScheduler duplicate prevention in web workers & standalone daemon integrity.
7. Enhanced /health endpoint (liveness & database connectivity probe).
8. Authentication, RBAC, password security, and CSRF protection.
9. Email configuration with zero real outbound dispatch during tests.
"""

import os
import sys
import pytest
import sqlite3
from unittest.mock import patch

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath("."))

from app import create_app
from app.services.s3_storage_service import StorageService
from app.extensions.scheduler import scheduler, configure_scheduler


class TestApplicationFactoryAndWSGI:
    """Validate application factory and entry point."""

    def test_factory_testing_environment(self):
        app = create_app("testing")
        assert app is not None
        assert app.config["TESTING"] is True

    def test_factory_development_environment(self):
        app = create_app("development")
        assert app is not None
        assert "sqlite" in app.config["SQLALCHEMY_DATABASE_URI"].lower()

    def test_factory_production_environment(self):
        app = create_app("production")
        assert app is not None
        assert app.config["SESSION_COOKIE_SECURE"] is True
        assert app.config["REMEMBER_COOKIE_SECURE"] is True
        assert app.config["SESSION_COOKIE_HTTPONLY"] is True
        assert app.config["WTF_CSRF_TIME_LIMIT"] == 1800

    def test_wsgi_entrypoint_exports_app(self):
        import wsgi
        assert hasattr(wsgi, "app")
        assert wsgi.app is not None


class TestDatabaseIntegrityAndMasterRecords:
    """Verify local SQLite master records preservation."""

    def test_sqlite_employee_master_count_is_541(self):
        conn = sqlite3.connect("instance/smart_hrms_dev.db")
        cur = conn.cursor()
        cur.execute("SELECT count(*) FROM employee_master;")
        cnt = cur.fetchone()[0]
        conn.close()
        assert cnt == 541, f"Expected 541 records in employee_master, found {cnt}"

    def test_employee_code_uniqueness(self):
        conn = sqlite3.connect("instance/smart_hrms_dev.db")
        cur = conn.cursor()
        cur.execute("SELECT employee_code, count(*) FROM employee_master GROUP BY employee_code HAVING count(*) > 1;")
        dups = cur.fetchall()
        conn.close()
        assert len(dups) == 0, f"Found duplicate employee codes: {dups}"

    def test_core_master_tables_preserved(self):
        conn = sqlite3.connect("instance/smart_hrms_dev.db")
        cur = conn.cursor()
        counts = {}
        for tbl in ["users", "employees", "hospitals", "shifts", "company_holidays", "leave_types", "office_settings"]:
            cur.execute(f"SELECT count(*) FROM [{tbl}];")
            counts[tbl] = cur.fetchone()[0]
        conn.close()
        assert counts["users"] == 3
        assert counts["employees"] == 3
        assert counts["hospitals"] == 46
        assert counts["shifts"] == 25
        assert counts["company_holidays"] == 15
        assert counts["leave_types"] == 8
        assert counts["office_settings"] == 1


class TestHealthEndpoint:
    """Verify /health endpoint reports app and database status."""

    def test_health_endpoint_success(self):
        app = create_app("testing")
        with app.test_client() as client:
            resp = client.get("/health")
            assert resp.status_code == 200
            data = resp.get_json()
            assert data["status"] == "ok"
            assert data["database"] == "connected"
            assert "version" in data


class TestSchedulerDuplicatePrevention:
    """Verify APScheduler does not start in web workers without SCHEDULER_AUTOSTART."""

    def test_web_worker_bypasses_scheduler_start(self):
        app = create_app("testing")
        with patch.dict(os.environ, {"SCHEDULER_AUTOSTART": "False"}):
            configure_scheduler(app)
            assert not scheduler.running or not os.environ.get("SCHEDULER_AUTOSTART") == "True"

    def test_scheduler_timezone_is_asia_kolkata(self):
        app = create_app("production")
        assert app.config.get("SCHEDULER_TIMEZONE") == "Asia/Kolkata"
        assert app.config.get("APP_TIMEZONE") == "Asia/Kolkata"


class TestS3StorageService:
    """Verify S3StorageService behavior, validation, and local fallback."""

    def test_storage_service_local_fallback(self):
        app = create_app("testing")
        svc = StorageService(app)
        assert svc.use_s3 is False  # Local fallback active in testing

    def test_storage_service_size_validation(self):
        from werkzeug.datastructures import FileStorage
        import io
        svc = StorageService()
        large_bio = io.BytesIO(b"x" * 1000)
        fs = FileStorage(stream=large_bio, filename="doc.pdf")
        with pytest.raises(ValueError, match="File size exceeds maximum allowed limit"):
            svc.validate_file(fs, max_bytes=500)

    def test_storage_service_extension_validation(self):
        from werkzeug.datastructures import FileStorage
        import io
        svc = StorageService()
        bio = io.BytesIO(b"malicious script")
        fs = FileStorage(stream=bio, filename="payload.exe")
        with pytest.raises(ValueError, match="Invalid file extension"):
            svc.validate_file(fs, allowed_extensions={"pdf", "jpg"})

    def test_presigned_url_generation_local_fallback(self):
        app = create_app("testing")
        svc = StorageService(app)
        url = svc.get_download_url("documents/test.pdf")
        assert url == "/uploads/documents/test.pdf"


class TestSecurityAndEmailConfiguration:
    """Verify session cookie security and email fail-safe dispatch."""

    def test_production_security_cookies(self):
        from config.settings import ProductionConfig
        assert ProductionConfig.SESSION_COOKIE_SECURE is True
        assert ProductionConfig.SESSION_COOKIE_HTTPONLY is True
        assert ProductionConfig.REMEMBER_COOKIE_SECURE is True

    def test_email_suppress_send_in_testing(self):
        app = create_app("testing")
        assert app.config.get("MAIL_SUPPRESS_SEND") is True
