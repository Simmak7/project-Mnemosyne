"""
Model Router with Feature Flags

Routes image analysis requests to appropriate model (Llama or Qwen) based on feature flags.
Implements Strangler Fig Pattern for gradual migration.
"""

import random
import logging
from typing import Dict, Optional
from enum import Enum

from adapters.llama_vision_adapter import LlamaVisionAdapter
from adapters.qwen_vision_adapter import QwenVisionAdapter
from adapters.generic_vision_adapter import GenericVisionAdapter
from prompts.adaptive_vision_prompt import AdaptiveVisionPrompt, ADAPTIVE_VISION_PROMPT_V1, LEGACY_PROMPT_TEXT
from core import config

logger = logging.getLogger(__name__)


class ModelSelection(Enum):
    """Which model was selected for this request"""
    OLD_MODEL = "old"
    NEW_MODEL = "new"


class PromptSelection(Enum):
    """Which prompt was selected for this request"""
    LEGACY = "legacy"
    HYBRID = "hybrid"
    ADAPTIVE = "adaptive"


class ModelRouter:
    """
    Routes image analysis requests to appropriate model based on feature flags.

    Feature flags (from config/environment):
    - USE_NEW_MODEL: Master switch (true/false)
    - NEW_MODEL_ROLLOUT_PERCENT: Gradual rollout percentage (0-100)
    - PROMPT_ROLLOUT_PERCENT: Prompt rollout percentage (0-100)
    - LOG_MODEL_SELECTION: Log which model/prompt is selected (true/false)

    Behavior:
    - If USE_NEW_MODEL=false: Always use old model (Llama)
    - If USE_NEW_MODEL=true: Use NEW_MODEL_ROLLOUT_PERCENT to decide
    - Example: NEW_MODEL_ROLLOUT_PERCENT=25 means 25% of requests use new model

    Rollout Strategy (Strangler Fig Pattern):
    Phase 3A: NEW_MODEL_ROLLOUT_PERCENT=10 (10% canary)
    Phase 3B: NEW_MODEL_ROLLOUT_PERCENT=25 (expand)
    Phase 3C: NEW_MODEL_ROLLOUT_PERCENT=75 (majority)
    Phase 3D: NEW_MODEL_ROLLOUT_PERCENT=100 (full)
    """

    def __init__(
        self,
        ollama_host: Optional[str] = None,
        use_new_model: Optional[bool] = None,
        new_model_rollout_percent: Optional[int] = None,
        prompt_rollout_percent: Optional[int] = None,
        vision_model: Optional[str] = None,
    ):
        """
        Initialize Model Router.

        Args:
            ollama_host: Ollama server URL (defaults to config.OLLAMA_HOST)
            use_new_model: Master feature flag (defaults to config.USE_NEW_MODEL)
            new_model_rollout_percent: Rollout % (defaults to config.NEW_MODEL_ROLLOUT_PERCENT)
            prompt_rollout_percent: Prompt rollout % (defaults to config.PROMPT_ROLLOUT_PERCENT)
        """
        # Use provided values or fallback to config
        self.ollama_host = ollama_host or config.OLLAMA_HOST
        self.use_new_model = use_new_model if use_new_model is not None else getattr(config, "USE_NEW_MODEL", False)
        self.new_model_rollout_percent = (
            new_model_rollout_percent if new_model_rollout_percent is not None
            else getattr(config, "NEW_MODEL_ROLLOUT_PERCENT", 0)
        )
        self.prompt_rollout_percent = (
            prompt_rollout_percent if prompt_rollout_percent is not None
            else getattr(config, "PROMPT_ROLLOUT_PERCENT", 0)
        )
        self.log_selection = getattr(config, "LOG_MODEL_SELECTION", True)

        # User-selected vision model override (bypasses feature flags)
        self.vision_model_override = vision_model

        # Initialize adapters
        self.llama_adapter = LlamaVisionAdapter(
            ollama_host=self.ollama_host,
            model_name=getattr(config, "OLLAMA_MODEL_OLD", "llama3.2-vision:11b")
        )
        self.qwen_adapter = QwenVisionAdapter(
            ollama_host=self.ollama_host,
            model_name=getattr(config, "OLLAMA_MODEL_NEW", "qwen2.5vl:7b-q4_K_M")
        )

        # Generic adapter for user-selected models
        self.generic_adapter = None
        if vision_model:
            self.generic_adapter = GenericVisionAdapter(
                ollama_host=self.ollama_host,
                model_name=vision_model,
            )

        logger.info(
            f"ModelRouter initialized: "
            f"use_new_model={self.use_new_model}, "
            f"rollout={self.new_model_rollout_percent}%, "
            f"prompt_rollout={self.prompt_rollout_percent}%"
            f"{f', vision_override={vision_model}' if vision_model else ''}"
        )

    def _should_use_new_model(self) -> bool:
        """
        Decide if this request should use the new model based on feature flags.

        Returns:
            True if new model should be used, False for old model
        """
        # If master switch is off, always use old model
        if not self.use_new_model:
            return False

        # If rollout is 0%, always use old model
        if self.new_model_rollout_percent <= 0:
            return False

        # If rollout is 100%, always use new model
        if self.new_model_rollout_percent >= 100:
            return True

        # Gradual rollout: random selection based on percentage
        # Example: if rollout=25, then 25% chance of using new model
        return random.randint(1, 100) <= self.new_model_rollout_percent

    def _get_prompt_version(self) -> str:
        """
        Get configured prompt version from config.

        Returns:
            Prompt version string: 'legacy', 'hybrid', or 'adaptive'
        """
        return getattr(config, "PROMPT_VERSION", "legacy").lower()

    def _should_use_prompt(self, using_new_model: bool) -> bool:
        """
        Decide if this request should use the configured prompt based on rollout percentage.

        Args:
            using_new_model: Whether the new model is being used

        Returns:
            True if configured prompt should be used, False for legacy prompt
        """
        # Legacy prompt for old model (always)
        if not using_new_model:
            return False

        # If prompt rollout is 0%, use legacy prompt even with new model
        if self.prompt_rollout_percent <= 0:
            return False

        # If prompt rollout is 100%, use configured prompt with new model
        if self.prompt_rollout_percent >= 100:
            return True

        # Gradual rollout for configured prompt
        return random.randint(1, 100) <= self.prompt_rollout_percent

    def _get_prompt(self, using_new_model: bool) -> tuple[str, PromptSelection]:
        """
        Get the appropriate prompt based on model, prompt version, and rollout percentage.

        Supports two prompt versions:
        - legacy: Original working prompt (simple and reliable)
        - adaptive: New 50-line observation-focused prompt (recommended)

        Args:
            using_new_model: Whether the new model is being used

        Returns:
            Tuple of (prompt_text, PromptSelection enum)
        """
        # Check if we should use the configured prompt (based on rollout percentage)
        use_configured = self._should_use_prompt(using_new_model)

        if not use_configured:
            # Use legacy prompt (old model or 0% rollout)
            return LEGACY_PROMPT_TEXT, PromptSelection.LEGACY

        # Get configured prompt version
        prompt_version = self._get_prompt_version()

        if prompt_version == "adaptive":
            return ADAPTIVE_VISION_PROMPT_V1, PromptSelection.ADAPTIVE
        else:
            # Default to legacy for safety (hybrid removed - was causing hallucinations)
            return LEGACY_PROMPT_TEXT, PromptSelection.LEGACY

    def analyze_image(
        self,
        image_path: str,
        custom_prompt: Optional[str] = None,
        timeout: int = 300
    ) -> Dict[str, any]:
        """
        Analyze an image using the appropriate model based on feature flags.

        Args:
            image_path: Path to the image file
            custom_prompt: Additional instructions from user (ADDITIVE to system prompt)
            timeout: Request timeout in seconds (default: 300)

        Returns:
            Dictionary with:
            - status: "success" or "error"
            - response: AI-generated analysis text
            - model: Model name used
            - model_selection: "old" or "new"
            - prompt_selection: "legacy" or "hybrid"
            - error: Error message (if status="error")
            - (other model-specific fields)
        """
        # If user selected a specific vision model, use generic adapter directly
        if self.generic_adapter:
            return self._analyze_with_generic(image_path, custom_prompt, timeout)

        # Decide which model to use
        use_new = self._should_use_new_model()
        model_selection = ModelSelection.NEW_MODEL if use_new else ModelSelection.OLD_MODEL

        # ALWAYS get the system prompt first
        base_prompt, prompt_selection = self._get_prompt(use_new)

        # If user provided additional instructions, APPEND them to system prompt
        if custom_prompt and custom_prompt.strip():
            prompt = f"""{base_prompt}

═══════════════════════════════════════════════════════════════════════

ADDITIONAL CONTEXT FROM USER:

{custom_prompt.strip()}

Please incorporate this context into your analysis while following all the instructions above."""
            if self.log_selection:
                logger.info(f"Using system prompt + user additions (additions: {len(custom_prompt)} chars)")
        else:
            prompt = base_prompt
            if self.log_selection:
                logger.info(f"Prompt selection: {prompt_selection.value}")

        # Log selection
        if self.log_selection:
            logger.info(
                f"Model selection: {model_selection.value} "
                f"({self.llama_adapter.model_name if not use_new else self.qwen_adapter.model_name})"
            )

        # Route to appropriate adapter (with fallback)
        result = None
        fell_back = False

        try:
            if use_new:
                result = self.qwen_adapter.analyze_image(
                    image_path=image_path,
                    prompt=prompt,
                    timeout=timeout
                )
                # Check for error result (model crash returns status="error")
                if result.get("status") == "error":
                    raise RuntimeError(result.get("error", "Qwen returned error"))
            else:
                result = self.llama_adapter.analyze_image(
                    image_path=image_path,
                    prompt=prompt,
                    timeout=timeout
                )

        except Exception as primary_error:
            # Fallback: if Qwen failed, retry with Llama
            if use_new:
                logger.warning(
                    f"Primary model (Qwen) failed: {str(primary_error)}. "
                    f"Falling back to Llama."
                )
                try:
                    fallback_prompt = base_prompt
                    if custom_prompt and custom_prompt.strip():
                        fallback_prompt = f"{base_prompt}\n\nADDITIONAL CONTEXT FROM USER:\n{custom_prompt.strip()}"

                    result = self.llama_adapter.analyze_image(
                        image_path=image_path,
                        prompt=fallback_prompt,
                        timeout=timeout
                    )
                    if result.get("status") == "error":
                        raise RuntimeError(result.get("error", "Llama fallback returned error"))
                    fell_back = True
                    model_selection = ModelSelection.OLD_MODEL
                    prompt_selection = PromptSelection.LEGACY
                    logger.info("Fallback to Llama succeeded.")
                except Exception as fallback_error:
                    error_msg = f"Both models failed. Primary: {str(primary_error)}. Fallback: {str(fallback_error)}"
                    logger.error(error_msg)
                    return {
                        "status": "error",
                        "error": error_msg,
                        "model_selection": model_selection.value,
                        "prompt_selection": prompt_selection.value if prompt_selection else "custom"
                    }
            else:
                error_msg = f"Model router error: {str(primary_error)}"
                logger.error(error_msg, exc_info=True)
                return {
                    "status": "error",
                    "error": error_msg,
                    "model_selection": model_selection.value,
                    "prompt_selection": prompt_selection.value if prompt_selection else "custom"
                }

        # Add routing metadata
        result["model_selection"] = model_selection.value
        result["prompt_selection"] = prompt_selection.value if prompt_selection else "custom"
        if fell_back:
            result["fell_back"] = True

        # Extract metadata based on prompt type
        if result.get("status") == "success":
            try:
                if prompt_selection == PromptSelection.ADAPTIVE:
                    metadata = AdaptiveVisionPrompt.extract_metadata(result["response"])
                    result["content_metadata"] = metadata
                    if self.log_selection:
                        logger.info(
                            f"[ADAPTIVE] Content type: {metadata.get('content_type', 'unknown')}, "
                            f"tags: {len(metadata.get('tags', []))}, "
                            f"wikilinks: {len(metadata.get('wikilinks', []))}, "
                            f"confidence: {metadata.get('confidence', 'unknown')}"
                        )
            except Exception as e:
                logger.warning(f"Failed to extract metadata: {str(e)}")

        return result

    def _analyze_with_generic(
        self, image_path: str, custom_prompt: Optional[str], timeout: int,
    ) -> Dict[str, any]:
        """Route analysis through the generic adapter (user-selected model)."""
        base_prompt, prompt_selection = self._get_prompt(True)
        if custom_prompt and custom_prompt.strip():
            prompt = f"{base_prompt}\n\nADDITIONAL CONTEXT FROM USER:\n{custom_prompt.strip()}"
        else:
            prompt = base_prompt

        logger.info(f"Using user-selected vision model: {self.generic_adapter.model_name}")
        result = self.generic_adapter.analyze_image(image_path, prompt, timeout)

        result["model_selection"] = "user_override"
        result["prompt_selection"] = prompt_selection.value

        if result.get("status") == "success" and prompt_selection == PromptSelection.ADAPTIVE:
            try:
                metadata = AdaptiveVisionPrompt.extract_metadata(result["response"])
                result["content_metadata"] = metadata
            except Exception as e:
                logger.warning(f"Failed to extract metadata: {e}")

        return result

    def health_check(self) -> Dict[str, bool]:
        """
        Check health of both model adapters.

        Returns:
            Dictionary with:
            - old_model: True if Llama model is healthy
            - new_model: True if Qwen model is healthy
            - router: True if router is configured correctly
        """
        old_model_healthy = self.llama_adapter.health_check()
        new_model_healthy = self.qwen_adapter.health_check()

        # Router is healthy if at least one model is available
        router_healthy = old_model_healthy or (self.use_new_model and new_model_healthy)

        health = {
            "old_model": old_model_healthy,
            "new_model": new_model_healthy,
            "router": router_healthy,
            "config": {
                "use_new_model": self.use_new_model,
                "new_model_rollout_percent": self.new_model_rollout_percent,
                "prompt_rollout_percent": self.prompt_rollout_percent
            }
        }

        logger.info(f"Health check: {health}")
        return health

    def __repr__(self):
        return (
            f"ModelRouter("
            f"use_new={self.use_new_model}, "
            f"rollout={self.new_model_rollout_percent}%, "
            f"prompt_rollout={self.prompt_rollout_percent}%"
            f")"
        )
