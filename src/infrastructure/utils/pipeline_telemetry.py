"""
Sidecar telemetry writers for quality, validation, and performance logs.
"""

from __future__ import annotations

import csv
import json
import threading
from pathlib import Path
from typing import Any, Dict

from ..config import settings as config

_quality_lock = threading.Lock()
_validation_lock = threading.Lock()
_performance_lock = threading.Lock()


def record_audio_quality(file_id: str, payload: Dict[str, Any]) -> None:
    config.AUDIO_QUALITY_AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with _quality_lock:
        existing: Dict[str, Any] = {}
        if config.AUDIO_QUALITY_AUDIT_FILE.exists():
            try:
                existing = json.loads(config.AUDIO_QUALITY_AUDIT_FILE.read_text(encoding="utf-8") or "{}")
            except json.JSONDecodeError:
                existing = {}
        existing[file_id] = payload
        config.AUDIO_QUALITY_AUDIT_FILE.write_text(
            json.dumps(existing, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def record_ai_validation(payload: Dict[str, Any]) -> None:
    config.AI_VALIDATION_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(payload, ensure_ascii=False)
    with _validation_lock:
        with config.AI_VALIDATION_LOG_FILE.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")


def record_performance(payload: Dict[str, Any]) -> None:
    config.PERFORMANCE_REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with _performance_lock:
        file_exists = config.PERFORMANCE_REPORT_FILE.exists()
        with config.PERFORMANCE_REPORT_FILE.open("a", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(payload.keys()))
            if not file_exists:
                writer.writeheader()
            writer.writerow(payload)
