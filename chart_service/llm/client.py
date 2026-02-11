"""
LLM client for chart configuration inference and image data extraction.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Optional

import pandas as pd

from chart_service.llm.prompts import (
    CHART_CONFIG_SYSTEM_PROMPT,
    CHART_CONFIG_USER_PROMPT,
    IMAGE_EXTRACTION_SYSTEM_PROMPT,
    IMAGE_EXTRACTION_USER_PROMPT,
)
from chart_service.llm.schema import CHART_CONFIG_SCHEMA, TABLE_EXTRACTION_SCHEMA
from chart_service.models import ChartConfig

logger = logging.getLogger(__name__)


def _get_api_key(api_key: str | None = None) -> str | None:
    """Resolve API key: explicit argument (including '') > config (from .env) > os.environ."""
    if api_key is not None:
        return api_key.strip() or None
    try:
        from config import config as app_config
        if getattr(app_config, "openai_api_key", ""):
            return app_config.openai_api_key.strip() or None
    except ImportError:
        pass
    return (os.environ.get("OPENAI_API_KEY") or "").strip() or None


class LLMClient:
    """Client for OpenAI API interactions."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gpt-4o-mini",
        vision_model: str = "gpt-4o",
    ):
        self._api_key_arg = api_key
        self.api_key = _get_api_key(api_key)
        self.model = model
        self.vision_model = vision_model
        self._client = None

    @property
    def is_available(self) -> bool:
        """Check if API key is configured (re-read from config/env at use time)."""
        key = _get_api_key(self._api_key_arg)
        if key and key != self.api_key:
            self.api_key = key
        return bool(self.api_key)

    def _get_client(self):
        """Lazy-initialize the OpenAI client."""
        key = _get_api_key(self._api_key_arg)
        if key:
            self.api_key = key
        if not self.api_key:
            return None
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key)
            except ImportError:
                raise ImportError("openai package is required. Install with: pip install openai")
        return self._client

    def infer_chart_config(
        self,
        df: pd.DataFrame,
        available_types: list[str] | None = None,
    ) -> ChartConfig | None:
        """
        Use LLM to suggest chart type and configuration for the given data.

        Args:
            df: The data to visualize.
            available_types: List of valid chart type names.

        Returns:
            ChartConfig if successful, None if LLM is unavailable or fails.
        """
        if not self.is_available:
            logger.warning("LLM not available (no API key). Falling back to rule-based.")
            return None

        try:
            # Prepare data summary as JSON (max 50 rows as per spec)
            sample = df.head(min(50, len(df)))
            sample_str = sample.to_json(orient="records", indent=2, default_handler=str)
            columns = list(df.columns)
            column_types = {col: str(df[col].dtype) for col in columns}
            column_types_str = "\n".join(f"  - {col}: {dtype}" for col, dtype in column_types.items())

            user_prompt = CHART_CONFIG_USER_PROMPT.format(
                columns=columns,
                n_rows=min(20, len(df)),
                sample_data=sample_str,
                total_rows=len(df),
                column_types=column_types_str,
            )

            client = self._get_client()
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": CHART_CONFIG_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=500,
            )

            result = json.loads(response.choices[0].message.content)
            logger.info(f"LLM suggested: {result}")

            # Validate chart type
            chart_type = result.get("chart_type", "bar")
            if available_types and chart_type not in available_types:
                logger.warning(
                    f"LLM suggested '{chart_type}' which is not available. "
                    f"Falling back to rule-based."
                )
                return None

            # Validate columns exist in dataframe
            x_col = result.get("x_column")
            y_cols = result.get("y_columns", [])
            if x_col and x_col not in df.columns:
                logger.warning(f"LLM suggested x_column '{x_col}' not in data columns.")
                return None
            for y in y_cols:
                if y not in df.columns:
                    logger.warning(f"LLM suggested y_column '{y}' not in data columns.")
                    return None

            return ChartConfig(
                chart_type=chart_type,
                x_column=x_col,
                y_columns=y_cols,
                title=result.get("title"),
                x_label=result.get("x_label"),
                y_label=result.get("y_label"),
            )

        except Exception as e:
            logger.error(f"LLM inference failed: {e}")
            return None

    def extract_table_from_image(
        self,
        image_bytes: bytes,
        mime_type: str = "image/png",
    ) -> dict[str, Any] | None:
        """
        Use Vision LLM to extract tabular data from an image.

        Args:
            image_bytes: Raw image bytes.
            mime_type: MIME type of the image.

        Returns:
            Dict with 'columns' and 'rows' keys, or None on failure.
        """
        if not self.is_available:
            logger.warning("[DEBUG] LLM not available for image extraction (no API key).")
            return None

        try:
            import base64
            b64_image = base64.b64encode(image_bytes).decode("utf-8")
            logger.info(
                "[DEBUG] Vision API: calling model=%s, image_bytes=%s, mime=%s",
                self.vision_model,
                len(image_bytes),
                mime_type,
            )

            client = self._get_client()
            response = client.chat.completions.create(
                model=self.vision_model,
                messages=[
                    {"role": "system", "content": IMAGE_EXTRACTION_SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": IMAGE_EXTRACTION_USER_PROMPT},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{b64_image}",
                                },
                            },
                        ],
                    },
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=4096,
            )

            raw_content = response.choices[0].message.content
            logger.info("[DEBUG] Vision API: response length=%s chars", len(raw_content) if raw_content else 0)
            print(f"[VISION] API response length={len(raw_content) if raw_content else 0} chars", flush=True)
            result = json.loads(raw_content)
            rows = result.get("rows", [])
            cols = result.get("columns", [])
            logger.info(
                "[DEBUG] Vision API: parsed result columns=%s, rows=%s",
                cols,
                len(rows),
            )
            if len(rows) and len(rows[0]) != len(cols):
                logger.warning(
                    "[DEBUG] Vision API: row length %s != columns %s",
                    len(rows[0]) if rows else 0,
                    len(cols),
                )

            if "columns" in result and "rows" in result:
                return result
            logger.warning("[DEBUG] Vision API: result missing 'columns' or 'rows', keys=%s", list(result.keys()))
            return None

        except Exception as e:
            logger.error("Image extraction failed: %s", e, exc_info=True)
            print(f"[VISION] API failed: {type(e).__name__}: {e}", flush=True)
            return None


# Global singleton
llm_client = LLMClient()
