"""
Circuit Breaker for LLM providers.

Prevents cascading failures when a provider (e.g. Ollama) is down
by fast-failing requests instead of letting each one time out.

States:
  CLOSED  - Normal operation, requests pass through
  OPEN    - Provider is down, requests fast-fail immediately
  HALF_OPEN - Recovery probe: one request allowed through to test
"""

import logging
import threading
import time
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)

DEFAULT_FAILURE_THRESHOLD: int = 3
DEFAULT_RECOVERY_TIMEOUT: float = 30.0


class CircuitState(str, Enum):
    """Possible states of the circuit breaker."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreakerOpen(Exception):
    """Raised when the circuit breaker is open and fast-failing."""

    def __init__(self, provider: str, retry_after: float):
        self.provider = provider
        self.retry_after = retry_after
        super().__init__(
            f"{provider} circuit breaker is OPEN. "
            f"Retry after {retry_after:.0f}s."
        )


class CircuitBreaker:
    """
    Thread-safe circuit breaker with three states.

    Args:
        name: Human-readable name (e.g. "ollama")
        failure_threshold: Consecutive failures before opening
        recovery_timeout: Seconds to wait before half-open probe
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = DEFAULT_FAILURE_THRESHOLD,
        recovery_timeout: float = DEFAULT_RECOVERY_TIMEOUT,
    ) -> None:
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout

        self._state: CircuitState = CircuitState.CLOSED
        self._failure_count: int = 0
        self._last_failure_time: Optional[float] = None
        self._lock = threading.Lock()

    @property
    def state(self) -> CircuitState:
        """Current circuit state, with automatic OPEN -> HALF_OPEN transition."""
        with self._lock:
            if self._state == CircuitState.OPEN:
                elapsed = time.monotonic() - (self._last_failure_time or 0)
                if elapsed >= self.recovery_timeout:
                    self._state = CircuitState.HALF_OPEN
                    logger.info(
                        f"Circuit breaker '{self.name}' -> HALF_OPEN "
                        f"(recovery timeout elapsed)"
                    )
            return self._state

    @property
    def failure_count(self) -> int:
        """Number of consecutive failures."""
        return self._failure_count

    def pre_request(self) -> None:
        """
        Call before making a request.

        Raises CircuitBreakerOpen if the circuit is open and the
        recovery timeout has not yet elapsed.
        """
        current = self.state  # triggers OPEN->HALF_OPEN check
        if current == CircuitState.OPEN:
            retry_after = self.recovery_timeout - (
                time.monotonic() - (self._last_failure_time or 0)
            )
            raise CircuitBreakerOpen(self.name, max(retry_after, 0))
        # CLOSED or HALF_OPEN: allow the request through

    def record_success(self) -> None:
        """Record a successful request; reset to CLOSED."""
        with self._lock:
            prev = self._state
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._last_failure_time = None
            if prev != CircuitState.CLOSED:
                logger.info(
                    f"Circuit breaker '{self.name}' -> CLOSED "
                    f"(success after {prev.value})"
                )

    def record_failure(self) -> None:
        """Record a failed request; may transition to OPEN."""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.monotonic()

            if self._state == CircuitState.HALF_OPEN:
                # Probe failed, go back to OPEN
                self._state = CircuitState.OPEN
                logger.warning(
                    f"Circuit breaker '{self.name}' -> OPEN "
                    f"(half-open probe failed)"
                )
            elif self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN
                logger.warning(
                    f"Circuit breaker '{self.name}' -> OPEN "
                    f"(failures={self._failure_count})"
                )

    def get_status(self) -> dict:
        """Return circuit breaker status for health endpoint."""
        current = self.state
        return {
            "state": current.value,
            "failure_count": self._failure_count,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout_s": self.recovery_timeout,
        }

    def reset(self) -> None:
        """Manually reset the circuit breaker to CLOSED."""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._last_failure_time = None
            logger.info(f"Circuit breaker '{self.name}' manually reset")
