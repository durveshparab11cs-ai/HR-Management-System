"""
tests/integration/test_auth_routes.py
=======================================
Integration tests for the authentication blueprint routes.

Tests use the Flask test client to make real HTTP requests through
the full WSGI stack (middleware, blueprints, error handlers).

CSRF is disabled in TestingConfig so form submissions work without tokens.
"""

import pytest


class TestLoginRoute:
    """GET and POST /auth/login"""

    def test_login_page_returns_200(self, client):
        response = client.get("/auth/login")
        assert response.status_code == 200

    def test_login_page_contains_form(self, client):
        response = client.get("/auth/login")
        assert b"email" in response.data
        assert b"password" in response.data

    def test_authenticated_user_redirected_from_login(self, auth_client):
        response = auth_client.get("/auth/login", follow_redirects=False)
        # Should redirect to dashboard
        assert response.status_code in (301, 302)


class TestLogoutRoute:
    """GET /auth/logout"""

    def test_logout_redirects_unauthenticated(self, client):
        response = client.get("/auth/logout", follow_redirects=False)
        assert response.status_code in (301, 302)

    def test_logout_clears_session(self, auth_client):
        response = auth_client.get("/auth/logout", follow_redirects=True)
        assert response.status_code == 200


class TestForgotPasswordRoute:
    """GET /auth/forgot-password"""

    def test_forgot_password_page_loads(self, client):
        response = client.get("/auth/forgot-password")
        assert response.status_code == 200
        assert b"email" in response.data


class TestProtectedRoutes:
    """Unauthenticated access to protected routes."""

    def test_dashboard_redirects_unauthenticated(self, client):
        response = client.get("/dashboard/", follow_redirects=False)
        assert response.status_code in (301, 302)
        location = response.headers.get("Location", "")
        assert "login" in location.lower()

    def test_employees_redirects_unauthenticated(self, client):
        response = client.get("/employees/", follow_redirects=False)
        assert response.status_code in (301, 302)

    def test_admin_panel_requires_super_admin(self, auth_client):
        """Regular employee should get 403 on admin panel."""
        response = auth_client.get("/admin/", follow_redirects=False)
        assert response.status_code in (302, 403)


class TestHealthEndpoint:
    """GET /health — liveness probe."""

    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_json(self, client):
        response = client.get("/health")
        data = response.get_json()
        assert data["status"] == "ok"

    def test_health_no_auth_required(self, client):
        """Health check must work without any authentication."""
        response = client.get("/health")
        assert response.status_code == 200


class TestAPIRoutes:
    """API v1 basic routes."""

    def test_api_health(self, client):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True

    def test_api_me_unauthenticated(self, client):
        response = client.get("/api/v1/me")
        assert response.status_code in (302, 401)
