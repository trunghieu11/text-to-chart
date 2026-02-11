"""
Text parser: handles raw tab/space/comma-separated text input.
"""

from __future__ import annotations

from io import StringIO
from typing import Optional, Union

import pandas as pd

from chart_service.parsers.base import BaseParser


class TextParser(BaseParser):
    """Parse raw text (tab/space/comma separated) into a DataFrame."""

    name = "text"
    supported_extensions = [".txt", ".tsv"]
    supported_mime_types = ["text/plain", "text/tab-separated-values"]

    def can_handle(
        self, raw_input: Union[str, bytes], filename: Optional[str] = None
    ) -> bool:
        """Text parser handles any string input without a recognized file extension."""
        if filename:
            ext = self._get_extension(filename)
            if ext in self.supported_extensions:
                return True
            # If the filename has another recognized extension, don't handle it
            if ext in (".csv", ".xlsx", ".xls", ".png", ".jpg", ".jpeg", ".webp"):
                return False
        # Handle any plain string input
        return isinstance(raw_input, str)

    def parse(
        self, raw_input: Union[str, bytes], filename: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Parse text input using pandas with automatic delimiter detection.

        Handles tab-separated, comma-separated, and space-separated text.
        First row is treated as headers.
        """
        if isinstance(raw_input, bytes):
            raw_input = raw_input.decode("utf-8")

        text = raw_input.strip()
        if not text:
            raise ValueError("Empty text input")

        try:
            df = pd.read_csv(
                StringIO(text),
                sep=None,
                engine="python",
                skipinitialspace=True,
            )
        except Exception as e:
            raise ValueError(f"Failed to parse text input: {e}") from e

        if df.empty:
            raise ValueError("Parsed text resulted in an empty DataFrame")

        # Try to convert numeric columns
        for col in df.columns:
            try:
                df[col] = pd.to_numeric(df[col])
            except (ValueError, TypeError):
                pass

        return df
