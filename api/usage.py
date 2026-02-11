"""
Usage tracking for API keys and tenants.

Tracks request counts per API key (legacy) or tenant_id per period.
"""

from __future__ import annotations

import sqlite3
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


class UsageTracker:
    """Track API usage per key or tenant using SQLite."""

    def __init__(self, db_path: str | None = None):
        if db_path is None:
            db_path = os.environ.get("USAGE_DB_PATH", "usage.db")
        self._db_path = db_path
        self._init_db()

    def _init_db(self):
        """Create usage table if it doesn't exist; add tenant_id if missing."""
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    api_key TEXT,
                    tenant_id INTEGER,
                    endpoint TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    period TEXT NOT NULL
                )
            """)
            conn.commit()
            # Add tenant_id to existing tables (ignore if already present)
            try:
                conn.execute("ALTER TABLE usage ADD COLUMN tenant_id INTEGER")
                conn.commit()
            except sqlite3.OperationalError:
                pass  # Column already exists
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_usage_key_period
                ON usage (api_key, period)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_usage_tenant_period
                ON usage (tenant_id, period)
            """)
            conn.commit()

    def record(self, api_key: str, endpoint: str = "/v1/charts") -> None:
        """Record a request for the given API key (legacy)."""
        now = datetime.now(timezone.utc)
        period = now.strftime("%Y-%m")

        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                "INSERT INTO usage (api_key, tenant_id, endpoint, timestamp, period) VALUES (?, ?, ?, ?, ?)",
                (api_key, None, endpoint, now.isoformat(), period),
            )
            conn.commit()

    def record_for_tenant(self, tenant_id: int, endpoint: str = "/v1/charts") -> None:
        """Record a request for the given tenant."""
        now = datetime.now(timezone.utc)
        period = now.strftime("%Y-%m")

        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                "INSERT INTO usage (api_key, tenant_id, endpoint, timestamp, period) VALUES (?, ?, ?, ?, ?)",
                ("", tenant_id, endpoint, now.isoformat(), period),
            )
            conn.commit()

    def get_count(self, api_key: str, period: str | None = None) -> int:
        """Get the request count for an API key in a period."""
        if period is None:
            period = datetime.now(timezone.utc).strftime("%Y-%m")

        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM usage WHERE api_key = ? AND period = ?",
                (api_key, period),
            )
            return cursor.fetchone()[0]

    def get_count_for_tenant(self, tenant_id: int, period: str | None = None) -> int:
        """Get the request count for a tenant in a period."""
        if period is None:
            period = datetime.now(timezone.utc).strftime("%Y-%m")

        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM usage WHERE tenant_id = ? AND period = ?",
                (tenant_id, period),
            )
            return cursor.fetchone()[0]

    def get_usage(self, api_key: str, period: str | None = None) -> dict:
        """Get usage stats for an API key."""
        if period is None:
            period = datetime.now(timezone.utc).strftime("%Y-%m")

        count = self.get_count(api_key, period)
        return {
            "api_key": api_key[:8] + "..." if api_key and len(api_key) >= 8 else "***",
            "period_start": f"{period}-01",
            "request_count": count,
        }

    def get_usage_for_tenant(
        self, tenant_id: int, period: str | None = None
    ) -> dict:
        """Get usage stats for a tenant."""
        if period is None:
            period = datetime.now(timezone.utc).strftime("%Y-%m")

        count = self.get_count_for_tenant(tenant_id, period)
        return {
            "tenant_id": tenant_id,
            "period_start": f"{period}-01",
            "request_count": count,
        }

    def get_usage_history_for_tenant(
        self, tenant_id: int, limit: int = 12
    ) -> list[dict]:
        """Get usage history (by period) for a tenant."""
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute("""
                SELECT period, COUNT(*) as count
                FROM usage
                WHERE tenant_id = ?
                GROUP BY period
                ORDER BY period DESC
                LIMIT ?
            """, (tenant_id, limit))
            rows = cursor.fetchall()
        return [
            {"period": r[0], "period_start": f"{r[0]}-01", "request_count": r[1]}
            for r in rows
        ]


# Global instance
usage_tracker = UsageTracker()
