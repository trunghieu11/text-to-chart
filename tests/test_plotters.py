"""
Tests for the plotter registry and individual plotters.
"""

import pandas as pd
import plotly.graph_objects as go
import pytest

from chart_service.plotters import plotter_registry
from chart_service.models import ChartConfig


class TestPlotterRegistry:
    def test_list_plotters(self):
        plotters = plotter_registry.list_plotters()
        assert "line" in plotters
        assert "bar" in plotters
        assert "scatter" in plotters
        assert "pie" in plotters

    def test_get_plotter(self):
        plotter = plotter_registry.get_plotter("bar")
        assert plotter.chart_type == "bar"

    def test_get_invalid_plotter(self):
        with pytest.raises(KeyError, match="No plotter"):
            plotter_registry.get_plotter("nonexistent")


class TestLinePlotter:
    def test_plot_single_y(self):
        df = pd.DataFrame({"Month": ["Jan", "Feb", "Mar"], "Sales": [100, 150, 200]})
        config = ChartConfig(chart_type="line", x_column="Month", y_columns=["Sales"])
        fig = plotter_registry.plot(df, config)
        assert isinstance(fig, go.Figure)

    def test_plot_multiple_y(self):
        df = pd.DataFrame({
            "Month": ["Jan", "Feb"],
            "Revenue": [1000, 1500],
            "Costs": [800, 900],
        })
        config = ChartConfig(
            chart_type="line",
            x_column="Month",
            y_columns=["Revenue", "Costs"],
        )
        fig = plotter_registry.plot(df, config)
        assert isinstance(fig, go.Figure)


class TestBarPlotter:
    def test_plot_basic_bar(self):
        df = pd.DataFrame({"Category": ["A", "B", "C"], "Value": [10, 20, 30]})
        config = ChartConfig(chart_type="bar", x_column="Category", y_columns=["Value"])
        fig = plotter_registry.plot(df, config)
        assert isinstance(fig, go.Figure)


class TestScatterPlotter:
    def test_plot_scatter(self):
        df = pd.DataFrame({"X": [1, 2, 3], "Y": [10, 20, 15]})
        config = ChartConfig(chart_type="scatter", x_column="X", y_columns=["Y"])
        fig = plotter_registry.plot(df, config)
        assert isinstance(fig, go.Figure)


class TestPiePlotter:
    def test_plot_pie(self):
        df = pd.DataFrame({"Fruit": ["Apple", "Banana", "Cherry"], "Count": [5, 3, 7]})
        config = ChartConfig(chart_type="pie", x_column="Fruit", y_columns=["Count"])
        fig = plotter_registry.plot(df, config)
        assert isinstance(fig, go.Figure)
