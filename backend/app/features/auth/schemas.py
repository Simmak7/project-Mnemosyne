"""
Auth Feature - Pydantic Schemas

Request/Response schemas for authentication endpoints.
"""

from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime


class UserBase(BaseModel):
    """Base user schema with common fields."""
    username: str
    email: EmailStr


class UserCreate(UserBase):
    """Schema for user registration request."""
    password: str


class UserResponse(UserBase):
    """Schema for user response (excludes password)."""
    id: int
    is_active: bool = True
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


# Alias for backward compatibility
User = UserResponse


class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str


class TokenWith2FA(BaseModel):
    """Schema for login response when 2FA is required."""
    requires_2fa: bool = True
    temp_token: str


class Login2FARequest(BaseModel):
    """Schema for completing login with 2FA code."""
    temp_token: str
    code: str


class TokenData(BaseModel):
    """Schema for decoded token data."""
    username: Optional[str] = None


class UserLogin(BaseModel):
    """Schema for login request body (alternative to form data)."""
    username: str
    password: str


# ============================================
# Password Management Schemas
# ============================================

class PasswordChange(BaseModel):
    """Schema for password change request."""
    current_password: str
    new_password: str
    confirm_password: str

    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, v, info):
        if 'new_password' in info.data and v != info.data['new_password']:
            raise ValueError('Passwords do not match')
        return v


class PasswordResetRequest(BaseModel):
    """Schema for password reset request (forgot password)."""
    email: EmailStr


class PasswordReset(BaseModel):
    """Schema for password reset completion."""
    token: str
    new_password: str
    confirm_password: str

    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, v, info):
        if 'new_password' in info.data and v != info.data['new_password']:
            raise ValueError('Passwords do not match')
        return v


class PasswordRequirements(BaseModel):
    """Schema for password requirements response."""
    min_length: int
    require_uppercase: bool
    require_lowercase: bool
    require_digit: bool
    require_special: bool
    special_characters: str


class PasswordStrength(BaseModel):
    """Schema for password strength response."""
    score: int
    strength: str
    feedback: List[str]


# ============================================
# 2FA Schemas
# ============================================

class TwoFactorSetupResponse(BaseModel):
    """Schema for 2FA setup response."""
    secret: str
    qr_code: str  # Base64 encoded PNG
    backup_codes: List[str]


class TwoFactorEnable(BaseModel):
    """Schema for enabling 2FA (verification code required)."""
    code: str


class TwoFactorDisable(BaseModel):
    """Schema for disabling 2FA."""
    code: str
    password: str


class TwoFactorVerify(BaseModel):
    """Schema for 2FA verification during login."""
    temp_token: str
    code: str


class TwoFactorStatus(BaseModel):
    """Schema for 2FA status response."""
    is_enabled: bool
    has_backup_codes: bool


# ============================================
# Session Management Schemas
# ============================================

class SessionInfo(BaseModel):
    """Schema for session information."""
    id: int
    device_info: Optional[str]
    ip_address: Optional[str]
    last_active: datetime
    created_at: datetime
    is_current: bool = False

    class Config:
        from_attributes = True


class SessionListResponse(BaseModel):
    """Schema for list of user sessions."""
    sessions: List[SessionInfo]
    total: int


# ============================================
# Login Attempt Schemas
# ============================================

class LoginAttemptInfo(BaseModel):
    """Schema for login attempt information."""
    ip_address: Optional[str]
    success: bool
    failure_reason: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class AccountLockStatus(BaseModel):
    """Schema for account lock status."""
    is_locked: bool
    locked_until: Optional[datetime]
    failed_attempts: int
    max_attempts: int


# ============================================
# Profile Management Schemas (Phase 2)
# ============================================

class ProfileResponse(BaseModel):
    """Schema for user profile response."""
    id: int
    username: str
    email: EmailStr
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: datetime
    last_login: Optional[datetime] = None
    password_changed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProfileUpdate(BaseModel):
    """Schema for profile update request."""
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None

    @field_validator('display_name')
    @classmethod
    def validate_display_name(cls, v):
        if v is not None and len(v) > 100:
            raise ValueError('Display name must be 100 characters or less')
        return v


# ============================================
# Email Change Schemas (Phase 2)
# ============================================

class EmailChangeRequest(BaseModel):
    """Schema for email change request."""
    new_email: EmailStr
    password: str


class EmailChangeVerify(BaseModel):
    """Schema for email change verification."""
    token: str


# ============================================
# Account Deletion Schemas (Phase 2)
# ============================================

class AccountDeleteRequest(BaseModel):
    """Schema for account deletion request."""
    password: str
    confirmation: str

    @field_validator('confirmation')
    @classmethod
    def validate_confirmation(cls, v):
        if v != "DELETE MY ACCOUNT":
            raise ValueError('Please type "DELETE MY ACCOUNT" to confirm')
        return v


class AccountDeleteResponse(BaseModel):
    """Schema for account deletion response."""
    message: str
    deletion_scheduled_at: datetime
    can_restore_until: datetime


class AccountRestoreRequest(BaseModel):
    """Schema for account restoration request."""
    username: str
    password: str


class AccountDeletionStatus(BaseModel):
    """Schema for account deletion status response."""
    scheduled_at: datetime
    permanent_deletion_at: datetime
    days_remaining: int
    can_restore: bool


class SessionRevokeResponse(BaseModel):
    """Schema for session revoke response."""
    message: str
    revoked_count: Optional[int] = None
