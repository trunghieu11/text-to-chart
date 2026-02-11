"""
Usage tracking for API keys.

Tracks request counts per API key per period.
"""

from __future__ import annotations

import sqlite3
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


class UsageTracker:
    """Track API usage per key using SQLite."""

    def __init__(self, db_path: str | None = None):
        if db_path is None:
            db_path = os.environ.get("USAGE_DB_PATH", "usage.db")
        self._db_path = db_path
        self._init_db()

    def _init_db(self):
        """Create usage table if it doesn't exist."""
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    api_key TEXT NOT NULL,
                    endpoint TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    period TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_usage_key_period
                ON usage (api_key, period)
            """)
            conn.commit()

    def record(self, api_key: str, endpoint: str = "/v1/charts") -> None:
        """Record a request for the given API key."""
        now = datetime.now(timezone.utc)
        period = now.strftime("%Y-%m")  # Monthly periods

        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                "INSERT INTO usage (api_key, endpoint, timestamp, period) VALUES (?, ?, ?, ?)",
                (api_key, endpoint, now.isoformat(), period),
            )
            conn.commit()

    def get_count(self, api_key: str, period: str | None = None) -> int:
        """
        Get the request count for an API key in a period.

        Args:
            api_key: The API key.
            period: Period string (e.g. "2025-01"). Defaults to current month.

        Returns:
            Request count.
        """
        if period is None:
            period = datetime.now(timezone.utc).strftime("%Y-%m")

        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM usage WHERE api_key = ? AND period = ?",
                (api_key, period),
            )
            return cursor.fetchone()[0]

    def get_usage(self, api_key: str, period: str | None = None) -> dict:
        """Get usage stats for an API key."""
        if period is None:
            period = datetime.now(timezone.utc).strftime("%Y-%m")

        count = self.get_count(api_key, period)
        return {
            "api_key": api_key[:8] + "...",  # Mask key
            "period_start": f"{period}-01",
            "request_count": count,
        }


# Global instance
usage_tracker = UsageTracker()
