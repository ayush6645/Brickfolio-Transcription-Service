"""
Base interfaces for transcription providers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List


@dataclass(frozen=True)
class ProviderResponse:
    provider: str
    model: str
    turns: List[Dict[str, Any]]
    raw_text: str
    raw_payload: Dict[str, Any]
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    latency_ms: int = 0


class BaseTranscriptionProvider(ABC):
    name: str

    @abstractmethod
    def is_available(self) -> bool:
        """Return True when the provider is configured and ready to use."""

    @abstractmethod
    def transcribe(self, input_file_path: Path, *, prompt: str, audio_duration_sec: float) -> ProviderResponse:
        """Transcribe an audio file into normalized turn data."""
