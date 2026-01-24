"""
Settings Feature - Pydantic Schemas

Request/Response schemas for user preferences endpoints.
"""

from pydantic import BaseModel, field_validator
from typing import Optional, Literal
from datetime import datetime


# Valid options for preferences
THEME_OPTIONS = ["light", "dark"]
ACCENT_COLOR_OPTIONS = ["blue", "purple", "green", "orange", "pink"]
UI_DENSITY_OPTIONS = ["compact", "comfortable", "spacious"]
FONT_SIZE_OPTIONS = ["small", "medium", "large"]
DEFAULT_VIEW_OPTIONS = ["notes", "gallery", "graph", "buckets"]


class UserPreferencesResponse(BaseModel):
    """Schema for user preferences response."""
    id: int
    user_id: int
    theme: str
    accent_color: str
    ui_density: str
    font_size: str
    sidebar_collapsed: bool
    default_view: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserPreferencesUpdate(BaseModel):
    """Schema for updating user preferences."""
    theme: Optional[Literal["light", "dark"]] = None
    accent_color: Optional[Literal["blue", "purple", "green", "orange", "pink"]] = None
    ui_density: Optional[Literal["compact", "comfortable", "spacious"]] = None
    font_size: Optional[Literal["small", "medium", "large"]] = None
    sidebar_collapsed: Optional[bool] = None
    default_view: Optional[Literal["notes", "gallery", "graph", "buckets"]] = None


class PreferencesOptions(BaseModel):
    """Schema for available preference options."""
    themes: list[str] = THEME_OPTIONS
    accent_colors: list[str] = ACCENT_COLOR_OPTIONS
    ui_density: list[str] = UI_DENSITY_OPTIONS
    font_sizes: list[str] = FONT_SIZE_OPTIONS
    default_views: list[str] = DEFAULT_VIEW_OPTIONS


class AccentColorInfo(BaseModel):
    """Schema for accent color with hex value."""
    value: str
    hex: str


class AccentColorsResponse(BaseModel):
    """Schema for accent colors with hex values."""
    colors: list[AccentColorInfo] = [
        AccentColorInfo(value="blue", hex="#3B82F6"),
        AccentColorInfo(value="purple", hex="#8B5CF6"),
        AccentColorInfo(value="green", hex="#10B981"),
        AccentColorInfo(value="orange", hex="#F59E0B"),
        AccentColorInfo(value="pink", hex="#EC4899"),
    ]


# ============================================
# Phase 4: Data Export Schemas
# ============================================

class DataExportRequest(BaseModel):
    """Schema for data export request."""
    include_notes: bool = True
    include_images: bool = True
    include_tags: bool = True
    include_activity: bool = False


class DataExportResponse(BaseModel):
    """Schema for data export job response."""
    job_id: str
    status: str
    message: str
    created_at: datetime


class DataExportStatus(BaseModel):
    """Schema for data export status response."""
    job_id: str
    status: str  # pending, processing, completed, failed
    progress: Optional[int] = None  # 0-100
    download_url: Optional[str] = None
    expires_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================
# Phase 4: Activity History Schemas
# ============================================

class ActivityItem(BaseModel):
    """Schema for a single activity item."""
    id: int
    type: str  # login, password_change, email_change, 2fa_enabled, etc.
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    success: bool
    failure_reason: Optional[str] = None
    details: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ActivityHistoryResponse(BaseModel):
    """Schema for activity history response."""
    activities: list[ActivityItem]
    total: int
    page: int
    limit: int
    has_more: bool


class ActivityStatsResponse(BaseModel):
    """Schema for activity statistics response."""
    total_logins: int
    successful_logins: int
    failed_logins: int
    unique_ips: int
    period_days: int = 30


# ============================================
# Phase 5: Notification Preferences Schemas
# ============================================

class NotificationPreferencesResponse(BaseModel):
    """Schema for notification preferences response."""
    id: int
    user_id: int
    email_security_alerts: bool
    email_weekly_digest: bool
    email_product_updates: bool
    push_enabled: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NotificationPreferencesUpdate(BaseModel):
    """Schema for updating notification preferences."""
    email_security_alerts: Optional[bool] = None
    email_weekly_digest: Optional[bool] = None
    email_product_updates: Optional[bool] = None
    push_enabled: Optional[bool] = None


class NotificationOptions(BaseModel):
    """Schema for available notification options."""
    email_types: list[dict] = [
        {"key": "email_security_alerts", "label": "Security Alerts", "description": "Password changes, new logins, suspicious activity"},
        {"key": "email_weekly_digest", "label": "Weekly Digest", "description": "Summary of your notes and activity"},
        {"key": "email_product_updates", "label": "Product Updates", "description": "New features and improvements"},
    ]
    push_available: bool = False  # Push notifications not implemented yet