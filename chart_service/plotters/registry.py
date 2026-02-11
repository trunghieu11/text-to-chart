"""
Plotter registry: manages plotter instances and add-on pipeline.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from chart_service.models import ChartConfig
from chart_service.plotters.base import BasePlotter
from chart_service.plotters.addons.base import PlotAddon


class PlotterRegistry:
    """Registry of chart plotters with an add-on pipeline."""

    def __init__(self) -> None:
        self._plotters: dict[str, BasePlotter] = {}
        self._addons: list[PlotAddon] = []

    def register_plotter(self, plotter: BasePlotter) -> None:
        """Register a plotter for a specific chart type."""
        self._plotters[plotter.chart_type] = plotter

    def register_addon(self, addon: PlotAddon) -> None:
        """Register a plot add-on. Add-ons are applied in order of their `order` attribute."""
        self._addons.append(addon)
        self._addons.sort(key=lambda a: a.order)

    def get_plotter(self, chart_type: str) -> BasePlotter:
        """
        Get the plotter for a chart type.

        Raises:
            KeyError: If no plotter is registered for the chart type.
        """
        if chart_type not in self._plotters:
            raise KeyError(
                f"No plotter registered for chart type '{chart_type}'. "
                f"Available: {list(self._plotters.keys())}"
            )
        return self._plotters[chart_type]

    def plot(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """
        Create a figure using the appropriate plotter and apply all add-ons.

        1. Find the plotter for config.chart_type
        2. Create base figure
        3. Apply each registered add-on in order

        Returns:
            Final Plotly figure.
        """
        plotter = self.get_plotter(config.chart_type)
        fig = plotter.plot(df, config)

        # Apply add-on pipeline
        for addon in self._addons:
            fig = addon.apply(fig, config)

        return fig

    def list_plotters(self) -> list[str]:
        """Return list of registered plotter chart types."""
        return list(self._plotters.keys())
