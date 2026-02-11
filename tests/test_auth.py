"""
Tests for API authentication middleware.
Tests both dev mode (no keys) and enforced mode (keys configured).
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

# Ensure project root on path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)


@pytest.fixture
def client_no_auth():
    """Client with no API keys configured (dev mode)."""
    with patch("api.middleware.auth.get_api_keys", return_value=set()):
        from api.main import app
        yield TestClient(app)


@pytest.fixture
def client_with_auth():
    """Client with API keys configured (enforced mode)."""
    with patch("api.middleware.auth.get_api_keys", return_value={"valid-key-1", "valid-key-2"}):
        from api.main import app
        yield TestClient(app)


class TestDevMode:
    """In dev mode (no API_KEYS set), all requests should be allowed."""

    def test_request_without_key_allowed(self, client_no_auth):
        resp = client_no_auth.post(
            "/v1/charts",
            data={"data": "A,B\n1,2\n3,4", "chart_type": "bar"},
        )
        assert resp.status_code == 200

    def test_request_with_any_key_allowed(self, client_no_auth):
        resp = client_no_auth.post(
            "/v1/charts",
            data={"data": "A,B\n1,2\n3,4", "chart_type": "bar"},
            headers={"X-API-Key": "random-key"},
        )
        assert resp.status_code == 200

    def test_health_always_works(self, client_no_auth):
        resp = client_no_auth.get("/health")
        assert resp.status_code == 200


class TestEnforcedAuth:
    """When API_KEYS are configured, authentication must be enforced."""

    def test_missing_key_returns_401(self, client_with_auth):
        resp = client_with_auth.post(
            "/v1/charts",
            data={"data": "A,B\n1,2\n3,4", "chart_type": "bar"},
        )
        assert resp.status_code == 401
        assert "Missing API key" in resp.json()["detail"]

    def test_invalid_key_returns_401(self, client_with_auth):
        resp = client_with_auth.post(
            "/v1/charts",
            data={"data": "A,B\n1,2\n3,4", "chart_type": "bar"},
            headers={"X-API-Key": "wrong-key"},
        )
        assert resp.status_code == 401
        assert "Invalid API key" in resp.json()["detail"]

    def test_valid_key_succeeds(self, client_with_auth):
        resp = client_with_auth.post(
            "/v1/charts",
            data={"data": "A,B\n1,2\n3,4", "chart_type": "bar"},
            headers={"X-API-Key": "valid-key-1"},
        )
        assert resp.status_code == 200

    def test_second_valid_key_succeeds(self, client_with_auth):
        resp = client_with_auth.post(
            "/v1/charts",
            data={"data": "A,B\n1,2\n3,4", "chart_type": "bar"},
            headers={"X-API-Key": "valid-key-2"},
        )
        assert resp.status_code == 200

    def test_get_chart_requires_auth(self, client_with_auth):
        resp = client_with_auth.get("/v1/charts/some-id")
        assert resp.status_code == 401

    def test_get_image_requires_auth(self, client_with_auth):
        resp = client_with_auth.get("/v1/charts/some-id/image")
        assert resp.status_code == 401

    def test_get_code_requires_auth(self, client_with_auth):
        resp = client_with_auth.get("/v1/charts/some-id/code")
        assert resp.status_code == 401

    def test_embed_is_public(self, client_with_auth):
        """Embed endpoint should NOT require auth (for public embedding)."""
        resp = client_with_auth.get("/v1/charts/some-id/embed")
        # 404 (not found), NOT 401 — no auth required on embed
        assert resp.status_code == 404
