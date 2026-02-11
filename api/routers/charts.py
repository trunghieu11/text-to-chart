"""
Chart API routes: /v1/charts
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, Response

from api.middleware.auth import TenantContext, verify_api_key
from api.middleware.rate_limit import DEFAULT_RATE_LIMIT, limiter
from api.models import ChartCreateResponse, ChartMetadataResponse, CodeResponse
from api.storage import chart_store
from chart_service import create_chart
from chart_service.exporters.code import CodeExporter
from chart_service.exporters.embed import EmbedExporter
from chart_service.exporters.image import ImageExporter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/charts", tags=["charts"])


@router.post("", response_model=ChartCreateResponse)
@limiter.limit(DEFAULT_RATE_LIMIT)
async def create_chart_endpoint(
    request: Request,
    data: Optional[str] = Form(None, description="Raw text data (tab/comma/space separated)"),
    file: Optional[UploadFile] = File(None, description="File upload (CSV, Excel, or Image)"),
    chart_type: str = Form("auto", description="Chart type: auto, line, bar, scatter, pie"),
    title: Optional[str] = Form(None, description="Optional chart title"),
    ctx: TenantContext = Depends(verify_api_key),
):
    """
    Create a chart from text data or file upload.

    - **data**: Raw text input (tab, comma, or space separated)
    - **file**: File upload (.csv, .xlsx, .xls, .png, .jpg, .jpeg, .webp)
    - **chart_type**: "auto" for AI/rule-based selection, or specific type
    - **title**: Optional chart title
    """
    if not data and not file:
        raise HTTPException(
            status_code=400,
            detail="Provide either 'data' (text) or 'file' (upload).",
        )

    # Quota check for SaaS tenants
    if ctx.has_quota():
        from api.usage import usage_tracker

        period = datetime.now(timezone.utc).strftime("%Y-%m")
        count = usage_tracker.get_count_for_tenant(ctx.tenant_id, period)
        if count >= ctx.monthly_quota:
            raise HTTPException(
                status_code=429,
                detail=f"Quota exceeded for this period. Limit: {ctx.monthly_quota} charts/month.",
            )

    try:
        if file:
            file_bytes = await file.read()
            filename = file.filename
            raw_input = file_bytes
        else:
            raw_input = data
            filename = None

        parsed, config, fig = create_chart(
            raw_input=raw_input,
            filename=filename,
            chart_type=chart_type,
            title=title,
        )

        # Store chart
        chart_id = chart_store.save(fig, parsed.dataframe, config)

        # Track usage
        try:
            from api.usage import usage_tracker

            if ctx.tenant_id is not None:
                usage_tracker.record_for_tenant(ctx.tenant_id, "/v1/charts")
            else:
                usage_tracker.record(ctx.api_key, "/v1/charts")
        except Exception:
            pass  # Don't fail on usage tracking errors

        # Build response
        base_url = str(request.base_url).rstrip("/")
        embed_url = f"{base_url}/v1/charts/{chart_id}/embed"

        chart_data = chart_store.get(chart_id)

        return ChartCreateResponse(
            id=chart_id,
            embed_url=embed_url,
            chart_type=config.chart_type,
            title=config.title,
            created_at=chart_data["created_at"],
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Chart creation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/{chart_id}", response_model=ChartMetadataResponse)
@limiter.limit(DEFAULT_RATE_LIMIT)
async def get_chart(
    request: Request,
    chart_id: str,
    ctx: TenantContext = Depends(verify_api_key),
):
    """Get chart metadata by ID."""
    data = chart_store.get(chart_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Chart not found.")

    base_url = str(request.base_url).rstrip("/")
    config = chart_store.get_config(chart_id)

    return ChartMetadataResponse(
        id=chart_id,
        embed_url=f"{base_url}/v1/charts/{chart_id}/embed",
        chart_type=config.chart_type if config else "unknown",
        title=config.title if config else None,
        created_at=data["created_at"],
    )


@router.get("/{chart_id}/image")
@limiter.limit(DEFAULT_RATE_LIMIT)
async def get_chart_image(
    request: Request,
    chart_id: str,
    ctx: TenantContext = Depends(verify_api_key),
):
    """Get chart as PNG image."""
    fig = chart_store.get_figure(chart_id)
    if fig is None:
        raise HTTPException(status_code=404, detail="Chart not found.")

    try:
        img_bytes = ImageExporter.to_bytes(fig)
        return Response(content=img_bytes, media_type="image/png")
    except Exception as e:
        logger.error(f"Image export failed: {e}")
        raise HTTPException(status_code=500, detail=f"Image export failed: {str(e)}")


@router.get("/{chart_id}/embed", response_class=HTMLResponse)
async def get_chart_embed(
    chart_id: str,
):
    """
    Get embeddable HTML page with the chart.

    Note: This endpoint is public (no auth required) for embedding.
    """
    fig = chart_store.get_figure(chart_id)
    if fig is None:
        raise HTTPException(status_code=404, detail="Chart not found.")

    html = EmbedExporter.generate_embed_html(fig)
    return HTMLResponse(content=html)


@router.get("/{chart_id}/code", response_model=CodeResponse)
@limiter.limit(DEFAULT_RATE_LIMIT)
async def get_chart_code(
    request: Request,
    chart_id: str,
    ctx: TenantContext = Depends(verify_api_key),
):
    """Get reproducible Python code for the chart."""
    df = chart_store.get_dataframe(chart_id)
    config = chart_store.get_config(chart_id)
    if df is None or config is None:
        raise HTTPException(status_code=404, detail="Chart not found.")

    code = CodeExporter.generate(df, config)
    return CodeResponse(code=code)
