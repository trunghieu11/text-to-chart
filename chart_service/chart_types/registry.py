"""
Chart type registry: manages chart type instances and provides type inference.
"""

from __future__ import annotations

import pandas as pd

from chart_service.chart_types.base import ChartType


class ChartTypeRegistry:
    """Registry of chart types with rule-based inference."""

    def __init__(self) -> None:
        self._types: dict[str, ChartType] = {}

    def register(self, chart_type: ChartType) -> None:
        """Register a chart type."""
        self._types[chart_type.name] = chart_type

    def get(self, name: str) -> ChartType:
        """
        Get a chart type by name.

        Raises:
            KeyError: If chart type is not registered.
        """
        if name not in self._types:
            raise KeyError(
                f"Chart type '{name}' not found. "
                f"Available types: {self.list_types()}"
            )
        return self._types[name]

    def list_types(self) -> list[str]:
        """Return list of registered chart type names."""
        return list(self._types.keys())

    def list_display_names(self) -> list[tuple[str, str]]:
        """Return list of (name, display_name) tuples."""
        return [(ct.name, ct.display_name) for ct in self._types.values()]

    def infer_best_type(self, df: pd.DataFrame) -> str:
        """
        Rule-based inference of the best chart type for the given data.

        Rules:
        - 1 numeric column only: bar chart
        - 1 categorical + 1 numeric, categorical has few unique values: pie (if <= 8)
        - 1 categorical + 1 numeric, categorical has many values: bar
        - 2 numeric columns: scatter
        - 1 categorical + multiple numeric: bar (grouped)
        - Time-series like x column: line
        - Default: bar
        """
        numeric_cols = list(df.select_dtypes(include="number").columns)
        cat_cols = list(df.select_dtypes(exclude="number").columns)
        n_num = len(numeric_cols)
        n_cat = len(cat_cols)

        # Check for time-series: first column looks like dates
        first_col = df.columns[0]
        if self._is_datetime_like(df[first_col]):
            if "line" in self._types:
                return "line"

        # Only numeric columns
        if n_cat == 0 and n_num >= 2:
            if n_num == 2 and "scatter" in self._types:
                return "scatter"
            if "line" in self._types:
                return "line"

        # 1 categorical + 1 numeric
        if n_cat >= 1 and n_num == 1:
            cat_col = cat_cols[0]
            unique_count = df[cat_col].nunique()
            if unique_count <= 8 and "pie" in self._types:
                return "pie"
            if "bar" in self._types:
                return "bar"

        # 1 categorical + multiple numeric
        if n_cat >= 1 and n_num > 1:
            if "bar" in self._types:
                return "bar"

        # 1 numeric column only (no categorical)
        if n_num == 1 and n_cat == 0:
            if "bar" in self._types:
                return "bar"

        # Default
        if "bar" in self._types:
            return "bar"

        # Fallback to first registered type
        return self.list_types()[0]

    @staticmethod
    def _is_datetime_like(series: pd.Series) -> bool:
        """Check if a series looks like datetime data."""
        if pd.api.types.is_datetime64_any_dtype(series):
            return True
        # Try parsing as dates
        if series.dtype == object:
            try:
                pd.to_datetime(series, format="mixed")
                return True
            except (ValueError, TypeError):
                pass
        return False
