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
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

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
API_VERSION = "1.0.0"

# RAG (Retrieval-Augmented Generation) Configuration
RAG_MODEL = os.getenv("RAG_MODEL", "llama3.2:3b")  # Smaller model for fast RAG responses
RAG_TIMEOUT = int(os.getenv("RAG_TIMEOUT", "120"))  # seconds
RAG_MAX_CONTEXT_TOKENS = int(os.getenv("RAG_MAX_CONTEXT_TOKENS", "4000"))
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
