"""
Tests for admin routes: tenants, keys, usage.
Uses temp saas.db and patched admin credentials.
Requires bcrypt (pip install bcrypt or passlib[bcrypt]).
"""

from __future__ import annotations

import os

import pytest

pytest.importorskip("bcrypt")
import tempfile
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

# Add project root to path
project_root = str(Path(__file__).parent.parent)
if project_root not in __import__("sys").path:
    __import__("sys").path.insert(0, project_root)

from api.db.schema import init_db, seed_plans


@pytest.fixture
def temp_saas_db():
    """Create a temp saas.db and patch config to use it."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    seed_plans(path)
    with patch("config.config.saas_db_path", path):
        with patch("api.saas.repository._get_db_path", return_value=path):
            yield path
    try:
        os.unlink(path)
    except OSError:
        pass


@pytest.fixture
def admin_headers():
    """Basic auth header for admin."""
    import base64
    credentials = base64.b64encode(b"admin:admin123").decode()
    return {"Authorization": f"Basic {credentials}"}


@pytest.fixture
def client(temp_saas_db, admin_headers):
    """Client with temp saas db and admin auth configured."""
    with patch("config.config.admin_username", "admin"):
        with patch("config.config.admin_password", "admin123"):
            with patch("api.middleware.auth.get_api_keys", return_value=set()):
                from api.main import app
                client = TestClient(app)
                client.admin_headers = admin_headers
                yield client


def _create_tenant_via_register(client):
    """Create a tenant by registering."""
    client.post(
        "/v1/account/register",
        json={"email": "tenant@admin.test", "password": "pass", "name": "Admin Test Tenant"},
    )
    # Get tenant_id from login/me
    login = client.post(
        "/v1/account/login",
        json={"email": "tenant@admin.test", "password": "pass"},
    )
    token = login.json()["access_token"]
    me = client.get("/v1/account/me", headers={"Authorization": f"Bearer {token}"})
    return me.json()["id"]


class TestAdminTenants:
    def test_list_tenants_empty(self, client):
        resp = client.get("/admin/v1/tenants", headers=client.admin_headers)
        assert resp.status_code == 200
        assert "tenants" in resp.json()
        assert resp.json()["tenants"] == []

    def test_list_tenants_after_register(self, client):
        _create_tenant_via_register(client)
        resp = client.get("/admin/v1/tenants", headers=client.admin_headers)
        assert resp.status_code == 200
        tenants = resp.json()["tenants"]
        assert len(tenants) == 1
        assert tenants[0]["email"] == "tenant@admin.test"

    def test_list_tenants_unauthorized(self, client):
        resp = client.get("/admin/v1/tenants")
        assert resp.status_code == 401

    def test_get_tenant_detail(self, client):
        tenant_id = _create_tenant_via_register(client)
        resp = client.get(
            f"/admin/v1/tenants/{tenant_id}",
            headers=client.admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == tenant_id
        assert data["email"] == "tenant@admin.test"
        assert data["plan_name"] == "free"
        assert data["status"] == "active"

    def test_update_tenant_status(self, client):
        tenant_id = _create_tenant_via_register(client)
        resp = client.patch(
            f"/admin/v1/tenants/{tenant_id}",
            json={"status": "suspended"},
            headers=client.admin_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "suspended"


class TestAdminKeys:
    def test_list_keys_for_tenant(self, client):
        tenant_id = _create_tenant_via_register(client)
        # Create a key via account
        login = client.post(
            "/v1/account/login",
            json={"email": "tenant@admin.test", "password": "pass"},
        )
        token = login.json()["access_token"]
        client.post(
            "/v1/account/keys",
            json={"name": "Admin Key"},
            headers={"Authorization": f"Bearer {token}"},
        )
        resp = client.get(
            f"/admin/v1/tenants/{tenant_id}/keys",
            headers=client.admin_headers,
        )
        assert resp.status_code == 200
        keys = resp.json()["keys"]
        assert len(keys) >= 1

    def test_admin_create_key(self, client):
        tenant_id = _create_tenant_via_register(client)
        resp = client.post(
            f"/admin/v1/tenants/{tenant_id}/keys",
            json={"name": "Admin-Created Key"},
            headers=client.admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
        assert "key" in data
        assert data["name"] == "Admin-Created Key"

    def test_admin_revoke_key(self, client):
        tenant_id = _create_tenant_via_register(client)
        create_resp = client.post(
            f"/admin/v1/tenants/{tenant_id}/keys",
            json={"name": "To Revoke"},
            headers=client.admin_headers,
        )
        key_id = create_resp.json()["id"]
        resp = client.delete(
            f"/admin/v1/tenants/{tenant_id}/keys/{key_id}",
            headers=client.admin_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "revoked"


class TestAdminUsage:
    def test_get_tenant_usage(self, client):
        tenant_id = _create_tenant_via_register(client)
        resp = client.get(
            f"/admin/v1/tenants/{tenant_id}/usage",
            headers=client.admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "current" in data
        assert "history" in data
        assert "request_count" in data["current"]
