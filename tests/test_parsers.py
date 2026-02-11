"""
Tests for the parser registry and individual parsers.
"""

import pandas as pd
import pytest

from chart_service.parsers import parser_registry
from chart_service.parsers.text_parser import TextParser
from chart_service.parsers.csv_parser import CSVParser
from chart_service.parsers.excel_parser import ExcelParser


class TestTextParser:
    def test_parse_tab_separated(self):
        text = "Name\tAge\tScore\nAlice\t30\t85\nBob\t25\t92"
        parser = TextParser()
        df = parser.parse(text)
        assert df.shape == (2, 3)
        assert list(df.columns) == ["Name", "Age", "Score"]
        assert df["Age"].dtype in ("int64", "float64")

    def test_parse_comma_separated(self):
        text = "City,Population\nNew York,8336817\nLos Angeles,3979576"
        parser = TextParser()
        df = parser.parse(text)
        assert df.shape == (2, 2)
        assert "City" in df.columns

    def test_parse_empty_raises(self):
        parser = TextParser()
        with pytest.raises(ValueError, match="Empty text input"):
            parser.parse("")

    def test_can_handle_string(self):
        parser = TextParser()
        assert parser.can_handle("some text") is True
        assert parser.can_handle(b"bytes data") is False

    def test_can_handle_ignores_csv_extension(self):
        parser = TextParser()
        assert parser.can_handle("text", filename="data.csv") is False


class TestCSVParser:
    def test_parse_csv_string(self):
        csv_text = "A,B,C\n1,2,3\n4,5,6"
        parser = CSVParser()
        df = parser.parse(csv_text)
        assert df.shape == (2, 3)

    def test_parse_csv_bytes(self):
        csv_bytes = b"X,Y\n10,20\n30,40"
        parser = CSVParser()
        df = parser.parse(csv_bytes)
        assert df.shape == (2, 2)
        assert df["X"].iloc[0] == 10

    def test_can_handle_by_extension(self):
        parser = CSVParser()
        assert parser.can_handle(b"data", filename="test.csv") is True
        assert parser.can_handle(b"data", filename="test.xlsx") is False
        assert parser.can_handle(b"data") is False


class TestParserRegistry:
    def test_get_parser_for_text(self):
        parser = parser_registry.get_parser_for("Name\tValue\nA\t1")
        assert isinstance(parser, TextParser)

    def test_get_parser_for_csv(self):
        parser = parser_registry.get_parser_for(b"A,B\n1,2", filename="data.csv")
        assert isinstance(parser, CSVParser)

    def test_get_parser_for_excel(self):
        parser = parser_registry.get_parser_for(b"binary", filename="data.xlsx")
        assert isinstance(parser, ExcelParser)

    def test_no_parser_found(self):
        with pytest.raises(ValueError, match="No parser found"):
            parser_registry.get_parser_for(b"random bytes")

    def test_list_parsers(self):
        names = parser_registry.list_parsers()
        assert "text" in names
        assert "csv" in names
        assert "excel" in names
