"""
Parser registry: manages parser instances and dispatches to the right one.
"""

from __future__ import annotations

import logging
from typing import Optional, Union

from chart_service.parsers.base import BaseParser

logger = logging.getLogger(__name__)


class ParserRegistry:
    """Registry of data parsers. Finds the right parser for a given input."""

    def __init__(self) -> None:
        self._parsers: dict[str, BaseParser] = {}

    def register(self, parser: BaseParser) -> None:
        """Register a parser instance."""
        self._parsers[parser.name] = parser

    def get_parser_for(
        self, raw_input: Union[str, bytes], filename: Optional[str] = None
    ) -> BaseParser:
        """
        Find and return the first parser that can handle the input.

        Priority: filename extension match first, then content-based detection.

        Raises:
            ValueError: If no parser can handle the input.
        """
        for parser in self._parsers.values():
            if parser.can_handle(raw_input, filename):
                logger.info(
                    "[DEBUG] Parser selected: %s (filename=%s, input_type=%s, input_len=%s)",
                    parser.name,
                    filename,
                    type(raw_input).__name__,
                    len(raw_input) if raw_input is not None else 0,
                )
                print(f"[PARSER] selected: {parser.name} filename={filename!r} input_len={len(raw_input) if raw_input else 0}", flush=True)
                return parser

        raise ValueError(
            f"No parser found for input (filename={filename}, "
            f"type={type(raw_input).__name__}, "
            f"length={len(raw_input)}). "
            f"Available parsers: {self.list_parsers()}"
        )

    def list_parsers(self) -> list[str]:
        """Return list of registered parser names."""
        return list(self._parsers.keys())
