"""
Bar chart type definition.
"""

from __future__ import annotations

import pandas as pd

from chart_service.chart_types.base import ChartType
from chart_service.models import ChartConfig


class BarChartType(ChartType):
    """Bar chart: best for categorical comparisons."""

    name = "bar"
    display_name = "Bar Chart"
    plotly_express_func = "bar"

    def is_suitable_for(self, df: pd.DataFrame, config: ChartConfig | None = None) -> bool:
        """Bar charts work well with categorical x and numeric y."""
        numeric_cols = self._get_numeric_columns(df)
        return len(numeric_cols) >= 1

    def get_default_config(self, df: pd.DataFrame) -> ChartConfig:
        """Auto-detect x and y columns for bar chart."""
        numeric_cols = self._get_numeric_columns(df)
        cat_cols = self._get_categorical_columns(df)

        if cat_cols:
            x_col = cat_cols[0]
            y_cols = numeric_cols[:3]  # Up to 3 numeric columns
        else:
            x_col = df.columns[0]
            y_cols = [c for c in numeric_cols if c != x_col][:3]
            if not y_cols:
                y_cols = numeric_cols[:1]

        return ChartConfig(
            chart_type=self.name,
            x_column=x_col,
            y_columns=y_cols,
            title=f"{', '.join(y_cols)} by {x_col}" if y_cols else "Bar Chart",
            x_label=x_col,
            y_label=y_cols[0] if len(y_cols) == 1 else "Value",
        )
