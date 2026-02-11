"""
Tests for data models: ChartConfig and ParsedData.
"""

import pandas as pd
import pytest

from chart_service.models import ChartConfig, ParsedData


class TestChartConfig:
    def test_default_values(self):
        config = ChartConfig()
        assert config.chart_type == "bar"
        assert config.x_column is None
        assert config.y_columns == []
        assert config.title is None
        assert config.template == "plotly_white"
        assert config.color_palette is None
        assert config.reference_lines is None
        assert config.annotations is None

    def test_custom_values(self):
        config = ChartConfig(
            chart_type="line",
            x_column="Date",
            y_columns=["Sales", "Revenue"],
            title="My Chart",
            x_label="Date",
            y_label="Amount",
            color_palette=["red", "blue"],
            template="plotly_dark",
        )
        assert config.chart_type == "line"
        assert config.x_column == "Date"
        assert len(config.y_columns) == 2
        assert config.title == "My Chart"

    def test_to_dict(self):
        config = ChartConfig(chart_type="scatter", x_column="X", y_columns=["Y"])
        d = config.to_dict()
        assert isinstance(d, dict)
        assert d["chart_type"] == "scatter"
        assert d["x_column"] == "X"
        assert d["y_columns"] == ["Y"]
        assert "template" in d

    def test_from_dict(self):
        data = {"chart_type": "pie", "x_column": "Name", "y_columns": ["Value"], "title": "Test"}
        config = ChartConfig.from_dict(data)
        assert config.chart_type == "pie"
        assert config.x_column == "Name"
        assert config.title == "Test"

    def test_from_dict_ignores_unknown_keys(self):
        data = {"chart_type": "bar", "unknown_field": "should_be_ignored"}
        config = ChartConfig.from_dict(data)
        assert config.chart_type == "bar"

    def test_roundtrip(self):
        original = ChartConfig(
            chart_type="line",
            x_column="X",
            y_columns=["Y1", "Y2"],
            title="Round Trip",
            template="plotly_dark",
        )
        d = original.to_dict()
        restored = ChartConfig.from_dict(d)
        assert restored.chart_type == original.chart_type
        assert restored.x_column == original.x_column
        assert restored.y_columns == original.y_columns
        assert restored.title == original.title
        assert restored.template == original.template


class TestParsedData:
    def test_basic_properties(self):
        df = pd.DataFrame({"Name": ["A", "B"], "Value": [1, 2], "Score": [10.0, 20.0]})
        parsed = ParsedData(dataframe=df, source_type="text")

        assert parsed.source_type == "text"
        assert parsed.columns == ["Name", "Value", "Score"]
        assert parsed.shape == (2, 3)

    def test_numeric_columns(self):
        df = pd.DataFrame({"Name": ["A", "B"], "Value": [1, 2], "Score": [10.0, 20.0]})
        parsed = ParsedData(dataframe=df)

        numeric = parsed.numeric_columns
        assert "Value" in numeric
        assert "Score" in numeric
        assert "Name" not in numeric

    def test_categorical_columns(self):
        df = pd.DataFrame({"Name": ["A", "B"], "Value": [1, 2]})
        parsed = ParsedData(dataframe=df)

        cats = parsed.categorical_columns
        assert "Name" in cats
        assert "Value" not in cats

    def test_default_source_type(self):
        df = pd.DataFrame({"A": [1]})
        parsed = ParsedData(dataframe=df)
        assert parsed.source_type == "unknown"
