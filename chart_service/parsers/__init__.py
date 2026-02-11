"""
Parser registry initialization.

All parsers are registered here on import.
"""

from chart_service.parsers.registry import ParserRegistry
from chart_service.parsers.text_parser import TextParser
from chart_service.parsers.csv_parser import CSVParser
from chart_service.parsers.excel_parser import ExcelParser
from chart_service.parsers.image_parser import ImageParser

# Create and populate the global parser registry
parser_registry = ParserRegistry()
parser_registry.register(CSVParser())
parser_registry.register(ExcelParser())
parser_registry.register(ImageParser())
parser_registry.register(TextParser())  # Text last: it's the fallback for string input

__all__ = [
    "parser_registry",
    "ParserRegistry",
    "TextParser",
    "CSVParser",
    "ExcelParser",
    "ImageParser",
]
