from __future__ import annotations

import io
import math
import struct
import wave
from contextlib import contextmanager
from pathlib import Path
import shutil
import uuid
from unittest.mock import patch

from src.infrastructure.config import settings as config


def make_wav_bytes(duration_sec: float = 1.0, sample_rate: int = 16000, frequency: float = 440.0) -> bytes:
    frames = int(duration_sec * sample_rate)
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        for index in range(frames):
            sample = int(32767 * math.sin(2 * math.pi * frequency * (index / sample_rate)))
            wav_file.writeframes(struct.pack("<h", sample))
    return buffer.getvalue()


def write_wav(path: Path, duration_sec: float = 1.0) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(make_wav_bytes(duration_sec=duration_sec))
    return path


@contextmanager
def workspace_temp_dir():
    scratch_dir = Path.cwd() / "scratch"
    scratch_dir.mkdir(parents=True, exist_ok=True)
    temp_dir = scratch_dir / f"test_{uuid.uuid4().hex}"
    temp_dir.mkdir(parents=True, exist_ok=True)
    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@contextmanager
def patched_config(base_dir: Path, **overrides):
    base_dir = Path(base_dir)
    data_dir = base_dir / "data"
    output_dir = base_dir / "output"
    metadata_dir = base_dir / "metadata"
    logs_dir = base_dir / "logs"
    values = {
        "BASE_DIR": base_dir,
        "DATA_DIR": data_dir,
        "OUTPUT_DIR": output_dir,
        "TEMP_PROCESSING_DIR": base_dir / "temp_processing",
        "RAW_AUDIO_DIR": base_dir / "Audio_Data",
        "STANDARDIZED_AUDIO_DIR": data_dir / "standardized",
        "CHUNKS_DIR": data_dir / "chunks",
        "CLEANED_DIR": data_dir / "cleaned",
        "TRANSCRIPTS_DIR": data_dir / "transcripts",
        "FINAL_DIR": data_dir / "final",
        "RESULTS_DIR": data_dir / "results",
        "OUTPUT_TRANSCRIPTS_DIR": output_dir / "transcripts",
        "OUTPUT_SUMMARIES_DIR": output_dir / "summaries",
        "LOGS_DIR": logs_dir,
        "METADATA_DIR": metadata_dir,
        "BILLING_DIR": metadata_dir / "billing",
        "PIPELINE_STATE_FILE": metadata_dir / "pipeline_state.json",
        "HASH_REGISTRY_FILE": metadata_dir / "audio_hash_registry.json",
        "AUDIO_QUALITY_AUDIT_FILE": metadata_dir / "audio_quality_audit.json",
        "AI_VALIDATION_LOG_FILE": logs_dir / "ai_validation.jsonl",
        "PERFORMANCE_REPORT_FILE": logs_dir / "performance_report.csv",
        "ENABLE_SPEECH_RESTORATION": False,
        "SEGMENT_THRESHOLD_SEC": 2,
        "CHUNK_LENGTH_SEC": 2,
        "CHUNK_LENGTH_MS": 2000,
        "OVERLAP_SEC": 1,
        "OVERLAP_MS": 1000,
        "MAX_CONCURRENT_CHUNKS": 2,
        "MIN_AUDIO_BYTES": 128,
        "MIN_AUDIO_DURATION_SEC": 0.1,
    }
    values.update(overrides)
    with patch.multiple(config, **values):
        yield
