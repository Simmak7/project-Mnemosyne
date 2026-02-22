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


class CircuitBreakerStatus(BaseModel):
    """Status of a circuit breaker."""
    state: str  # 'closed', 'open', 'half_open'
    failure_count: int
    failure_threshold: int
    recovery_timeout_s: float


class HealthResponse(BaseModel):
    """Response schema for health check endpoint."""
    status: str  # 'healthy', 'degraded', 'unhealthy'
    version: Optional[str] = None
    build: Optional[int] = None
    components: Dict[str, str]
    circuit_breakers: Optional[Dict[str, CircuitBreakerStatus]] = None


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


class GpuLoadedModel(BaseModel):
    """A model currently loaded in Ollama."""
    name: str
    size: int = 0
    size_vram: int = 0
    digest: str = ""
    expires_at: str = ""


class GpuInfoResponse(BaseModel):
    """Response schema for GPU info endpoint."""
    gpu_detected: bool
    total_vram_bytes: int = 0
    total_vram_gb: float = 0.0
    loaded_models: list[GpuLoadedModel] = []
    error: Optional[str] = None


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
    is_available: bool = True  # Whether model is downloaded/accessible
    provider: str = "ollama"  # Provider source: ollama, anthropic, openai, custom


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


class ModelUpdateStatus(BaseModel):
    """Update status for a single model."""
    model: str
    update_available: bool
    status: str  # 'up_to_date', 'update_available', 'unknown', 'error'
    local_digest: Optional[str] = None
    remote_digest: Optional[str] = None


class ModelUpdatesResponse(BaseModel):
    """Response schema for model updates check."""
    updates: list[ModelUpdateStatus]
    checked_count: int
