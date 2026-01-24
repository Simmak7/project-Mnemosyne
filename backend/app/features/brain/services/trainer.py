"""LoRA Training Service - Full PEFT-based implementation.

Handles:
- Model loading with 4-bit quantization
- LoRA adapter configuration
- Training loop with progress tracking
- Adapter saving and versioning
"""

import os
import logging
import time
from typing import Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy.orm import Session

from ..models import BrainAdapter, TrainingSample
from .storage import AdapterStorage
from .dataset import DatasetPreparator

logger = logging.getLogger(__name__)

# Default model for training (can be overridden)
DEFAULT_BASE_MODEL = os.getenv("LORA_BASE_MODEL", "TinyLlama/TinyLlama-1.1B-Chat-v1.0")


@dataclass
class TrainingConfig:
    """LoRA training hyperparameters."""
    base_model: str = DEFAULT_BASE_MODEL
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    epochs: int = 3
    learning_rate: float = 2e-4
    batch_size: int = 4
    max_seq_length: int = 512
    gradient_accumulation_steps: int = 4
    warmup_ratio: float = 0.03
    use_4bit: bool = True
    target_modules: List[str] = field(default_factory=lambda: [
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj"
    ])


@dataclass
class TrainingResult:
    """Result of a training run."""
    adapter_id: int
    version: int
    status: str
    samples_trained: int
    training_time_seconds: int
    adapter_path: Optional[str] = None
    error_message: Optional[str] = None


class LoRATrainer:
    """Handles LoRA fine-tuning of base models."""

    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id
        self.storage = AdapterStorage(user_id)
        self.dataset_prep = DatasetPreparator(db, user_id)

    def get_next_version(self) -> int:
        """Get the next adapter version number."""
        latest = (
            self.db.query(BrainAdapter)
            .filter(BrainAdapter.owner_id == self.user_id)
            .order_by(BrainAdapter.version.desc())
            .first()
        )
        return (latest.version + 1) if latest else 1

    def create_adapter_record(self, config: TrainingConfig) -> BrainAdapter:
        """Create a new adapter record before training."""
        version = self.get_next_version()

        adapter = BrainAdapter(
            owner_id=self.user_id,
            version=version,
            base_model=config.base_model,
            training_config={
                "lora_r": config.lora_r,
                "lora_alpha": config.lora_alpha,
                "lora_dropout": config.lora_dropout,
                "epochs": config.epochs,
                "learning_rate": config.learning_rate,
                "batch_size": config.batch_size,
                "max_seq_length": config.max_seq_length,
                "use_4bit": config.use_4bit,
            },
            status="created"
        )

        self.db.add(adapter)
        self.db.commit()

        return adapter

    def _load_model_and_tokenizer(self, config: TrainingConfig):
        """Load model with optional 4-bit quantization."""
        try:
            import torch
            from transformers import (
                AutoModelForCausalLM,
                AutoTokenizer,
                BitsAndBytesConfig
            )
        except ImportError as e:
            raise ImportError(f"Missing training dependencies: {e}")

        logger.info(f"Loading model: {config.base_model}")

        # Tokenizer
        tokenizer = AutoTokenizer.from_pretrained(
            config.base_model,
            trust_remote_code=True
        )
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        # Quantization config for 4-bit
        if config.use_4bit:
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
            )
            model = AutoModelForCausalLM.from_pretrained(
                config.base_model,
                quantization_config=bnb_config,
                device_map="auto",
                trust_remote_code=True
            )
        else:
            model = AutoModelForCausalLM.from_pretrained(
                config.base_model,
                device_map="auto",
                torch_dtype=torch.float16,
                trust_remote_code=True
            )

        model.config.use_cache = False

        return model, tokenizer

    def _configure_lora(self, model, config: TrainingConfig):
        """Configure LoRA adapters on model."""
        try:
            from peft import (
                LoraConfig,
                get_peft_model,
                prepare_model_for_kbit_training
            )
        except ImportError:
            raise ImportError("PEFT not installed: pip install peft")

        # Prepare for training if using quantization
        if config.use_4bit:
            model = prepare_model_for_kbit_training(model)

        # LoRA config
        lora_config = LoraConfig(
            r=config.lora_r,
            lora_alpha=config.lora_alpha,
            lora_dropout=config.lora_dropout,
            target_modules=config.target_modules,
            bias="none",
            task_type="CAUSAL_LM"
        )

        model = get_peft_model(model, lora_config)

        trainable_params = sum(
            p.numel() for p in model.parameters() if p.requires_grad
        )
        total_params = sum(p.numel() for p in model.parameters())

        logger.info(
            f"LoRA configured: {trainable_params:,} trainable / "
            f"{total_params:,} total ({100 * trainable_params / total_params:.2f}%)"
        )

        return model

    def _prepare_training_dataset(self, tokenizer, config: TrainingConfig):
        """Prepare dataset for training."""
        samples = self.dataset_prep.get_pending_samples()

        if not samples:
            raise ValueError("No training samples available")

        examples = self.dataset_prep.samples_to_examples(samples)
        dataset = self.dataset_prep.create_huggingface_dataset(
            examples, format_type="alpaca"
        )

        # Tokenize
        def tokenize(example):
            result = tokenizer(
                example["text"],
                truncation=True,
                max_length=config.max_seq_length,
                padding="max_length",
            )
            result["labels"] = result["input_ids"].copy()
            return result

        tokenized = dataset.map(
            tokenize,
            remove_columns=dataset.column_names,
            desc="Tokenizing"
        )

        return tokenized, [s.id for s in samples]

    async def train(
        self,
        config: TrainingConfig,
        adapter: BrainAdapter,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> TrainingResult:
        """Execute LoRA training.

        Args:
            config: Training configuration
            adapter: Adapter record to update
            progress_callback: Optional callback(progress_pct, step_name)

        Returns:
            TrainingResult with training statistics
        """
        start_time = time.time()

        def update_progress(pct: int, step: str):
            if progress_callback:
                progress_callback(pct, step)
            logger.info(f"Training progress: {pct}% - {step}")

        try:
            update_progress(5, "Loading model")

            # Load model
            model, tokenizer = self._load_model_and_tokenizer(config)

            update_progress(20, "Configuring LoRA")

            # Configure LoRA
            model = self._configure_lora(model, config)

            update_progress(30, "Preparing dataset")

            # Prepare dataset
            dataset, sample_ids = self._prepare_training_dataset(
                tokenizer, config
            )

            update_progress(40, "Setting up trainer")

            # Training arguments
            try:
                from transformers import TrainingArguments, Trainer
            except ImportError:
                raise ImportError("transformers not installed")

            # Create adapter directory
            adapter_dir = self.storage.create_adapter_dir(adapter.version)
            output_dir = adapter_dir / "checkpoints"

            training_args = TrainingArguments(
                output_dir=str(output_dir),
                num_train_epochs=config.epochs,
                per_device_train_batch_size=config.batch_size,
                gradient_accumulation_steps=config.gradient_accumulation_steps,
                warmup_ratio=config.warmup_ratio,
                learning_rate=config.learning_rate,
                fp16=True,
                logging_steps=10,
                save_strategy="epoch",
                save_total_limit=2,
                report_to="none",
                optim="paged_adamw_8bit" if config.use_4bit else "adamw_torch",
            )

            trainer = Trainer(
                model=model,
                args=training_args,
                train_dataset=dataset,
            )

            update_progress(50, "Training LoRA")

            # Train
            adapter.status = "training"
            adapter.training_started_at = datetime.utcnow()
            self.db.commit()

            trainer.train()

            update_progress(85, "Saving adapter")

            # Save adapter weights
            adapter_weights_dir = adapter_dir / "adapter"
            model.save_pretrained(str(adapter_weights_dir))
            tokenizer.save_pretrained(str(adapter_weights_dir))

            # Save metadata
            training_time = int(time.time() - start_time)
            self.storage.save_metadata(adapter.version, {
                "version": adapter.version,
                "base_model": config.base_model,
                "parent_version": adapter.version - 1 if adapter.version > 1 else None,
                "dataset_size": len(sample_ids),
                "training_config": {
                    "lora_r": config.lora_r,
                    "lora_alpha": config.lora_alpha,
                    "epochs": config.epochs,
                    "learning_rate": config.learning_rate,
                },
                "training_time_seconds": training_time,
            })

            update_progress(95, "Updating records")

            # Update adapter record
            adapter.status = "ready"
            adapter.adapter_path = str(adapter_weights_dir)
            adapter.dataset_size = len(sample_ids)
            adapter.training_completed_at = datetime.utcnow()
            self.db.commit()

            # Mark samples as trained
            (
                self.db.query(TrainingSample)
                .filter(TrainingSample.id.in_(sample_ids))
                .update(
                    {
                        "is_trained": "trained",
                        "adapter_version": adapter.version
                    },
                    synchronize_session=False
                )
            )
            self.db.commit()

            update_progress(100, "Complete")

            logger.info(
                f"Training complete: v{adapter.version}, "
                f"{len(sample_ids)} samples, {training_time}s"
            )

            return TrainingResult(
                adapter_id=adapter.id,
                version=adapter.version,
                status="ready",
                samples_trained=len(sample_ids),
                training_time_seconds=training_time,
                adapter_path=str(adapter_weights_dir)
            )

        except Exception as e:
            logger.error(f"Training failed: {e}")

            adapter.status = "failed"
            adapter.error_message = str(e)
            self.db.commit()

            return TrainingResult(
                adapter_id=adapter.id,
                version=adapter.version,
                status="failed",
                samples_trained=0,
                training_time_seconds=int(time.time() - start_time),
                error_message=str(e)
            )

    def activate_adapter(self, version: int) -> bool:
        """Set an adapter as the active version."""
        # Deactivate all adapters
        (
            self.db.query(BrainAdapter)
            .filter(BrainAdapter.owner_id == self.user_id)
            .update({"is_active": False})
        )

        # Activate specified version
        adapter = (
            self.db.query(BrainAdapter)
            .filter(
                BrainAdapter.owner_id == self.user_id,
                BrainAdapter.version == version
            )
            .first()
        )

        if adapter and adapter.status == "ready":
            adapter.is_active = True
            self.db.commit()

            # Update filesystem symlink
            self.storage.set_active_adapter(version)

            logger.info(f"Activated adapter v{version}")
            return True

        return False

    def get_active_adapter(self) -> Optional[BrainAdapter]:
        """Get the currently active adapter."""
        return (
            self.db.query(BrainAdapter)
            .filter(
                BrainAdapter.owner_id == self.user_id,
                BrainAdapter.is_active == True
            )
            .first()
        )

    def list_adapters(self) -> List[BrainAdapter]:
        """List all adapters for this user."""
        return (
            self.db.query(BrainAdapter)
            .filter(BrainAdapter.owner_id == self.user_id)
            .order_by(BrainAdapter.version.desc())
            .all()
        )
