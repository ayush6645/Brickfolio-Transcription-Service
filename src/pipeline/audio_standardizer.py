"""
Stage 01: Audio standardization via FFmpeg.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from ..infrastructure.config import settings as config
from ..infrastructure.utils.logger import get_logger

logger = get_logger("audio_standardizer")


def standardize_audio(input_file_path: Path, output_file_path: Path) -> Path:
    input_file_path = Path(input_file_path)
    output_file_path = Path(output_file_path)

    if output_file_path.exists():
        logger.info(f"Reusing standardized artifact '{output_file_path.name}'.")
        return output_file_path

    ffmpeg_bin = shutil.which("ffmpeg")
    if not ffmpeg_bin:
        raise RuntimeError("ffmpeg is not installed or not available on PATH.")

    output_file_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        ffmpeg_bin,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(input_file_path),
        "-ar",
        str(config.TARGET_SAMPLE_RATE),
        "-ac",
        str(config.TARGET_CHANNELS),
        str(output_file_path),
    ]

    logger.info(f"Standardizing '{input_file_path.name}' -> '{output_file_path.name}'")
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        stderr = result.stderr.strip() or "Unknown ffmpeg error"
        logger.error(f"FFmpeg conversion failed for {input_file_path.name}: {stderr}")
        raise RuntimeError(f"FFmpeg technical failure: {stderr}")

    return output_file_path
