"""
Health check models for RAG Agent API.

Contains Pydantic models for /health endpoint responses.
"""

from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel, Field


class ServiceStatus(BaseModel):
    """Status of a dependent service."""

    name: str = Field(..., description="Service name")
    status: str = Field(
        ...,
        description="Service status: 'healthy' | 'degraded' | 'unavailable'",
    )
    latency_ms: Optional[float] = Field(
        None,
        ge=0,
        description="Response latency in milliseconds",
    )
    error: Optional[str] = Field(
        None,
        description="Error message if unhealthy",
    )


class HealthResponse(BaseModel):
    """Health check response for /health endpoint."""

    status: str = Field(
        ...,
        description="Overall status: 'healthy' | 'degraded' | 'unavailable'",
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Health check timestamp",
    )
    services: Dict[str, ServiceStatus] = Field(
        default_factory=dict,
        description="Status of dependent services",
    )
    version: str = Field(
        default="0.1.0",
        description="API version",
    )
