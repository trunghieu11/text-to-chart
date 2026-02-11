"""
Tests for account routes: register, login, me, keys, usage.
Uses temp saas.db for isolation.
Requires bcrypt (pip install bcrypt or passlib[bcrypt]).
"""

from __future__ import annotations

import os
import tempfile

import pytest

pytest.importorskip("bcrypt")
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
def client(temp_saas_db):
    """Client with temp saas db and dev auth (no API_KEYS)."""
    with patch("api.middleware.auth.get_api_keys", return_value=set()):
        from api.main import app
        yield TestClient(app)


class TestAccountRegister:
    def test_register_returns_token(self, client):
        resp = client.post(
            "/v1/account/register",
            json={"email": "user@test.com", "password": "secret123", "name": "Test User"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_register_duplicate_email_returns_400(self, client):
        client.post(
            "/v1/account/register",
            json={"email": "dup@test.com", "password": "secret", "name": "First"},
        )
        resp = client.post(
            "/v1/account/register",
            json={"email": "dup@test.com", "password": "other", "name": "Second"},
        )
        assert resp.status_code == 400
        assert "already registered" in resp.json()["detail"].lower()


class TestAccountLogin:
    def test_login_returns_token(self, client):
        client.post(
            "/v1/account/register",
            json={"email": "login@test.com", "password": "mypass", "name": "Login User"},
        )
        resp = client.post(
            "/v1/account/login",
            json={"email": "login@test.com", "password": "mypass"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data

    def test_login_wrong_password_returns_401(self, client):
        client.post(
            "/v1/account/register",
            json={"email": "wrong@test.com", "password": "correct", "name": "User"},
        )
        resp = client.post(
            "/v1/account/login",
            json={"email": "wrong@test.com", "password": "wrong"},
        )
        assert resp.status_code == 401

    def test_login_nonexistent_returns_401(self, client):
        resp = client.post(
            "/v1/account/login",
            json={"email": "nonexistent@test.com", "password": "any"},
        )
        assert resp.status_code == 401


class TestAccountMe:
    def test_me_returns_tenant_info(self, client):
        client.post(
            "/v1/account/register",
            json={"email": "me@test.com", "password": "pass", "name": "Me User"},
        )
        login = client.post(
            "/v1/account/login",
            json={"email": "me@test.com", "password": "pass"},
        )
        token = login.json()["access_token"]
        resp = client.get(
            "/v1/account/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "me@test.com"
        assert data["name"] == "Me User"
        assert data["plan"] == "free"
        assert data["status"] == "active"

    def test_me_without_token_returns_401(self, client):
        resp = client.get("/v1/account/me")
        assert resp.status_code in [401, 403]  # Unauthorized when missing auth


class TestAccountKeys:
    def _get_token(self, client, email="keys@test.com", password="pass"):
        client.post(
            "/v1/account/register",
            json={"email": email, "password": password, "name": "Keys User"},
        )
        login = client.post("/v1/account/login", json={"email": email, "password": password})
        return login.json()["access_token"]

    def test_create_key_returns_full_key_once(self, client):
        token = self._get_token(client)
        resp = client.post(
            "/v1/account/keys",
            json={"name": "My Key"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
        assert "key" in data
        assert len(data["key"]) > 8
        assert data["name"] == "My Key"

    def test_list_keys_returns_masked(self, client):
        token = self._get_token(client)
        create = client.post(
            "/v1/account/keys",
            json={"name": "List Key"},
            headers={"Authorization": f"Bearer {token}"},
        )
        key_id = create.json()["id"]
        resp = client.get(
            "/v1/account/keys",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        keys = resp.json()["keys"]
        assert len(keys) >= 1
        found = next((k for k in keys if k["id"] == key_id), None)
        assert found
        assert "key_prefix" in found
        assert "key" not in found  # Full key not in list

    def test_revoke_key(self, client):
        token = self._get_token(client)
        create = client.post(
            "/v1/account/keys",
            json={"name": "Revoke Key"},
            headers={"Authorization": f"Bearer {token}"},
        )
        key_id = create.json()["id"]
        resp = client.delete(
            f"/v1/account/keys/{key_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "revoked"
        list_resp = client.get(
            "/v1/account/keys",
            headers={"Authorization": f"Bearer {token}"},
        )
        ids = [k["id"] for k in list_resp.json()["keys"]]
        assert key_id not in ids


class TestAccountUsage:
    def test_usage_returns_period_and_count(self, client):
        token = self._get_token(client)
        resp = client.get(
            "/v1/account/usage",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "period_start" in data
        assert "request_count" in data
        assert "history" in data

    def _get_token(self, client, email="usage@test.com", password="pass"):
        client.post(
            "/v1/account/register",
            json={"email": email, "password": password, "name": "Usage User"},
        )
        login = client.post("/v1/account/login", json={"email": email, "password": password})
        return login.json()["access_token"]
