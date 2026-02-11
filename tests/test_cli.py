"""
Tests for the CLI interface using Click's CliRunner.
Mocks fig.write_image since kaleido/Chrome may not be available in CI.
"""

from __future__ import annotations

import os
import tempfile
from unittest.mock import patch, MagicMock

import pytest
from click.testing import CliRunner

from cli import main


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def csv_file():
    """Create a temporary CSV file for testing."""
    content = "Category,Value\nApple,10\nBanana,20\nCherry,30\n"
    fd, path = tempfile.mkstemp(suffix=".csv")
    os.write(fd, content.encode())
    os.close(fd)
    yield path
    os.unlink(path)


def _mock_write_image(self, path, **kwargs):
    """Write a fake PNG file so the CLI thinks export succeeded."""
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\nfake")


class TestCLIHelp:
    def test_main_help(self, runner):
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Text-to-Chart" in result.output

    def test_chart_help(self, runner):
        result = runner.invoke(main, ["chart", "--help"])
        assert result.exit_code == 0
        assert "--input" in result.output
        assert "--text" in result.output
        assert "--output" in result.output
        assert "--type" in result.output
        assert "--title" in result.output


class TestCLITextInput:
    @patch("plotly.graph_objs.Figure.write_image", _mock_write_image)
    def test_text_to_chart_with_output(self, runner):
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            output_path = f.name

        try:
            result = runner.invoke(main, [
                "chart",
                "--text", "Name\\tValue\\nA\\t10\\nB\\t20\\nC\\t30",
                "--output", output_path,
            ])
            assert result.exit_code == 0
            assert "Chart saved to" in result.output
            assert "Parser: text" in result.output
            assert os.path.exists(output_path)
            assert os.path.getsize(output_path) > 0
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    @patch("plotly.graph_objs.Figure.write_image", _mock_write_image)
    def test_text_with_explicit_type(self, runner):
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            output_path = f.name

        try:
            result = runner.invoke(main, [
                "chart",
                "--text", "X\\tY\\n1\\t10\\n2\\t20",
                "--type", "line",
                "--output", output_path,
            ])
            assert result.exit_code == 0
            assert "Chart type: line" in result.output
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    @patch("plotly.graph_objs.Figure.write_image", _mock_write_image)
    def test_text_with_title(self, runner):
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            output_path = f.name

        try:
            result = runner.invoke(main, [
                "chart",
                "--text", "A\\tB\\n1\\t2",
                "--title", "My Title",
                "--output", output_path,
            ])
            assert result.exit_code == 0
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)


class TestCLIFileInput:
    @patch("plotly.graph_objs.Figure.write_image", _mock_write_image)
    def test_csv_file_input(self, runner, csv_file):
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            output_path = f.name

        try:
            result = runner.invoke(main, [
                "chart",
                "--input", csv_file,
                "--output", output_path,
            ])
            assert result.exit_code == 0
            assert "Parser: csv" in result.output
            assert "Data shape:" in result.output
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)


class TestCLIErrors:
    def test_no_input_shows_error(self, runner):
        result = runner.invoke(main, ["chart"])
        assert result.exit_code != 0
        assert "Error" in result.output or "Provide either" in result.output

    def test_nonexistent_file_shows_error(self, runner):
        result = runner.invoke(main, ["chart", "--input", "/nonexistent/file.csv"])
        assert result.exit_code != 0
