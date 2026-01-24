"""
Settings Feature Module

Phase 3: User preferences for appearance and UI customization
Phase 4: Data export (GDPR) and activity history
Phase 5: Notification preferences
"""

from features.settings.router import router as settings_router
from features.settings.schemas import (
    UserPreferencesResponse,
    UserPreferencesUpdate,
    DataExportRequest,
    DataExportResponse,
    DataExportStatus,
    ActivityHistoryResponse,
    ActivityStatsResponse,
    NotificationPreferencesResponse,
    NotificationPreferencesUpdate,
    NotificationOptions,
)
from features.settings.service import (
    get_user_preferences,
    update_user_preferences,
    create_default_preferences,
)
from features.settings import data_export
from features.settings import activity
from features.settings import notifications

__all__ = [
    # Router
    "settings_router",
    # Phase 3 Schemas
    "UserPreferencesResponse",
    "UserPreferencesUpdate",
    # Phase 4 Schemas
    "DataExportRequest",
    "DataExportResponse",
    "DataExportStatus",
    "ActivityHistoryResponse",
    "ActivityStatsResponse",
    # Phase 5 Schemas
    "NotificationPreferencesResponse",
    "NotificationPreferencesUpdate",
    "NotificationOptions",
    # Services
    "get_user_preferences",
    "update_user_preferences",
    "create_default_preferences",
    # Phase 4 modules
    "data_export",
    "activity",
    # Phase 5 modules
    "notifications",
]
