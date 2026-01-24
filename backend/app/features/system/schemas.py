"""
System Feature - Pydantic Schemas

Request/Response schemas for system endpoints.
"""

from pydantic import BaseModel
from typing import Dict, Optional


class ComponentStatus(BaseModel):
    """Status of a single system component."""
    name: str
    status: str  # 'connected', 'disconnected', 'ok', 'missing', 'timeout'
    message: Optional[str] = None


class HealthResponse(BaseModel):
    """Response schema for health check endpoint."""
    status: str  # 'healthy', 'degraded', 'unhealthy'
    components: Dict[str, str]


class RootResponse(BaseModel):
    """Response schema for root endpoint."""
    message: str
    version: str
    status: str


class SystemInfoResponse(BaseModel):
    """Extended system information response."""
    api_title: str
    api_version: str
    environment: str
    uptime_seconds: Optional[float] = None
    components: Dict[str, str]
