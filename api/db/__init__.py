"""
Database initialization and schema for SaaS (plans, tenants, api_keys).
"""

from __future__ import annotations

from api.db.schema import init_db, seed_plans


def _get_db_path() -> str:
    try:
        from config import config
        return config.saas_db_path
    except Exception:
        return "saas.db"


def ensure_db() -> None:
    """Ensure DB exists with schema and seed data."""
    path = _get_db_path()
    init_db(path)
    seed_plans(path)
