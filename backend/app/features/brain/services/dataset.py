"""Dataset Preparation - Convert TrainingSamples to training format.

Prepares training data in instruction-following format compatible with
LoRA fine-tuning pipelines.
"""

import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


@dataclass
class TrainingExample:
    """Single training example in instruction format."""
    instruction: str
    input_text: str
    output: str
    metadata: Dict[str, Any]


class DatasetPreparator:
    """Prepares training datasets from TrainingSample records."""

    # Instruction template for formatting prompts
    ALPACA_TEMPLATE = """Below is an instruction that describes a task. Write a response that appropriately completes the request.

### Instruction:
{instruction}

### Input:
{input}

### Response:
{output}"""

    ALPACA_NO_INPUT_TEMPLATE = """Below is an instruction that describes a task. Write a response that appropriately completes the request.

### Instruction:
{instruction}

### Response:
{output}"""

    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id

    def get_pending_samples(self) -> List[Any]:
        """Get all pending training samples for user."""
        from ..models import TrainingSample

        return (
            self.db.query(TrainingSample)
            .filter(
                TrainingSample.owner_id == self.user_id,
                TrainingSample.is_trained == "pending"
            )
            .order_by(TrainingSample.confidence.desc())
            .all()
        )

    def get_all_samples(self) -> List[Any]:
        """Get all training samples for user."""
        from ..models import TrainingSample

        return (
            self.db.query(TrainingSample)
            .filter(TrainingSample.owner_id == self.user_id)
            .order_by(TrainingSample.confidence.desc())
            .all()
        )

    def samples_to_examples(
        self,
        samples: List[Any],
        include_metadata: bool = True
    ) -> List[TrainingExample]:
        """Convert TrainingSample records to TrainingExample objects."""
        examples = []

        for sample in samples:
            example = TrainingExample(
                instruction=sample.instruction,
                input_text=sample.input_text or "",
                output=sample.output,
                metadata={
                    "id": sample.id,
                    "type": sample.sample_type,
                    "memory_type": str(sample.memory_type),
                    "confidence": sample.confidence,
                } if include_metadata else {}
            )
            examples.append(example)

        return examples

    def format_for_training(
        self,
        examples: List[TrainingExample],
        format_type: str = "alpaca"
    ) -> List[Dict[str, str]]:
        """Format examples for training.

        Args:
            examples: List of TrainingExample objects
            format_type: Format type - "alpaca", "chatml", or "raw"

        Returns:
            List of formatted training dictionaries
        """
        formatted = []

        for example in examples:
            if format_type == "alpaca":
                formatted.append(self._format_alpaca(example))
            elif format_type == "chatml":
                formatted.append(self._format_chatml(example))
            else:  # raw
                formatted.append(self._format_raw(example))

        return formatted

    def _format_alpaca(self, example: TrainingExample) -> Dict[str, str]:
        """Format as Alpaca-style instruction."""
        if example.input_text:
            text = self.ALPACA_TEMPLATE.format(
                instruction=example.instruction,
                input=example.input_text,
                output=example.output
            )
        else:
            text = self.ALPACA_NO_INPUT_TEMPLATE.format(
                instruction=example.instruction,
                output=example.output
            )

        return {"text": text}

    def _format_chatml(self, example: TrainingExample) -> Dict[str, str]:
        """Format as ChatML conversation."""
        messages = []

        # System message for personalization context
        messages.append({
            "role": "system",
            "content": "You are a helpful AI assistant with knowledge about the user's personal context."
        })

        # User message
        user_content = example.instruction
        if example.input_text:
            user_content += f"\n\nContext: {example.input_text}"
        messages.append({"role": "user", "content": user_content})

        # Assistant response
        messages.append({"role": "assistant", "content": example.output})

        return {"messages": messages}

    def _format_raw(self, example: TrainingExample) -> Dict[str, str]:
        """Format as raw instruction-output pair."""
        return {
            "instruction": example.instruction,
            "input": example.input_text,
            "output": example.output
        }

    def export_to_jsonl(
        self,
        examples: List[TrainingExample],
        output_path: Path,
        format_type: str = "alpaca"
    ) -> int:
        """Export training data to JSONL file.

        Args:
            examples: Training examples
            output_path: Path to output JSONL file
            format_type: Format type for training

        Returns:
            Number of examples exported
        """
        formatted = self.format_for_training(examples, format_type)

        with open(output_path, "w") as f:
            for item in formatted:
                f.write(json.dumps(item) + "\n")

        logger.info(f"Exported {len(formatted)} examples to {output_path}")
        return len(formatted)

    def prepare_dataset(
        self,
        output_dir: Path,
        pending_only: bool = True,
        format_type: str = "alpaca"
    ) -> Dict[str, Any]:
        """Prepare complete training dataset.

        Args:
            output_dir: Directory to save dataset files
            pending_only: If True, only use pending samples
            format_type: Format type for training

        Returns:
            Dataset statistics and file paths
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        # Get samples
        if pending_only:
            samples = self.get_pending_samples()
        else:
            samples = self.get_all_samples()

        if not samples:
            return {
                "status": "no_samples",
                "count": 0,
                "files": {}
            }

        # Convert to examples
        examples = self.samples_to_examples(samples)

        # Export to JSONL
        train_path = output_dir / "train.jsonl"
        count = self.export_to_jsonl(examples, train_path, format_type)

        # Calculate statistics
        by_type = {}
        for sample in samples:
            t = sample.sample_type
            by_type[t] = by_type.get(t, 0) + 1

        return {
            "status": "prepared",
            "count": count,
            "sample_ids": [s.id for s in samples],
            "by_type": by_type,
            "files": {
                "train": str(train_path)
            }
        }

    def create_huggingface_dataset(
        self,
        examples: List[TrainingExample],
        format_type: str = "alpaca"
    ):
        """Create HuggingFace Dataset object for training.

        Returns:
            datasets.Dataset object ready for training
        """
        try:
            from datasets import Dataset
        except ImportError:
            logger.error("datasets library not installed")
            raise ImportError("Install datasets: pip install datasets")

        formatted = self.format_for_training(examples, format_type)

        # For alpaca format, we have {"text": "..."} entries
        if format_type == "alpaca":
            dataset = Dataset.from_dict({
                "text": [item["text"] for item in formatted]
            })
        else:
            dataset = Dataset.from_list(formatted)

        logger.info(f"Created HuggingFace dataset with {len(dataset)} examples")
        return dataset
