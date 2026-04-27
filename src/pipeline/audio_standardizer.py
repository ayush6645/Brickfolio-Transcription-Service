"""
Stage 01: Audio Standardization

This stage ensures that all incoming audio files, regardless of their source 
format (MP3, WAV, M4A, etc.), are converted into a uniform internal format:
- Sample Rate: As defined in config (usually 16kHz for LLM/ASR compatibility)
- Channels: Mono (to simplify diarization processing)
- Format: WAV (container for lossless processing)

Leverages subprocess-level FFmpeg to handle extremely large files without 
risking Python memory saturation.
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

# Ensure internal modules are discoverable
sys.path.append(str(Path(__file__).parent.parent))
from ..infrastructure.config import settings as config
from ..infrastructure.utils.logger import get_logger

# Initialize stage-specific logger
logger = get_logger("audio_standardizer")

def standardize_audio(input_file_path: Path, output_file_path: Path) -> Path:
    """
    Normalizes an audio file using FFmpeg.

    Args:
        input_file_path: Path to the original source recording.
        output_file_path: Target path for the standardized WAV file.

    Returns:
        Path: The absolute path to the standardized file.

    Raises:
        RuntimeError: If FFmpeg fails or the file cannot be written.
    """
    input_file_path = Path(input_file_path)
    output_file_path = Path(output_file_path)
    
    try:
        logger.info(f"Standardizing '{input_file_path.name}' -> '{output_file_path.name}' [FFmpeg Stream]")
        
        # Ensure target directory exists for output
        output_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # FFmpeg Command Construction:
        # -y : Overwrite output without asking
        # -i : Input source
        # -ar: Force target audio sample rate (e.g., 16000)
        # -ac: Force target channels (1 = Mono)
        command = [
            "ffmpeg", "-y", "-i", str(input_file_path),
            "-ar", str(config.TARGET_SAMPLE_RATE),
            "-ac", str(config.TARGET_CHANNELS),
            str(output_file_path)
        ]
        
        # Execute conversion as a separate OS process to preserve memory
        result = subprocess.run(
            command, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode != 0:
            logger.error(f"FFmpeg conversion failed. Code: {result.returncode}")
            raise RuntimeError(f"FFmpeg technical failure: {result.stderr}")
            
        logger.info(f"Successfully normalized '{input_file_path.name}'. Ready for cleaning/transcription.")
        
        return output_file_path
        
    except Exception as e:
        logger.error(f"Critical error during audio standardization for {input_file_path}: {e}")
        raise
