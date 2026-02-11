"""
Pie chart type definition.
"""

from __future__ import annotations

import pandas as pd

from chart_service.chart_types.base import ChartType
from chart_service.models import ChartConfig


class PieChartType(ChartType):
    """Pie chart: best for showing parts of a whole."""

    name = "pie"
    display_name = "Pie Chart"
    plotly_express_func = "pie"

    def is_suitable_for(self, df: pd.DataFrame, config: ChartConfig | None = None) -> bool:
        """Pie charts need 1 categorical + 1 numeric, with few categories."""
        numeric_cols = self._get_numeric_columns(df)
        cat_cols = self._get_categorical_columns(df)
        if len(numeric_cols) >= 1 and len(cat_cols) >= 1:
            return df[cat_cols[0]].nunique() <= 15
        return False

    def get_default_config(self, df: pd.DataFrame) -> ChartConfig:
        """Auto-detect names and values columns for pie chart."""
        numeric_cols = self._get_numeric_columns(df)
        cat_cols = self._get_categorical_columns(df)

        if cat_cols and numeric_cols:
            names_col = cat_cols[0]
            values_col = numeric_cols[0]
        elif len(df.columns) >= 2:
            names_col = df.columns[0]
            values_col = df.columns[1]
        else:
            names_col = df.columns[0]
            values_col = df.columns[0]

        return ChartConfig(
            chart_type=self.name,
            x_column=names_col,  # names for pie
            y_columns=[values_col],  # values for pie
            title=f"{values_col} Distribution by {names_col}",
            x_label=names_col,
            y_label=values_col,
        )
