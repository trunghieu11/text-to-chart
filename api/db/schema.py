"""
SaaS database schema: plans, tenants, api_keys.
"""

from __future__ import annotations

import sqlite3
from typing import Optional


def init_db(db_path: str) -> None:
    """Create tables if they don't exist."""
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                rate_limit TEXT NOT NULL DEFAULT '60/minute',
                monthly_quota INTEGER NOT NULL DEFAULT 1000,
                features TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tenants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                plan_id INTEGER NOT NULL REFERENCES plans(id),
                status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'suspended')),
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id INTEGER NOT NULL REFERENCES tenants(id),
                key_hash TEXT NOT NULL UNIQUE,
                key_prefix TEXT NOT NULL,
                name TEXT NOT NULL DEFAULT 'Default',
                created_at TEXT NOT NULL,
                expires_at TEXT
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_api_keys_key_hash ON api_keys(key_hash)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_api_keys_tenant ON api_keys(tenant_id)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_tenants_email ON tenants(email)
        """)
        conn.commit()


def seed_plans(db_path: str) -> None:
    """Seed default plans if none exist."""
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute("SELECT COUNT(*) FROM plans")
        if cursor.fetchone()[0] > 0:
            return
        conn.execute("""
            INSERT INTO plans (name, rate_limit, monthly_quota, features)
            VALUES
                ('free', '10/minute', 100, '{"image_parsing": false}'),
                ('pro', '100/minute', 10000, '{"image_parsing": true}'),
                ('enterprise', '1000/minute', 100000, '{"image_parsing": true, "priority": true}')
        """)
        conn.commit()
