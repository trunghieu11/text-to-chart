"""
Admin routes for operators: tenants, keys, usage.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, HTTPBasic, HTTPBasicCredentials

from api.saas.repository import (
    create_api_key,
    get_plan,
    get_tenant,
    list_api_keys_for_tenant,
    list_tenants,
    revoke_api_key,
    update_tenant,
)
from api.usage import usage_tracker

router = APIRouter(prefix="/admin/v1", tags=["admin"])
security_bearer = HTTPBearer(auto_error=False)
security_basic = HTTPBasic(auto_error=False)


async def verify_admin(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    basic: Optional[HTTPBasicCredentials] = Depends(security_basic),
) -> None:
    """Verify admin credentials. Raises 401 if invalid."""
    from config import config

    username = config.admin_username
    password = config.admin_password

    if not username or not password:
        raise HTTPException(status_code=503, detail="Admin auth not configured.")

    # Check Bearer token (username:password as token for simplicity, or use ADMIN_SECRET)
    if credentials and credentials.scheme.lower() == "bearer":
        # Token could be base64 of "user:pass" or a shared secret
        token = credentials.credentials
        if token == password or (":" in token and token.split(":")[0] == username and token.split(":")[1] == password):
            return
        # Allow token = admin password as simple secret
        if token == password:
            return

    # Check Basic auth
    if basic:
        if basic.username == username and basic.password == password:
            return

    raise HTTPException(status_code=401, detail="Invalid admin credentials.")


@router.get("/tenants")
async def admin_list_tenants(_: None = Depends(verify_admin)):
    """List all tenants."""
    return {"tenants": list_tenants()}


@router.get("/tenants/{tenant_id}")
async def admin_get_tenant(
    tenant_id: int,
    _: None = Depends(verify_admin),
):
    """Get tenant detail."""
    tenant = get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found.")
    plan = get_plan(tenant.plan_id)
    return {
        "id": tenant.id,
        "name": tenant.name,
        "email": tenant.email,
        "plan_id": tenant.plan_id,
        "plan_name": plan.name if plan else None,
        "status": tenant.status,
        "created_at": tenant.created_at,
    }


from pydantic import BaseModel


class TenantUpdateRequest(BaseModel):
    status: Optional[str] = None
    plan_id: Optional[int] = None


@router.patch("/tenants/{tenant_id}")
async def admin_update_tenant(
    tenant_id: int,
    body: TenantUpdateRequest = TenantUpdateRequest(),
    _: None = Depends(verify_admin),
):
    """Update tenant status or plan."""
    tenant = update_tenant(tenant_id, status=body.status, plan_id=body.plan_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found.")
    plan = get_plan(tenant.plan_id)
    return {
        "id": tenant.id,
        "name": tenant.name,
        "status": tenant.status,
        "plan_id": tenant.plan_id,
        "plan_name": plan.name if plan else None,
    }


@router.get("/tenants/{tenant_id}/keys")
async def admin_list_keys(
    tenant_id: int,
    _: None = Depends(verify_admin),
):
    """List API keys for a tenant."""
    keys = list_api_keys_for_tenant(tenant_id)
    return {
        "keys": [
            {"id": k.id, "name": k.name, "key_prefix": k.key_prefix, "created_at": k.created_at}
            for k in keys
        ]
    }


class KeyCreateBody(BaseModel):
    name: str = "Default"


@router.post("/tenants/{tenant_id}/keys")
async def admin_create_key(
    tenant_id: int,
    body: KeyCreateBody = KeyCreateBody(),
    _: None = Depends(verify_admin),
):
    """Create API key for a tenant."""
    raw_key, info = create_api_key(tenant_id, body.name)
    return {"id": info.id, "key": raw_key, "name": info.name}


@router.delete("/tenants/{tenant_id}/keys/{key_id}")
async def admin_revoke_key(
    tenant_id: int,
    key_id: int,
    _: None = Depends(verify_admin),
):
    """Revoke an API key."""
    ok = revoke_api_key(key_id, tenant_id=tenant_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Key not found.")
    return {"status": "revoked"}


@router.get("/tenants/{tenant_id}/usage")
async def admin_get_usage(
    tenant_id: int,
    _: None = Depends(verify_admin),
):
    """Get usage for a tenant."""
    usage = usage_tracker.get_usage_for_tenant(tenant_id)
    history = usage_tracker.get_usage_history_for_tenant(tenant_id)
    return {"current": usage, "history": history}
