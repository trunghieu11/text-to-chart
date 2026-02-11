"""
Base plotter interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd
import plotly.graph_objects as go

from chart_service.models import ChartConfig


class BasePlotter(ABC):
    """Abstract base class for chart plotters."""

    chart_type: str = "base"

    @abstractmethod
    def plot(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """
        Create a Plotly figure from data and config.

        Args:
            df: The data to plot.
            config: Chart configuration.

        Returns:
            A plotly Figure object.
        """
        ...
