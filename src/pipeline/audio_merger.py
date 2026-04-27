"""
Stage 06: Cleaned Audio Merging

This stage takes independently processed audio fragments (which have been cleaned 
via Stage 03) and stitches them back together into a single, seamless 
full-length recording.

Key Logic:
1. Sorts fragments numerically to ensure chronological order.
2. Uses pydub.append with specific crossfade lengths matching the pipeline's 
   OVERLAP_MS setting. This ensures there are no audible 'clicks' or 'stutters' 
   at the fragment boundaries.
3. Exports a finalized 'Studio-Clean' master file for archiving or CRM playback.
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple

from pydub import AudioSegment

# Ensure internal modules are discoverable
sys.path.append(str(Path(__file__).parent.parent))
from ..infrastructure.config import settings as config
from ..infrastructure.utils.logger import get_logger

# Initialize stage-specific logger for monitoring audio stitching
logger = get_logger("audio_merger")

def merge_cleaned_audio(cleaned_dir: Path, output_file: Path, base_filename: str) -> Path:
    """
    Reconstructs the full audio stream from cleaned fragments.

    Args:
        cleaned_dir: Directory containing the cleaned chunk artifacts.
        output_file: Target path designated for the merged master file.
        base_filename: Filter key to find the correct chunks.

    Returns:
        Path: The file path to the finalized merged audio recording.

    Raises:
        RuntimeError: If audio files are unreadable or concatenation fails.
    """
    cleaned_dir = Path(cleaned_dir)
    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        logger.info(f"Merging cleaned fragments for '{base_filename}' [Seamless Stitching]...")
        
        # Locate fragments matching the specific lead file
        chunk_files_raw = list(cleaned_dir.glob(f"{base_filename}_chunk_*_cleaned.wav"))
        
        if not chunk_files_raw:
            logger.warning(f"No cleaned audio fragments found for {base_filename} in {cleaned_dir}.")
            return output_file
            
        # Extract numerical indices to ensure correct chronological sequence
        files_with_idx: List[Tuple[int, Path]] = []
        for file_path in chunk_files_raw:
            match = re.search(r"_chunk_(\d+)_cleaned.wav", file_path.name)
            if match:
                files_with_idx.append((int(match.group(1)), file_path))
                
        files_with_idx.sort(key=lambda x: x[0])
        sorted_files = [x[1] for x in files_with_idx]
        
        # Initialize master track with the first segment
        logger.debug(f"Loading seed fragment: {sorted_files[0].name}")
        combined_audio = AudioSegment.from_file(sorted_files[0])
        
        # Sequentially attach remaining segments with crossfade blending
        for file_path in sorted_files[1:]:
            next_chunk = AudioSegment.from_file(file_path)
            
            # The crossfade smoothly blends the overlapping boundary, 
            # effectively 'hiding' the join from the listener.
            # Safety check for extremely short fragments (though unlikely in this pipeline).
            if len(next_chunk) <= config.OVERLAP_MS:
                combined_audio = combined_audio + next_chunk
            else:
                combined_audio = combined_audio.append(next_chunk, crossfade=config.OVERLAP_MS)
                
        # Export the master cleaned version
        logger.info(f"Exporting finalized master cleaning to '{output_file.name}'...")
        combined_audio.export(output_file, format=config.TARGET_FORMAT)
        
        logger.info(f"Audio reconstruction complete. Master file stabilized.")
        return output_file
        
    except Exception as e:
        logger.error(f"Critical error during audio stream reconstruction for {base_filename}: {e}")
        raise
