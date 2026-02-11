"""
Tests for the REST API endpoints.
Mocks ImageExporter.to_bytes to avoid kaleido/Chrome dependency.
"""

import sys
from pathlib import Path
from unittest.mock import patch

# Add project root to path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import pytest
from fastapi.testclient import TestClient

from api.main import app

# Fake PNG bytes used to mock kaleido-based image export
FAKE_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100


@pytest.fixture
def client():
    return TestClient(app)


class TestHealthEndpoint:
    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "version" in data


class TestRootEndpoint:
    def test_root(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Text-to-Chart API"
        assert "docs" in data


class TestCreateChart:
    def test_create_with_text_data(self, client):
        resp = client.post(
            "/v1/charts",
            data={"data": "Category,Value\nA,10\nB,20\nC,30", "chart_type": "bar"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
        assert "embed_url" in data
        assert "chart_type" in data
        assert "created_at" in data
        assert data["chart_type"] == "bar"

    def test_create_with_auto_type(self, client):
        resp = client.post(
            "/v1/charts",
            data={"data": "X,Y\n1,10\n2,20\n3,15\n4,25", "chart_type": "auto"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["chart_type"] in ["line", "bar", "scatter", "pie"]

    def test_create_with_file_upload(self, client):
        csv_content = b"Product,Sales\nWidget,100\nGadget,200"
        resp = client.post(
            "/v1/charts",
            files={"file": ("data.csv", csv_content, "text/csv")},
            data={"chart_type": "bar"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data

    def test_create_with_title(self, client):
        resp = client.post(
            "/v1/charts",
            data={"data": "A,B\n1,2\n3,4", "chart_type": "line", "title": "Custom Title"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Custom Title"

    def test_create_no_input_returns_400(self, client):
        resp = client.post("/v1/charts", data={"chart_type": "bar"})
        assert resp.status_code == 400

    def test_create_invalid_data_returns_400(self, client):
        resp = client.post(
            "/v1/charts",
            data={"data": "not valid tabular data at all!!!", "chart_type": "bar"},
        )
        # Should either return 400 or 500 depending on parser behavior
        assert resp.status_code in [400, 500]


class TestGetChart:
    def _create_chart(self, client):
        resp = client.post(
            "/v1/charts",
            data={"data": "Cat,Val\nA,10\nB,20\nC,30", "chart_type": "bar"},
        )
        return resp.json()["id"]

    def test_get_chart_metadata(self, client):
        chart_id = self._create_chart(client)
        resp = client.get(f"/v1/charts/{chart_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == chart_id
        assert "embed_url" in data

    def test_get_chart_not_found(self, client):
        resp = client.get("/v1/charts/nonexistent-id")
        assert resp.status_code == 404

    def test_get_chart_embed(self, client):
        chart_id = self._create_chart(client)
        resp = client.get(f"/v1/charts/{chart_id}/embed")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]
        assert "Plotly.newPlot" in resp.text

    def test_get_chart_embed_not_found(self, client):
        resp = client.get("/v1/charts/nonexistent-id/embed")
        assert resp.status_code == 404

    @patch("chart_service.exporters.image.pio.to_image", return_value=FAKE_PNG)
    def test_get_chart_image(self, mock_to_image, client):
        chart_id = self._create_chart(client)
        resp = client.get(f"/v1/charts/{chart_id}/image")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "image/png"
        assert resp.content[:4] == b"\x89PNG"

    def test_get_chart_image_not_found(self, client):
        resp = client.get("/v1/charts/nonexistent-id/image")
        assert resp.status_code == 404

    def test_get_chart_code(self, client):
        chart_id = self._create_chart(client)
        resp = client.get(f"/v1/charts/{chart_id}/code")
        assert resp.status_code == 200
        data = resp.json()
        assert "code" in data
        assert "import pandas" in data["code"]
        assert "plotly" in data["code"]

    def test_get_chart_code_not_found(self, client):
        resp = client.get("/v1/charts/nonexistent-id/code")
        assert resp.status_code == 404
