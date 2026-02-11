"""
API key authentication middleware.
"""

from __future__ import annotations

from typing import Optional

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

# API key header schemes
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_api_keys() -> set:
    """Load API keys from centralized config."""
    from config import config

    if not config.api_keys:
        # If no keys configured, allow all (development mode)
        return set()
    return set(config.api_keys)


async def verify_api_key(
    api_key: Optional[str] = Security(api_key_header),
) -> str:
    """
    Verify the API key from the X-API-Key header.

    Returns the API key if valid.

    Raises:
        HTTPException 401 if key is missing or invalid.
    """
    valid_keys = get_api_keys()

    # If no keys configured, allow all requests (dev mode)
    if not valid_keys:
        return api_key or "dev"

    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API key. Provide X-API-Key header.",
        )

    if api_key not in valid_keys:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key.",
        )

    return api_key
