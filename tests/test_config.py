"""
Tests for AppConfig: loading from environment variables.
"""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from config import AppConfig


class TestAppConfigDefaults:
    def test_default_values(self):
        with patch.dict(os.environ, {}, clear=True):
            config = AppConfig.from_env()
            assert config.openai_api_key == ""
            assert config.llm_model == "gpt-4o-mini"
            assert config.vision_model == "gpt-4o"
            assert config.api_keys == []
            assert config.rate_limit == "60/minute"
            assert config.api_host == "0.0.0.0"
            assert config.api_port == 8000
            assert config.ui_host == "0.0.0.0"
            assert config.ui_port == 5000
            assert config.chart_ttl_hours == 24
            assert config.usage_db_path == "usage.db"
            assert config.default_template == "plotly_white"


class TestAppConfigFromEnv:
    def test_openai_key(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test123"}, clear=True):
            config = AppConfig.from_env()
            assert config.openai_api_key == "sk-test123"

    def test_api_keys_single(self):
        with patch.dict(os.environ, {"API_KEYS": "key1"}, clear=True):
            config = AppConfig.from_env()
            assert config.api_keys == ["key1"]

    def test_api_keys_multiple(self):
        with patch.dict(os.environ, {"API_KEYS": "key1,key2,key3"}, clear=True):
            config = AppConfig.from_env()
            assert config.api_keys == ["key1", "key2", "key3"]

    def test_api_keys_with_spaces(self):
        with patch.dict(os.environ, {"API_KEYS": " key1 , key2 "}, clear=True):
            config = AppConfig.from_env()
            assert config.api_keys == ["key1", "key2"]

    def test_api_keys_empty(self):
        with patch.dict(os.environ, {"API_KEYS": ""}, clear=True):
            config = AppConfig.from_env()
            assert config.api_keys == []

    def test_rate_limit(self):
        with patch.dict(os.environ, {"RATE_LIMIT": "100/minute"}, clear=True):
            config = AppConfig.from_env()
            assert config.rate_limit == "100/minute"

    def test_api_port(self):
        with patch.dict(os.environ, {"API_PORT": "9000"}, clear=True):
            config = AppConfig.from_env()
            assert config.api_port == 9000

    def test_chart_ttl(self):
        with patch.dict(os.environ, {"CHART_TTL_HOURS": "48"}, clear=True):
            config = AppConfig.from_env()
            assert config.chart_ttl_hours == 48

    def test_custom_template(self):
        with patch.dict(os.environ, {"CHART_TEMPLATE": "plotly_dark"}, clear=True):
            config = AppConfig.from_env()
            assert config.default_template == "plotly_dark"

    def test_llm_model_override(self):
        with patch.dict(os.environ, {"LLM_MODEL": "gpt-4", "VISION_MODEL": "gpt-4-turbo"}, clear=True):
            config = AppConfig.from_env()
            assert config.llm_model == "gpt-4"
            assert config.vision_model == "gpt-4-turbo"

    def test_all_env_vars_together(self):
        env = {
            "OPENAI_API_KEY": "sk-full",
            "LLM_MODEL": "gpt-4",
            "VISION_MODEL": "gpt-4v",
            "API_KEYS": "k1,k2",
            "RATE_LIMIT": "30/minute",
            "API_HOST": "127.0.0.1",
            "API_PORT": "3000",
            "UI_HOST": "127.0.0.1",
            "UI_PORT": "3001",
            "CHART_TTL_HOURS": "12",
            "USAGE_DB_PATH": "/tmp/test.db",
            "CHART_TEMPLATE": "plotly_dark",
        }
        with patch.dict(os.environ, env, clear=True):
            config = AppConfig.from_env()
            assert config.openai_api_key == "sk-full"
            assert config.api_port == 3000
            assert config.ui_port == 3001
            assert config.chart_ttl_hours == 12
            assert config.usage_db_path == "/tmp/test.db"
