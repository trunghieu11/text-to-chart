"""
Line chart type definition.
"""

from __future__ import annotations

import pandas as pd

from chart_service.chart_types.base import ChartType
from chart_service.models import ChartConfig


class LineChartType(ChartType):
    """Line chart: best for time-series and continuous data."""

    name = "line"
    display_name = "Line Chart"
    plotly_express_func = "line"

    def is_suitable_for(self, df: pd.DataFrame, config: ChartConfig | None = None) -> bool:
        """Line charts are suitable when x-axis has ordered/sequential data."""
        numeric_cols = self._get_numeric_columns(df)
        return len(numeric_cols) >= 1 and len(df) >= 2

    def get_default_config(self, df: pd.DataFrame) -> ChartConfig:
        """Auto-detect x and y columns for line chart."""
        numeric_cols = self._get_numeric_columns(df)
        cat_cols = self._get_categorical_columns(df)

        # Use first column as x
        x_col = df.columns[0]
        # Use numeric columns (excluding x if numeric) as y
        y_cols = [c for c in numeric_cols if c != x_col]
        if not y_cols and len(numeric_cols) >= 2:
            x_col = numeric_cols[0]
            y_cols = numeric_cols[1:]
        elif not y_cols:
            y_cols = numeric_cols[:1]

        return ChartConfig(
            chart_type=self.name,
            x_column=x_col,
            y_columns=y_cols,
            title=f"{', '.join(y_cols)} over {x_col}" if y_cols else "Line Chart",
            x_label=x_col,
            y_label=y_cols[0] if len(y_cols) == 1 else "Value",
        )
