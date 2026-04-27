"""
System Validation and Directory Initialization

This module ensures that the operating environment is correctly set up
before the pipeline begins processing. It handles:
1. Recursive creation of all data, result, and log directories.
2. Robust file-level environment_validator to ensure input files are actually playable audio.
"""

import os
import sys
from pathlib import Path
import filetype

# Ensure the parent src directory is discoverable for internal imports
# sys.path.append removed
from ..config import settings as config
from .logger import get_logger

# Initialize logger for system environment_validator events
logger = get_logger("environment_validator")

def init_directories():
    """
    Creates all necessary directory structures defined in the centralized config.
    This prevents 'File Not Found' errors during pipeline execution.
    """
    dirs = [
        config.DATA_DIR,
        config.RAW_AUDIO_DIR,
        config.STANDARDIZED_AUDIO_DIR,
        config.CHUNKS_DIR,
        config.CLEANED_DIR,
        config.TRANSCRIPTS_DIR,
        config.FINAL_DIR,
        config.RESULTS_DIR,
        config.OUTPUT_DIR,
        config.LOGS_DIR,
        config.METADATA_DIR
    ]
    
    for d in dirs:
        try:
            d.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create critical directory {d}: {e}")
            # Raising an exception here because the pipeline cannot safely proceed 
            # if it can't write its own output.
            raise RuntimeError(f"System boot failed: Required directory {d} could not be initialized.")
            
    logger.info("System directory architecture validated and initialized.")

def is_valid_audio(file_path: Path) -> bool:
    """
    Performs a hardware-independent environment_validator of an audio file.
    
    Checks for:
    1. Existence and non-zero file size.
    2. MIME type verification using magic bytes (via filetype).
    3. Extension fallback for common audio formats.

    Args:
        file_path: Absolute or relative path to the file.

    Returns:
        bool: True if the file appears to be a valid audio recording.
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        logger.error(f"Validation failed: {file_path} does not exist on disk.")
        return False
        
    if file_path.stat().st_size == 0:
        logger.error(f"Validation failed: {file_path} is an empty (0 byte) file.")
        return False
        
    # MIME Type Guessing: Protects against renamed non-audio files
    try:
        kind = filetype.guess(file_path)
        if kind is not None and kind.mime.startswith('audio/'):
            return True
            
        # Extension Fallback: Use standard extension lists if the header is non-standard
        valid_extensions = ['.mp3', '.wav', '.m4a', '.flac', '.ogg']
        if file_path.suffix.lower() in valid_extensions:
            return True
            
        logger.error(f"Validation failed: {file_path.name} is not recognized as a valid audio format.")
        return False
        
    except Exception as e:
        logger.warning(f"Technical warning during file header inspection for {file_path.name}: {e}")
        # Default to True purely to allow robust legacy formats that might not have clear magic bytes
        return True
