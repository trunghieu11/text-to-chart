"""
Scatter chart type definition.
"""

from __future__ import annotations

import pandas as pd

from chart_service.chart_types.base import ChartType
from chart_service.models import ChartConfig


class ScatterChartType(ChartType):
    """Scatter chart: best for showing relationships between two numeric variables."""

    name = "scatter"
    display_name = "Scatter Chart"
    plotly_express_func = "scatter"

    def is_suitable_for(self, df: pd.DataFrame, config: ChartConfig | None = None) -> bool:
        """Scatter charts need at least 2 numeric columns."""
        numeric_cols = self._get_numeric_columns(df)
        return len(numeric_cols) >= 2

    def get_default_config(self, df: pd.DataFrame) -> ChartConfig:
        """Auto-detect x and y columns for scatter chart."""
        numeric_cols = self._get_numeric_columns(df)

        if len(numeric_cols) >= 2:
            x_col = numeric_cols[0]
            y_cols = [numeric_cols[1]]
        else:
            x_col = df.columns[0]
            y_cols = numeric_cols[:1]

        return ChartConfig(
            chart_type=self.name,
            x_column=x_col,
            y_columns=y_cols,
            title=f"{y_cols[0]} vs {x_col}" if y_cols else "Scatter Chart",
            x_label=x_col,
            y_label=y_cols[0] if y_cols else "Value",
        )
