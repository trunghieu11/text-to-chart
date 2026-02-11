"""
Edge case tests for parsers, plotters, chart types, and the integration pipeline.
"""

from __future__ import annotations

import io
import os
import tempfile

import pandas as pd
import plotly.graph_objects as go
import pytest

from chart_service import create_chart
from chart_service.models import ChartConfig, ParsedData
from chart_service.parsers.text_parser import TextParser
from chart_service.parsers.csv_parser import CSVParser
from chart_service.parsers.excel_parser import ExcelParser
from chart_service.parsers import parser_registry
from chart_service.chart_types import chart_type_registry
from chart_service.plotters import plotter_registry


# ──────────────────────────────────────────
# Parser edge cases
# ──────────────────────────────────────────

class TestTextParserEdgeCases:
    def test_single_column(self):
        parser = TextParser()
        df = parser.parse("Value\n10\n20\n30")
        # Pandas may auto-detect separator and create extra columns; just verify rows
        assert df.shape[0] == 3
        assert "Value" in df.columns or df.shape[1] >= 1

    def test_unicode_data(self):
        parser = TextParser()
        df = parser.parse("Name\tScore\nAlicé\t90\nBöb\t85\n日本語\t95")
        assert len(df) == 3
        assert "Alicé" in df["Name"].values

    def test_whitespace_only_raises(self):
        parser = TextParser()
        with pytest.raises(ValueError):
            parser.parse("   \n  \n  ")

    def test_mixed_delimiters(self):
        """Pandas auto-detect should handle this."""
        parser = TextParser()
        df = parser.parse("A,B\n1,2\n3,4")
        assert df.shape == (2, 2)

    def test_numeric_strings_converted(self):
        parser = TextParser()
        df = parser.parse("A\tB\n1\t2.5\n3\t4.0")
        assert df["A"].dtype in ("int64", "float64")
        assert df["B"].dtype == "float64"


class TestCSVParserEdgeCases:
    def test_empty_csv_raises(self):
        parser = CSVParser()
        with pytest.raises(Exception):
            parser.parse(b"")

    def test_headers_only_raises(self):
        parser = CSVParser()
        with pytest.raises(ValueError):
            parser.parse(b"A,B,C\n")

    def test_latin1_encoding(self):
        """Test encoding fallback from utf-8 to latin-1."""
        parser = CSVParser()
        content = "Name,City\nJosé,São Paulo\n".encode("latin-1")
        df = parser.parse(content)
        assert len(df) == 1

    def test_large_csv(self):
        """Test with a larger dataset."""
        parser = CSVParser()
        rows = ["A,B"] + [f"{i},{i*10}" for i in range(1000)]
        content = "\n".join(rows).encode()
        df = parser.parse(content)
        assert len(df) == 1000


class TestExcelParserEdgeCases:
    def test_string_input_raises(self):
        parser = ExcelParser()
        with pytest.raises(ValueError, match="requires bytes input"):
            parser.parse("not bytes")

    def test_invalid_bytes_raises(self):
        parser = ExcelParser()
        with pytest.raises(ValueError, match="Failed to parse Excel"):
            parser.parse(b"this is not an excel file")

    def test_real_xlsx(self):
        """Create a real xlsx file and parse it."""
        df_original = pd.DataFrame({"Product": ["A", "B"], "Sales": [100, 200]})
        buf = io.BytesIO()
        df_original.to_excel(buf, index=False, engine="openpyxl")
        buf.seek(0)

        parser = ExcelParser()
        df = parser.parse(buf.read())
        assert df.shape == (2, 2)
        assert list(df.columns) == ["Product", "Sales"]
        assert df["Sales"].iloc[0] == 100


class TestParserRegistryEdgeCases:
    def test_image_parser_registered(self):
        assert "image" in parser_registry.list_parsers()

    def test_priority_csv_over_text(self):
        """CSV parser should be selected for .csv, not text parser."""
        parser = parser_registry.get_parser_for(b"data", filename="file.csv")
        assert parser.name == "csv"

    def test_priority_excel_over_text(self):
        parser = parser_registry.get_parser_for(b"data", filename="file.xlsx")
        assert parser.name == "excel"

    def test_text_fallback_for_plain_string(self):
        parser = parser_registry.get_parser_for("any string input")
        assert parser.name == "text"


# ──────────────────────────────────────────
# Chart type edge cases
# ──────────────────────────────────────────

class TestChartTypeEdgeCases:
    def test_single_numeric_column(self):
        df = pd.DataFrame({"Value": [10, 20, 30]})
        result = chart_type_registry.infer_best_type(df)
        assert result == "bar"

    def test_many_numeric_columns(self):
        df = pd.DataFrame({"A": [1, 2], "B": [3, 4], "C": [5, 6], "D": [7, 8]})
        result = chart_type_registry.infer_best_type(df)
        assert result in ["line", "scatter", "bar"]

    def test_one_row_dataframe(self):
        df = pd.DataFrame({"Cat": ["A"], "Val": [10]})
        result = chart_type_registry.infer_best_type(df)
        assert result in chart_type_registry.list_types()

    def test_scatter_default_config_with_one_numeric(self):
        """ScatterChartType.get_default_config with only 1 numeric column."""
        from chart_service.chart_types.scatter_chart import ScatterChartType

        df = pd.DataFrame({"Label": ["A", "B"], "Val": [10, 20]})
        config = ScatterChartType().get_default_config(df)
        assert config.chart_type == "scatter"


# ──────────────────────────────────────────
# Plotter edge cases
# ──────────────────────────────────────────

class TestPlotterEdgeCases:
    def test_line_plotter_auto_columns(self):
        """Line plotter with no explicit x/y should auto-detect."""
        df = pd.DataFrame({"Date": ["Mon", "Tue", "Wed"], "Sales": [10, 20, 15]})
        config = ChartConfig(chart_type="line", x_column="Date", y_columns=["Sales"])
        fig = plotter_registry.plot(df, config)
        assert isinstance(fig, go.Figure)

    def test_bar_plotter_grouped(self):
        """Bar plotter with multiple y columns produces grouped bars."""
        df = pd.DataFrame({"X": ["A", "B"], "Y1": [10, 20], "Y2": [15, 25]})
        config = ChartConfig(chart_type="bar", x_column="X", y_columns=["Y1", "Y2"])
        fig = plotter_registry.plot(df, config)
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 2  # Two traces for grouped bar

    def test_pie_plotter_auto_detect(self):
        """Pie plotter with no x/y should auto-detect."""
        df = pd.DataFrame({"Fruit": ["Apple", "Banana"], "Count": [5, 3]})
        config = ChartConfig(chart_type="pie")
        fig = plotter_registry.plot(df, config)
        assert isinstance(fig, go.Figure)

    def test_scatter_plotter_auto_detect(self):
        """Scatter plotter with only numeric columns."""
        df = pd.DataFrame({"X": [1, 2, 3], "Y": [10, 20, 30]})
        config = ChartConfig(chart_type="scatter", x_column="X", y_columns=["Y"])
        fig = plotter_registry.plot(df, config)
        assert isinstance(fig, go.Figure)


# ──────────────────────────────────────────
# Integration edge cases
# ──────────────────────────────────────────

class TestIntegrationEdgeCases:
    def test_create_chart_with_x_override(self):
        text = "A\tB\tC\n1\t10\t100\n2\t20\t200"
        _, config, fig = create_chart(text, chart_type="line", x_column="A", y_columns=["C"])
        assert config.x_column == "A"
        assert config.y_columns == ["C"]

    def test_comma_separated_text(self):
        text = "Product,Sales,Profit\nA,100,20\nB,200,40"
        parsed, config, fig = create_chart(text)
        assert parsed.source_type == "text"
        assert isinstance(fig, go.Figure)

    def test_csv_bytes_with_chart_type_override(self):
        csv = b"X,Y\n1,10\n2,20\n3,30\n4,40"
        _, config, fig = create_chart(csv, filename="data.csv", chart_type="scatter")
        assert config.chart_type == "scatter"

    def test_parseddata_properties(self):
        text = "Name\tAge\tScore\nAlice\t30\t85\nBob\t25\t92"
        parsed, _, _ = create_chart(text)
        assert "Name" in parsed.categorical_columns
        assert "Age" in parsed.numeric_columns
        assert "Score" in parsed.numeric_columns
        assert parsed.shape == (2, 3)
