"""
API Keys Schemas - Request/Response models for cloud AI key management.
"""

from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime


class APIKeyCreate(BaseModel):
    """Schema for saving an API key."""
    provider: str  # anthropic, openai, custom
    api_key: str
    base_url: Optional[str] = None  # Required for custom provider

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v):
        valid = {"anthropic", "openai", "custom"}
        if v not in valid:
            raise ValueError(f"Invalid provider. Must be one of: {valid}")
        return v

    @field_validator("api_key")
    @classmethod
    def validate_key_not_empty(cls, v):
        if not v or len(v.strip()) < 8:
            raise ValueError("API key must be at least 8 characters")
        return v.strip()


class APIKeySummary(BaseModel):
    """Schema for API key summary (never exposes full key)."""
    provider: str
    key_hint: Optional[str] = None
    is_valid: bool = True
    base_url: Optional[str] = None
    last_validated_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class APIKeyTestResult(BaseModel):
    """Schema for API key test result."""
    provider: str
    valid: bool
    message: str
    models_available: int = 0
