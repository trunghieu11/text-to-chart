"""
Pydantic request/response models for the API.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ChartCreateResponse(BaseModel):
    """Response after creating a chart."""

    id: str
    embed_url: str
    chart_type: str
    title: Optional[str] = None
    created_at: str


class ChartMetadataResponse(BaseModel):
    """Response for chart metadata."""

    id: str
    embed_url: str
    chart_type: str
    title: Optional[str] = None
    created_at: str


class CodeResponse(BaseModel):
    """Response containing generated Python code."""

    code: str


class ErrorResponse(BaseModel):
    """Standard error response."""

    detail: str


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "ok"
    version: str = "0.1.0"


class UsageResponse(BaseModel):
    """Usage statistics response."""

    api_key: str
    period_start: str
    request_count: int


# Account (Developer Portal)
class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AccountMeResponse(BaseModel):
    id: int
    name: str
    email: str
    plan: str
    status: str


class KeyCreateRequest(BaseModel):
    name: str = "Default"


class KeyCreateResponse(BaseModel):
    id: int
    key: str  # Full key, shown once
    name: str


class KeyListItem(BaseModel):
    id: int
    name: str
    key_prefix: str
    created_at: str


class KeyListResponse(BaseModel):
    keys: list[KeyListItem]


class AccountUsageResponse(BaseModel):
    period_start: str
    request_count: int
    history: Optional[list[dict]] = None
