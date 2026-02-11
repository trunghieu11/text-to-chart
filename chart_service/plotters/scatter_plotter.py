"""
Scatter chart plotter using Plotly Express.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from chart_service.models import ChartConfig
from chart_service.plotters.base import BasePlotter


class ScatterPlotter(BasePlotter):
    """Plotter for scatter charts."""

    chart_type = "scatter"

    def plot(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        x_col = config.x_column or df.columns[0]
        y_cols = config.y_columns or [
            c for c in df.select_dtypes(include="number").columns if c != x_col
        ]

        if not y_cols:
            numeric = list(df.select_dtypes(include="number").columns)
            if len(numeric) >= 2:
                x_col = numeric[0]
                y_cols = [numeric[1]]
            else:
                y_cols = numeric[:1]

        fig = px.scatter(
            df,
            x=x_col,
            y=y_cols[0] if y_cols else df.columns[1],
            title=config.title or f"{y_cols[0] if y_cols else 'Y'} vs {x_col}",
            template=config.template,
        )

        fig.update_layout(
            xaxis_title=config.x_label or x_col,
            yaxis_title=config.y_label or (y_cols[0] if y_cols else "Value"),
        )

        return fig
