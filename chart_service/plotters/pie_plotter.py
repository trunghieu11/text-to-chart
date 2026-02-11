"""
Pie chart plotter using Plotly Express.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from chart_service.models import ChartConfig
from chart_service.plotters.base import BasePlotter


class PiePlotter(BasePlotter):
    """Plotter for pie charts."""

    chart_type = "pie"

    def plot(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        names_col = config.x_column  # names for pie chart
        values_col = config.y_columns[0] if config.y_columns else None

        if not names_col or not values_col:
            cat_cols = list(df.select_dtypes(exclude="number").columns)
            num_cols = list(df.select_dtypes(include="number").columns)
            names_col = names_col or (cat_cols[0] if cat_cols else df.columns[0])
            values_col = values_col or (num_cols[0] if num_cols else df.columns[1])

        fig = px.pie(
            df,
            names=names_col,
            values=values_col,
            title=config.title or f"{values_col} Distribution by {names_col}",
            template=config.template,
        )

        return fig
