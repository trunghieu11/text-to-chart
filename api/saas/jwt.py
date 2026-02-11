"""
JWT utilities for account (Developer Portal) authentication.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

JWT_SECRET = os.environ.get("JWT_SECRET", "change-me-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRES_HOURS = 24 * 7  # 7 days


def create_token(tenant_id: int, email: str) -> str:
    """Create a JWT for the given tenant."""
    from jose import jwt

    now = datetime.now(timezone.utc)
    expire = now + timedelta(hours=JWT_EXPIRES_HOURS)
    payload = {
        "sub": str(tenant_id),
        "email": email,
        "iat": now,
        "exp": expire,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate JWT. Returns payload or None."""
    from jose import JWTError, jwt

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        return None
