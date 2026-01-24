"""Inference Service - Generate responses using trained LoRA adapters.

Handles:
- Loading trained adapters
- Generating personalized responses
- Adapter switching
"""

import os
import logging
from typing import Optional, Dict, Any
from pathlib import Path

from sqlalchemy.orm import Session

from ..models import BrainAdapter
from .storage import AdapterStorage

logger = logging.getLogger(__name__)

# Cache for loaded models
_model_cache: Dict[str, Any] = {}


class BrainInference:
    """Generate responses using trained LoRA adapters."""

    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id
        self.storage = AdapterStorage(user_id)
        self._model = None
        self._tokenizer = None
        self._loaded_version = None

    def get_active_adapter(self) -> Optional[BrainAdapter]:
        """Get the currently active adapter for this user."""
        return (
            self.db.query(BrainAdapter)
            .filter(
                BrainAdapter.owner_id == self.user_id,
                BrainAdapter.is_active == True
            )
            .first()
        )

    def _get_cache_key(self, adapter_path: str) -> str:
        """Generate cache key for model."""
        return f"user_{self.user_id}_{adapter_path}"

    def load_adapter(self, adapter: BrainAdapter) -> bool:
        """Load a trained adapter into memory.

        Args:
            adapter: BrainAdapter record with adapter_path

        Returns:
            True if loaded successfully
        """
        if not adapter.adapter_path:
            logger.error(f"No adapter path for v{adapter.version}")
            return False

        adapter_path = Path(adapter.adapter_path)
        if not adapter_path.exists():
            logger.error(f"Adapter path not found: {adapter_path}")
            return False

        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
            from peft import PeftModel

            cache_key = self._get_cache_key(str(adapter_path))

            # Check cache
            if cache_key in _model_cache:
                cached = _model_cache[cache_key]
                self._model = cached["model"]
                self._tokenizer = cached["tokenizer"]
                self._loaded_version = adapter.version
                logger.info(f"Loaded adapter v{adapter.version} from cache")
                return True

            logger.info(f"Loading adapter from: {adapter_path}")

            # Load tokenizer
            self._tokenizer = AutoTokenizer.from_pretrained(
                str(adapter_path),
                trust_remote_code=True
            )

            # Load base model
            base_model = AutoModelForCausalLM.from_pretrained(
                adapter.base_model,
                device_map="auto",
                torch_dtype=torch.float16,
                trust_remote_code=True
            )

            # Load LoRA adapter
            self._model = PeftModel.from_pretrained(
                base_model,
                str(adapter_path)
            )
            self._model.eval()

            self._loaded_version = adapter.version

            # Cache the loaded model
            _model_cache[cache_key] = {
                "model": self._model,
                "tokenizer": self._tokenizer
            }

            logger.info(f"Successfully loaded adapter v{adapter.version}")
            return True

        except Exception as e:
            logger.error(f"Failed to load adapter: {e}")
            return False

    def generate(
        self,
        prompt: str,
        max_length: int = 256,
        temperature: float = 0.7,
        top_p: float = 0.9,
        do_sample: bool = True
    ) -> Optional[str]:
        """Generate a response using the loaded adapter.

        Args:
            prompt: Input prompt
            max_length: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Top-p (nucleus) sampling
            do_sample: Whether to use sampling

        Returns:
            Generated text or None if failed
        """
        if not self._model or not self._tokenizer:
            # Try to load active adapter
            adapter = self.get_active_adapter()
            if not adapter:
                logger.warning("No active adapter found")
                return None

            if not self.load_adapter(adapter):
                return None

        try:
            import torch

            # Tokenize
            inputs = self._tokenizer(
                prompt,
                return_tensors="pt",
                truncation=True,
                max_length=512
            )

            # Move to device
            device = next(self._model.parameters()).device
            inputs = {k: v.to(device) for k, v in inputs.items()}

            # Generate
            with torch.no_grad():
                outputs = self._model.generate(
                    **inputs,
                    max_new_tokens=max_length,
                    temperature=temperature if do_sample else 1.0,
                    top_p=top_p if do_sample else 1.0,
                    do_sample=do_sample,
                    pad_token_id=self._tokenizer.pad_token_id,
                    eos_token_id=self._tokenizer.eos_token_id
                )

            # Decode
            generated_text = self._tokenizer.decode(
                outputs[0][inputs["input_ids"].shape[1]:],
                skip_special_tokens=True
            )

            return generated_text.strip()

        except Exception as e:
            logger.error(f"Generation failed: {e}")
            return None

    def chat(
        self,
        messages: list,
        max_length: int = 256,
        temperature: float = 0.7
    ) -> Optional[str]:
        """Generate a chat response.

        Args:
            messages: List of {"role": str, "content": str} messages
            max_length: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            Assistant response or None if failed
        """
        if not self._model or not self._tokenizer:
            adapter = self.get_active_adapter()
            if not adapter:
                return None
            if not self.load_adapter(adapter):
                return None

        # Format messages as prompt
        prompt = self._format_chat_prompt(messages)

        return self.generate(
            prompt,
            max_length=max_length,
            temperature=temperature
        )

    def _format_chat_prompt(self, messages: list) -> str:
        """Format chat messages as a prompt."""
        # Try to use tokenizer's chat template if available
        if hasattr(self._tokenizer, "apply_chat_template"):
            try:
                return self._tokenizer.apply_chat_template(
                    messages,
                    tokenize=False,
                    add_generation_prompt=True
                )
            except Exception:
                pass

        # Fallback: simple format
        prompt_parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")

        prompt_parts.append("Assistant:")
        return "\n\n".join(prompt_parts)

    def unload(self):
        """Unload the current model from memory."""
        self._model = None
        self._tokenizer = None
        self._loaded_version = None

    @property
    def is_loaded(self) -> bool:
        """Check if a model is currently loaded."""
        return self._model is not None

    @property
    def loaded_version(self) -> Optional[int]:
        """Get the currently loaded adapter version."""
        return self._loaded_version


def clear_model_cache():
    """Clear the global model cache."""
    global _model_cache
    _model_cache.clear()
    logger.info("Cleared model cache")
