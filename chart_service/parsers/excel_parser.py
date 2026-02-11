"""
Excel parser: handles .xlsx and .xls file uploads.
"""

from __future__ import annotations

from io import BytesIO
from typing import Optional, Union

import pandas as pd

from chart_service.parsers.base import BaseParser


class ExcelParser(BaseParser):
    """Parse Excel file bytes into a DataFrame."""

    name = "excel"
    supported_extensions = [".xlsx", ".xls"]
    supported_mime_types = [
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel",
    ]

    def can_handle(
        self, raw_input: Union[str, bytes], filename: Optional[str] = None
    ) -> bool:
        if filename:
            return self._get_extension(filename) in self.supported_extensions
        return False

    def parse(
        self, raw_input: Union[str, bytes], filename: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Parse Excel file bytes (reads first sheet by default).
        """
        if isinstance(raw_input, str):
            raise ValueError("Excel parser requires bytes input, not string")

        try:
            df = pd.read_excel(BytesIO(raw_input), sheet_name=0, engine="openpyxl")
        except Exception as e:
            raise ValueError(f"Failed to parse Excel file: {e}") from e

        if df.empty:
            raise ValueError("Excel file resulted in an empty DataFrame")

        # Try to convert numeric columns
        for col in df.columns:
            try:
                df[col] = pd.to_numeric(df[col])
            except (ValueError, TypeError):
                pass

        return df
