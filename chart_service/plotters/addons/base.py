"""
Base add-on interface for the plotter pipeline.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import plotly.graph_objects as go

from chart_service.models import ChartConfig


class PlotAddon(ABC):
    """Abstract base class for plotter add-ons."""

    name: str = "base_addon"
    order: int = 0  # Lower = applied first

    @abstractmethod
    def apply(self, fig: go.Figure, config: ChartConfig) -> go.Figure:
        """
        Apply this add-on to a figure.

        Args:
            fig: The Plotly figure to modify.
            config: Chart configuration with add-on options.

        Returns:
            The modified figure.
        """
        ...
