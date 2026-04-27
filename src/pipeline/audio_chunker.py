"""
Stage 02: Low-memory chunking using ffprobe + ffmpeg.
"""

from __future__ import annotations

import math
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List

from ..infrastructure.config import settings as config
from ..infrastructure.utils.environment_validator import get_audio_duration
from ..infrastructure.utils.logger import get_logger

logger = get_logger("audio_chunker")


@dataclass(frozen=True)
class ChunkMetadata:
    chunk_name: str
    chunk_index: int
    start_sec: float
    end_sec: float
    overlap_sec: float
    source_path: str
    path: Path
    is_temporary: bool

    def to_dict(self) -> dict:
        return {
            "chunk_name": self.chunk_name,
            "chunk_index": self.chunk_index,
            "start_sec": round(self.start_sec, 3),
            "end_sec": round(self.end_sec, 3),
            "overlap_sec": round(self.overlap_sec, 3),
            "source_path": self.source_path,
            "path": str(self.path),
            "is_temporary": self.is_temporary,
        }


def _export_chunk(input_file_path: Path, output_file: Path, start_sec: float, duration_sec: float) -> None:
    ffmpeg_bin = shutil.which("ffmpeg")
    if not ffmpeg_bin:
        raise RuntimeError("ffmpeg is not installed or not available on PATH.")

    command = [
        ffmpeg_bin,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-ss",
        f"{start_sec:.3f}",
        "-i",
        str(input_file_path),
        "-t",
        f"{duration_sec:.3f}",
        "-ar",
        str(config.TARGET_SAMPLE_RATE),
        "-ac",
        str(config.TARGET_CHANNELS),
        str(output_file),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        stderr = result.stderr.strip() or "Unknown ffmpeg error"
        raise RuntimeError(f"FFmpeg chunk export failed for {output_file.name}: {stderr}")


def chunk_audio(input_file_path: Path, output_dir: Path) -> List[ChunkMetadata]:
    input_file_path = Path(input_file_path)
    output_dir = Path(output_dir)
    duration_sec = get_audio_duration(input_file_path)

    logger.info(
        "Preparing chunk plan for '%s' (duration %.2fs, threshold %ss).",
        input_file_path.name,
        duration_sec,
        config.SEGMENT_THRESHOLD_SEC,
    )

    if duration_sec <= config.SEGMENT_THRESHOLD_SEC:
        return [
            ChunkMetadata(
                chunk_name="chunk_000",
                chunk_index=0,
                start_sec=0.0,
                end_sec=duration_sec,
                overlap_sec=0.0,
                source_path=str(input_file_path),
                path=input_file_path,
                is_temporary=False,
            )
        ]

    output_dir.mkdir(parents=True, exist_ok=True)
    chunk_length = float(config.CHUNK_LENGTH_SEC)
    overlap = float(config.OVERLAP_SEC)
    step = chunk_length - overlap
    if step <= 0:
        raise RuntimeError("Chunk overlap must be smaller than chunk length.")

    num_chunks = math.ceil(max(duration_sec - overlap, 0.0) / step)
    chunk_metadata: List[ChunkMetadata] = []
    for index in range(num_chunks):
        start_sec = index * step
        end_sec = min(start_sec + chunk_length, duration_sec)
        if index == num_chunks - 1 and (end_sec - start_sec) < 1.0 and num_chunks > 1:
            logger.debug(f"Discarding negligible tail chunk at index {index}.")
            break

        chunk_name = f"chunk_{index:03d}"
        output_file = output_dir / f"{input_file_path.stem}_{chunk_name}.wav"
        if not output_file.exists():
            _export_chunk(input_file_path, output_file, start_sec, end_sec - start_sec)

        chunk_metadata.append(
            ChunkMetadata(
                chunk_name=chunk_name,
                chunk_index=index,
                start_sec=start_sec,
                end_sec=end_sec,
                overlap_sec=overlap if index > 0 else 0.0,
                source_path=str(input_file_path),
                path=output_file,
                is_temporary=True,
            )
        )

    logger.info(f"Generated {len(chunk_metadata)} chunk definitions for '{input_file_path.name}'.")
    return chunk_metadata
