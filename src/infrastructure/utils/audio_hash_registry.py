"""
Content-hash registry for deduplication and resumable processing.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import portalocker

from ..config import settings as config


@dataclass(frozen=True)
class HashRegistryResult:
    file_hash: str
    should_process: bool
    status: str
    final_output_path: str | None = None


class AudioHashRegistry:
    """
    Tracks whether a file hash is pending, in progress, failed, or completed.
    """

    def __init__(self) -> None:
        config.METADATA_DIR.mkdir(parents=True, exist_ok=True)
        self.registry_file = config.HASH_REGISTRY_FILE

    def _update_locked(self, mutator):
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)
        with portalocker.Lock(self.registry_file, mode="a+", timeout=10, encoding="utf-8") as handle:
            handle.seek(0)
            content = handle.read()
            data = json.loads(content) if content.strip() else {}
            result = mutator(data)
            handle.seek(0)
            handle.truncate()
            json.dump(data, handle, indent=2, ensure_ascii=False)
            handle.flush()
            return result

    def _read_locked(self) -> Dict[str, Dict[str, Any]]:
        if not self.registry_file.exists():
            return {}
        with portalocker.Lock(self.registry_file, mode="r", timeout=10, encoding="utf-8") as handle:
            content = handle.read()
            return json.loads(content) if content.strip() else {}

    def compute_file_hash(self, file_path: Path) -> str:
        hasher = hashlib.sha256()
        with Path(file_path).open("rb") as handle:
            while chunk := handle.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()

    def get_entry(self, file_hash: str) -> Dict[str, Any]:
        return self._read_locked().get(file_hash, {})

    def prepare_processing(self, file_hash: str, file_path: Path, file_id: str) -> HashRegistryResult:
        file_path = Path(file_path)
        now = datetime.now(timezone.utc).isoformat()

        def mutate(data: Dict[str, Dict[str, Any]]) -> HashRegistryResult:
            entry = data.get(file_hash, {})
            status = entry.get("status")
            final_output_path = entry.get("final_output_path")

            if status == "completed" and final_output_path:
                return HashRegistryResult(
                    file_hash=file_hash,
                    should_process=False,
                    status=status,
                    final_output_path=final_output_path,
                )

            data[file_hash] = {
                "file_hash": file_hash,
                "file_id": file_id,
                "filename": file_path.name,
                "source_path": str(file_path),
                "status": "in_progress",
                "final_output_path": final_output_path,
                "last_error": entry.get("last_error"),
                "updated_at": now,
            }
            return HashRegistryResult(
                file_hash=file_hash,
                should_process=True,
                status=status or "new",
                final_output_path=final_output_path,
            )

        return self._update_locked(mutate)

    def mark_completed(self, file_hash: str, file_id: str, final_output_path: Path) -> None:
        now = datetime.now(timezone.utc).isoformat()

        def mutate(data: Dict[str, Dict[str, Any]]) -> None:
            entry = data.setdefault(file_hash, {"file_hash": file_hash})
            entry.update(
                {
                    "file_id": file_id,
                    "status": "completed",
                    "final_output_path": str(final_output_path),
                    "last_error": None,
                    "updated_at": now,
                }
            )

        self._update_locked(mutate)

    def mark_failed(self, file_hash: str, file_id: str, error_msg: str) -> None:
        now = datetime.now(timezone.utc).isoformat()

        def mutate(data: Dict[str, Dict[str, Any]]) -> None:
            entry = data.setdefault(file_hash, {"file_hash": file_hash})
            entry.update(
                {
                    "file_id": file_id,
                    "status": "failed",
                    "last_error": error_msg,
                    "updated_at": now,
                }
            )

        self._update_locked(mutate)

    def check_and_register(self, file_path: Path) -> bool:
        """
        Compatibility wrapper used by older code paths.
        """
        file_path = Path(file_path)
        file_hash = self.compute_file_hash(file_path)
        result = self.prepare_processing(file_hash, file_path, file_id=file_path.stem)
        return not result.should_process


registry = AudioHashRegistry()
