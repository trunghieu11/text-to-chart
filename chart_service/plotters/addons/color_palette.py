"""
Color palette add-on: applies custom or preset color palettes to charts.
"""

from __future__ import annotations

import plotly.graph_objects as go

from chart_service.models import ChartConfig
from chart_service.plotters.addons.base import PlotAddon

# Preset palettes
PALETTES = {
    "default": None,  # Use plotly default
    "vibrant": ["#e6194b", "#3cb44b", "#ffe119", "#4363d8", "#f58231", "#911eb4", "#42d4f4", "#f032e6"],
    "pastel": ["#fbb4ae", "#b3cde3", "#ccebc5", "#decbe4", "#fed9a6", "#ffffcc", "#e5d8bd", "#fddaec"],
    "earth": ["#8c510a", "#d8b365", "#f6e8c3", "#c7eae5", "#5ab4ac", "#01665e"],
    "ocean": ["#023e8a", "#0077b6", "#0096c7", "#00b4d8", "#48cae4", "#90e0ef", "#ade8f4"],
    "sunset": ["#ff6b6b", "#ffa06b", "#ffd93d", "#6bff6b", "#6bd9ff", "#6b6bff", "#ff6bff"],
}


class ColorPaletteAddon(PlotAddon):
    """Apply a color palette to the chart."""

    name = "color_palette"
    order = 10

    def apply(self, fig: go.Figure, config: ChartConfig) -> go.Figure:
        if not config.color_palette:
            return fig

        palette = config.color_palette
        # Check if it's a preset name
        if len(palette) == 1 and palette[0] in PALETTES:
            palette = PALETTES[palette[0]]
            if palette is None:
                return fig

        # Apply colors to traces
        for i, trace in enumerate(fig.data):
            # Pie charts use marker.colors (plural) — set all sector colors at once
            if isinstance(trace, go.Pie):
                trace.marker.colors = palette
                continue

            if i < len(palette):
                if hasattr(trace, "marker") and trace.marker is not None:
                    trace.marker.color = palette[i]
                if hasattr(trace, "line") and trace.line is not None:
                    trace.line.color = palette[i]

        return fig
