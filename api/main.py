"""
FastAPI application entry point for Text-to-Chart REST API.

Run with: uvicorn api.main:app --reload --port 8000
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# Add project root to path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Load .env from project root (via config)
import config  # noqa: F401

from fastapi import Depends, FastAPI, Request

# Ensure SaaS DB is initialized on startup
try:
    from api.db import ensure_db
    ensure_db()
except Exception:
    pass  # Non-fatal; will retry on first use
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from api.middleware.auth import TenantContext, verify_api_key
from api.middleware.rate_limit import limiter
from api.models import HealthResponse
from api.routers import account, admin, charts

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Text-to-Chart API",
    description=(
        "Convert text, CSV, Excel, and images into beautiful charts. "
        "Supports automatic chart type selection via AI or rule-based logic."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(charts.router)
app.include_router(account.router)
app.include_router(admin.router)


@app.get("/health", response_model=HealthResponse, tags=["system"])
async def health_check():
    """Health check endpoint."""
    return HealthResponse(status="ok", version="0.1.0")


@app.get("/v1/usage", tags=["system"])
async def get_usage(
    ctx: TenantContext = Depends(verify_api_key),
):
    """Get usage statistics for the current API key or tenant."""
    from api.models import UsageResponse
    from api.usage import usage_tracker

    if ctx.tenant_id is not None:
        usage = usage_tracker.get_usage_for_tenant(ctx.tenant_id)
        return UsageResponse(
            api_key=f"tenant:{ctx.tenant_id}",
            period_start=usage["period_start"],
            request_count=usage["request_count"],
        )
    usage = usage_tracker.get_usage(ctx.api_key)
    return UsageResponse(**usage)


@app.get("/", tags=["system"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Text-to-Chart API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
