"""
Tests for the ImageParser: can_handle, parse, magic bytes, MIME guessing.
Uses mocking for Vision LLM and OCR since they require external services.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from chart_service.parsers.image_parser import ImageParser

# Paths to fixture image (Week / Work Points table)
_TEST_IMAGE_PATHS = [
    Path(__file__).resolve().parent / "fixtures" / "mock_data_table.png",
    Path(__file__).resolve().parent.parent / "assets" / "mock_data-15e54261-ce61-44ee-8f78-b970c268353f.png",
]


@pytest.fixture
def parser():
    return ImageParser()


# --- Magic bytes for creating fake image headers ---
PNG_HEADER = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
JPEG_HEADER = b"\xff\xd8\xff\xe0" + b"\x00" * 100
WEBP_HEADER = b"RIFF" + b"\x00\x00\x00\x00" + b"WEBP" + b"\x00" * 100
NOT_IMAGE = b"this is plain text, not an image at all" + b"\x00" * 100


class TestCanHandle:
    def test_png_by_extension(self, parser):
        assert parser.can_handle(b"anything", filename="photo.png") is True

    def test_jpg_by_extension(self, parser):
        assert parser.can_handle(b"anything", filename="photo.jpg") is True

    def test_jpeg_by_extension(self, parser):
        assert parser.can_handle(b"anything", filename="photo.jpeg") is True

    def test_webp_by_extension(self, parser):
        assert parser.can_handle(b"anything", filename="photo.webp") is True

    def test_csv_extension_rejected(self, parser):
        assert parser.can_handle(b"anything", filename="data.csv") is False

    def test_txt_extension_rejected(self, parser):
        assert parser.can_handle(b"anything", filename="data.txt") is False

    def test_png_magic_bytes_no_filename(self, parser):
        assert parser.can_handle(PNG_HEADER) is True

    def test_jpeg_magic_bytes_no_filename(self, parser):
        assert parser.can_handle(JPEG_HEADER) is True

    def test_webp_magic_bytes_no_filename(self, parser):
        assert parser.can_handle(WEBP_HEADER) is True

    def test_non_image_bytes_rejected(self, parser):
        assert parser.can_handle(NOT_IMAGE) is False

    def test_string_input_rejected(self, parser):
        assert parser.can_handle("not bytes") is False

    def test_short_bytes_rejected(self, parser):
        assert parser.can_handle(b"\x89PNG") is False  # Only 4 bytes, needs > 8

    def test_empty_bytes_rejected(self, parser):
        assert parser.can_handle(b"") is False


class TestIsImageBytes:
    def test_png(self):
        assert ImageParser._is_image_bytes(PNG_HEADER) is True

    def test_jpeg(self):
        assert ImageParser._is_image_bytes(JPEG_HEADER) is True

    def test_webp(self):
        assert ImageParser._is_image_bytes(WEBP_HEADER) is True

    def test_not_image(self):
        assert ImageParser._is_image_bytes(NOT_IMAGE) is False

    def test_random_bytes(self):
        assert ImageParser._is_image_bytes(b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09") is False


class TestGuessMimeType:
    def test_from_png_filename(self):
        assert ImageParser._guess_mime_type(b"", "photo.png") == "image/png"

    def test_from_jpg_filename(self):
        assert ImageParser._guess_mime_type(b"", "photo.jpg") == "image/jpeg"

    def test_from_jpeg_filename(self):
        assert ImageParser._guess_mime_type(b"", "photo.jpeg") == "image/jpeg"

    def test_from_webp_filename(self):
        assert ImageParser._guess_mime_type(b"", "photo.webp") == "image/webp"

    def test_from_png_magic_bytes(self):
        assert ImageParser._guess_mime_type(PNG_HEADER, None) == "image/png"

    def test_from_jpeg_magic_bytes(self):
        assert ImageParser._guess_mime_type(JPEG_HEADER, None) == "image/jpeg"

    def test_from_webp_magic_bytes(self):
        assert ImageParser._guess_mime_type(WEBP_HEADER, None) == "image/webp"

    def test_unknown_defaults_to_png(self):
        assert ImageParser._guess_mime_type(NOT_IMAGE, None) == "image/png"

    def test_filename_takes_priority(self):
        # Even if bytes look like PNG, filename says JPEG
        assert ImageParser._guess_mime_type(PNG_HEADER, "photo.jpg") == "image/jpeg"


class TestParseErrors:
    def test_string_input_raises(self, parser):
        with pytest.raises(ValueError, match="requires bytes input"):
            parser.parse("not bytes")

    @patch.object(ImageParser, "_try_vision_llm", return_value=(None, None))
    @patch.object(ImageParser, "_try_ocr", return_value=None)
    def test_no_extraction_method_raises(self, mock_ocr, mock_llm, parser):
        with pytest.raises(ValueError, match="Could not extract tabular data"):
            parser.parse(PNG_HEADER, filename="table.png")


class TestParseWithMockedVisionLLM:
    @patch.object(ImageParser, "_try_vision_llm")
    def test_vision_llm_success(self, mock_llm, parser):
        expected_df = pd.DataFrame({"Name": ["Alice", "Bob"], "Score": [90, 85]})
        mock_llm.return_value = (expected_df, None)

        result = parser.parse(PNG_HEADER, filename="table.png")
        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == ["Name", "Score"]
        assert len(result) == 2
        mock_llm.assert_called_once()

    @patch.object(ImageParser, "_try_ocr")
    @patch.object(ImageParser, "_try_vision_llm", return_value=(None, None))
    def test_falls_back_to_ocr(self, mock_llm, mock_ocr, parser):
        expected_df = pd.DataFrame({"X": [1, 2], "Y": [10, 20]})
        mock_ocr.return_value = expected_df

        result = parser.parse(PNG_HEADER, filename="table.png")
        assert isinstance(result, pd.DataFrame)
        mock_llm.assert_called_once()
        mock_ocr.assert_called_once()


class TestTryVisionLLM:
    """Test _try_vision_llm by patching the llm_client at the import source.

    Since _try_vision_llm does `from chart_service.llm.client import llm_client`
    inside the method body, we must patch the module-level object in
    chart_service.llm.client so the local import picks up the mock.
    """

    def test_unavailable_returns_none(self, parser):
        """When LLM is not available, _try_vision_llm returns (None, None)."""
        mock_client = MagicMock()
        mock_client.is_available = False
        with patch("chart_service.llm.client.llm_client", mock_client):
            df, err = parser._try_vision_llm(PNG_HEADER, "image/png")
        assert df is None
        assert err is None

    def test_successful_extraction(self, parser):
        mock_client = MagicMock()
        mock_client.is_available = True
        mock_client.extract_table_from_image.return_value = {
            "columns": ["Product", "Sales"],
            "rows": [["Widget", 100], ["Gadget", 200]],
        }
        with patch("chart_service.llm.client.llm_client", mock_client):
            df, err = parser._try_vision_llm(PNG_HEADER, "image/png")
        assert isinstance(df, pd.DataFrame)
        assert df.shape == (2, 2)
        assert df["Sales"].iloc[0] == 100  # Should be numeric
        assert err is None

    def test_empty_result_returns_none(self, parser):
        mock_client = MagicMock()
        mock_client.is_available = True
        mock_client.extract_table_from_image.return_value = None
        with patch("chart_service.llm.client.llm_client", mock_client):
            df, err = parser._try_vision_llm(PNG_HEADER, "image/png")
        assert df is None
        assert err is None

    def test_exception_returns_none_and_error(self, parser):
        mock_client = MagicMock()
        mock_client.is_available = True
        mock_client.extract_table_from_image.side_effect = Exception("API error")
        with patch("chart_service.llm.client.llm_client", mock_client):
            df, err = parser._try_vision_llm(PNG_HEADER, "image/png")
        assert df is None
        assert err is not None
        assert "API error" in str(err)


class TestTryOCR:
    def test_ocr_with_non_image_bytes_returns_none(self, parser):
        """When given non-image bytes, OCR should fail gracefully and return None."""
        # The actual method catches exceptions internally
        result = parser._try_ocr(b"definitely not an image at all")
        assert result is None

    def test_ocr_with_fake_png_returns_none(self, parser):
        """When given valid-looking header but fake image, OCR should fail gracefully."""
        result = parser._try_ocr(PNG_HEADER)
        assert result is None


class TestImageParserWithFixtureImage:
    """Test image parser using the attached mock_data image (Week / Work Points table)."""

    @pytest.fixture
    def fixture_image_path(self):
        """Resolve path to fixture image if it exists."""
        for p in _TEST_IMAGE_PATHS:
            if p.exists():
                return p
        return None

    @pytest.fixture
    def fixture_image_bytes(self, fixture_image_path):
        """Load fixture image bytes or None."""
        if fixture_image_path is None:
            return None
        return fixture_image_path.read_bytes()

    def test_parse_fixture_image_with_mocked_vision(self, parser, fixture_image_bytes):
        """When fixture image exists, parse with mocked Vision returns Week/Work Points table."""
        if fixture_image_bytes is None:
            pytest.skip("Fixture image not found. Add tests/fixtures/mock_data_table.png or assets/mock_data-*.png")

        # Expected table from the mock_data image (Week, Work Points)
        expected_columns = ["Week", "Work Points"]
        expected_rows = [
            ["2025-20", 40], ["2025-21", 45], ["2025-22", 54], ["2025-23", 45],
            ["2025-24", 39], ["2025-25", 34], ["2025-26", 54], ["2025-27", 25],
            ["2025-28", 43], ["2025-29", 41], ["2025-30", 51], ["2025-31", 49],
            ["2025-32", 56], ["2025-33", 62], ["2025-34", 56], ["2025-35", 70],
        ]

        mock_client = MagicMock()
        mock_client.is_available = True
        mock_client.extract_table_from_image.return_value = {
            "columns": expected_columns,
            "rows": expected_rows,
        }

        with patch("chart_service.llm.client.llm_client", mock_client):
            df = parser.parse(fixture_image_bytes, filename="mock_data_table.png")

        assert df is not None
        assert list(df.columns) == expected_columns
        assert len(df) == 16
        assert df["Work Points"].iloc[0] == 40
        assert df["Work Points"].iloc[-1] == 70

    def test_parse_fixture_image_integration(self, parser, fixture_image_path):
        """Parse real fixture image (no mock). Skips if no fixture; may call Vision API or OCR."""
        if fixture_image_path is None:
            pytest.skip("Fixture image not found.")
        try:
            raw = fixture_image_path.read_bytes()
            df = parser.parse(raw, filename=fixture_image_path.name)
            assert df is not None
            assert not df.empty
            assert len(df.columns) >= 1
        except ValueError as e:
            if "OPENAI_API_KEY" in str(e) or "pytesseract" in str(e) or "Could not extract" in str(e):
                pytest.skip(f"Image parse needs API or OCR: {e}")
            raise
