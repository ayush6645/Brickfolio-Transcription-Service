"""
Environment validation helpers for directories and input audio files.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import filetype

from ..config import settings as config
from .logger import get_logger

logger = get_logger("environment_validator")


class AudioValidationError(RuntimeError):
    """Raised when an input file cannot be safely processed as audio."""


@dataclass(frozen=True)
class AudioValidationInfo:
    file_path: Path
    duration_sec: float
    sample_rate: int | None
    channels: int | None
    codec_name: str | None
    format_name: str | None
    size_bytes: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": str(self.file_path),
            "duration_sec": round(self.duration_sec, 3),
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "codec_name": self.codec_name,
            "format_name": self.format_name,
            "size_bytes": self.size_bytes,
        }


def init_directories() -> None:
    """Ensure all runtime directories exist before the pipeline runs."""
    directories = [
        config.DATA_DIR,
        config.RAW_AUDIO_DIR,
        config.STANDARDIZED_AUDIO_DIR,
        config.CHUNKS_DIR,
        config.CLEANED_DIR,
        config.TRANSCRIPTS_DIR,
        config.FINAL_DIR,
        config.RESULTS_DIR,
        config.OUTPUT_DIR,
        config.OUTPUT_TRANSCRIPTS_DIR,
        config.OUTPUT_SUMMARIES_DIR,
        config.TEMP_PROCESSING_DIR,
        config.LOGS_DIR,
        config.METADATA_DIR,
        config.BILLING_DIR,
    ]

    for directory in directories:
        try:
            directory.mkdir(parents=True, exist_ok=True)
        except Exception as exc:  # pragma: no cover - fatal environment errors
            logger.error(f"Failed to create critical directory {directory}: {exc}")
            raise RuntimeError(f"System boot failed: required directory {directory} could not be initialized.")


def _run_ffprobe(file_path: Path) -> Dict[str, Any]:
    ffprobe_bin = shutil.which("ffprobe")
    if not ffprobe_bin:
        raise AudioValidationError("ffprobe is not installed or not available on PATH.")

    command = [
        ffprobe_bin,
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_streams",
        "-show_format",
        str(file_path),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        stderr = result.stderr.strip() or "Unknown ffprobe error"
        raise AudioValidationError(f"ffprobe failed for {file_path.name}: {stderr}")

    try:
        return json.loads(result.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise AudioValidationError(f"ffprobe returned unreadable metadata for {file_path.name}: {exc}") from exc


def probe_audio(file_path: Path) -> AudioValidationInfo:
    file_path = Path(file_path)
    stats = file_path.stat()
    probe = _run_ffprobe(file_path)

    audio_stream = next(
        (stream for stream in probe.get("streams", []) if stream.get("codec_type") == "audio"),
        None,
    )
    if not audio_stream:
        raise AudioValidationError(f"{file_path.name} does not contain a readable audio stream.")

    format_data = probe.get("format", {})
    duration_sec = float(format_data.get("duration") or audio_stream.get("duration") or 0.0)
    sample_rate_raw = audio_stream.get("sample_rate")
    channels_raw = audio_stream.get("channels")

    return AudioValidationInfo(
        file_path=file_path,
        duration_sec=duration_sec,
        sample_rate=int(sample_rate_raw) if sample_rate_raw else None,
        channels=int(channels_raw) if channels_raw else None,
        codec_name=audio_stream.get("codec_name"),
        format_name=format_data.get("format_name"),
        size_bytes=stats.st_size,
    )


def get_audio_duration(file_path: Path) -> float:
    """Return the detected duration for an audio file in seconds."""
    return probe_audio(file_path).duration_sec


def validate_audio_or_raise(file_path: Path) -> AudioValidationInfo:
    """
    Perform fail-fast validation for an input audio file.
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise AudioValidationError(f"{file_path} does not exist on disk.")

    if not file_path.is_file():
        raise AudioValidationError(f"{file_path} is not a regular file.")

    size_bytes = file_path.stat().st_size
    if size_bytes < config.MIN_AUDIO_BYTES:
        raise AudioValidationError(
            f"{file_path.name} is too small to be a valid recording ({size_bytes} bytes)."
        )

    if file_path.suffix.lower() not in config.SUPPORTED_AUDIO_EXTENSIONS:
        raise AudioValidationError(f"{file_path.name} has an unsupported audio extension.")

    kind = filetype.guess(file_path)
    if kind is not None and not kind.mime.startswith("audio/"):
        logger.warning(
            "Magic-byte inspection returned non-audio MIME %s for %s; ffprobe validation will decide.",
            kind.mime,
            file_path.name,
        )

    info = probe_audio(file_path)
    if info.duration_sec < config.MIN_AUDIO_DURATION_SEC:
        raise AudioValidationError(
            f"{file_path.name} is shorter than the minimum supported duration ({info.duration_sec:.3f}s)."
        )

    return info


def is_valid_audio(file_path: Path) -> bool:
    """Boolean wrapper for validation checks."""
    try:
        validate_audio_or_raise(file_path)
        return True
    except AudioValidationError as exc:
        logger.error(f"Validation failed for {Path(file_path).name}: {exc}")
        return False
