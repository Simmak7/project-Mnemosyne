"""
LLM Cost Tracker - Token usage logging and cost estimation.

Tracks per-user token usage and estimated costs for cloud providers.
"""

import logging
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import text

from core.llm.base import LLMResponse, ProviderType

logger = logging.getLogger(__name__)

# Cost per 1M tokens (input, output) in USD
COST_TABLE = {
    # Anthropic
    "claude-opus-4-0520": (15.0, 75.0),
    "claude-sonnet-4-5-20250929": (3.0, 15.0),
    "claude-sonnet-4-20250514": (3.0, 15.0),
    "claude-haiku-4-5-20251001": (0.80, 4.0),
    # OpenAI
    "gpt-4o": (2.50, 10.0),
    "gpt-4o-mini": (0.15, 0.60),
    "o1": (15.0, 60.0),
    "o3-mini": (1.10, 4.40),
    "gpt-4.1": (2.0, 8.0),
    "gpt-4.1-mini": (0.40, 1.60),
}

# Default cost for unknown models
DEFAULT_COST = (1.0, 3.0)


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate cost in USD for a given model and token counts."""
    input_rate, output_rate = COST_TABLE.get(model, DEFAULT_COST)
    cost = (input_tokens * input_rate / 1_000_000) + (output_tokens * output_rate / 1_000_000)
    return round(cost, 6)


def log_token_usage(
    db: Session,
    user_id: int,
    response: LLMResponse,
    use_case: str = "rag",
    conversation_id: int = None,
) -> None:
    """Log token usage for a cloud AI response."""
    if response.provider == ProviderType.OLLAMA:
        return  # Don't track local model usage

    cost = estimate_cost(
        response.model, response.input_tokens, response.output_tokens
    )

    try:
        db.execute(text("""
            INSERT INTO ai_usage_logs
                (user_id, provider, model, input_tokens, output_tokens,
                 estimated_cost_usd, use_case, conversation_id)
            VALUES
                (:user_id, :provider, :model, :input_tokens, :output_tokens,
                 :cost, :use_case, :conversation_id)
        """), {
            "user_id": user_id,
            "provider": response.provider.value,
            "model": response.model,
            "input_tokens": response.input_tokens,
            "output_tokens": response.output_tokens,
            "cost": cost,
            "use_case": use_case,
            "conversation_id": conversation_id,
        })
        db.commit()
    except Exception as e:
        logger.warning(f"Failed to log token usage: {e}")
        db.rollback()


def log_stream_usage(
    db: Session,
    user_id: int,
    provider_type: ProviderType,
    model: str,
    input_tokens: int,
    output_tokens: int,
    use_case: str = "rag",
    conversation_id: int = None,
) -> None:
    """Log token usage from streaming (where we accumulate tokens)."""
    if provider_type == ProviderType.OLLAMA:
        return

    cost = estimate_cost(model, input_tokens, output_tokens)

    try:
        db.execute(text("""
            INSERT INTO ai_usage_logs
                (user_id, provider, model, input_tokens, output_tokens,
                 estimated_cost_usd, use_case, conversation_id)
            VALUES
                (:user_id, :provider, :model, :input_tokens, :output_tokens,
                 :cost, :use_case, :conversation_id)
        """), {
            "user_id": user_id,
            "provider": provider_type.value,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost": cost,
            "use_case": use_case,
            "conversation_id": conversation_id,
        })
        db.commit()
    except Exception as e:
        logger.warning(f"Failed to log stream usage: {e}")
        db.rollback()


def get_usage_summary(db: Session, user_id: int, days: int = 30) -> dict:
    """Get usage summary for a user over the last N days."""
    since = datetime.now(timezone.utc) - timedelta(days=days)

    try:
        result = db.execute(text("""
            SELECT
                COALESCE(SUM(input_tokens), 0) as total_input,
                COALESCE(SUM(output_tokens), 0) as total_output,
                COALESCE(SUM(estimated_cost_usd), 0) as total_cost,
                COUNT(*) as total_requests
            FROM ai_usage_logs
            WHERE user_id = :user_id AND created_at >= :since
        """), {"user_id": user_id, "since": since})

        row = result.fetchone()
        return {
            "total_input_tokens": int(row[0]),
            "total_output_tokens": int(row[1]),
            "total_cost_usd": float(row[2]),
            "total_requests": int(row[3]),
            "period_days": days,
        }
    except Exception as e:
        logger.warning(f"Failed to get usage summary: {e}")
        return {
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_cost_usd": 0.0,
            "total_requests": 0,
            "period_days": days,
        }


def get_daily_usage(db: Session, user_id: int, days: int = 30) -> list:
    """Get daily usage breakdown for charts."""
    since = datetime.now(timezone.utc) - timedelta(days=days)

    try:
        result = db.execute(text("""
            SELECT
                DATE(created_at) as day,
                provider,
                SUM(input_tokens) as input_tokens,
                SUM(output_tokens) as output_tokens,
                SUM(estimated_cost_usd) as cost,
                COUNT(*) as requests
            FROM ai_usage_logs
            WHERE user_id = :user_id AND created_at >= :since
            GROUP BY DATE(created_at), provider
            ORDER BY day DESC
        """), {"user_id": user_id, "since": since})

        return [
            {
                "date": str(row[0]),
                "provider": row[1],
                "input_tokens": int(row[2]),
                "output_tokens": int(row[3]),
                "cost_usd": float(row[4]),
                "requests": int(row[5]),
            }
            for row in result.fetchall()
        ]
    except Exception as e:
        logger.warning(f"Failed to get daily usage: {e}")
        return []
