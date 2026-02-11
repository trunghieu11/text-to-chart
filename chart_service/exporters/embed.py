"""
Embed exporter: generates standalone HTML for embedding charts.
"""

from __future__ import annotations

import json
import uuid
from typing import Optional

import plotly.graph_objects as go
import plotly.io as pio


# In-memory store for embeddable charts
_chart_store: dict[str, dict] = {}


class EmbedExporter:
    """Export charts as embeddable HTML."""

    @staticmethod
    def store_chart(fig: go.Figure, chart_id: str | None = None) -> str:
        """
        Store a chart figure and return its ID.

        Args:
            fig: The Plotly figure.
            chart_id: Optional custom ID. If None, generates UUID.

        Returns:
            The chart ID.
        """
        from datetime import datetime, timezone

        if chart_id is None:
            chart_id = str(uuid.uuid4())

        _chart_store[chart_id] = {
            "figure_json": json.loads(pio.to_json(fig)),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        return chart_id

    @staticmethod
    def get_chart(chart_id: str) -> dict | None:
        """Retrieve a stored chart by ID."""
        return _chart_store.get(chart_id)

    @staticmethod
    def generate_embed_html(fig: go.Figure) -> str:
        """
        Generate a standalone HTML page with the Plotly chart.

        Args:
            fig: The Plotly figure.

        Returns:
            Complete HTML string.
        """
        fig_json = pio.to_json(fig)

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chart</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{ margin: 0; padding: 0; }}
        #chart {{ width: 100%; height: 100vh; }}
    </style>
</head>
<body>
    <div id="chart"></div>
    <script>
        var figData = {fig_json};
        Plotly.newPlot('chart', figData.data, figData.layout, {{responsive: true}});
    </script>
</body>
</html>"""
        return html

    @staticmethod
    def get_embed_url(chart_id: str, base_url: str = "http://localhost:8000") -> str:
        """Get the embed URL for a stored chart."""
        return f"{base_url}/v1/charts/{chart_id}/embed"

    @staticmethod
    def clear_store():
        """Clear the in-memory chart store."""
        _chart_store.clear()

    @staticmethod
    def get_store() -> dict:
        """Get reference to the chart store (for API use)."""
        return _chart_store
