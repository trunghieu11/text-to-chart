"""
Data models for the chart service.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import pandas as pd


@dataclass
class ChartConfig:
    """Configuration for chart generation."""

    chart_type: str = "bar"
    x_column: Optional[str] = None
    y_columns: list[str] = field(default_factory=list)
    title: Optional[str] = None
    x_label: Optional[str] = None
    y_label: Optional[str] = None

    # Add-on options (Phase 4)
    color_palette: Optional[list[str]] = None
    reference_lines: Optional[list[dict]] = None
    annotations: Optional[list[dict]] = None
    template: str = "plotly_white"

    def to_dict(self) -> dict:
        """Serialize config to dict."""
        return {
            "chart_type": self.chart_type,
            "x_column": self.x_column,
            "y_columns": self.y_columns,
            "title": self.title,
            "x_label": self.x_label,
            "y_label": self.y_label,
            "color_palette": self.color_palette,
            "reference_lines": self.reference_lines,
            "annotations": self.annotations,
            "template": self.template,
        }

    @classmethod
    def from_dict(cls, data: dict) -> ChartConfig:
        """Deserialize config from dict."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ParsedData:
    """Wrapper around a parsed DataFrame with metadata."""

    dataframe: pd.DataFrame
    source_type: str = "unknown"  # text, csv, excel, image

    @property
    def columns(self) -> list[str]:
        return list(self.dataframe.columns)

    @property
    def shape(self) -> tuple[int, int]:
        return self.dataframe.shape

    @property
    def numeric_columns(self) -> list[str]:
        return list(self.dataframe.select_dtypes(include="number").columns)

    @property
    def categorical_columns(self) -> list[str]:
        return list(self.dataframe.select_dtypes(exclude="number").columns)
