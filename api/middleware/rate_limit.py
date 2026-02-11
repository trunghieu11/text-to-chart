"""
Rate limiting middleware using slowapi.
"""

from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address


def _get_api_key_or_ip(request) -> str:
    """Extract rate limit key from API key header or IP address."""
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return f"key:{api_key}"
    return get_remote_address(request)


def _get_rate_limit() -> str:
    """Load rate limit from centralized config."""
    from config import config
    return config.rate_limit


# Default rate limit (read from config)
DEFAULT_RATE_LIMIT = _get_rate_limit()

# Create limiter instance
limiter = Limiter(key_func=_get_api_key_or_ip)
