"""
Tests for the LLM client: availability, chart config inference, graceful fallback.
Uses mocking to avoid real API calls.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from chart_service.llm.client import LLMClient
from chart_service.models import ChartConfig


class TestLLMClientAvailability:
    def test_available_with_key(self):
        client = LLMClient(api_key="sk-test-key")
        assert client.is_available is True

    def test_unavailable_without_key(self):
        # When api_key=None, client reads from config/env; patch so no key is found
        with patch("chart_service.llm.client._get_api_key", return_value=None):
            client = LLMClient(api_key=None)
            assert client.is_available is False

    def test_unavailable_with_empty_key(self):
        client = LLMClient(api_key="")
        assert client.is_available is False

    def test_custom_models(self):
        client = LLMClient(api_key="key", model="gpt-4", vision_model="gpt-4-vision")
        assert client.model == "gpt-4"
        assert client.vision_model == "gpt-4-vision"


class TestInferChartConfig:
    def test_returns_none_when_unavailable(self):
        client = LLMClient(api_key="")
        df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
        result = client.infer_chart_config(df)
        assert result is None

    def test_successful_inference(self):
        client = LLMClient(api_key="sk-test")

        # Mock the OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "chart_type": "bar",
            "x_column": "Category",
            "y_columns": ["Value"],
            "title": "Values by Category",
            "x_label": "Category",
            "y_label": "Value",
        })

        mock_openai = MagicMock()
        mock_openai.chat.completions.create.return_value = mock_response
        client._client = mock_openai

        df = pd.DataFrame({"Category": ["A", "B", "C"], "Value": [10, 20, 30]})
        result = client.infer_chart_config(df, available_types=["line", "bar", "scatter", "pie"])

        assert isinstance(result, ChartConfig)
        assert result.chart_type == "bar"
        assert result.x_column == "Category"
        assert result.y_columns == ["Value"]
        assert result.title == "Values by Category"

    def test_invalid_chart_type_returns_none(self):
        client = LLMClient(api_key="sk-test")

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "chart_type": "radar",  # Not in available_types
            "x_column": "A",
            "y_columns": ["B"],
            "title": "Test",
        })

        mock_openai = MagicMock()
        mock_openai.chat.completions.create.return_value = mock_response
        client._client = mock_openai

        df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
        result = client.infer_chart_config(df, available_types=["line", "bar"])
        assert result is None  # radar is not available

    def test_invalid_x_column_returns_none(self):
        client = LLMClient(api_key="sk-test")

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "chart_type": "bar",
            "x_column": "NonExistentColumn",
            "y_columns": ["B"],
            "title": "Test",
        })

        mock_openai = MagicMock()
        mock_openai.chat.completions.create.return_value = mock_response
        client._client = mock_openai

        df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
        result = client.infer_chart_config(df)
        assert result is None

    def test_invalid_y_column_returns_none(self):
        client = LLMClient(api_key="sk-test")

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "chart_type": "bar",
            "x_column": "A",
            "y_columns": ["B", "NonExistent"],
            "title": "Test",
        })

        mock_openai = MagicMock()
        mock_openai.chat.completions.create.return_value = mock_response
        client._client = mock_openai

        df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
        result = client.infer_chart_config(df)
        assert result is None

    def test_api_exception_returns_none(self):
        client = LLMClient(api_key="sk-test")

        mock_openai = MagicMock()
        mock_openai.chat.completions.create.side_effect = Exception("API timeout")
        client._client = mock_openai

        df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
        result = client.infer_chart_config(df)
        assert result is None  # Graceful degradation

    def test_malformed_json_returns_none(self):
        client = LLMClient(api_key="sk-test")

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "NOT VALID JSON"

        mock_openai = MagicMock()
        mock_openai.chat.completions.create.return_value = mock_response
        client._client = mock_openai

        df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
        result = client.infer_chart_config(df)
        assert result is None


class TestExtractTableFromImage:
    def test_returns_none_when_unavailable(self):
        client = LLMClient(api_key="")
        result = client.extract_table_from_image(b"fake image bytes")
        assert result is None

    def test_successful_extraction(self):
        client = LLMClient(api_key="sk-test")

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "columns": ["Name", "Score"],
            "rows": [["Alice", 90], ["Bob", 85]],
        })

        mock_openai = MagicMock()
        mock_openai.chat.completions.create.return_value = mock_response
        client._client = mock_openai

        result = client.extract_table_from_image(b"fake-image-bytes", "image/png")
        assert result is not None
        assert result["columns"] == ["Name", "Score"]
        assert len(result["rows"]) == 2

    def test_missing_columns_returns_none(self):
        client = LLMClient(api_key="sk-test")

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({"data": "no columns key"})

        mock_openai = MagicMock()
        mock_openai.chat.completions.create.return_value = mock_response
        client._client = mock_openai

        result = client.extract_table_from_image(b"fake-image-bytes")
        assert result is None

    def test_api_error_returns_none(self):
        client = LLMClient(api_key="sk-test")

        mock_openai = MagicMock()
        mock_openai.chat.completions.create.side_effect = Exception("Vision API error")
        client._client = mock_openai

        result = client.extract_table_from_image(b"fake-image-bytes")
        assert result is None
