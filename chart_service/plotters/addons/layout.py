"""
Layout add-on: configures chart layout (template, margins, legend).
"""

from __future__ import annotations

import plotly.graph_objects as go

from chart_service.models import ChartConfig
from chart_service.plotters.addons.base import PlotAddon


class LayoutAddon(PlotAddon):
    """Apply layout customizations to the chart."""

    name = "layout"
    order = 100  # Applied last

    def apply(self, fig: go.Figure, config: ChartConfig) -> go.Figure:
        layout_updates = {}

        # Apply template
        if config.template:
            layout_updates["template"] = config.template

        # Apply annotations
        if config.annotations:
            annotations = []
            for ann in config.annotations:
                annotations.append(
                    dict(
                        x=ann.get("x"),
                        y=ann.get("y"),
                        text=ann.get("text", ""),
                        showarrow=ann.get("showarrow", True),
                        arrowhead=ann.get("arrowhead", 2),
                        font=dict(size=ann.get("font_size", 12)),
                    )
                )
            layout_updates["annotations"] = annotations

        # Standard layout improvements
        layout_updates.update(
            {
                "font": dict(family="Inter, Arial, sans-serif"),
                "hoverlabel": dict(bgcolor="white", font_size=13),
                "margin": dict(l=60, r=30, t=60, b=60),
            }
        )

        if layout_updates:
            fig.update_layout(**layout_updates)

        return fig
