"""
Stage 04: Provider-backed transcription with validation and fallback.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from ..infrastructure.config import settings as config
from ..infrastructure.utils.logger import get_logger
from ..infrastructure.utils.pipeline_telemetry import record_ai_validation
from .providers import DeepgramProvider, GeminiProvider
from .providers.base import BaseTranscriptionProvider, ProviderResponse

logger = get_logger("audio_transcriber")


class TranscriptValidationError(RuntimeError):
    """Raised when a provider transcript cannot be normalized into usable turns."""


@dataclass(frozen=True)
class TranscriptionArtifact:
    transcript_path: Path
    text_path: Path
    provider: str
    model: str
    turns: List[Dict[str, Any]]
    validation: Dict[str, Any]
    fallback_used: bool
    raw_payload: Dict[str, Any]
    attempts_used: int
    latency_ms: int = 0
    tokens_in: int = 0
    tokens_out: int = 0


def _provider_registry() -> Dict[str, BaseTranscriptionProvider]:
    return {
        "gemini": GeminiProvider(),
        "deepgram": DeepgramProvider(),
    }


def _provider_sequence() -> List[BaseTranscriptionProvider]:
    registry = _provider_registry()
    sequence: List[BaseTranscriptionProvider] = []
    primary = registry.get(config.PRIMARY_TRANSCRIPTION_PROVIDER)
    if primary:
        sequence.append(primary)
    if config.ENABLE_PROVIDER_FALLBACK:
        fallback = registry.get(config.FALLBACK_TRANSCRIPTION_PROVIDER)
        if fallback and fallback.name != getattr(primary, "name", None):
            sequence.append(fallback)
    return sequence


def normalize_turns(raw_turns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized: List[Dict[str, Any]] = []
    for index, turn in enumerate(raw_turns or []):
        text = str(turn.get("text", "")).strip()
        if not text:
            continue
        start = turn.get("start", turn.get("start_ms", 0) / 1000.0)
        end = turn.get("end", turn.get("end_ms", 0) / 1000.0)
        speaker = str(turn.get("speaker") or f"Speaker {index % 2}")
        normalized.append(
            {
                "speaker": speaker,
                "start": round(float(start), 3),
                "end": round(float(end), 3),
                "text": text,
            }
        )
    normalized.sort(key=lambda turn: (turn["start"], turn["end"]))
    return normalized


def validate_turns(turns: List[Dict[str, Any]], *, duration_hint_sec: float) -> Dict[str, Any]:
    issues: List[str] = []
    empty_segments = 0
    total_chars = 0
    previous_start = -1.0

    if not turns:
        issues.append("no_turns")

    for turn in turns:
        text = str(turn.get("text", "")).strip()
        if not text:
            empty_segments += 1
            continue
        total_chars += len(text)
        start = float(turn.get("start", 0.0))
        end = float(turn.get("end", 0.0))
        if start < 0 or end <= start:
            issues.append("invalid_timestamp_range")
        if previous_start > start + 0.001:
            issues.append("non_monotonic_start_times")
        previous_start = max(previous_start, start)

    if empty_segments:
        issues.append("empty_segments")

    if turns and duration_hint_sec > 0:
        if turns[-1]["end"] > duration_hint_sec + max(config.OVERLAP_SEC, 2):
            issues.append("timestamp_exceeds_chunk_duration")

    if duration_hint_sec >= 30 and total_chars < 10:
        issues.append("suspiciously_short_transcript")

    deduped_issues = sorted(set(issues))
    return {
        "is_valid": not deduped_issues,
        "issues": deduped_issues,
        "total_turns": len(turns),
        "empty_segments_count": empty_segments,
        "total_chars": total_chars,
        "duration_hint_sec": round(duration_hint_sec, 3),
    }


def _write_artifacts(
    *,
    output_dir: Path,
    chunk_name: str,
    response: ProviderResponse,
    turns: List[Dict[str, Any]],
    validation: Dict[str, Any],
    attempts_used: int,
) -> TranscriptionArtifact:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"{chunk_name}_transcript.json"
    txt_path = output_dir / f"{chunk_name}_transcript.txt"
    validation = {**validation, "attempts_used": attempts_used}

    full_text = "\n".join(f"{turn['speaker']}: {turn['text']}" for turn in turns)
    payload = {
        "source": f"{response.provider} ({response.model})",
        "full_text": full_text,
        "structured_turns": turns,
        "segment_summary": response.raw_payload.get("segment_summary", ""),
        "metadata": {
            "provider": response.provider,
            "model": response.model,
            "timestamp": time.time(),
            "validation": validation,
        },
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    txt_path.write_text(full_text, encoding="utf-8")
    return TranscriptionArtifact(
        transcript_path=json_path,
        text_path=txt_path,
        provider=response.provider,
        model=response.model,
        turns=turns,
        validation=validation,
        fallback_used=response.provider != config.PRIMARY_TRANSCRIPTION_PROVIDER,
        raw_payload=response.raw_payload,
        attempts_used=attempts_used,
        latency_ms=response.latency_ms,
        tokens_in=response.tokens_in,
        tokens_out=response.tokens_out,
    )


def transcribe_chunk(
    input_file_path: Path,
    output_dir: Path,
    *,
    chunk_name: str,
    duration_sec: float,
    file_id: str | None = None,
) -> TranscriptionArtifact:
    input_file_path = Path(input_file_path)
    last_error = "No provider attempted."
    providers = _provider_sequence()
    if not providers:
        raise RuntimeError("No transcription providers are configured.")

    attempts_used = 0
    for provider in providers:
        if not provider.is_available():
            continue
        for attempt in range(config.MAX_TRANSCRIPTION_VALIDATION_RETRIES):
            attempts_used += 1
            try:
                response = provider.transcribe(
                    input_file_path,
                    prompt=config.STRUCTURED_TRANSCRIPTION_PROMPT,
                    audio_duration_sec=duration_sec,
                )
                turns = normalize_turns(response.turns)
                validation = validate_turns(turns, duration_hint_sec=duration_sec)
                record_ai_validation(
                    {
                        "file_id": file_id,
                        "chunk_name": chunk_name,
                        "provider": provider.name,
                        "model": response.model,
                        "attempt": attempts_used,
                        "json_validity": validation["is_valid"],
                        "issues": validation["issues"],
                        "total_turns_captured": validation["total_turns"],
                        "empty_segments_count": validation["empty_segments_count"],
                    }
                )
                if not validation["is_valid"]:
                    last_error = f"{provider.name} validation failed: {', '.join(validation['issues'])}"
                    logger.warning(last_error)
                    continue
                return _write_artifacts(
                    output_dir=output_dir,
                    chunk_name=chunk_name,
                    response=response,
                    turns=turns,
                    validation=validation,
                    attempts_used=attempts_used,
                )
            except Exception as exc:
                last_error = f"{provider.name} transcription failed: {exc}"
                logger.warning(last_error)
                record_ai_validation(
                    {
                        "file_id": file_id,
                        "chunk_name": chunk_name,
                        "provider": provider.name,
                        "model": getattr(provider, "name", provider.name),
                        "attempt": attempts_used,
                        "json_validity": False,
                        "issues": ["provider_error"],
                        "error": str(exc),
                        "total_turns_captured": 0,
                        "empty_segments_count": 0,
                    }
                )
                continue

    raise TranscriptValidationError(last_error)


def transcribe_full_audio(input_clean_file_path: Path, output_dir: Path) -> Path:
    """
    Compatibility wrapper for older single-file call sites.
    """
    artifact = transcribe_chunk(
        input_clean_file_path,
        output_dir,
        chunk_name="chunk_000",
        duration_sec=0.0,
    )
    return artifact.transcript_path
