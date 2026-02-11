"""
Base chart type interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd

from chart_service.models import ChartConfig


class ChartType(ABC):
    """Abstract base class for chart types."""

    name: str = "base"
    display_name: str = "Base Chart"
    plotly_express_func: str = ""  # e.g. "line", "bar"

    @abstractmethod
    def is_suitable_for(self, df: pd.DataFrame, config: ChartConfig | None = None) -> bool:
        """Check if this chart type is suitable for the given data."""
        ...

    @abstractmethod
    def get_default_config(self, df: pd.DataFrame) -> ChartConfig:
        """Generate a default ChartConfig for the given data."""
        ...

    def _get_numeric_columns(self, df: pd.DataFrame) -> list[str]:
        """Helper: get numeric column names."""
        return list(df.select_dtypes(include="number").columns)

    def _get_categorical_columns(self, df: pd.DataFrame) -> list[str]:
        """Helper: get non-numeric column names."""
        return list(df.select_dtypes(exclude="number").columns)
