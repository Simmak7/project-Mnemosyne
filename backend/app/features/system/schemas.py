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
    version: Optional[str] = None
    build: Optional[int] = None
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


class ModelInfoResponse(BaseModel):
    """Response schema for a single AI model."""
    id: str
    name: str
    description: str
    size_gb: float
    parameters: str
    category: str
    use_cases: list[str]
    context_length: int
    features: list[str]
    recommended_for: Optional[str] = None
    is_default_rag: bool = False
    is_default_brain: bool = False
    is_available: bool = True  # Whether model is downloaded in Ollama


class ModelsListResponse(BaseModel):
    """Response schema for models list endpoint."""
    models: list[ModelInfoResponse]
    current_rag_model: str
    current_brain_model: str
    current_nexus_model: Optional[str] = None
    current_vision_model: str


class ModelConfigResponse(BaseModel):
    """Response schema for current model configuration."""
    rag_model: str
    brain_model: str
    rag_model_info: Optional[ModelInfoResponse] = None
    brain_model_info: Optional[ModelInfoResponse] = None
