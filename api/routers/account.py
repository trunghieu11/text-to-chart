"""
Account routes for Developer Portal: register, login, API keys, usage.
"""

from __future__ import annotations

import sqlite3
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from api.models import (
    AccountMeResponse,
    AccountUsageResponse,
    KeyCreateRequest,
    KeyCreateResponse,
    KeyListItem,
    KeyListResponse,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
)
from api.saas.jwt import create_token, decode_token
from passlib.context import CryptContext

from api.saas.repository import (
    create_api_key,
    create_tenant,
    get_plan,
    get_tenant,
    list_api_keys_for_tenant,
    revoke_api_key,
)
from api.usage import usage_tracker

router = APIRouter(prefix="/v1/account", tags=["account"])
security = HTTPBearer(auto_error=False)


async def get_current_tenant_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> int:
    """Extract tenant_id from JWT. Raises 401 if invalid."""
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header.")
    token = credentials.credentials
    payload = decode_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
    return int(payload["sub"])


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.post("/register", response_model=TokenResponse)
async def register(req: RegisterRequest):
    """Register a new tenant (account)."""
    password_hash = pwd_context.hash(req.password)

    import sqlite3

    try:
        tenant = create_tenant(
            name=req.name,
            email=req.email.lower(),
            password_hash=password_hash,
            plan_id=1,  # Free plan
        )
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Email already registered.")

    token = create_token(tenant.id, tenant.email)
    return TokenResponse(access_token=token)


def _get_saas_db_path() -> str:
    try:
        from config import config
        return config.saas_db_path
    except Exception:
        return "saas.db"


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    """Login and get JWT."""
    from api.db import ensure_db

    ensure_db()

    with sqlite3.connect(_get_saas_db_path()) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT id, name, email, password_hash FROM tenants WHERE email = ? AND status = 'active'",
            (req.email.lower(),),
        ).fetchone()

    if not row or not pwd_context.verify(req.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    token = create_token(row["id"], row["email"])
    return TokenResponse(access_token=token)


@router.get("/me", response_model=AccountMeResponse)
async def get_me(tenant_id: int = Depends(get_current_tenant_id)):
    """Get current tenant (account) info."""
    tenant = get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Account not found.")
    plan = get_plan(tenant.plan_id)
    plan_name = plan.name if plan else "free"
    return AccountMeResponse(
        id=tenant.id,
        name=tenant.name,
        email=tenant.email,
        plan=plan_name,
        status=tenant.status,
    )


@router.post("/keys", response_model=KeyCreateResponse)
async def create_key(
    req: KeyCreateRequest = KeyCreateRequest(),
    tenant_id: int = Depends(get_current_tenant_id),
):
    """Create a new API key. Full key is returned only once."""
    raw_key, info = create_api_key(tenant_id, req.name)
    return KeyCreateResponse(id=info.id, key=raw_key, name=info.name)


@router.get("/keys", response_model=KeyListResponse)
async def list_keys(tenant_id: int = Depends(get_current_tenant_id)):
    """List API keys for the current tenant (masked)."""
    keys = list_api_keys_for_tenant(tenant_id)
    return KeyListResponse(
        keys=[
            KeyListItem(
                id=k.id,
                name=k.name,
                key_prefix=k.key_prefix,
                created_at=k.created_at,
            )
            for k in keys
        ]
    )


@router.delete("/keys/{key_id}")
async def delete_key(
    key_id: int,
    tenant_id: int = Depends(get_current_tenant_id),
):
    """Revoke an API key."""
    ok = revoke_api_key(key_id, tenant_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Key not found.")
    return {"status": "revoked"}


@router.get("/usage", response_model=AccountUsageResponse)
async def get_account_usage(tenant_id: int = Depends(get_current_tenant_id)):
    """Get usage for the current tenant."""
    usage = usage_tracker.get_usage_for_tenant(tenant_id)
    history = usage_tracker.get_usage_history_for_tenant(tenant_id)
    return AccountUsageResponse(
        period_start=usage["period_start"],
        request_count=usage["request_count"],
        history=history,
    )
