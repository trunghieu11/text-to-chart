"""
Tests for the chart type registry and inference.
"""

import pandas as pd
import pytest

from chart_service.chart_types import chart_type_registry
from chart_service.chart_types.line_chart import LineChartType
from chart_service.chart_types.bar_chart import BarChartType
from chart_service.chart_types.scatter_chart import ScatterChartType
from chart_service.chart_types.pie_chart import PieChartType
from chart_service.models import ChartConfig


class TestChartTypeRegistry:
    def test_list_types(self):
        types = chart_type_registry.list_types()
        assert "line" in types
        assert "bar" in types
        assert "scatter" in types
        assert "pie" in types

    def test_get_valid_type(self):
        ct = chart_type_registry.get("bar")
        assert isinstance(ct, BarChartType)

    def test_get_invalid_type(self):
        with pytest.raises(KeyError, match="not found"):
            chart_type_registry.get("nonexistent")


class TestInferBestType:
    def test_categorical_few_unique_becomes_pie(self):
        df = pd.DataFrame({"Category": ["A", "B", "C"], "Value": [10, 20, 30]})
        result = chart_type_registry.infer_best_type(df)
        assert result == "pie"

    def test_categorical_many_unique_becomes_bar(self):
        df = pd.DataFrame({
            "Category": [f"Cat_{i}" for i in range(20)],
            "Value": list(range(20)),
        })
        result = chart_type_registry.infer_best_type(df)
        assert result == "bar"

    def test_two_numeric_becomes_scatter(self):
        df = pd.DataFrame({"X": [1, 2, 3, 4], "Y": [10, 20, 15, 25]})
        result = chart_type_registry.infer_best_type(df)
        assert result == "scatter"

    def test_timeseries_becomes_line(self):
        df = pd.DataFrame({
            "Date": ["2025-01-01", "2025-01-02", "2025-01-03"],
            "Value": [100, 150, 130],
        })
        result = chart_type_registry.infer_best_type(df)
        assert result == "line"


class TestChartTypeDefaultConfig:
    def test_bar_default_config(self):
        df = pd.DataFrame({"Category": ["A", "B"], "Value": [10, 20]})
        config = BarChartType().get_default_config(df)
        assert config.chart_type == "bar"
        assert config.x_column == "Category"
        assert "Value" in config.y_columns

    def test_line_default_config(self):
        df = pd.DataFrame({"Date": ["Mon", "Tue"], "Sales": [100, 200]})
        config = LineChartType().get_default_config(df)
        assert config.chart_type == "line"
        assert config.x_column is not None

    def test_pie_default_config(self):
        df = pd.DataFrame({"Fruit": ["Apple", "Banana"], "Count": [5, 3]})
        config = PieChartType().get_default_config(df)
        assert config.chart_type == "pie"
        assert config.x_column == "Fruit"
        assert "Count" in config.y_columns
