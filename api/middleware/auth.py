"""
API key authentication middleware.

Supports:
1. SaaS tenant keys (DB lookup by hash)
2. Env-based API_KEYS fallback (no tenant, default rate limit, no quota)
3. Dev mode (no keys configured)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

# API key header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


@dataclass
class TenantContext:
    """Context from API key auth: tenant_id, plan, and api_key for rate limit/usage."""

    api_key: str
    tenant_id: Optional[int] = None
    plan: Optional[object] = None

    @property
    def rate_limit(self) -> str:
        """Rate limit string from plan or config default."""
        if self.plan is not None and hasattr(self.plan, "rate_limit"):
            return self.plan.rate_limit
        from config import config
        return config.rate_limit

    @property
    def monthly_quota(self) -> Optional[int]:
        """Monthly quota from plan. None means no quota (env fallback)."""
        if self.plan is not None and hasattr(self.plan, "monthly_quota"):
            return self.plan.monthly_quota
        return None

    def has_quota(self) -> bool:
        """True if quota should be enforced (tenant from DB)."""
        return self.tenant_id is not None and self.monthly_quota is not None


def get_api_keys() -> set:
    """Load API keys from centralized config (env fallback)."""
    from config import config

    if not config.api_keys:
        return set()
    return set(config.api_keys)


async def verify_api_key(
    api_key: Optional[str] = Security(api_key_header),
) -> TenantContext:
    """
    Verify the API key from the X-API-Key header.

    Returns TenantContext with tenant_id, plan (if from DB), or fallback for env/dev.

    Raises:
        HTTPException 401 if key is missing or invalid.
    """
    # 1. Try SaaS DB lookup first (if key provided)
    if api_key:
        try:
            from api.saas.repository import get_tenant_by_key

            result = get_tenant_by_key(api_key)
            if result is not None:
                return TenantContext(
                    api_key=api_key,
                    tenant_id=result.tenant.id,
                    plan=result.plan,
                )
        except Exception:
            pass  # Fall through to env check

        # 2. Env fallback: check if key is in API_KEYS
        valid_keys = get_api_keys()
        if valid_keys and api_key in valid_keys:
            return TenantContext(api_key=api_key, tenant_id=None, plan=None)

    # 3. No keys configured = dev mode
    valid_keys = get_api_keys()
    if not valid_keys:
        return TenantContext(api_key=api_key or "dev", tenant_id=None, plan=None)

    # 4. Reject
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API key. Provide X-API-Key header.",
        )

    raise HTTPException(
        status_code=401,
        detail="Invalid API key.",
    )
