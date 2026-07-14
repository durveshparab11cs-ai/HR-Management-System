"""
tests/integration/test_error_handlers.py
==========================================
Integration tests verifying all error handlers return correct status codes
and appropriate response bodies for both HTML and JSON requests.
"""

import pytest


class TestHTMLErrorHandlers:
    """Browser requests — expect HTML error pages."""

    def test_404_html(self, client):
        response = client.get("/this-path-does-not-exist-at-all")
        assert response.status_code == 404
        assert b"404" in response.data or b"Not Found" in response.data

    def test_405_html(self, client):
        # Login only accepts GET/POST — PATCH should 405
        response = client.patch("/auth/login")
        assert response.status_code == 405


class TestJSONErrorHandlers:
    """API requests — expect JSON error envelope."""

    def _api_headers(self):
        return {"Accept": "application/json"}

    def test_404_json(self, client):
        response = client.get("/api/v1/nonexistent", headers=self._api_headers())
        assert response.status_code == 404
        data = response.get_json()
        assert data["success"] is False
        assert "error" in data

    def test_json_error_has_code_and_message(self, client):
        response = client.get(
            "/api/v1/this-does-not-exist",
            headers={"Accept": "application/json"},
        )
        assert response.status_code == 404
        data = response.get_json()
        assert "code" in data["error"]
        assert "message" in data["error"]
