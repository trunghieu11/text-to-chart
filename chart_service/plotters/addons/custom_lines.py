"""
Custom lines add-on: adds reference lines (horizontal/vertical) to charts.
"""

from __future__ import annotations

import plotly.graph_objects as go

from chart_service.models import ChartConfig
from chart_service.plotters.addons.base import PlotAddon


class CustomLinesAddon(PlotAddon):
    """Add reference lines to the chart."""

    name = "custom_lines"
    order = 20

    def apply(self, fig: go.Figure, config: ChartConfig) -> go.Figure:
        if not config.reference_lines:
            return fig

        for line_spec in config.reference_lines:
            orientation = line_spec.get("orientation", "h")
            value = line_spec.get("value")
            color = line_spec.get("color", "red")
            dash = line_spec.get("dash", "dash")
            label = line_spec.get("label", "")
            width = line_spec.get("width", 2)

            if value is None:
                continue

            if orientation == "h":
                fig.add_hline(
                    y=value,
                    line_dash=dash,
                    line_color=color,
                    line_width=width,
                    annotation_text=label,
                )
            elif orientation == "v":
                fig.add_vline(
                    x=value,
                    line_dash=dash,
                    line_color=color,
                    line_width=width,
                    annotation_text=label,
                )

        return fig
