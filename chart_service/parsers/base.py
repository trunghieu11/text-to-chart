"""
Base parser interface for the parser registry.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Union

import pandas as pd


class BaseParser(ABC):
    """Abstract base class for all data parsers."""

    name: str = "base"
    supported_extensions: list[str] = []
    supported_mime_types: list[str] = []

    def can_handle(
        self, raw_input: Union[str, bytes], filename: Optional[str] = None
    ) -> bool:
        """
        Check if this parser can handle the given input.

        Default implementation checks file extension if filename is provided.
        Subclasses can override for more sophisticated detection.
        """
        if filename:
            ext = self._get_extension(filename)
            if ext in self.supported_extensions:
                return True
        return False

    @abstractmethod
    def parse(
        self, raw_input: Union[str, bytes], filename: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Parse the raw input into a pandas DataFrame.

        Args:
            raw_input: Raw text string or file bytes.
            filename: Optional filename for format detection.

        Returns:
            Parsed DataFrame with proper column names and types.
        """
        ...

    @staticmethod
    def _get_extension(filename: str) -> str:
        """Extract lowercase file extension from filename."""
        import os

        _, ext = os.path.splitext(filename)
        return ext.lower()
