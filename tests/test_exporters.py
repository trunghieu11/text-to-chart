"""
Tests for chart exporters: embed, image, and code.

ImageExporter tests mock pio.to_image to avoid requiring kaleido/Chrome.
"""

import os
import tempfile
from unittest.mock import patch

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pytest

from chart_service.exporters.code import CodeExporter
from chart_service.exporters.embed import EmbedExporter
from chart_service.exporters.image import ImageExporter
from chart_service.models import ChartConfig

# Fake PNG bytes (valid header + minimal content) used to mock kaleido
FAKE_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100


@pytest.fixture
def sample_fig():
    """Create a sample Plotly figure for testing."""
    df = pd.DataFrame({"Category": ["A", "B", "C"], "Value": [10, 20, 30]})
    return px.bar(df, x="Category", y="Value", title="Test Chart")


@pytest.fixture
def sample_df():
    return pd.DataFrame({"Category": ["A", "B", "C"], "Value": [10, 20, 30]})


@pytest.fixture
def sample_config():
    return ChartConfig(
        chart_type="bar",
        x_column="Category",
        y_columns=["Value"],
        title="Test Chart",
        x_label="Category",
        y_label="Value",
    )


class TestEmbedExporter:
    def test_store_and_get_chart(self, sample_fig):
        chart_id = EmbedExporter.store_chart(sample_fig)
        assert chart_id is not None
        assert len(chart_id) > 0

        stored = EmbedExporter.get_chart(chart_id)
        assert stored is not None
        assert "figure_json" in stored
        assert "created_at" in stored

    def test_store_with_custom_id(self, sample_fig):
        chart_id = EmbedExporter.store_chart(sample_fig, chart_id="custom-123")
        assert chart_id == "custom-123"

        stored = EmbedExporter.get_chart("custom-123")
        assert stored is not None

    def test_get_nonexistent_chart(self):
        result = EmbedExporter.get_chart("nonexistent-id")
        assert result is None

    def test_generate_embed_html(self, sample_fig):
        html = EmbedExporter.generate_embed_html(sample_fig)
        assert "<!DOCTYPE html>" in html
        assert "Plotly.newPlot" in html
        assert "plotly-latest.min.js" in html

    def test_get_embed_url(self):
        url = EmbedExporter.get_embed_url("test-id")
        assert url == "http://localhost:8000/v1/charts/test-id/embed"

    def test_get_embed_url_custom_base(self):
        url = EmbedExporter.get_embed_url("test-id", base_url="https://api.example.com")
        assert url == "https://api.example.com/v1/charts/test-id/embed"

    def test_clear_store(self, sample_fig):
        EmbedExporter.store_chart(sample_fig, chart_id="to-clear")
        assert EmbedExporter.get_chart("to-clear") is not None
        EmbedExporter.clear_store()
        assert EmbedExporter.get_chart("to-clear") is None


class TestImageExporter:
    """Tests for ImageExporter. Mocks pio.to_image to avoid kaleido/Chrome dependency."""

    @patch("plotly.io.to_image", return_value=FAKE_PNG)
    def test_to_bytes(self, mock_to_image, sample_fig):
        img_bytes = ImageExporter.to_bytes(sample_fig)
        assert isinstance(img_bytes, bytes)
        assert len(img_bytes) > 0
        # PNG magic bytes
        assert img_bytes[:4] == b"\x89PNG"
        mock_to_image.assert_called_once()

    @patch("plotly.io.to_image", return_value=FAKE_PNG)
    def test_to_base64(self, mock_to_image, sample_fig):
        b64 = ImageExporter.to_base64(sample_fig)
        assert isinstance(b64, str)
        assert len(b64) > 0
        # Base64 only contains valid chars
        import base64
        decoded = base64.b64decode(b64)
        assert decoded[:4] == b"\x89PNG"

    @patch("plotly.io.to_image", return_value=FAKE_PNG)
    def test_to_data_uri(self, mock_to_image, sample_fig):
        uri = ImageExporter.to_data_uri(sample_fig)
        assert uri.startswith("data:image/png;base64,")

    @patch("plotly.io.to_image", return_value=FAKE_PNG)
    def test_save(self, mock_to_image, sample_fig):
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            path = f.name
        try:
            result = ImageExporter.save(sample_fig, path)
            assert result.exists()
            assert result.stat().st_size > 0
            # Verify it's a PNG
            with open(path, "rb") as f:
                assert f.read(4) == b"\x89PNG"
        finally:
            os.unlink(path)


class TestCodeExporter:
    def test_generate_bar(self, sample_df, sample_config):
        code = CodeExporter.generate(sample_df, sample_config)
        assert "import pandas as pd" in code
        assert "import plotly.express as px" in code
        assert "pd.DataFrame" in code
        assert "px.bar" in code
        assert 'x="Category"' in code
        assert 'y="Value"' in code
        assert "fig.show()" in code
        assert "if __name__" in code

    def test_generate_line(self, sample_df):
        config = ChartConfig(
            chart_type="line",
            x_column="Category",
            y_columns=["Value"],
            title="Line Test",
        )
        code = CodeExporter.generate(sample_df, config)
        assert "px.line" in code

    def test_generate_pie(self, sample_df):
        config = ChartConfig(
            chart_type="pie",
            x_column="Category",
            y_columns=["Value"],
            title="Pie Test",
        )
        code = CodeExporter.generate(sample_df, config)
        assert "px.pie" in code
        assert "names=" in code
        assert "values=" in code

    def test_generate_multi_y(self):
        df = pd.DataFrame({"X": [1, 2], "Y1": [10, 20], "Y2": [30, 40]})
        config = ChartConfig(
            chart_type="bar",
            x_column="X",
            y_columns=["Y1", "Y2"],
            title="Multi-Y",
        )
        code = CodeExporter.generate(df, config)
        assert "Y1" in code
        assert "Y2" in code

    def test_save(self, sample_df, sample_config):
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as f:
            path = f.name
        try:
            result = CodeExporter.save(sample_df, sample_config, path)
            assert result.exists()
            content = result.read_text()
            assert "import pandas" in content
        finally:
            os.unlink(path)

    def test_generated_code_contains_data(self, sample_df, sample_config):
        code = CodeExporter.generate(sample_df, sample_config)
        # Data should be serialized in the code
        assert '"A"' in code or "'A'" in code
        assert "10" in code
        assert "20" in code
        assert "30" in code
