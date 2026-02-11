"""
CSV parser: handles .csv file uploads.
"""

from __future__ import annotations

from io import BytesIO, StringIO
from typing import Optional, Union

import pandas as pd

from chart_service.parsers.base import BaseParser


class CSVParser(BaseParser):
    """Parse CSV file bytes into a DataFrame."""

    name = "csv"
    supported_extensions = [".csv"]
    supported_mime_types = ["text/csv", "application/csv"]

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
        Parse CSV file bytes with encoding fallback (utf-8 -> latin-1).
        """
        if isinstance(raw_input, str):
            df = pd.read_csv(StringIO(raw_input))
        else:
            try:
                df = pd.read_csv(BytesIO(raw_input), encoding="utf-8")
            except UnicodeDecodeError:
                df = pd.read_csv(BytesIO(raw_input), encoding="latin-1")

        if df.empty:
            raise ValueError("CSV file resulted in an empty DataFrame")

        # Try to convert numeric columns
        for col in df.columns:
            try:
                df[col] = pd.to_numeric(df[col])
            except (ValueError, TypeError):
                pass

        return df
