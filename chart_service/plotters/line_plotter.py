"""
Line chart plotter using Plotly Express.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from chart_service.models import ChartConfig
from chart_service.plotters.base import BasePlotter


class LinePlotter(BasePlotter):
    """Plotter for line charts."""

    chart_type = "line"

    def plot(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        x_col = config.x_column or df.columns[0]
        y_cols = config.y_columns or [
            c for c in df.select_dtypes(include="number").columns if c != x_col
        ]

        if len(y_cols) == 1:
            fig = px.line(
                df,
                x=x_col,
                y=y_cols[0],
                title=config.title or f"{y_cols[0]} over {x_col}",
                template=config.template,
            )
        else:
            fig = px.line(
                df,
                x=x_col,
                y=y_cols,
                title=config.title or "Line Chart",
                template=config.template,
            )

        fig.update_layout(
            xaxis_title=config.x_label or x_col,
            yaxis_title=config.y_label or (y_cols[0] if len(y_cols) == 1 else "Value"),
        )

        return fig
