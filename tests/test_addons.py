"""
Tests for plotter add-ons: color palette, custom lines, layout.
"""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import pytest

from chart_service.models import ChartConfig
from chart_service.plotters.addons.color_palette import ColorPaletteAddon, PALETTES
from chart_service.plotters.addons.custom_lines import CustomLinesAddon
from chart_service.plotters.addons.layout import LayoutAddon


@pytest.fixture
def sample_fig():
    df = pd.DataFrame({"X": ["A", "B", "C"], "Y": [10, 20, 30]})
    return px.bar(df, x="X", y="Y")


class TestColorPaletteAddon:
    def test_no_palette_returns_unchanged(self, sample_fig):
        addon = ColorPaletteAddon()
        config = ChartConfig(chart_type="bar")
        result = addon.apply(sample_fig, config)
        assert result is sample_fig

    def test_custom_palette_applied(self, sample_fig):
        addon = ColorPaletteAddon()
        config = ChartConfig(chart_type="bar", color_palette=["#ff0000", "#00ff00", "#0000ff"])
        result = addon.apply(sample_fig, config)
        assert isinstance(result, go.Figure)

    def test_preset_palette_name(self, sample_fig):
        addon = ColorPaletteAddon()
        config = ChartConfig(chart_type="bar", color_palette=["vibrant"])
        result = addon.apply(sample_fig, config)
        assert isinstance(result, go.Figure)

    def test_default_preset_no_change(self, sample_fig):
        addon = ColorPaletteAddon()
        config = ChartConfig(chart_type="bar", color_palette=["default"])
        result = addon.apply(sample_fig, config)
        assert result is sample_fig

    def test_palettes_defined(self):
        assert "vibrant" in PALETTES
        assert "pastel" in PALETTES
        assert "earth" in PALETTES
        assert "ocean" in PALETTES
        assert "sunset" in PALETTES


class TestCustomLinesAddon:
    def test_no_lines_returns_unchanged(self, sample_fig):
        addon = CustomLinesAddon()
        config = ChartConfig(chart_type="bar")
        result = addon.apply(sample_fig, config)
        assert result is sample_fig

    def test_horizontal_line(self, sample_fig):
        addon = CustomLinesAddon()
        config = ChartConfig(
            chart_type="bar",
            reference_lines=[{"orientation": "h", "value": 15, "color": "red", "label": "Target"}],
        )
        result = addon.apply(sample_fig, config)
        assert isinstance(result, go.Figure)
        # Check that shapes were added (hline adds a shape)
        assert len(result.layout.shapes) > 0

    def test_vertical_line(self):
        """Vertical lines need a numeric x-axis to work correctly."""
        df = pd.DataFrame({"X": [1, 2, 3, 4], "Y": [10, 20, 15, 25]})
        fig = px.scatter(df, x="X", y="Y")
        addon = CustomLinesAddon()
        config = ChartConfig(
            chart_type="scatter",
            reference_lines=[{"orientation": "v", "value": 2.5, "color": "blue"}],
        )
        result = addon.apply(fig, config)
        assert isinstance(result, go.Figure)
        assert len(result.layout.shapes) > 0

    def test_multiple_lines(self, sample_fig):
        addon = CustomLinesAddon()
        config = ChartConfig(
            chart_type="bar",
            reference_lines=[
                {"orientation": "h", "value": 10},
                {"orientation": "h", "value": 25, "color": "green"},
            ],
        )
        result = addon.apply(sample_fig, config)
        assert isinstance(result, go.Figure)

    def test_line_without_value_skipped(self, sample_fig):
        addon = CustomLinesAddon()
        config = ChartConfig(
            chart_type="bar",
            reference_lines=[{"orientation": "h"}],  # No value
        )
        result = addon.apply(sample_fig, config)
        assert isinstance(result, go.Figure)


class TestLayoutAddon:
    def test_default_layout_applied(self, sample_fig):
        addon = LayoutAddon()
        config = ChartConfig(chart_type="bar", template="plotly_white")
        result = addon.apply(sample_fig, config)
        assert isinstance(result, go.Figure)
        assert result.layout.template is not None

    def test_annotations_applied(self, sample_fig):
        addon = LayoutAddon()
        config = ChartConfig(
            chart_type="bar",
            annotations=[{"x": "A", "y": 10, "text": "Note here"}],
        )
        result = addon.apply(sample_fig, config)
        assert len(result.layout.annotations) > 0
        assert result.layout.annotations[0].text == "Note here"

    def test_font_settings_applied(self, sample_fig):
        addon = LayoutAddon()
        config = ChartConfig(chart_type="bar")
        result = addon.apply(sample_fig, config)
        assert result.layout.font.family is not None

    def test_addon_order(self):
        """Verify add-ons have correct ordering."""
        assert ColorPaletteAddon().order < CustomLinesAddon().order
        assert CustomLinesAddon().order < LayoutAddon().order


class TestAddonPipeline:
    """Test that add-ons work together via the plotter registry."""

    def test_full_pipeline_with_addons(self):
        from chart_service.plotters import plotter_registry

        df = pd.DataFrame({"Cat": ["A", "B", "C"], "Val": [10, 20, 30]})
        config = ChartConfig(
            chart_type="bar",
            x_column="Cat",
            y_columns=["Val"],
            color_palette=["#ff0000", "#00ff00", "#0000ff"],
            reference_lines=[{"orientation": "h", "value": 20, "color": "red", "label": "Avg"}],
            annotations=[{"x": "B", "y": 20, "text": "Peak"}],
            template="plotly_white",
        )
        fig = plotter_registry.plot(df, config)
        assert isinstance(fig, go.Figure)
        # Layout addon should have set font
        assert fig.layout.font.family is not None
        # Reference line should have added a shape
        assert len(fig.layout.shapes) > 0
        # Annotation should be present
        assert len(fig.layout.annotations) > 0
