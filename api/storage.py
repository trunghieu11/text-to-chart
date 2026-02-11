"""
In-memory chart storage for the API.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio

from chart_service.models import ChartConfig


class ChartStore:
    """In-memory chart storage with TTL support."""

    def __init__(self, ttl_hours: int = 24):
        self._store: dict[str, dict[str, Any]] = {}
        self._ttl_hours = ttl_hours

    def save(
        self,
        fig: go.Figure,
        df: pd.DataFrame,
        config: ChartConfig,
        chart_id: str | None = None,
    ) -> str:
        """
        Save a chart and return its ID.

        Returns:
            The chart ID.
        """
        if chart_id is None:
            chart_id = str(uuid.uuid4())

        self._store[chart_id] = {
            "figure_json": json.loads(pio.to_json(fig)),
            "dataframe_dict": df.to_dict("list"),
            "config": config.to_dict(),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        self._cleanup()
        return chart_id

    def get(self, chart_id: str) -> dict[str, Any] | None:
        """Get chart data by ID."""
        return self._store.get(chart_id)

    def get_figure(self, chart_id: str) -> go.Figure | None:
        """Reconstruct the Plotly figure from storage."""
        data = self.get(chart_id)
        if data is None:
            return None
        return go.Figure(data["figure_json"])

    def get_dataframe(self, chart_id: str) -> pd.DataFrame | None:
        """Reconstruct the DataFrame from storage."""
        data = self.get(chart_id)
        if data is None:
            return None
        return pd.DataFrame(data["dataframe_dict"])

    def get_config(self, chart_id: str) -> ChartConfig | None:
        """Reconstruct the ChartConfig from storage."""
        data = self.get(chart_id)
        if data is None:
            return None
        return ChartConfig.from_dict(data["config"])

    def exists(self, chart_id: str) -> bool:
        """Check if a chart exists."""
        return chart_id in self._store

    def delete(self, chart_id: str) -> bool:
        """Delete a chart. Returns True if it existed."""
        return self._store.pop(chart_id, None) is not None

    def _cleanup(self):
        """Remove expired charts."""
        now = datetime.now(timezone.utc)
        expired = []
        for cid, data in self._store.items():
            created = datetime.fromisoformat(data["created_at"])
            age_hours = (now - created).total_seconds() / 3600
            if age_hours > self._ttl_hours:
                expired.append(cid)
        for cid in expired:
            del self._store[cid]


# Global store instance (reads TTL from config)
def _create_store() -> ChartStore:
    try:
        from config import config
        return ChartStore(ttl_hours=config.chart_ttl_hours)
    except Exception:
        return ChartStore()


chart_store = _create_store()
