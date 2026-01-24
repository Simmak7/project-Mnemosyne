"""Adapter Storage Service - Manages LoRA adapter files on disk.

Handles:
- Adapter directory creation and structure
- Saving/loading adapter weights
- Active adapter symlink management
- Cleanup of old adapters
"""

import os
import json
import shutil
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# Base directory for adapters
ADAPTERS_BASE_DIR = os.getenv("ADAPTERS_DIR", "/data/adapters")


class AdapterStorage:
    """Manages LoRA adapter file storage."""

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.user_dir = Path(ADAPTERS_BASE_DIR) / str(user_id)

    def ensure_user_dir(self) -> Path:
        """Create user adapter directory if it doesn't exist."""
        self.user_dir.mkdir(parents=True, exist_ok=True)
        return self.user_dir

    def get_adapter_path(self, version: int) -> Path:
        """Get path for a specific adapter version."""
        return self.user_dir / f"brain_v{version}"

    def create_adapter_dir(self, version: int) -> Path:
        """Create directory for a new adapter version."""
        self.ensure_user_dir()
        adapter_dir = self.get_adapter_path(version)
        adapter_dir.mkdir(parents=True, exist_ok=True)
        return adapter_dir

    def save_metadata(
        self,
        version: int,
        metadata: Dict[str, Any]
    ) -> Path:
        """Save adapter metadata to JSON file."""
        adapter_dir = self.get_adapter_path(version)
        metadata_path = adapter_dir / "metadata.json"

        # Add timestamp if not present
        if "created_at" not in metadata:
            metadata["created_at"] = datetime.utcnow().isoformat()

        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Saved adapter metadata: {metadata_path}")
        return metadata_path

    def load_metadata(self, version: int) -> Optional[Dict[str, Any]]:
        """Load adapter metadata from JSON file."""
        metadata_path = self.get_adapter_path(version) / "metadata.json"

        if not metadata_path.exists():
            return None

        with open(metadata_path, "r") as f:
            return json.load(f)

    def set_active_adapter(self, version: int) -> bool:
        """Set the active adapter via symlink."""
        self.ensure_user_dir()
        active_link = self.user_dir / "active"
        adapter_dir = self.get_adapter_path(version)

        if not adapter_dir.exists():
            logger.error(f"Adapter directory not found: {adapter_dir}")
            return False

        # Remove existing symlink if present
        if active_link.exists() or active_link.is_symlink():
            active_link.unlink()

        # Create new symlink
        active_link.symlink_to(adapter_dir.name)
        logger.info(f"Set active adapter to v{version}")
        return True

    def get_active_adapter_path(self) -> Optional[Path]:
        """Get path to the currently active adapter."""
        active_link = self.user_dir / "active"

        if not active_link.exists():
            return None

        # Resolve symlink
        return active_link.resolve()

    def get_active_version(self) -> Optional[int]:
        """Get the version number of the active adapter."""
        active_path = self.get_active_adapter_path()

        if not active_path:
            return None

        # Extract version from directory name (brain_v{N})
        name = active_path.name
        if name.startswith("brain_v"):
            try:
                return int(name[7:])
            except ValueError:
                return None
        return None

    def adapter_exists(self, version: int) -> bool:
        """Check if an adapter version exists on disk."""
        adapter_dir = self.get_adapter_path(version)
        return adapter_dir.exists()

    def delete_adapter(self, version: int) -> bool:
        """Delete an adapter version from disk."""
        adapter_dir = self.get_adapter_path(version)

        if not adapter_dir.exists():
            return False

        # Check if this is the active adapter
        active_version = self.get_active_version()
        if active_version == version:
            logger.warning(f"Cannot delete active adapter v{version}")
            return False

        # Remove directory
        shutil.rmtree(adapter_dir)
        logger.info(f"Deleted adapter v{version}")
        return True

    def list_adapter_versions(self) -> list:
        """List all adapter versions on disk."""
        if not self.user_dir.exists():
            return []

        versions = []
        for item in self.user_dir.iterdir():
            if item.is_dir() and item.name.startswith("brain_v"):
                try:
                    version = int(item.name[7:])
                    versions.append(version)
                except ValueError:
                    continue

        return sorted(versions, reverse=True)

    def get_disk_usage(self) -> Dict[str, int]:
        """Get disk usage statistics for user's adapters."""
        if not self.user_dir.exists():
            return {"total_bytes": 0, "total_mb": 0.0, "adapter_count": 0}

        total_bytes = 0
        adapter_count = 0

        for item in self.user_dir.iterdir():
            if item.is_dir() and item.name.startswith("brain_v"):
                adapter_count += 1
                for file in item.rglob("*"):
                    if file.is_file():
                        total_bytes += file.stat().st_size

        return {
            "total_bytes": total_bytes,
            "total_mb": round(total_bytes / (1024 * 1024), 2),
            "adapter_count": adapter_count
        }

    def cleanup_old_adapters(self, keep_count: int = 5) -> int:
        """Remove old adapters, keeping the most recent N versions."""
        versions = self.list_adapter_versions()

        if len(versions) <= keep_count:
            return 0

        active_version = self.get_active_version()
        deleted = 0

        for version in versions[keep_count:]:
            if version != active_version:
                if self.delete_adapter(version):
                    deleted += 1

        return deleted
