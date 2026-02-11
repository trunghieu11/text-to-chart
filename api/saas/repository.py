"""
SaaS repository: tenant, plan, API key CRUD and lookup.
"""

from __future__ import annotations

import hashlib
import secrets
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

# Ensure DB is initialized on first use
from api.db import ensure_db


@dataclass
class Plan:
    id: int
    name: str
    rate_limit: str
    monthly_quota: int
    features: Optional[str]


@dataclass
class Tenant:
    id: int
    name: str
    email: str
    plan_id: int
    status: str
    created_at: str


@dataclass
class TenantWithPlan:
    tenant: Tenant
    plan: Plan


@dataclass
class ApiKeyInfo:
    id: int
    tenant_id: int
    key_prefix: str
    name: str
    created_at: str


def _get_db_path() -> str:
    try:
        from config import config
        return config.saas_db_path
    except Exception:
        return "saas.db"


def _ensure_db():
    ensure_db()


def _hash_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode()).hexdigest()


def get_tenant_by_key(api_key: str) -> Optional[TenantWithPlan]:
    """
    Look up tenant and plan by API key.
    Returns None if not found, tenant suspended, or key expired.
    """
    _ensure_db()
    key_hash = _hash_key(api_key)
    db_path = _get_db_path()

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("""
            SELECT k.id, k.tenant_id, k.expires_at,
                   t.id as t_id, t.name as t_name, t.email, t.plan_id, t.status, t.created_at as t_created,
                   p.id as p_id, p.name as p_name, p.rate_limit, p.monthly_quota, p.features
            FROM api_keys k
            JOIN tenants t ON k.tenant_id = t.id
            JOIN plans p ON t.plan_id = p.id
            WHERE k.key_hash = ? AND t.status = 'active'
        """, (key_hash,)).fetchone()

    if row is None:
        return None

    expires_at = row["expires_at"]
    if expires_at:
        try:
            exp = datetime.fromisoformat(expires_at)
            if datetime.now(timezone.utc).replace(tzinfo=None) > exp.replace(tzinfo=None):
                return None
        except (ValueError, TypeError):
            pass

    tenant = Tenant(
        id=row["t_id"],
        name=row["t_name"],
        email=row["email"],
        plan_id=row["plan_id"],
        status=row["status"],
        created_at=row["t_created"],
    )
    plan = Plan(
        id=row["p_id"],
        name=row["p_name"],
        rate_limit=row["rate_limit"],
        monthly_quota=row["monthly_quota"],
        features=row["features"],
    )
    return TenantWithPlan(tenant=tenant, plan=plan)


def get_plan(plan_id: int) -> Optional[Plan]:
    _ensure_db()
    with sqlite3.connect(_get_db_path()) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT id, name, rate_limit, monthly_quota, features FROM plans WHERE id = ?",
            (plan_id,),
        ).fetchone()
    if row is None:
        return None
    return Plan(
        id=row["id"],
        name=row["name"],
        rate_limit=row["rate_limit"],
        monthly_quota=row["monthly_quota"],
        features=row["features"],
    )


def get_tenant(tenant_id: int) -> Optional[Tenant]:
    _ensure_db()
    with sqlite3.connect(_get_db_path()) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT id, name, email, plan_id, status, created_at FROM tenants WHERE id = ?",
            (tenant_id,),
        ).fetchone()
    if row is None:
        return None
    return Tenant(
        id=row["id"],
        name=row["name"],
        email=row["email"],
        plan_id=row["plan_id"],
        status=row["status"],
        created_at=row["created_at"],
    )


def create_tenant(
    name: str,
    email: str,
    password_hash: str,
    plan_id: int = 1,
) -> Tenant:
    """Create a new tenant. plan_id=1 is typically Free."""
    _ensure_db()
    now = datetime.now(timezone.utc).isoformat()
    with sqlite3.connect(_get_db_path()) as conn:
        cursor = conn.execute(
            "INSERT INTO tenants (name, email, password_hash, plan_id, status, created_at) VALUES (?, ?, ?, ?, 'active', ?)",
            (name, email, password_hash, plan_id, now),
        )
        tenant_id = cursor.lastrowid
    result = get_tenant(tenant_id)
    assert result is not None
    return result


def update_tenant(
    tenant_id: int,
    *,
    status: Optional[str] = None,
    plan_id: Optional[int] = None,
) -> Optional[Tenant]:
    _ensure_db()
    updates = []
    params = []
    if status is not None:
        updates.append("status = ?")
        params.append(status)
    if plan_id is not None:
        updates.append("plan_id = ?")
        params.append(plan_id)
    if not updates:
        return get_tenant(tenant_id)
    params.append(tenant_id)
    with sqlite3.connect(_get_db_path()) as conn:
        conn.execute(
            f"UPDATE tenants SET {', '.join(updates)} WHERE id = ?",
            params,
        )
    return get_tenant(tenant_id)


def list_tenants() -> list[dict]:
    """List all tenants with plan name."""
    _ensure_db()
    with sqlite3.connect(_get_db_path()) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("""
            SELECT t.id, t.name, t.email, t.status, t.created_at, p.name as plan_name, p.id as plan_id
            FROM tenants t
            JOIN plans p ON t.plan_id = p.id
            ORDER BY t.created_at DESC
        """).fetchall()
    return [dict(r) for r in rows]


def create_api_key(tenant_id: int, name: str = "Default") -> tuple[str, ApiKeyInfo]:
    """
    Create a new API key for the tenant.
    Returns (raw_key, ApiKeyInfo). Raw key is shown only once.
    """
    _ensure_db()
    raw_key = secrets.token_urlsafe(32)
    key_hash = _hash_key(raw_key)
    key_prefix = raw_key[:8] if len(raw_key) >= 8 else raw_key
    now = datetime.now(timezone.utc).isoformat()

    with sqlite3.connect(_get_db_path()) as conn:
        cursor = conn.execute(
            "INSERT INTO api_keys (tenant_id, key_hash, key_prefix, name, created_at) VALUES (?, ?, ?, ?, ?)",
            (tenant_id, key_hash, key_prefix, name, now),
        )
        key_id = cursor.lastrowid

    return raw_key, ApiKeyInfo(
        id=key_id,
        tenant_id=tenant_id,
        key_prefix=key_prefix,
        name=name,
        created_at=now,
    )


def list_api_keys_for_tenant(tenant_id: int) -> list[ApiKeyInfo]:
    _ensure_db()
    with sqlite3.connect(_get_db_path()) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT id, tenant_id, key_prefix, name, created_at FROM api_keys WHERE tenant_id = ? ORDER BY created_at DESC",
            (tenant_id,),
        ).fetchall()
    return [
        ApiKeyInfo(
            id=r["id"],
            tenant_id=r["tenant_id"],
            key_prefix=r["key_prefix"],
            name=r["name"],
            created_at=r["created_at"],
        )
        for r in rows
    ]


def revoke_api_key(key_id: int, tenant_id: Optional[int] = None) -> bool:
    """Revoke (delete) an API key. If tenant_id provided, verify ownership."""
    _ensure_db()
    with sqlite3.connect(_get_db_path()) as conn:
        if tenant_id is not None:
            cursor = conn.execute(
                "DELETE FROM api_keys WHERE id = ? AND tenant_id = ?",
                (key_id, tenant_id),
            )
        else:
            cursor = conn.execute("DELETE FROM api_keys WHERE id = ?", (key_id,))
        return cursor.rowcount > 0
