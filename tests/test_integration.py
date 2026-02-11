"""
Integration tests: end-to-end chart creation.
"""

import plotly.graph_objects as go
import pytest

from chart_service import create_chart
from chart_service.models import ParsedData, ChartConfig


class TestCreateChart:
    def test_text_to_bar_chart(self):
        text = "Category\tValue\nA\t10\nB\t20\nC\t30\nD\t40\nE\t50\nF\t60\nG\t70\nH\t80\nI\t90"
        parsed, config, fig = create_chart(text)
        assert isinstance(parsed, ParsedData)
        assert isinstance(config, ChartConfig)
        assert isinstance(fig, go.Figure)
        assert parsed.source_type == "text"

    def test_text_to_line_chart_explicit(self):
        text = "Week\tSales\n1\t100\n2\t150\n3\t200"
        parsed, config, fig = create_chart(text, chart_type="line")
        assert config.chart_type == "line"
        assert isinstance(fig, go.Figure)

    def test_text_to_scatter_chart(self):
        text = "Height\tWeight\n170\t65\n175\t70\n180\t80"
        parsed, config, fig = create_chart(text, chart_type="scatter")
        assert config.chart_type == "scatter"

    def test_text_to_pie_chart(self):
        text = "Fruit\tCount\nApple\t5\nBanana\t3\nCherry\t7"
        parsed, config, fig = create_chart(text, chart_type="pie")
        assert config.chart_type == "pie"

    def test_auto_detection_timeseries(self):
        text = "Date\tValue\n2025-01-01\t100\n2025-01-02\t150\n2025-01-03\t130"
        parsed, config, fig = create_chart(text)
        assert config.chart_type == "line"

    def test_auto_detection_two_numeric(self):
        text = "X\tY\n1\t10\n2\t20\n3\t15\n4\t25"
        parsed, config, fig = create_chart(text)
        assert config.chart_type == "scatter"

    def test_csv_bytes_input(self):
        csv_bytes = b"Product,Sales\nWidget,100\nGadget,200\nDoohickey,150"
        parsed, config, fig = create_chart(csv_bytes, filename="sales.csv")
        assert parsed.source_type == "csv"
        assert isinstance(fig, go.Figure)

    def test_custom_title(self):
        text = "A\tB\n1\t2\n3\t4"
        _, config, fig = create_chart(text, chart_type="line", title="My Custom Chart")
        assert config.title == "My Custom Chart"

    def test_invalid_chart_type(self):
        text = "A\tB\n1\t2"
        with pytest.raises(KeyError, match="not found"):
            create_chart(text, chart_type="nonexistent")
