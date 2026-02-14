"""
Application configuration module.

Loads settings from environment variables with sensible defaults.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/ai_notes_db")

# Redis Configuration (for Celery task queue)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "YOUR-SECRET-KEY-CHANGE-THIS-IN-PRODUCTION")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))  # Reduced for security
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))  # Refresh token lasts 7 days

# Ollama Configuration
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")

# AI Model Configuration (Phase 1: Migration to Qwen 2.5-VL)
# Feature flags for gradual model migration
USE_NEW_MODEL = os.getenv("USE_NEW_MODEL", "false").lower() == "true"
NEW_MODEL_ROLLOUT_PERCENT = int(os.getenv("NEW_MODEL_ROLLOUT_PERCENT", "0"))
OLLAMA_MODEL_OLD = os.getenv("OLLAMA_MODEL_OLD", "llama3.2-vision:11b")
OLLAMA_MODEL_NEW = os.getenv("OLLAMA_MODEL_NEW", "qwen2.5vl:7b-q4_K_M")

# Prompt Configuration
# Options: legacy, adaptive (recommended) - hybrid removed (was causing hallucinations)
PROMPT_VERSION = os.getenv("PROMPT_VERSION", "adaptive")
PROMPT_ROLLOUT_PERCENT = int(os.getenv("PROMPT_ROLLOUT_PERCENT", "100"))

# Monitoring & Logging
LOG_MODEL_SELECTION = os.getenv("LOG_MODEL_SELECTION", "true").lower() == "true"
LOG_DETECTED_CONTENT_TYPE = os.getenv("LOG_DETECTED_CONTENT_TYPE", "true").lower() == "true"
METRICS_ENABLED = os.getenv("METRICS_ENABLED", "true").lower() == "true"

# File Upload Configuration
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "10"))
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024
ALLOWED_FILE_TYPES = os.getenv("ALLOWED_FILE_TYPES", "image/jpeg,image/png,image/gif,image/webp").split(",")

# Directory Configuration
UPLOAD_DIR = "uploaded_images"

# API Configuration
API_TITLE = "AI Notes Notetaker API"
API_VERSION = "1.1.0"
# Build number tracks development iterations (project started November 2025)
APP_BUILD = 20

# RAG (Retrieval-Augmented Generation) Configuration
# Default: Qwen3 8B - excellent reasoning with thinking mode
RAG_MODEL = os.getenv("RAG_MODEL", "qwen3:8b")
RAG_TIMEOUT = int(os.getenv("RAG_TIMEOUT", "180"))  # seconds (increased for larger model)
RAG_MAX_CONTEXT_TOKENS = int(os.getenv("RAG_MAX_CONTEXT_TOKENS", "8000"))  # Qwen3 supports 32K
RAG_TEMPERATURE = float(os.getenv("RAG_TEMPERATURE", "0.3"))  # Lower for factual responses

# Security Configuration (Phase 1: Settings)
MAX_LOGIN_ATTEMPTS = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
LOCKOUT_DURATION_MINUTES = int(os.getenv("LOCKOUT_DURATION_MINUTES", "30"))
ATTEMPT_WINDOW_MINUTES = int(os.getenv("ATTEMPT_WINDOW_MINUTES", "15"))
PASSWORD_RESET_EXPIRE_MINUTES = int(os.getenv("PASSWORD_RESET_EXPIRE_MINUTES", "60"))

# Email Configuration (Resend)
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
EMAIL_FROM_ADDRESS = os.getenv("EMAIL_FROM_ADDRESS", "noreply@mnemosyne.app")
EMAIL_FROM_NAME = os.getenv("EMAIL_FROM_NAME", "Mnemosyne")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# Password Requirements
PASSWORD_MIN_LENGTH = int(os.getenv("PASSWORD_MIN_LENGTH", "8"))
PASSWORD_REQUIRE_UPPERCASE = os.getenv("PASSWORD_REQUIRE_UPPERCASE", "true").lower() == "true"
PASSWORD_REQUIRE_LOWERCASE = os.getenv("PASSWORD_REQUIRE_LOWERCASE", "true").lower() == "true"
PASSWORD_REQUIRE_DIGIT = os.getenv("PASSWORD_REQUIRE_DIGIT", "true").lower() == "true"
PASSWORD_REQUIRE_SPECIAL = os.getenv("PASSWORD_REQUIRE_SPECIAL", "true").lower() == "true"

# 2FA Configuration
TOTP_ISSUER_NAME = os.getenv("TOTP_ISSUER_NAME", "Mnemosyne")

# Password Breach Checking (haveibeenpwned)
# Set to false to disable checking passwords against known breaches
PASSWORD_CHECK_BREACH = os.getenv("PASSWORD_CHECK_BREACH", "true").lower() == "true"

# CORS Configuration
# In production, set CORS_ORIGINS to your actual frontend domain(s)
# Example: "https://app.mnemosyne.com,https://www.mnemosyne.com"
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:8000"
).split(",")

# Restrict CORS methods and headers for better security
CORS_ALLOW_METHODS = os.getenv(
    "CORS_ALLOW_METHODS",
    "GET,POST,PUT,DELETE,OPTIONS,PATCH"
).split(",")

CORS_ALLOW_HEADERS = os.getenv(
    "CORS_ALLOW_HEADERS",
    "Authorization,Content-Type,Accept,Origin,X-Requested-With,X-CSRF-Token"
).split(",")

# Security Headers Configuration
# Enable HSTS only in production with valid HTTPS certificate
ENABLE_HSTS = os.getenv("ENABLE_HSTS", "false").lower() == "true"

# Environment indicator (development, staging, production)
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Document (PDF) Configuration
MAX_PDF_SIZE_MB = int(os.getenv("MAX_PDF_SIZE_MB", "50"))
DOCUMENT_UPLOAD_DIR = os.getenv("DOCUMENT_UPLOAD_DIR", "uploaded_documents")
DOCUMENT_THUMBNAIL_DIR = os.getenv("DOCUMENT_THUMBNAIL_DIR", "uploaded_documents/thumbnails")
DOCUMENT_VISION_FALLBACK = os.getenv("DOCUMENT_VISION_FALLBACK", "true").lower() == "true"

# Mnemosyne Brain Configuration
# Default: llama3.2:3b - lightweight, reliable model for brain conversations
BRAIN_MODEL = os.getenv("BRAIN_MODEL", "llama3.2:3b")
BRAIN_MAX_CONTEXT_TOKENS = int(os.getenv("BRAIN_MAX_CONTEXT_TOKENS", "6000"))
BRAIN_CORE_TOKEN_BUDGET = int(os.getenv("BRAIN_CORE_TOKEN_BUDGET", "4000"))
BRAIN_TOPIC_TOKEN_BUDGET = int(os.getenv("BRAIN_TOPIC_TOKEN_BUDGET", "6000"))
BRAIN_TEMPERATURE = float(os.getenv("BRAIN_TEMPERATURE", "0.7"))
BRAIN_MIN_NOTES = int(os.getenv("BRAIN_MIN_NOTES", "3"))

# Dynamic Context Scaling - scales brain budget to the model's context window
BRAIN_MIN_CONTEXT_TOKENS = int(os.getenv("BRAIN_MIN_CONTEXT_TOKENS", "2000"))
BRAIN_CONTEXT_RATIO = float(os.getenv("BRAIN_CONTEXT_RATIO", "0.6"))

# NEXUS Configuration - Graph-Native Adaptive Retrieval
NEXUS_NAVIGATION_MODEL = os.getenv("NEXUS_NAVIGATION_MODEL", "llama3.2:3b")
NEXUS_NAVIGATION_TIMEOUT = int(os.getenv("NEXUS_NAVIGATION_TIMEOUT", "15"))
NEXUS_MAX_CONTEXT_TOKENS = int(os.getenv("NEXUS_MAX_CONTEXT_TOKENS", "6000"))
NEXUS_SOURCE_TOKEN_BUDGET = int(os.getenv("NEXUS_SOURCE_TOKEN_BUDGET", "4000"))
NEXUS_CONNECTION_TOKEN_BUDGET = int(os.getenv("NEXUS_CONNECTION_TOKEN_BUDGET", "800"))
NEXUS_ORIGIN_TOKEN_BUDGET = int(os.getenv("NEXUS_ORIGIN_TOKEN_BUDGET", "400"))
NEXUS_CONVERSATION_TOKEN_BUDGET = int(os.getenv("NEXUS_CONVERSATION_TOKEN_BUDGET", "800"))
