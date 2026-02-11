"""
Tests for API chart storage.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pytest

from api.storage import ChartStore
from chart_service.models import ChartConfig


@pytest.fixture
def store():
    return ChartStore(ttl_hours=24)


@pytest.fixture
def sample_fig():
    df = pd.DataFrame({"X": ["A", "B"], "Y": [10, 20]})
    return px.bar(df, x="X", y="Y")


@pytest.fixture
def sample_df():
    return pd.DataFrame({"X": ["A", "B"], "Y": [10, 20]})


@pytest.fixture
def sample_config():
    return ChartConfig(chart_type="bar", x_column="X", y_columns=["Y"])


class TestChartStore:
    def test_save_and_get(self, store, sample_fig, sample_df, sample_config):
        chart_id = store.save(sample_fig, sample_df, sample_config)
        assert chart_id is not None

        data = store.get(chart_id)
        assert data is not None
        assert "figure_json" in data
        assert "dataframe_dict" in data
        assert "config" in data
        assert "created_at" in data

    def test_save_with_custom_id(self, store, sample_fig, sample_df, sample_config):
        chart_id = store.save(sample_fig, sample_df, sample_config, chart_id="my-custom-id")
        assert chart_id == "my-custom-id"
        assert store.exists("my-custom-id")

    def test_get_nonexistent(self, store):
        assert store.get("does-not-exist") is None

    def test_exists(self, store, sample_fig, sample_df, sample_config):
        chart_id = store.save(sample_fig, sample_df, sample_config)
        assert store.exists(chart_id) is True
        assert store.exists("nope") is False

    def test_delete(self, store, sample_fig, sample_df, sample_config):
        chart_id = store.save(sample_fig, sample_df, sample_config)
        assert store.delete(chart_id) is True
        assert store.exists(chart_id) is False
        assert store.delete(chart_id) is False  # Already deleted

    def test_get_figure(self, store, sample_fig, sample_df, sample_config):
        chart_id = store.save(sample_fig, sample_df, sample_config)
        fig = store.get_figure(chart_id)
        assert isinstance(fig, go.Figure)

    def test_get_figure_nonexistent(self, store):
        assert store.get_figure("nope") is None

    def test_get_dataframe(self, store, sample_fig, sample_df, sample_config):
        chart_id = store.save(sample_fig, sample_df, sample_config)
        df = store.get_dataframe(chart_id)
        assert isinstance(df, pd.DataFrame)
        assert list(df.columns) == ["X", "Y"]
        assert len(df) == 2

    def test_get_config(self, store, sample_fig, sample_df, sample_config):
        chart_id = store.save(sample_fig, sample_df, sample_config)
        config = store.get_config(chart_id)
        assert isinstance(config, ChartConfig)
        assert config.chart_type == "bar"
        assert config.x_column == "X"
