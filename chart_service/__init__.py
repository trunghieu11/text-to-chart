"""
Text-to-Chart: Chart Service Core

Provides parser registry, chart type registry, plotter registry,
and an orchestration function to go from raw input to Plotly figure.
"""

from __future__ import annotations

import logging
from typing import List, Optional, Tuple, Union

from chart_service.models import ChartConfig, ParsedData
from chart_service.parsers import parser_registry
from chart_service.chart_types import chart_type_registry
from chart_service.plotters import plotter_registry

logger = logging.getLogger(__name__)


def create_chart(
    raw_input: Union[str, bytes],
    filename: Optional[str] = None,
    chart_type: str = "auto",
    title: Optional[str] = None,
    x_column: Optional[str] = None,
    y_columns: Optional[List[str]] = None,
) -> Tuple[ParsedData, ChartConfig, "go.Figure"]:
    """
    End-to-end: parse input -> decide chart type -> plot figure.

    Args:
        raw_input: Raw text or file bytes.
        filename: Optional filename for parser selection.
        chart_type: "auto" for AI/rule-based, or specific type name.
        title: Optional chart title.
        x_column: Optional x-axis column override.
        y_columns: Optional y-axis columns override.

    Returns:
        Tuple of (ParsedData, ChartConfig, plotly Figure).
    """
    import plotly.graph_objects as go

    # 1. Parse
    logger.info(
        "[DEBUG] create_chart: raw_input type=%s, len=%s, filename=%s",
        type(raw_input).__name__,
        len(raw_input) if raw_input is not None else 0,
        filename,
    )
    print(f"[CREATE_CHART] start type={type(raw_input).__name__} len={len(raw_input) if raw_input else 0} filename={filename!r}", flush=True)
    parser = parser_registry.get_parser_for(raw_input, filename)
    print(f"[CREATE_CHART] parsing with {parser.name}...", flush=True)
    df = parser.parse(raw_input, filename)
    source_type = parser.name
    logger.info("[DEBUG] create_chart: parsed source=%s, shape=%s", source_type, df.shape)
    print(f"[CREATE_CHART] parsed source={source_type} shape={df.shape}", flush=True)
    parsed = ParsedData(dataframe=df, source_type=source_type)

    # 2. Decide chart type and build config
    config = None

    if chart_type == "auto":
        # Try LLM first, then fall back to rules
        try:
            from chart_service.llm.client import llm_client

            if llm_client.is_available:
                config = llm_client.infer_chart_config(
                    df, available_types=chart_type_registry.list_types()
                )
        except Exception:
            pass  # Graceful degradation

        if config is None:
            chosen_type = chart_type_registry.infer_best_type(df)
            ct = chart_type_registry.get(chosen_type)
            config = ct.get_default_config(df)
            config.chart_type = chosen_type
    else:
        chart_type_registry.get(chart_type)  # validate it exists
        ct = chart_type_registry.get(chart_type)
        config = ct.get_default_config(df)
        config.chart_type = chart_type

    # 3. Apply overrides
    if title:
        config.title = title
    if x_column:
        config.x_column = x_column
    if y_columns:
        config.y_columns = y_columns

    # 4. Plot
    fig = plotter_registry.plot(df, config)
    logger.info("[DEBUG] create_chart: plot done, figure has %s traces", len(fig.data))
    return parsed, config, fig
