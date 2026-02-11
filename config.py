"""
Application configuration.

All configuration is loaded from environment variables with sensible defaults.
If a .env file exists in the project root, it is loaded automatically (python-dotenv).
"""

from __future__ import annotations

import os
from pathlib import Path

from dataclasses import dataclass, field

# Load .env from project root when this module is first imported
_env_path = Path(__file__).resolve().parent / ".env"
if _env_path.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(_env_path)
    except ImportError:
        pass  # python-dotenv optional; env vars can be set by shell instead


@dataclass
class AppConfig:
    """Application configuration loaded from environment."""

    # LLM
    openai_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    vision_model: str = "gpt-4o"

    # API
    api_keys: list[str] = field(default_factory=list)
    rate_limit: str = "60/minute"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Taipy UI
    ui_host: str = "0.0.0.0"
    ui_port: int = 5000

    # Storage
    chart_ttl_hours: int = 24
    usage_db_path: str = "usage.db"
    saas_db_path: str = "saas.db"

    # Admin (for Admin UI)
    admin_username: str = ""
    admin_password: str = ""

    # Chart defaults
    default_template: str = "plotly_white"

    @classmethod
    def from_env(cls) -> AppConfig:
        """Load configuration from environment variables."""
        api_keys_str = os.environ.get("API_KEYS", "")
        api_keys = [k.strip() for k in api_keys_str.split(",") if k.strip()]

        return cls(
            openai_api_key=os.environ.get("OPENAI_API_KEY", ""),
            llm_model=os.environ.get("LLM_MODEL", "gpt-4o-mini"),
            vision_model=os.environ.get("VISION_MODEL", "gpt-4o"),
            api_keys=api_keys,
            rate_limit=os.environ.get("RATE_LIMIT", "60/minute"),
            api_host=os.environ.get("API_HOST", "0.0.0.0"),
            api_port=int(os.environ.get("API_PORT", "8000")),
            ui_host=os.environ.get("UI_HOST", "0.0.0.0"),
            ui_port=int(os.environ.get("UI_PORT", "5000")),
            chart_ttl_hours=int(os.environ.get("CHART_TTL_HOURS", "24")),
            usage_db_path=os.environ.get("USAGE_DB_PATH", "usage.db"),
            saas_db_path=os.environ.get("SAAS_DB_PATH", "saas.db"),
            admin_username=os.environ.get("ADMIN_USERNAME", ""),
            admin_password=os.environ.get("ADMIN_PASSWORD", ""),
            default_template=os.environ.get("CHART_TEMPLATE", "plotly_white"),
        )


# Global config singleton
config = AppConfig.from_env()
